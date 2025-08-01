import os
import threading
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from models.DBKismetModels import MACVendorTable
from utils import util
from repository.RepositoryImpl import RepositoryImpl
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('.env')

# Rate limiting and retry configuration
MIN_API_INTERVAL = float(os.getenv('MACVENDOR_API_INTERVAL', '3.0'))
API_TIMEOUT = float(os.getenv('MACVENDOR_API_TIMEOUT', '20.0'))
MAX_QUEUE_SIZE = 50  # Maximum failed MACs in queue
MAX_CONSECUTIVE_FAILURES = 10  # Circuit breaker threshold
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes circuit breaker timeout

# Rate-limited cache configuration
RATE_LIMITED_CACHE_DAYS = int(os.getenv('MACVENDOR_RATE_LIMITED_CACHE_DAYS', '7'))  # Default 7 days

# Global variables for rate limiting and retry
current_api_interval = MIN_API_INTERVAL
rate_limit_lock = threading.Lock()
api_lock = threading.Lock()
last_api_call = 0

# API capacity measurement
api_capacity_interval = MIN_API_INTERVAL
api_capacity_lock = threading.Lock()

# Failed MACs queue with size limit
failed_macs_queue = []
failed_macs_lock = threading.Lock()

# Circuit breaker for API failures
consecutive_failures = 0
circuit_breaker_last_failure = 0
circuit_breaker_lock = threading.Lock()

# API cache
api_cache = {}
api_cache_lock = threading.Lock()

# Database lock
db_lock = threading.Lock()

# MAC processing locks
mac_locks = {}
mac_locks_lock = threading.Lock()
macs_in_process = set()
macs_in_process_lock = threading.Lock()

# Global set to track MACs currently being processed (prevents race conditions)
macs_in_process = set()
macs_in_process_lock = threading.Lock()

# Configure logging
logger = logging.getLogger(__name__)

# Log configuration
logger.info("MacVendor API Configuration:")
logger.info(f"  - Initial API Interval: {MIN_API_INTERVAL}s between calls")
logger.info(f"  - API Timeout: {API_TIMEOUT}s")
logger.info(f"  - Max Queue Size: {MAX_QUEUE_SIZE} failed MACs")
logger.info(f"  - Circuit Breaker: {MAX_CONSECUTIVE_FAILURES} consecutive failures")
logger.info(f"  - Circuit Breaker Timeout: {CIRCUIT_BREAKER_TIMEOUT}s")


def check_circuit_breaker():
    """Check if circuit breaker is open due to consecutive failures"""
    global consecutive_failures, circuit_breaker_last_failure
    
    with circuit_breaker_lock:
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            current_time = time.time()
            time_since_failure = current_time - circuit_breaker_last_failure
            
            if time_since_failure < CIRCUIT_BREAKER_TIMEOUT:
                # Only log once when circuit breaker opens
                if time_since_failure < 1:  # Log only in the first second
                    remaining_time = CIRCUIT_BREAKER_TIMEOUT - time_since_failure
                    logger.warning(f"🚨 Circuit breaker OPEN - API appears down. Waiting {remaining_time:.0f}s before retry")
                return True
            else:
                # Reset circuit breaker
                consecutive_failures = 0
                logger.info("✅ Circuit breaker CLOSED - attempting API calls again")
                return False
        return False


def record_api_failure():
    """Record an API failure for circuit breaker"""
    global consecutive_failures, circuit_breaker_last_failure
    
    with circuit_breaker_lock:
        consecutive_failures += 1
        circuit_breaker_last_failure = time.time()
        
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.error(f"🚨 Circuit breaker TRIGGERED after {consecutive_failures} consecutive failures")


def record_api_success():
    """Record an API success to reset circuit breaker"""
    global consecutive_failures
    
    with circuit_breaker_lock:
        if consecutive_failures > 0:
            logger.info(f"✅ API success - resetting consecutive failures counter ({consecutive_failures} -> 0)")
            consecutive_failures = 0


