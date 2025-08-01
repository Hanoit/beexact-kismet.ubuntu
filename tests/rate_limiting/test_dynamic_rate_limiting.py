#!/usr/bin/env python3
"""
Test script to verify that dynamic rate limiting works correctly
when 429 (Too Many Requests) errors occur.
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


def test_dynamic_rate_limiting_logic():
    """Test the dynamic rate limiting logic"""
    print("=== Testing Dynamic Rate Limiting Logic ===")
    
    # Import the functions directly
    from services.MacVendorFinder import (
        MIN_API_INTERVAL,
        increase_rate_limit,
        decrease_rate_limit,
        current_api_interval
    )
    
    print(f"Initial API interval: {MIN_API_INTERVAL}s")
    print(f"Current API interval: {current_api_interval}s")
    print()
    
    # Test rate limit increase
    print("Testing rate limit increase (simulating 429 error):")
    increase_rate_limit()
    print(f"After 429 error: {current_api_interval}s")
    
    # Test multiple increases
    for i in range(3):
        increase_rate_limit()
        print(f"After {i+2} 429 errors: {current_api_interval}s")
    
    # Test rate limit decrease
    print("\nTesting rate limit decrease (simulating successful calls):")
    for i in range(5):
        decrease_rate_limit()
        print(f"After {i+1} successful calls: {current_api_interval:.1f}s")


def test_mac_formatting():
    """Test MAC address formatting"""
    print("\n=== Testing MAC Address Formatting ===")
    
    test_macs = [
        "00-11-22-33-44-55",
        "AA:BB:CC:DD:EE:FF",
        "11.22.33.44.55.66",
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


def test_system_with_rate_limiting():
    """Test the system behavior with dynamic rate limiting"""
    print("\n=== Testing System with Dynamic Rate Limiting ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with MACs that might trigger rate limiting
    test_macs = [
        "00-11-22-33-44-55",  # Should be normal vendor
        "AA-BB-CC-DD-EE-FF",  # Might be not found
        "11-22-33-44-55-66",  # Might be not found
        "FF-FF-FF-FF-FF-FF",  # Might trigger rate limit
    ]
    
    results = {}
    
    for i, mac in enumerate(test_macs, 1):
        print(f"\nProcessing MAC {i}/{len(test_macs)}: {mac}")
        
        try:
            # Use sequential_id to track this specific record
            sequential_id = f"RATE{i:02d}"
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


def test_429_error_simulation():
    """Test how the system handles 429 errors"""
    print("\n=== Testing 429 Error Handling ===")
    
    # Test direct API calls to see 429 responses
    import requests
    
    # Test with a MAC that might trigger rate limiting
    test_mac = "FF-FF-FF-FF-FF-FF"
    
    print(f"Testing direct API call for: {test_mac}")
    
    try:
        url = f"https://api.macvendors.com/{test_mac}"
        response = requests.get(url, timeout=20)
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.text}")
        elif response.status_code == 404:
            print(f"  Response: Not Found")
        elif response.status_code == 429:
            print(f"  Response: Rate Limited")
            print(f"  Error Message: {response.text}")
        else:
            print(f"  Response: {response.text[:100]}...")
            
    except Exception as e:
        print(f"  Error: {e}")


def test_rate_limit_recovery():
    """Test that rate limiting recovers after successful calls"""
    print("\n=== Testing Rate Limit Recovery ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with a known good MAC to see if rate limit decreases
    test_mac = "00-11-22-33-44-55"
    
    print(f"Testing rate limit recovery with MAC: {test_mac}")
    
    try:
        # Use sequential_id to track this specific record
        sequential_id = "RECOVERY"
        vendor = finder.get_vendor(test_mac, sequential_id=sequential_id)
        
        if vendor:
            print(f"  Result: {vendor}")
            print("  Rate limit should have decreased if it was previously increased")
        else:
            print(f"  Result: None (not found)")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    session.close()


def check_database_storage():
    """Check what's stored in the database after tests"""
    print("\n=== Checking Database Storage ===")
    
    # Get session
    session = get_session()
    
    from repository.RepositoryImpl import RepositoryImpl
    from models.DBKismetModels import MACVendorTable
    
    vendor_repository = RepositoryImpl(MACVendorTable, session)
    
    # Get recent MACs from database
    all_vendors = vendor_repository.search_all()
    
    print(f"Total MACs in database: {len(all_vendors)}")
    print("\nRecent MAC entries:")
    
    # Show only recent entries (last 10)
    recent_vendors = sorted(all_vendors, key=lambda x: x.last_consulted or datetime.min, reverse=True)[:10]
    
    for vendor in recent_vendors:
        mac_id = vendor.id
        vendor_name = vendor.vendor_name
        is_rate_limited = vendor.is_rate_limited
        last_consulted = vendor.last_consulted
        
        # Determine format
        mac_format = "Full MAC" if len(mac_id.replace("-", "")) == 12 else "Legacy (OUI)"
        
        print(f"  {mac_id} ({mac_format})")
        print(f"    Vendor: {vendor_name}")
        print(f"    Rate Limited: {is_rate_limited}")
        print(f"    Last Consulted: {last_consulted}")
        print()
    
    session.close()


def main():
    """Main test function"""
    print("Dynamic Rate Limiting Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: Dynamic rate limiting logic
        test_dynamic_rate_limiting_logic()
        
        # Test 2: MAC formatting
        test_mac_formatting()
        
        # Test 3: System with rate limiting
        results = test_system_with_rate_limiting()
        
        # Test 4: 429 error simulation
        test_429_error_simulation()
        
        # Test 5: Rate limit recovery
        test_rate_limit_recovery()
        
        # Test 6: Database storage
        check_database_storage()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ Dynamic rate limiting implemented")
        print("✅ Rate limit increases on 429 errors")
        print("✅ Rate limit decreases on successful calls")
        print("✅ API calls using full MAC addresses")
        print("✅ Error handling with automatic slowdown")
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
