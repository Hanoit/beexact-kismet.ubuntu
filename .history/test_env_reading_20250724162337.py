#!/usr/bin/env python3
"""
Test script to verify .env file reading
"""
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_env_loading():
    """Test if .env file is loaded correctly"""
    logger.info("Testing .env file loading...")
    
    # Load environment variables
    load_dotenv()
    
    # Test all environment variables
    env_vars = {
        'WATCH_DIRECTORY': 'Directory where Kismet files are saved',
        'CHECK_INTERVAL': 'How often the directory is checked for new files (in seconds)',
        'NUM_WORKERS': 'Number of CPU cores to dedicate for processing',
        'FLIP_XY': 'Flip the coordinates if needed (0 = False, 1 = True)',
        'API_KEY_MACVENDOR': 'API Key for MacVendor API',
        'OUT_DIRECTORY': 'Directory where the output CSV files will be saved',
        'DB_DIRECTORY': 'Directory where the database files are located',
        'BASIC_VERBOSE': 'Show basic processing progress in the console (0 = False, 1 = True)',
        'ADVANCE_VERBOSE': 'Show detailed processing progress in the console (0 = False, 1 = True)'
    }
    
    logger.info("Environment variables:")
    for var_name, description in env_vars.items():
        value = os.getenv(var_name)
        if value is not None:
            logger.info(f"  {var_name}: {value} ({description})")
        else:
            logger.warning(f"  {var_name}: NOT FOUND ({description})")
    
    # Test specific values
    watch_dir = os.getenv('WATCH_DIRECTORY')
    if watch_dir:
        logger.info(f"Watch directory: {watch_dir}")
        if os.path.exists(watch_dir):
            logger.info(f"Watch directory exists: {watch_dir}")
        else:
            logger.warning(f"Watch directory does not exist: {watch_dir}")
    else:
        logger.error("WATCH_DIRECTORY not found in environment variables")

if __name__ == '__main__':
    test_env_loading() 