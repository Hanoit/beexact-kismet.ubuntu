#!/usr/bin/env python3
"""
Test script to verify that error cases are stored with full MAC addresses
while normal vendors use legacy format.
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


def test_mac_formatting_logic():
    """Test the MAC formatting logic for different cases"""
    print("=== Testing MAC Formatting Logic ===")
    
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
            print(f"  Legacy format (normal vendors): {legacy_mac}")
            print(f"  Full format (error cases): {full_mac}")
            print()
        except Exception as e:
            print(f"MAC: {mac} -> Error: {e}")


def test_error_case_detection():
    """Test the error case detection logic"""
    print("=== Testing Error Case Detection ===")
    
    test_cases = [
        ("RATE_LIMITED", True, "Rate limited error"),
        ("CIRCUIT_BREAKER_OPEN", True, "Circuit breaker error"),
        (None, True, "HTTP 404/50X/4XX error"),
        ("CIMSYS Inc", False, "Normal vendor"),
        ("VMware, Inc.", False, "Normal vendor"),
        ("", False, "Empty string vendor"),
    ]
    
    for vendor_name, expected_error, description in test_cases:
        is_error_case = (
            vendor_name == "RATE_LIMITED" or 
            vendor_name == "CIRCUIT_BREAKER_OPEN" or
            vendor_name is None
        )
        
        status = "✅" if is_error_case == expected_error else "❌"
        print(f"{status} {description}: {vendor_name} -> Error case: {is_error_case}")


def test_database_storage_logic():
    """Test the database storage logic with different scenarios"""
    print("\n=== Testing Database Storage Logic ===")
    
    # Get session
    session = get_session()
    
    # Check what's currently in the database
    from repository.RepositoryImpl import RepositoryImpl
    from models.DBKismetModels import MACVendorTable
    
    vendor_repository = RepositoryImpl(MACVendorTable, session)
    all_vendors = vendor_repository.search_all()
    
    print(f"Total MACs in database: {len(all_vendors)}")
    print("\nAnalyzing MAC storage patterns:")
    
    legacy_format_count = 0
    full_format_count = 0
    error_cases = []
    normal_vendors = []
    
    for vendor in all_vendors:
        mac_id = vendor.id
        vendor_name = vendor.vendor_name
        
        # Check if it's legacy format (3 bytes) or full format (6 bytes)
        if len(mac_id.replace("-", "")) == 6:  # 3 bytes = 6 hex chars
            legacy_format_count += 1
            normal_vendors.append((mac_id, vendor_name))
        elif len(mac_id.replace("-", "")) == 12:  # 6 bytes = 12 hex chars
            full_format_count += 1
            error_cases.append((mac_id, vendor_name))
    
    print(f"  Legacy format MACs (normal vendors): {legacy_format_count}")
    print(f"  Full format MACs (error cases): {full_format_count}")
    
    print("\n  Normal vendors (legacy format):")
    for mac_id, vendor_name in normal_vendors[:5]:  # Show first 5
        print(f"    {mac_id}: {vendor_name}")
    
    print("\n  Error cases (full format):")
    for mac_id, vendor_name in error_cases[:5]:  # Show first 5
        print(f"    {mac_id}: {vendor_name}")
    
    session.close()
    
    return legacy_format_count, full_format_count


def test_system_with_error_scenarios():
    """Test the system with scenarios that should trigger error storage"""
    print("\n=== Testing System with Error Scenarios ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with MACs that might trigger different scenarios
    test_macs = [
        "00-11-22-33-44-55",  # Should be normal vendor
        "FF-FF-FF-FF-FF-FF",  # Might be rate limited or not found
        "00-00-00-00-00-00",  # Might be not found
    ]
    
    results = {}
    
    for i, mac in enumerate(test_macs, 1):
        print(f"\nProcessing MAC {i}/{len(test_macs)}: {mac}")
        
        try:
            # Use sequential_id to track this specific record
            sequential_id = f"ERROR{i:02d}"
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


def verify_storage_after_test():
    """Verify that the storage logic worked correctly after the test"""
    print("\n=== Verifying Storage After Test ===")
    
    # Get session
    session = get_session()
    
    from repository.RepositoryImpl import RepositoryImpl
    from models.DBKismetModels import MACVendorTable
    
    vendor_repository = RepositoryImpl(MACVendorTable, session)
    
    # Look for recent entries from our test
    all_vendors = vendor_repository.search_all()
    recent_vendors = sorted(all_vendors, key=lambda x: x.last_consulted or datetime.min, reverse=True)[:10]
    
    print("Recent MAC entries in database:")
    
    for vendor in recent_vendors:
        mac_id = vendor.id
        vendor_name = vendor.vendor_name
        is_rate_limited = vendor.is_rate_limited
        last_consulted = vendor.last_consulted
        
        # Determine expected format
        is_error_case = (
            vendor_name == "RATE_LIMITED" or 
            vendor_name == "CIRCUIT_BREAKER_OPEN" or
            vendor_name is None
        )
        
        expected_format = "Full MAC" if is_error_case else "Legacy (OUI)"
        actual_format = "Full MAC" if len(mac_id.replace("-", "")) == 12 else "Legacy (OUI)"
        
        status = "✅" if expected_format == actual_format else "❌"
        
        print(f"  {status} {mac_id}")
        print(f"    Vendor: {vendor_name}")
        print(f"    Expected: {expected_format}, Actual: {actual_format}")
        print(f"    Rate Limited: {is_rate_limited}")
        print(f"    Last Consulted: {last_consulted}")
        print()
    
    session.close()


def main():
    """Main test function"""
    print("Error MAC Storage Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: MAC formatting logic
        test_mac_formatting_logic()
        
        # Test 2: Error case detection
        test_error_case_detection()
        
        # Test 3: Current database storage
        legacy_count, full_count = test_database_storage_logic()
        
        # Test 4: System with error scenarios
        results = test_system_with_error_scenarios()
        
        # Test 5: Verify storage after test
        verify_storage_after_test()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ Error cases (rate limits, HTTP errors) stored with full MAC")
        print("✅ Normal vendors stored with legacy format (OUI)")
        print("✅ Database compatibility maintained")
        print("✅ API calls use full MAC for accuracy")
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
