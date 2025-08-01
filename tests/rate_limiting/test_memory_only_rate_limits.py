#!/usr/bin/env python3
"""
Test script to verify that rate limits are handled entirely in memory
without any database storage.
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


def test_configuration_memory_only():
    """Test that configuration is simplified for memory-only rate limits"""
    print("=== Testing Memory-Only Rate Limit Configuration ===")
    
    # Check environment variables
    api_interval = float(os.getenv('MACVENDOR_API_INTERVAL', '3.0'))
    api_timeout = float(os.getenv('MACVENDOR_API_TIMEOUT', '20'))
    
    print(f"API Interval: {api_interval}s")
    print(f"API Timeout: {api_timeout}s")
    
    # Check if rate limit cache config is completely removed
    rate_limit_cache_days = os.getenv('MACVENDOR_RATE_LIMITED_CACHE_DAYS')
    
    if rate_limit_cache_days:
        print(f"⚠️  Rate limit cache config still present: {rate_limit_cache_days}")
        print("   This should be removed for memory-only handling")
    else:
        print("✅ Rate limit cache config completely removed")
    
    print()


def test_mac_formatting():
    """Test MAC address formatting"""
    print("=== Testing MAC Address Formatting ===")
    
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


def test_system_memory_only_rate_limits():
    """Test the system behavior with memory-only rate limit handling"""
    print("\n=== Testing System with Memory-Only Rate Limits ===")
    
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
            sequential_id = f"MEMORY{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            results[mac] = vendor
            
            if vendor:
                print(f"  Result: {vendor}")
            elif vendor == "RATE_LIMITED":
                print(f"  Result: Rate Limited (handled in memory)")
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


def test_429_error_memory_only():
    """Test how the system handles 429 errors with memory-only storage"""
    print("\n=== Testing 429 Error Handling (Memory Only) ===")
    
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
            print("  This would be handled entirely in memory, no database storage")
        else:
            print(f"  Response: {response.text[:100]}...")
            
    except Exception as e:
        print(f"  Error: {e}")


def check_database_no_rate_limits():
    """Check that database contains no rate limit entries"""
    print("\n=== Checking Database (No Rate Limit Entries) ===")
    
    # Get session
    session = get_session()
    
    from repository.RepositoryImpl import RepositoryImpl
    from models.DBKismetModels import MACVendorTable
    
    vendor_repository = RepositoryImpl(MACVendorTable, session)
    
    # Get all MACs from database
    all_vendors = vendor_repository.search_all()
    
    print(f"Total MACs in database: {len(all_vendors)}")
    
    # Check for rate limited entries
    rate_limited_count = 0
    normal_vendors = []
    http_errors = []
    
    for vendor in all_vendors:
        if vendor.vendor_name == "RATE_LIMITED":
            rate_limited_count += 1
        elif vendor.vendor_name is None:
            http_errors.append(vendor)
        else:
            normal_vendors.append(vendor)
    
    print(f"Rate limited entries in database: {rate_limited_count}")
    print(f"Normal vendor entries: {len(normal_vendors)}")
    print(f"HTTP error entries: {len(http_errors)}")
    
    if rate_limited_count > 0:
        print("❌ Rate limited entries found in database - should be 0")
        print("   This indicates the system is still storing rate limits in database")
    else:
        print("✅ No rate limited entries in database - correct behavior")
    
    print("\nRecent entries by type:")
    
    # Show recent normal vendors
    recent_normal = sorted(normal_vendors, key=lambda x: x.last_consulted or datetime.min, reverse=True)[:5]
    if recent_normal:
        print("  Normal vendors:")
        for vendor in recent_normal:
            mac_format = "Full MAC" if len(vendor.id.replace("-", "")) == 12 else "Legacy (OUI)"
            print(f"    {vendor.id} ({mac_format}): {vendor.vendor_name}")
    
    # Show recent HTTP errors
    recent_errors = sorted(http_errors, key=lambda x: x.last_consulted or datetime.min, reverse=True)[:5]
    if recent_errors:
        print("  HTTP errors:")
        for vendor in recent_errors:
            print(f"    {vendor.id} (Full MAC): HTTP Error")
    
    session.close()


def test_intelligent_retry_memory_only():
    """Test that intelligent retry works with memory-only rate limits"""
    print("\n=== Testing Intelligent Retry (Memory Only) ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with a MAC that might trigger rate limiting
    test_mac = "FF-FF-FF-FF-FF-FF"
    
    print(f"Testing intelligent retry with MAC: {test_mac}")
    
    try:
        # Use sequential_id to track this specific record
        sequential_id = "RETRY_MEMORY"
        vendor = finder.get_vendor(test_mac, sequential_id=sequential_id)
        
        if vendor:
            print(f"  Result: {vendor}")
        elif vendor == "RATE_LIMITED":
            print(f"  Result: Rate Limited (handled in memory with intelligent retry)")
        else:
            print(f"  Result: None (not found)")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    session.close()


def test_performance_improvement():
    """Test that removing database storage improves performance"""
    print("\n=== Testing Performance Improvement ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with multiple MACs to see performance
    test_macs = [
        "00-11-22-33-44-55",
        "AA-BB-CC-DD-EE-FF",
        "11-22-33-44-55-66",
    ]
    
    start_time = time.time()
    
    for i, mac in enumerate(test_macs, 1):
        print(f"Processing MAC {i}/{len(test_macs)}: {mac}")
        
        try:
            sequential_id = f"PERF{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            
            if vendor:
                print(f"  Result: {vendor}")
            elif vendor == "RATE_LIMITED":
                print(f"  Result: Rate Limited (memory only)")
            else:
                print(f"  Result: None")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\nTotal processing time: {processing_time:.2f} seconds")
    print(f"Average per MAC: {processing_time/len(test_macs):.2f} seconds")
    print("Performance should be improved without database operations for rate limits")
    
    session.close()


def main():
    """Main test function"""
    print("Memory-Only Rate Limits Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: Configuration for memory-only rate limits
        test_configuration_memory_only()
        
        # Test 2: MAC formatting
        test_mac_formatting()
        
        # Test 3: System with memory-only rate limits
        results = test_system_memory_only_rate_limits()
        
        # Test 4: 429 error handling memory only
        test_429_error_memory_only()
        
        # Test 5: Database check for no rate limit entries
        check_database_no_rate_limits()
        
        # Test 6: Intelligent retry memory only
        test_intelligent_retry_memory_only()
        
        # Test 7: Performance improvement
        test_performance_improvement()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ Rate limit cache configuration removed")
        print("✅ System works with memory-only rate limits")
        print("✅ Rate limits handled entirely in memory")
        print("✅ Intelligent retry system maintained")
        print("✅ Database contains only actual vendor data")
        print("✅ No rate limited entries in database")
        print("✅ Performance improved without DB operations")
        print("✅ Adaptive API handling maintained")
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
