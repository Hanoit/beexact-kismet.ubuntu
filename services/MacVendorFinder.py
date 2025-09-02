import os
import threading
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError, OperationalError
from models.DBKismetModels import MACVendorTable, MACsNotFoundTable
from utils import util
from repository.RepositoryImpl import RepositoryImpl
from dotenv import load_dotenv
import logging
import concurrent.futures
from collections import defaultdict
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('.env')

# ADAPTIVE CONFIGURATION FROM .ENV - OPTIMIZED FOR PERFORMANCE
# MacVendors plan configuration
PLAN_TYPE = os.getenv('MACVENDOR_PLAN_TYPE', 'free').lower()
REQUESTS_PER_SECOND = int(os.getenv('MACVENDOR_REQUESTS_PER_SECOND', '1' if PLAN_TYPE == 'free' else '25'))
REQUESTS_PER_DAY = int(os.getenv('MACVENDOR_REQUESTS_PER_DAY', '1000' if PLAN_TYPE == 'free' else '100000'))

# Adaptive rate limiting based on plan
MIN_API_INTERVAL = 1.0 / REQUESTS_PER_SECOND if REQUESTS_PER_SECOND > 0 else float(os.getenv('MACVENDOR_API_INTERVAL', '1.0'))
MACVENDOR_API_TIMEOUT = float(os.getenv('MACVENDOR_API_TIMEOUT', '8.0'))

# Optimized cache configuration
MACS_NOT_FOUND_CACHE_MONTHS = int(os.getenv('MACS_NOT_FOUND_CACHE_MONTHS', '6'))

# Batch processing configuration
BATCH_SIZE = int(os.getenv('MACVENDOR_BATCH_SIZE', '25'))
MAX_WORKERS = int(os.getenv('MACVENDOR_MAX_WORKERS', '25'))
BATCH_TIMEOUT = float(os.getenv('MACVENDOR_BATCH_TIMEOUT', '35.0'))

# Global variables for rate limiting and retry - OPTIMIZED
current_api_interval = MIN_API_INTERVAL
rate_limit_lock = threading.Lock()
api_call_lock = threading.Lock()
# Database lock - OPTIMIZED for batch operations
db_lock = threading.Lock()

# Configure logging
logger = logging.getLogger(__name__)

# Log configuration
VERBOSE_ADVANCE = bool(int(os.getenv('ADVANCE_VERBOSE', '0')))

# Database retry configuration
DB_RETRY_ATTEMPTS = int(os.getenv('DB_RETRY_ATTEMPTS', '3'))
DB_RETRY_DELAY = float(os.getenv('DB_RETRY_DELAY', '0.1'))  # 100ms base delay


def retry_db_operation(operation_func, max_attempts=DB_RETRY_ATTEMPTS, base_delay=DB_RETRY_DELAY):
    """
    Execute a database operation with retries in case of database lock
    """
    for attempt in range(max_attempts):
        try:
            return operation_func()
        except OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_attempts - 1:
                # Wait with exponential backoff + jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.05)
                time.sleep(delay)
                logger.debug(f"Database locked, retrying in {delay:.3f}s (attempt {attempt + 1}/{max_attempts})")
                continue
            else:
                raise e
        except Exception as e:
            raise e
    
    raise OperationalError("Database operation failed after all retry attempts", None, None)


logger.info("MacVendor API Configuration - ADAPTIVA Y OPTIMIZADA:")
logger.info(f"  - Plan Type: {PLAN_TYPE.upper()}")
logger.info(f"  - Requests per second: {REQUESTS_PER_SECOND}")
logger.info(f"  - Requests per day: {REQUESTS_PER_DAY}")
logger.info(f"  - API Interval: {MIN_API_INTERVAL:.3f}s ({1/MIN_API_INTERVAL:.1f} RPS)")
logger.info(f"  - API Timeout: {MACVENDOR_API_TIMEOUT}s")
logger.info(f"  - Batch Size: {BATCH_SIZE}")
logger.info(f"  - Max Workers: {MAX_WORKERS}")
logger.info(f"  - MACs Cache: {MACS_NOT_FOUND_CACHE_MONTHS} months")


