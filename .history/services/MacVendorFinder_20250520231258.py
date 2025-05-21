import os
import threading
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

# Load environment variables from .env file
load_dotenv()


def fetch_vendor_from_api(mac_id):
    # Reemplaza 'Your_API_Token' con tu token real
    api_token = os.getenv('API_KEY_MACVENDOR', None)
    url = f"https://api.macvendors.com/v1/lookup/{mac_id}" if api_token else f"https://api.macvendors.com/{mac_id}"

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/json'
    } if api_token else {}

    try:
        response = requests.get(url, headers=headers)
        if response.ok:
            try:
                data = response.json()
                return data.get('organization_name', None)
            except ValueError as e:
                logger.error(f"JSON parse failed for MAC {mac_id}: {response.text}")
                return None
        else:
            logger.warning(f"MacVendor API returned status {response.status_code} for MAC {mac_id}: {response.text}")
    except requests.RequestException as e:
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
