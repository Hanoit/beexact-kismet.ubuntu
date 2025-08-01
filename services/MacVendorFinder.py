import os
import threading
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from models.DBKismetModels import MACVendorTable, MACsNotFoundTable
from utils import util
from repository.RepositoryImpl import RepositoryImpl
from dotenv import load_dotenv
import logging
import concurrent.futures
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('.env')

# Rate limiting and retry configuration - OPTIMIZADO PARA PERFORMANCE
MIN_API_INTERVAL = float(os.getenv('MACVENDOR_API_INTERVAL', '0.05'))  # 50ms por defecto (AGRESIVO)
MACVENDOR_API_TIMEOUT = float(os.getenv('MACVENDOR_API_TIMEOUT', '5.0'))  # 5s timeout (OPTIMIZADO)
# MACs Not Found cache configuration
MACS_NOT_FOUND_CACHE_MONTHS = int(os.getenv('MACS_NOT_FOUND_CACHE_MONTHS', '6'))  # 6 meses por defecto

# Global variables for rate limiting and retry - OPTIMIZADOS
current_api_interval = MIN_API_INTERVAL
rate_limit_lock = threading.Lock()
api_call_lock = threading.Lock()
# Database lock - OPTIMIZADO para batch operations
db_lock = threading.Lock()

# Configure logging
logger = logging.getLogger(__name__)

# Log configuration
VERBOSE_ADVANCE = bool(int(os.getenv('ADVANCE_VERBOSE', '0')))
logger.info("MacVendor API Configuration - PERFORMANCE OPTIMIZED:")
logger.info(f"  - Initial API Interval: {MIN_API_INTERVAL}s between calls (AGGRESSIVE)")
logger.info(f"  - API Timeout: {MACVENDOR_API_TIMEOUT}s (OPTIMIZED)")
logger.info(f"  - MACs Not Found Cache: {MACS_NOT_FOUND_CACHE_MONTHS} months")


def increase_rate_limit():
    """Increase the API call interval when rate limited - OPTIMIZADO"""
    global current_api_interval
    with rate_limit_lock:
        old_interval = current_api_interval
        # Incremento más agresivo para recuperación rápida
        current_api_interval = min(current_api_interval * 1.5, 2.0)  # Máximo 2s
        if old_interval != current_api_interval and VERBOSE_ADVANCE:
            logger.warning(f"⚠️ Rate limit hit! Increasing API interval to {current_api_interval:.3f}s")


def decrease_rate_limit():
    """Decrease the API call interval on successful calls - OPTIMIZADO"""
    global current_api_interval
    with rate_limit_lock:
        # Reducción más agresiva para máximo performance
        current_api_interval = max(current_api_interval * 0.8, MIN_API_INTERVAL)


def fetch_vendor_from_api(mac_id, sequential_id):
    global current_api_interval

    # Get API token
    api_token = os.getenv('API_KEY_MACVENDOR', None)
    
    # Use the correct API endpoint based on documentation
    if api_token:
        url = f"https://api.macvendors.com/v1/lookup/{mac_id}"
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json'
        }
    else:
        # Free API endpoint - returns plain text
        url = f"https://api.macvendors.com/{mac_id}"
        headers = {}

    try:
        # 🔒 LOCK OPTIMIZADO para controlar acceso a la API
        with api_call_lock:
            # Esperar el intervalo mínimo DENTRO del lock (OPTIMIZADO)
            if current_api_interval > 0:
                time.sleep(current_api_interval)
            
            # Hacer la llamada a la API con timeout optimizado
            response = requests.get(url, headers=headers, timeout=MACVENDOR_API_TIMEOUT)
        
        if response.ok:
            if api_token:
                # Paid API - JSON
                try:
                    decrease_rate_limit()  # Reducir intervalo en éxito
                    data = response.json()
                    return data.get('organization_name', None)
                except ValueError:
                    return response.text.strip()
            else:
                # Free API - plain text
                decrease_rate_limit()  # Reducir intervalo en éxito
                return response.text.strip()
        elif response.status_code == 429:
            # Rate limit exceeded - OPTIMIZADO para recuperación rápida
            if VERBOSE_ADVANCE:
                seq_info = f" [{sequential_id}]" if sequential_id else ""
                logger.warning(f"MacVendor API rate limit exceeded for MAC {mac_id}{seq_info}| Response: {response.text}")
            # Increase rate limiting
            increase_rate_limit()
            # NO recursión - retornar None para evitar stack overflow
            return None
        elif response.status_code == 404:
            # MAC not found - return special value to indicate this
            return "NOT_FOUND"
        else:
            if VERBOSE_ADVANCE:
                # Other errors - log and return None
                seq_info = f" [{sequential_id}]" if sequential_id else ""
                logger.warning(f"MacVendor API returned status {response.status_code} for MAC {mac_id}{seq_info}: {response.text}")
            return None
    except ValueError as e:
        seq_info = f" [{sequential_id}]" if sequential_id else ""
        logger.debug(f"JSON parse failed for MAC {mac_id}{seq_info}, trying plain text: {response.text}")
        return None
    except requests.RequestException as e:
        # Network errors - log and return None
        seq_info = f" [{sequential_id}]" if sequential_id else ""
        logger.error(f"Request exception for MAC {mac_id}{seq_info}: {e}")
        return None


