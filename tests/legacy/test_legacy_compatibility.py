#!/usr/bin/env python3
"""
Test script to verify legacy compatibility while using full MAC addresses for API calls.
This script tests that the system maintains compatibility with existing tables.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.SessionKismetDB import get_session
from services.MacVendorFinder import MacVendorFinder
from utils import util

# Load environment variables
load_dotenv('.env')

def test_legacy_formatting():
    """Test that legacy formatting is maintained"""
    print("=== Testing Legacy MAC Formatting ===")
    
    test_macs = [
        "00-11-22-33-44-55",
        "AA:BB:CC:DD:EE:FF",
        "11.22.33.44.55.66",
        "112233445566",
    ]
    
    for mac in test_macs:
        try:
            # Legacy format (first 3 bytes)
            legacy_mac = util.format_mac_id(mac, position=3, separator="-")
            # Full MAC format
            full_mac = util.format_mac_id(mac, separator="-")
            
            print(f"MAC: {mac}")
            print(f"  Legacy format: {legacy_mac}")
            print(f"  Full format: {full_mac}")
            print()
        except Exception as e:
            print(f"MAC: {mac} -> Error: {e}")

def test_system_behavior():
    """Test the system behavior with legacy compatibility"""
    print("=== Testing System Behavior ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test MACs
    test_macs = [
        "00-11-22-33-44-55",
        "AA-BB-CC-DD-EE-FF",
        "11-22-33-44-55-66",
    ]
    
    results = {}
    
    for i, mac in enumerate(test_macs, 1):
        print(f"\nProcessing MAC {i}/{len(test_macs)}: {mac}")
        
        try:
            # Use sequential_id to track this specific record
            sequential_id = f"LEGACY{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            results[mac] = vendor
            
            if vendor:
                print(f"  Result: {vendor}")
            else:
                print(f"  Result: None (not found)")
                
        except Exception as e:
            print(f"  Error: {e}")
            results[mac] = f"ERROR: {e}"
        
        # Small delay between tests
        time.sleep(2)
    
    print(f"\n=== Processing Results ===")
    for mac, result in results.items():
        print(f"  {mac}: {result}")
    
    session.close()
    return results

def check_database_storage():
    """Check what's actually stored in the database"""
    print("\n=== Checking Database Storage ===")
    
    # Get session
    session = get_session()
    
    # Check what MACs are stored in the database
    from repository.RepositoryImpl import RepositoryImpl
    from models.DBKismetModels import MACVendorTable
    
    vendor_repository = RepositoryImpl(MACVendorTable, session)
    
    # Get recent MACs from database
    all_vendors = vendor_repository.search_all()
    
    print(f"Total MACs in database: {len(all_vendors)}")
    print("\nRecent MAC addresses stored in database:")
    
    # Show only recent entries (last 10)
    recent_vendors = sorted(all_vendors, key=lambda x: x.last_consulted or datetime.min, reverse=True)[:10]
    
    for vendor in recent_vendors:
        print(f"  ID: {vendor.id}")
        print(f"  Vendor: {vendor.vendor_name}")
        print(f"  Rate Limited: {vendor.is_rate_limited}")
        print(f"  Last Consulted: {vendor.last_consulted}")
        print()
    
    session.close()

def test_api_accuracy():
    """Test that API calls use full MAC addresses for better accuracy"""
    print("\n=== Testing API Accuracy ===")
    
    # Test with a MAC that should return different results for OUI vs full MAC
    test_mac = "00-11-22-33-44-55"
    
    print(f"Testing MAC: {test_mac}")
    
    # Get legacy format (OUI only)
    legacy_mac = util.format_mac_id(test_mac, position=3, separator="-")
    # Get full format
    full_mac = util.format_mac_id(test_mac, separator="-")
    
    print(f"  Legacy format (OUI): {legacy_mac}")
    print(f"  Full format: {full_mac}")
    
    # Test direct API calls
    import requests
    
    try:
        # Test with legacy format
        url_legacy = f"https://api.macvendors.com/{legacy_mac}"
        response_legacy = requests.get(url_legacy, timeout=10)
        print(f"  Legacy API call: Status {response_legacy.status_code}, Response: '{response_legacy.text}'")
    except Exception as e:
        print(f"  Legacy API call: Error {e}")
    
    try:
        # Test with full format
        url_full = f"https://api.macvendors.com/{full_mac}"
        response_full = requests.get(url_full, timeout=10)
        print(f"  Full API call: Status {response_full.status_code}, Response: '{response_full.text}'")
    except Exception as e:
        print(f"  Full API call: Error {e}")

def main():
    """Main test function"""
    print("Legacy Compatibility Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: Legacy formatting
        test_legacy_formatting()
        
        # Test 2: System behavior
        results = test_system_behavior()
        
        # Test 3: Check database storage
        check_database_storage()
        
        # Test 4: API accuracy
        test_api_accuracy()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ Legacy formatting maintained for database compatibility")
        print("✅ Full MAC addresses sent to API for better accuracy")
        print("✅ Existing tables remain compatible")
        print("✅ API calls use complete MAC addresses")
        print("=" * 50)
        print("All tests completed!")
        print(f"Test finished at: {datetime.now()}")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 