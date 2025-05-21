#!/usr/bin/env python3
"""
Test script for improved MacVendor API handling
"""
import os
import time
from dotenv import load_dotenv
from services.MacVendorFinder import MacVendorFinder
from database.SessionKismetDB import get_session

# Load environment variables
load_dotenv()

def test_improved_macvendor():
    """Test the improved MacVendor API handling"""
    
    print("Testing Improved MacVendor API Handling...")
    print("=" * 60)
    
    # Initialize session and finder
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test MAC addresses (mix of known and unknown)
    test_macs = [
        "00:1B:63:12:34:56",  # Apple (should work)
        "00:8C:88:12:34:56",  # Unknown (should return None)
        "02:02:6F:12:34:56",  # Unknown (should return None)
        "00:50:56:12:34:56",  # VMware (should work)
        "00:0C:29:12:34:56",  # VMware (should work)
    ]
    
    print("Testing MAC vendor lookup with rate limiting...")
    print()
    
    start_time = time.time()
    
    for i, mac in enumerate(test_macs, 1):
        print(f"Test {i}: MAC {mac}")
        
        try:
            vendor = finder.get_vendor(mac)
            if vendor:
                print(f"  ✅ Vendor: {vendor}")
            else:
                print(f"  ❌ No vendor found (404)")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Total time for {len(test_macs)} requests: {total_time:.2f} seconds")
    print(f"Average time per request: {total_time/len(test_macs):.2f} seconds")
    print()
    
    # Test rate limiting
    print("Testing rate limiting with multiple rapid requests...")
    print()
    
    rapid_macs = ["00:1B:63:12:34:56"] * 5  # Same MAC 5 times
    
    start_time = time.time()
    
    for i, mac in enumerate(rapid_macs, 1):
        print(f"Rapid request {i}: MAC {mac}")
        
        try:
            vendor = finder.get_vendor(mac)
            if vendor:
                print(f"  ✅ Vendor: {vendor}")
            else:
                print(f"  ❌ No vendor found")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Total time for {len(rapid_macs)} rapid requests: {total_time:.2f} seconds")
    print(f"Average time per rapid request: {total_time/len(rapid_macs):.2f} seconds")
    
    session.close()

if __name__ == '__main__':
    test_improved_macvendor() 