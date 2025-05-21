import os
import threading
import time
import requests
from sqlalchemy.exc import IntegrityError
from models.DBKismetModels import MACVendorTable
from utils import util
from repository.RepositoryImpl import RepositoryImpl
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_lock = threading.Lock()
api_lock = threading.Lock()
last_api_call = 0
MIN_API_INTERVAL = 0.1  # Minimum 100ms between API calls

# Load environment variables from .env file
load_dotenv()


def fetch_vendor_from_api(mac_id):
    global last_api_call
    
    # Rate limiting
    with api_lock:
        current_time = time.time()
        time_since_last_call = current_time - last_api_call
        if time_since_last_call < MIN_API_INTERVAL:
            sleep_time = MIN_API_INTERVAL - time_since_last_call
            time.sleep(sleep_time)
        last_api_call = time.time()
    
    # Reemplaza 'Your_API_Token' con tu token real
    api_token = os.getenv('API_KEY_MACVENDOR', None)
    url = f"https://api.macvendors.com/v1/lookup/{mac_id}" if api_token else f"https://api.macvendors.com/{mac_id}"

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/json'
    } if api_token else {}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.ok:
            try:
                data = response.json()
                # Try to get organization_name from the new API format
                if 'data' in data and 'organization_name' in data['data']:
                    return data['data']['organization_name']
                elif 'organization_name' in data:
                    return data['organization_name']
                else:
                    # Fallback to plain text response (old API format)
                    return response.text.strip()
            except ValueError as e:
                # If JSON parsing fails, try plain text response
                logger.debug(f"JSON parse failed for MAC {mac_id}, trying plain text: {response.text}")
                return response.text.strip() if response.text.strip() else None
        elif response.status_code == 404:
            # MAC not found in database - this is normal for many MACs
            logger.debug(f"MAC {mac_id} not found in MacVendor database (404)")
            return None
        elif response.status_code != 404:  # Don't log 404s as warnings since they're normal
            logger.warning(f"MacVendor API returned status {response.status_code} for MAC {mac_id}: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Request exception for MAC {mac_id}: {e}")
        raise e
    return None


class MacVendorFinder:

    def __init__(self, session):
        self.__session = session

    def get_vendor(self, mac_address):
        mac_id = util.format_mac_id(mac_address, position=3, separator="-")
        vendor_repository = RepositoryImpl(MACVendorTable, self.__session)

        with db_lock:
            cached_vendor = vendor_repository.search_by_id(mac_id)

        if cached_vendor:
            return cached_vendor.vendor_name

        try:
            # Fetch from API if not cached
            vendor_name = fetch_vendor_from_api(mac_id)
        except Exception as e:
            logger.error(f"MacVendor Api does not work: \n {e}")
            return None

        if vendor_name:
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
