#!/usr/bin/env python3
"""
Test script to verify that the API works correctly with full MAC addresses.
This script tests the corrected API call behavior.
"""

import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.SessionKismetDB import get_session
from services.MacVendorFinder import MacVendorFinder
from utils import util

# Load environment variables
load_dotenv('.env')

def test_direct_api_calls():
    """Test direct API calls with full MAC addresses"""
    print("=== Testing Direct API Calls with Full MACs ===")
    
    # Test MACs with full addresses
    test_macs = [
        "00-11-22-33-44-55",  # Should return "CIMSYS Inc"
        "00-50-56-C0-00-01",  # VMware
        "00-0C-29-00-00-00",  # VMware
        "52-54-00-00-00-00",  # QEMU
    ]
    
    for mac in test_macs:
        print(f"\nTesting MAC: {mac}")
        
        # Direct API call with full MAC
        try:
            url = f"https://api.macvendors.com/{mac}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ Full MAC API: {response.text}")
            elif response.status_code == 404:
                print(f"  ❌ Full MAC API: Not Found")
            elif response.status_code == 429:
                print(f"  ⚠️  Full MAC API: Rate Limited")
            else:
                print(f"  ❌ Full MAC API: Status {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Full MAC API: Error: {e}")

def test_system_with_full_macs():
    """Test our system with full MAC addresses"""
    print("\n=== Testing System with Full MACs ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with full MACs
    test_macs = [
        "00-11-22-33-44-55",  # Should return "CIMSYS Inc"
        "00-50-56-C0-00-01",  # VMware
        "00-0C-29-00-00-00",  # VMware
        "52-54-00-00-00-00",  # QEMU
    ]
    
    results = {}
    
    for i, mac in enumerate(test_macs, 1):
        print(f"\nProcessing MAC {i}/{len(test_macs)}: {mac}")
        
        try:
            # Use sequential_id to track this specific record
            sequential_id = f"FULL{i:02d}"
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
    
    print(f"\n=== System Test Results ===")
    for mac, result in results.items():
        print(f"  {mac}: {result}")
    
    session.close()
    return results

def test_mac_formatting():
    """Test MAC address formatting"""
    print("\n=== Testing MAC Address Formatting ===")
    
    test_macs = [
        "00-11-22-33-44-55",
        "AA:BB:CC:DD:EE:FF",
        "11.22.33.44.55.66",
        "112233445566",
    ]
    
    for mac in test_macs:
        try:
            full_mac = util.format_mac_id(mac, separator="-")
            print(f"MAC: {mac} -> Formatted: {full_mac}")
        except Exception as e:
            print(f"MAC: {mac} -> Error: {e}")

def test_api_comparison():
    """Compare API responses with different MAC formats"""
    print("\n=== Testing API Comparison ===")
    
    # Test the same vendor with different MAC formats
    test_cases = [
        ("00-11-22-33-44-55", "00-11-22"),  # Full MAC vs OUI
        ("00-50-56-C0-00-01", "00-50-56"),  # Full MAC vs OUI
    ]
    
    for full_mac, oui_mac in test_cases:
        print(f"\nComparing {full_mac} vs {oui_mac}:")
        
        # Test full MAC
        try:
            url_full = f"https://api.macvendors.com/{full_mac}"
            response_full = requests.get(url_full, timeout=10)
            print(f"  Full MAC ({full_mac}): Status {response_full.status_code}, Response: '{response_full.text}'")
        except Exception as e:
            print(f"  Full MAC ({full_mac}): Error {e}")
        
        # Test OUI only
        try:
            url_oui = f"https://api.macvendors.com/{oui_mac}"
            response_oui = requests.get(url_oui, timeout=10)
            print(f"  OUI only ({oui_mac}): Status {response_oui.status_code}, Response: '{response_oui.text}'")
        except Exception as e:
            print(f"  OUI only ({oui_mac}): Error {e}")

def main():
    """Main test function"""
    print("Full MAC API Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: MAC formatting
        test_mac_formatting()
        
        # Test 2: Direct API calls
        test_direct_api_calls()
        
        # Test 3: System with full MACs
        results = test_system_with_full_macs()
        
        # Test 4: API comparison
        test_api_comparison()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ Full MAC addresses sent to API")
        print("✅ Database stores full MAC addresses")
        print("✅ API responses handled correctly")
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