def increase_rate_limit():
    """Increase the API call interval when rate limited"""
    global current_api_interval
    with rate_limit_lock:
        old_interval = current_api_interval
        current_api_interval = min(current_api_interval * 2, 60.0)
        if old_interval != current_api_interval:
            logger.warning(f"⚠️ Rate limit hit! Increasing API interval to {current_api_interval:.1f}s")


def decrease_rate_limit():
    """Decrease the API call interval on successful calls"""
    global current_api_interval
    with rate_limit_lock:
        if current_api_interval > MIN_API_INTERVAL:
            old_interval = current_api_interval
            current_api_interval = max(current_api_interval * 0.8, MIN_API_INTERVAL)
            if old_interval != current_api_interval:
                logger.info(f"📈 API calls successful, decreasing interval to {current_api_interval:.1f}s")


def measure_api_capacity():
    """Measure API capacity by testing with a known MAC"""
    global api_capacity_interval
    
    # Test with a known MAC to measure response time
    test_mac = "00-11-22-33-44-55"  # Known vendor
    
    try:
        start_time = time.time()
        
        # Get API token
        api_token = os.getenv('API_KEY_MACVENDOR', None)
        
        if api_token:
            url = f"https://api.macvendors.com/v1/lookup/{test_mac}"
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Accept': 'application/json'
            }
        else:
            url = f"https://api.macvendors.com/{test_mac}"
            headers = {}
        
        response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            # API is working, measure optimal interval
            response_time = time.time() - start_time
            
            # Calculate safe interval based on response time
            # Add buffer to prevent rate limiting
            safe_interval = max(response_time * 2, MIN_API_INTERVAL)
            
            with api_capacity_lock:
                api_capacity_interval = min(safe_interval, 10.0)  # Cap at 10 seconds
            
            logger.info(f"📊 API capacity measured: {api_capacity_interval:.1f}s interval")
            record_api_success()
            return True
            
        elif response.status_code == 429:
            # Still rate limited, increase interval
            with api_capacity_lock:
                api_capacity_interval = min(api_capacity_interval * 1.5, 30.0)
            logger.warning(f"⚠️ API still rate limited, increasing interval to {api_capacity_interval:.1f}s")
            record_api_failure()
            return False
            
        elif response.status_code == 522:
            # Cloudflare timeout - API is down
            logger.error("🚨 API test failed with 522 (Cloudflare timeout) - API appears to be down")
            record_api_failure()
            return False
            
        else:
            # Other error, use conservative interval
            with api_capacity_lock:
                api_capacity_interval = 15.0
            logger.warning(f"⚠️ API test failed with status {response.status_code}, using conservative interval")
            record_api_failure()
            return False
            
    except Exception as e:
        logger.error(f"🚨 Error measuring API capacity: {e}")
        with api_capacity_lock:
            api_capacity_interval = 15.0
        record_api_failure()
        return False


def add_failed_mac(mac_id, sequential_id=None):
    """Add a failed MAC to the retry queue with size limit"""
    with failed_macs_lock:
        # Check if queue is full
        if len(failed_macs_queue) >= MAX_QUEUE_SIZE:
            # Remove oldest entry to make room
            removed_mac, _ = failed_macs_queue.pop(0)
            logger.warning(f"🔄 Queue full ({MAX_QUEUE_SIZE}), removing oldest MAC: {removed_mac}")
        
        failed_macs_queue.append((mac_id, sequential_id))
        # Only log queue size every 10 additions to reduce verbosity
        if len(failed_macs_queue) % 10 == 0:
            logger.info(f"📋 Retry queue size: {len(failed_macs_queue)} MACs")