def increase_rate_limit():
    """Increase the API call interval when rate limited - OPTIMIZADO"""
    global current_api_interval
    with rate_limit_lock:
        old_interval = current_api_interval
        # More aggressive increment for fast recovery
        current_api_interval = min(current_api_interval * 1.5, 2.0)  # Maximum 2s
        if old_interval != current_api_interval and VERBOSE_ADVANCE:
            logger.warning(f"⚠️ Rate limit hit! Increasing API interval to {current_api_interval:.3f}s")


def decrease_rate_limit():
    """Decrease the API call interval on successful calls - OPTIMIZADO"""
    global current_api_interval
    with rate_limit_lock:
        # More aggressive reduction for maximum performance
        current_api_interval = max(current_api_interval * 0.8, MIN_API_INTERVAL)


def fetch_vendor_from_api(mac_id, sequential_id):
    """
    Fetch vendor information from MacVendors API with adaptive rate limiting.
    
    Args:
        mac_id (str): MAC address formatted for API lookup (XX-XX-XX format)
        sequential_id (str): Sequential ID for tracking and logging purposes
        
    Returns:
        str: Vendor name if found, "NOT_FOUND" if MAC not in database, None on error
    """
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
        # 🚀 RATE LIMITING PARALELO - Sin lock para aprovechar 25 RPS
        # Solo esperar si es necesario (sin bloquear otros threads)
        if current_api_interval > 0:
            time.sleep(current_api_interval)
        
        # Make API call with optimized timeout and robust configuration
        response = requests.get(
            url,
            headers={**headers, 'Connection': 'close'},  # Evitar conexiones persistentes
            timeout=(MACVENDOR_API_TIMEOUT / 2, MACVENDOR_API_TIMEOUT),  # (connect, read)
            allow_redirects=False,  # Evitar redirecciones que puedan colgar
            stream=False  # No usar streaming
        )
        
        if response.ok:
            if api_token:
                # Paid API - JSON
                try:
                    decrease_rate_limit()  # Reduce interval on success
                    data = response.json()
                    return data.get('organization_name', None)
                except ValueError:
                    return response.text.strip()
            else:
                # Free API - plain text
                decrease_rate_limit()  # Reduce interval on success
                return response.text.strip()
        elif response.status_code == 429:
            # Rate limit exceeded - OPTIMIZED for fast recovery
            if VERBOSE_ADVANCE:
                seq_info = f" [{sequential_id}]" if sequential_id else ""
                logger.warning(f"MacVendor API rate limit exceeded for MAC {mac_id}{seq_info}| Response: {response.text}")
            # Increase rate limiting
            increase_rate_limit()
            # NO recursion - return None to avoid stack overflow
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
        """Process multiple MACs in parallel for better performance"""
        if not mac_addresses:
            return {}
        
        results = {}
        
        # Dividir en batches para evitar sobrecarga
        for i in range(0, len(mac_addresses), BATCH_SIZE):
            batch_macs = mac_addresses[i:i + BATCH_SIZE]
            batch_ids = sequential_ids[i:i + BATCH_SIZE] if sequential_ids else [None] * len(batch_macs)
            
            # Process batch in parallel with adaptive configuration
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(batch_macs), MAX_WORKERS)) as executor:
                future_to_mac = {
                    executor.submit(self.get_vendor, mac, seq_id): mac 
                    for mac, seq_id in zip(batch_macs, batch_ids)
                }
                
                # Manejo robusto de timeouts y futures pendientes
                completed_count = 0
                try:
                    for future in concurrent.futures.as_completed(future_to_mac, timeout=BATCH_TIMEOUT):
                        mac = future_to_mac[future]
                        try:
                            vendor = future.result()
                            results[mac] = vendor
                            completed_count += 1
                        except Exception as e:
                            logger.error(f"Error processing MAC {mac}: {e}")
                            results[mac] = None
                            completed_count += 1
                            
                except concurrent.futures.TimeoutError:
                    # Manejar futures que no completaron en el timeout
                    unfinished_count = len(future_to_mac) - completed_count
                    if unfinished_count > 0:
                        unfinished_macs = []
                        logger.error(f"Error in batch vendor lookup: {unfinished_count} (of {len(future_to_mac)}) futures unfinished after {BATCH_TIMEOUT}s timeout")
                        
                        # Cancelar futures pendientes y asignar None
                        for future, mac in future_to_mac.items():
                            if not future.done():
                                unfinished_macs.append(mac)
                                future.cancel()
                                results[mac] = None
                        
                        # Detailed logging for diagnostics
                        if VERBOSE_ADVANCE:
                            logger.warning(f"Unfinished MACs: {unfinished_macs[:3]}{'...' if len(unfinished_macs) > 3 else ''}")
                            logger.info(f"Batch config: size={len(batch_macs)}, workers={min(len(batch_macs), MAX_WORKERS)}, timeout={BATCH_TIMEOUT}s, api_timeout={MACVENDOR_API_TIMEOUT}s")
        
        return results

    def get_vendor(self, mac_address, sequential_id):
        mac_id = util.format_mac_id(mac_address, position=3, separator="-")
        # Usar la sesión existente por ahora para evitar complejidad adicional  
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
                
                def remove_expired():
                    with db_lock:
                        try:
                            not_found_repository.delete_by_id(mac_id)
                            self.__session.commit()
                        except Exception as e:
                            self.__session.rollback()
                            raise e
                
                try:
                    retry_db_operation(remove_expired)
                except Exception as e:
                    logger.error(f"Error removing expired NOT_FOUND record for MAC {mac_id}: {e}")

        # 3. Si no está en cache o expiró, consultar API
        try:
            vendor_name = fetch_vendor_from_api(mac_id, sequential_id)
        except Exception as e:
            logger.error(f"MacVendor Api does not work: \n {e}")
            return None

        if vendor_name == "NOT_FOUND" or vendor_name == "Unknown":

            # MAC no encontrada - guardar o actualizar en tabla NOT_FOUND
            def save_not_found():
                with db_lock:
                    try:
                        if not_found_record:
                            # Actualizar fecha de consulta del registro existente
                            not_found_record.last_consulted = datetime.utcnow()
                            self.__session.merge(not_found_record)  # merge en lugar de commit directo
                            self.__session.commit()
                            if VERBOSE_ADVANCE:
                                seq_info = f" [{sequential_id}]" if sequential_id else ""
                                logger.info(f"Updated NOT_FOUND cache date for MAC {mac_id}{seq_info}")
                        else:
                            # Verificar si ya existe antes de crear (thread-safe)
                            existing = not_found_repository.search_by_id(mac_id)
                            if not existing:
                                new_not_found = MACsNotFoundTable(id=mac_id, last_consulted=datetime.utcnow())
                                self.__session.merge(new_not_found)  # merge para evitar conflictos
                                self.__session.commit()
                                if VERBOSE_ADVANCE:
                                    seq_info = f" [{sequential_id}]" if sequential_id else ""
                                    logger.info(f"Added MAC {mac_id}{seq_info} to NOT_FOUND cache")
                    except IntegrityError:
                        self.__session.rollback()
                        # Conflicto de integridad - otro thread ya creó el registro
                        if VERBOSE_ADVANCE:
                            logger.debug(f"MAC {mac_id} already exists in NOT_FOUND cache (created by another thread)")
                    except Exception as e:
                        self.__session.rollback()
                        raise e
            
            try:
                retry_db_operation(save_not_found)
            except Exception as e:
                logger.error(f"Error saving NOT_FOUND record for MAC {mac_id}: {e}")
            
            return None
        elif vendor_name:

            # Vendor encontrado - guardar en tabla de vendors
            def save_vendor():
                with db_lock:
                    try:
                        # Verificar si ya existe antes de crear
                        existing_vendor = vendor_repository.search_by_id(mac_id)
                        if not existing_vendor:
                            new_vendor = MACVendorTable(id=mac_id, vendor_name=vendor_name)
                            self.__session.merge(new_vendor)  # merge para evitar conflictos
                            self.__session.commit()
                    except IntegrityError:
                        self.__session.rollback()
                        # Otro thread ya creó el vendor
                        pass
                    except Exception as e:
                        self.__session.rollback()
                        raise e
            
            try:
                retry_db_operation(save_vendor)
            except Exception as e:
                logger.error(f"Error saving vendor for MAC {mac_id}: {e}")
            
            return vendor_name  # Retornar el vendor aunque no se pudo guardar
        
        return None