class MacVendorFinder:

    def __init__(self, session):
        self.__session = session
        self.__batch_cache = defaultdict(dict)  # Cache para batch processing

    def process_mac_batch(self, mac_addresses, sequential_ids):
        """Procesar múltiples MACs en paralelo para mejor performance"""
        if not mac_addresses:
            return {}
        
        results = {}
        
        # Dividir en batches para evitar sobrecarga
        for i in range(0, len(mac_addresses), BATCH_SIZE):
            batch_macs = mac_addresses[i:i + BATCH_SIZE]
            batch_ids = sequential_ids[i:i + BATCH_SIZE] if sequential_ids else [None] * len(batch_macs)
            
            # Procesar batch en paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(batch_macs), 10)) as executor:
                future_to_mac = {
                    executor.submit(self.get_vendor, mac, seq_id): mac 
                    for mac, seq_id in zip(batch_macs, batch_ids)
                }
                
                for future in concurrent.futures.as_completed(future_to_mac, timeout=BATCH_TIMEOUT):
                    mac = future_to_mac[future]
                    try:
                        vendor = future.result()
                        results[mac] = vendor
                    except Exception as e:
                        logger.error(f"Error processing MAC {mac}: {e}")
                        results[mac] = None
        
        return results

    def get_vendor(self, mac_address, sequential_id):
        mac_id = util.format_mac_id(mac_address, position=3, separator="-")
        vendor_repository = RepositoryImpl(MACVendorTable, self.__session)
        not_found_repository = RepositoryImpl(MACsNotFoundTable, self.__session)

        # 1. Primero buscar en la tabla de vendors
        with db_lock:
            cached_vendor = vendor_repository.search_by_id(mac_id)

        if cached_vendor:
            return cached_vendor.vendor_name

        # 2. Si no existe vendor, consultar en la tabla de MACs no encontradas
        with db_lock:
            not_found_record = not_found_repository.search_by_id(mac_id)

        if not_found_record:
            # Calcular si ha pasado el tiempo de cache
            cache_expiry_date = not_found_record.last_consulted + timedelta(days=MACS_NOT_FOUND_CACHE_MONTHS * 30)
            current_time = datetime.utcnow()
            
            if current_time < cache_expiry_date:
                # MAC está en cache y no ha expirado - retornar None sin consultar API
                if VERBOSE_ADVANCE:
                    seq_info = f" [{sequential_id}]" if sequential_id else ""
                    logger.info(f"MAC {mac_id}{seq_info} found in NOT_FOUND cache (expires in {cache_expiry_date - current_time})")
                return None
            else:
                # Cache expirado - eliminar registro y continuar con API
                if VERBOSE_ADVANCE:
                    seq_info = f" [{sequential_id}]" if sequential_id else ""
                    logger.info(f"MAC {mac_id}{seq_info} NOT_FOUND cache expired, removing and retrying API")
                with db_lock:
                    try:
                        not_found_repository.delete_by_id(mac_id)
                        self.__session.commit()
                    except Exception as e:
                        self.__session.rollback()
                        logger.error(f"Error removing expired NOT_FOUND record for MAC {mac_id}: {e}")

        # 3. Si no está en cache o expiró, consultar API
        try:
            vendor_name = fetch_vendor_from_api(mac_id, sequential_id)
        except Exception as e:
            logger.error(f"MacVendor Api does not work: \n {e}")
            return None

        if vendor_name == "NOT_FOUND":
            # MAC no encontrada - guardar o actualizar en tabla NOT_FOUND
            with db_lock:
                try:
                    if not_found_record:
                        # Actualizar fecha de consulta
                        not_found_record.last_consulted = datetime.utcnow()
                        self.__session.commit()
                        if VERBOSE_ADVANCE:
                            seq_info = f" [{sequential_id}]" if sequential_id else ""
                            logger.info(f"Updated NOT_FOUND cache date for MAC {mac_id}{seq_info}")
                    else:
                        # Crear nuevo registro
                        new_not_found = MACsNotFoundTable(id=mac_id, last_consulted=datetime.utcnow())
                        self.__session.add(new_not_found)
                        self.__session.commit()
                        if VERBOSE_ADVANCE:
                            seq_info = f" [{sequential_id}]" if sequential_id else ""
                            logger.info(f"Added MAC {mac_id}{seq_info} to NOT_FOUND cache")
                except IntegrityError:
                    self.__session.rollback()
                    # Si hay conflicto de integridad, intentar actualizar
                    try:
                        existing_record = not_found_repository.search_by_id(mac_id)
                        if existing_record:
                            existing_record.last_consulted = datetime.utcnow()
                            self.__session.commit()
                    except Exception as e:
                        self.__session.rollback()
                        logger.error(f"Error updating NOT_FOUND record for MAC {mac_id}: {e}")
                except Exception as e:
                    self.__session.rollback()
                    logger.error(f"Error saving NOT_FOUND record for MAC {mac_id}: {e}")
            
            return None
        elif vendor_name:
            # Vendor encontrado - guardar en tabla de vendors
            with db_lock:
                try:
                    new_vendor = MACVendorTable(id=mac_id, vendor_name=vendor_name)
                    self.__session.add(new_vendor)
                    self.__session.commit()
                    return vendor_name
                except IntegrityError:
                    self.__session.rollback()
                    return vendor_name
                except Exception as e:
                    self.__session.rollback()  # Rollback on general exceptions
                    raise e
        
        return None