def retry_failed_macs():
    """Retry all failed MACs with measured capacity"""
    global failed_macs_queue
    
    if not failed_macs_queue:
        return
    
    queue_size = len(failed_macs_queue)
    logger.info(f"🔄 Retrying {queue_size} failed MACs...")
    
    # Get current capacity interval
    with api_capacity_lock:
        retry_interval = api_capacity_interval
    
    # Process failed MACs
    retry_results = {}
    success_count = 0
    failure_count = 0
    
    for i, (mac_id, sequential_id) in enumerate(failed_macs_queue, 1):
        # Only log progress every 10 retries to reduce verbosity
        if i % 10 == 0 or i == queue_size:
            logger.info(f"📊 Retry progress: {i}/{queue_size} MACs")
        
        # Wait for the measured interval
        time.sleep(retry_interval)
        
        # Retry the API call
        try:
            result = fetch_vendor_from_api(mac_id, sequential_id)
            retry_results[mac_id] = result
            
            if result and result != "RATE_LIMITED":
                success_count += 1
            else:
                failure_count += 1
                
        except Exception as e:
            logger.error(f"Retry exception for MAC {mac_id}: {e}")
            retry_results[mac_id] = f"ERROR: {e}"
            failure_count += 1
    
    # Clear the queue
    with failed_macs_lock:
        failed_macs_queue.clear()
    
    logger.info(f"✅ Retry completed: {success_count} successful, {failure_count} failed")
    return retry_results


def fetch_vendor_from_api(mac_id, sequential_id=None):
    """Fetch vendor information from MacVendor API with intelligent retry"""
    global last_api_call
    
    # Check circuit breaker first
    if check_circuit_breaker():
        # Don't log individual MAC skips - circuit breaker status already logged
        return "RATE_LIMITED"
    
    # Check cache first
    with api_cache_lock:
        if mac_id in api_cache:
            seq_info = f" [{sequential_id}]" if sequential_id else ""
            logger.debug(f"MAC {mac_id}{seq_info} found in cache: {api_cache[mac_id]}")
            return api_cache[mac_id]
    
    # Dynamic rate limiting
    with api_lock:
        current_time = time.time()
        time_since_last_call = current_time - last_api_call
        
        # Use current dynamic interval
        with rate_limit_lock:
            wait_time = current_api_interval
        
        if time_since_last_call < wait_time:
            sleep_time = wait_time - time_since_last_call
            seq_info = f" [{sequential_id}]" if sequential_id else ""
            logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s before next API call{seq_info}")
            time.sleep(sleep_time)
        last_api_call = time.time()
    
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
        response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
        
        if response.ok:
            # Handle response based on API type
            if api_token:
                # Paid API - returns JSON
                try:
                    data = response.json()
                    # Try to get organization_name from the new API format
                    if 'data' in data and 'organization_name' in data['data']:
                        result = data['data']['organization_name']
                    elif 'organization_name' in data:
                        result = data['organization_name']
                    else:
                        # Fallback to plain text response
                        result = response.text.strip()
                except ValueError as e:
                    # If JSON parsing fails, try plain text response
                    seq_info = f" [{sequential_id}]" if sequential_id else ""
                    logger.debug(f"JSON parse failed for MAC {mac_id}{seq_info}, trying plain text: {response.text}")
                    result = response.text.strip() if response.text.strip() else None
            else:
                # Free API - returns plain text directly
                result = response.text.strip()
            
            # Successful call - gradually decrease rate limit
            decrease_rate_limit()
            record_api_success()
            
            # Cache the result
            with api_cache_lock:
                api_cache[mac_id] = result
            return result
                
        elif response.status_code == 404:
            # MAC not found in database - this is normal for many MACs
            seq_info = f" [{sequential_id}]" if sequential_id else ""
            logger.debug(f"MAC {mac_id}{seq_info} not found in MacVendor database (404)")
            
            # 404 is not a rate limit issue, so we can decrease rate limit
            decrease_rate_limit()
            record_api_success()
            
            with api_cache_lock:
                api_cache[mac_id] = None
            return None
            
        elif response.status_code == 429:
            # Rate limit exceeded - measure capacity and add to retry queue
            seq_info = f" [{sequential_id}]" if sequential_id else ""
            logger.warning(f"MacVendor API rate limit exceeded for MAC {mac_id}{seq_info}")
            logger.warning(f"Response: {response.text}")
            
            # Record failure for circuit breaker
            record_api_failure()
            
            # Increase rate limiting
            increase_rate_limit()
            
            # Add to failed queue for immediate retry
            add_failed_mac(mac_id, sequential_id)
            
            # Measure API capacity
            if measure_api_capacity():
                # Retry failed MACs immediately with measured capacity
                retry_failed_macs()
            
            with api_cache_lock:
                api_cache[mac_id] = "RATE_LIMITED"
            return "RATE_LIMITED"
                
        elif response.status_code == 522:
            # Cloudflare timeout - API is down
            seq_info = f" [{sequential_id}]" if sequential_id else ""
            logger.error(f"MacVendor API returned 522 (Cloudflare timeout) for MAC {mac_id}{seq_info} - API appears to be down")
            
            # Record failure for circuit breaker
            record_api_failure()
            
            with api_cache_lock:
                api_cache[mac_id] = "RATE_LIMITED"
            return "RATE_LIMITED"
            
        else:
            # Other errors - log and return None
            seq_info = f" [{sequential_id}]" if sequential_id else ""
            logger.warning(f"MacVendor API returned status {response.status_code} for MAC {mac_id}{seq_info}: {response.text}")
            
            # Record failure for circuit breaker on server errors
            if response.status_code >= 500:
                record_api_failure()
            
            # For other errors, don't change rate limit
            with api_cache_lock:
                api_cache[mac_id] = None
            return None
            
    except requests.RequestException as e:
        # Network errors - log and return None
        seq_info = f" [{sequential_id}]" if sequential_id else ""
        logger.error(f"Request exception for MAC {mac_id}{seq_info}: {e}")
        
        # Record failure for circuit breaker on network errors
        record_api_failure()
        
        # For network errors, don't change rate limit
        with api_cache_lock:
            api_cache[mac_id] = None
        return None
    
    return None


class MacVendorFinder:

    def __init__(self, session):
        self.__session = session

    def get_vendor(self, mac_address, sequential_id=None):
        # Format the MAC for database storage (maintains legacy compatibility)
        mac_id = util.format_mac_id(mac_address, position=3, separator="-")
        # Format the full MAC for API lookup
        full_mac_id = util.format_mac_id(mac_address, separator="-")
        
        vendor_repository = RepositoryImpl(MACVendorTable, self.__session)
        seq_info = f" [{sequential_id}]" if sequential_id else ""

        # Check if this MAC is already being processed by another thread
        with macs_in_process_lock:
            if mac_id in macs_in_process:
                logger.debug(f"MAC {mac_id}{seq_info} is already being processed by another thread, waiting...")
                # Wait for the other thread to finish processing this MAC
                while mac_id in macs_in_process:
                    macs_in_process_lock.release()
                    time.sleep(0.1)  # Small delay to avoid busy waiting
                    macs_in_process_lock.acquire()
                
                # Now check the database for the result
                with db_lock:
                    cached_vendor = vendor_repository.search_by_id(mac_id)
                    if cached_vendor:
                        logger.debug(f"MAC {mac_id}{seq_info} was processed by another thread: {cached_vendor.vendor_name}")
                        return cached_vendor.vendor_name

            # Mark this MAC as being processed
            macs_in_process.add(mac_id)

        try:
            # Get or create MAC-specific lock to prevent duplicate insertions
            with mac_locks_lock:
                if mac_id not in mac_locks:
                    mac_locks[mac_id] = threading.Lock()
                mac_lock = mac_locks[mac_id]

            # Use MAC-specific lock for the entire operation
            with mac_lock:
                # Check database cache first - try both legacy and full MAC formats
                with db_lock:
                    cached_vendor = vendor_repository.search_by_id(mac_id)
                    if not cached_vendor:
                        # Try full MAC format for error cases
                        cached_vendor = vendor_repository.search_by_id(full_mac_id)

                if cached_vendor:
                    # Check if this is a rate-limited MAC and if we should retry
                    if cached_vendor.vendor_name == "RATE_LIMITED":
                        # Check if enough time has passed to retry
                        if cached_vendor.last_consulted:
                            days_since_last_consult = (datetime.utcnow() - cached_vendor.last_consulted).days
                            if days_since_last_consult >= RATE_LIMITED_CACHE_DAYS:
                                logger.info(f"MAC {cached_vendor.id}{seq_info} was rate-limited {days_since_last_consult} days ago, retrying...")
                                # Remove from cache to force API call
                                with db_lock:
                                    try:
                                        self.__session.delete(cached_vendor)
                                        self.__session.commit()
                                    except Exception as e:
                                        self.__session.rollback()
                                        logger.error(f"Error removing rate-limited MAC {cached_vendor.id}: {e}")
                            else:
                                logger.debug(f"MAC {cached_vendor.id}{seq_info} still rate-limited (last consulted {days_since_last_consult} days ago)")
                                return "RATE_LIMITED"
                        else:
                            # No last_consulted date, treat as old entry and retry
                            logger.info(f"MAC {cached_vendor.id}{seq_info} has no consultation date, retrying...")
                            with db_lock:
                                try:
                                    self.__session.delete(cached_vendor)
                                    self.__session.commit()
                                except Exception as e:
                                    self.__session.rollback()
                                    logger.error(f"Error removing MAC {cached_vendor.id}: {e}")
                    else:
                        # Normal cached vendor, update last consulted time
                        logger.debug(f"MAC {cached_vendor.id}{seq_info} found in database cache: {cached_vendor.vendor_name}")
                        with db_lock:
                            cached_vendor.last_consulted = datetime.utcnow()
                            self.__session.commit()
                        return cached_vendor.vendor_name

                # Double-check cache after potential removal (race condition protection)
                if not cached_vendor:
                    with db_lock:
                        cached_vendor = vendor_repository.search_by_id(mac_id)
                        if not cached_vendor:
                            cached_vendor = vendor_repository.search_by_id(full_mac_id)
                    if cached_vendor:
                        logger.debug(f"MAC {cached_vendor.id}{seq_info} found in database after double-check: {cached_vendor.vendor_name}")
                        return cached_vendor.vendor_name

                try:
                    # Fetch from API using the full MAC address for better accuracy
                    vendor_name = fetch_vendor_from_api(full_mac_id, sequential_id=sequential_id)
                except Exception as e:
                    logger.error(f"MacVendor API does not work{seq_info}: \n {e}")
                    return None

                if vendor_name:
                    with db_lock:
                        try:
                            # Determine if this is an error case that should use full MAC
                            is_error_case = (
                                vendor_name == "RATE_LIMITED" or 
                                vendor_name is None  # HTTP 404, 50X, 4XX errors
                            )
                            
                            # Use full MAC for error cases, legacy format for normal vendors
                            db_mac_id = full_mac_id if is_error_case else mac_id
                            
                            # Final check to prevent duplicate insertion
                            existing_vendor = vendor_repository.search_by_id(db_mac_id)
                            
                            # Check if this is a rate-limited response
                            is_rate_limited = vendor_name == "RATE_LIMITED"
                            
                            if existing_vendor:
                                # Update existing record
                                existing_vendor.vendor_name = vendor_name
                                existing_vendor.last_consulted = datetime.utcnow()
                                existing_vendor.is_rate_limited = is_rate_limited
                                logger.debug(f"Updated existing MAC {db_mac_id}{seq_info}: {vendor_name}")
                            else:
                                # Create new record with appropriate MAC format
                                new_vendor = MACVendorTable(
                                    id=db_mac_id,
                                    vendor_name=vendor_name,
                                    last_consulted=datetime.utcnow(),
                                    is_rate_limited=is_rate_limited
                                )
                                self.__session.add(new_vendor)
                                logger.debug(f"Created new MAC {db_mac_id}{seq_info}: {vendor_name} ({'error case' if is_error_case else 'normal vendor'})")
                            
                            self.__session.commit()
                            return vendor_name
                        except IntegrityError:
                            self.__session.rollback()
                            # Another thread inserted the same MAC, fetch the result
                            with db_lock:
                                final_vendor = vendor_repository.search_by_id(db_mac_id)
                                if final_vendor:
                                    logger.debug(f"MAC {db_mac_id}{seq_info} was inserted by another thread: {final_vendor.vendor_name}")
                                    return final_vendor.vendor_name
                            return vendor_name
                        except Exception as e:
                            self.__session.rollback()  # Rollback on general exceptions
                            logger.error(f"Error saving vendor for MAC {db_mac_id}: {e}")
                            return vendor_name
                return None
        finally:
            # Always remove this MAC from the processing set
            with macs_in_process_lock:
                macs_in_process.discard(mac_id)
