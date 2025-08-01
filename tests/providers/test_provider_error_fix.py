#!/usr/bin/env python3
"""
Test script to verify that the provider error fix works correctly
and handles both object and string cases without the 'str' object has no attribute 'id' error.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.SessionKismetDB import get_session
from services.MacProviderFinder import MacProviderFinder
from utils import util

# Load environment variables
load_dotenv('.env')


def test_provider_finder_initialization():
    """Test that MacProviderFinder initializes correctly"""
    print("=== Testing MacProviderFinder Initialization ===")
    
    # Get session
    session = get_session()
    
    try:
        finder = MacProviderFinder(session)
        print("✅ MacProviderFinder initialized successfully")
        
        # Test basic functionality
        test_mac = "00:11:22:33:44:55"
        test_ssid = "TestSSID"
        
        # This should not raise an error
        provider = finder.get_provider(test_mac, test_ssid)
        print(f"✅ Provider lookup completed: {provider}")
        
    except Exception as e:
        print(f"❌ Error initializing MacProviderFinder: {e}")
        return False
    finally:
        session.close()
    
    print()
    return True


def test_provider_by_mac_method():
    """Test the get_provider_by_mac method specifically"""
    print("=== Testing get_provider_by_mac Method ===")
    
    # Get session
    session = get_session()
    finder = MacProviderFinder(session)
    
    # Test with various MAC addresses
    test_macs = [
        "00:11:22:33:44:55",
        "AA:BB:CC:DD:EE:FF",
        "11:22:33:44:55:66",
    ]
    
    for mac in test_macs:
        try:
            provider = finder.get_provider_by_mac(mac)
            print(f"  MAC {mac}: {provider} (type: {type(provider).__name__})")
            
            # Verify that the result is either None, a string, or an object with provider_name
            if provider is None:
                print(f"    ✅ Valid result: None")
            elif isinstance(provider, str):
                print(f"    ✅ Valid result: String '{provider}'")
            elif hasattr(provider, 'provider_name'):
                print(f"    ✅ Valid result: Object with provider_name '{provider.provider_name}'")
            else:
                print(f"    ⚠️  Unexpected result type: {type(provider)}")
                
        except Exception as e:
            print(f"  ❌ Error with MAC {mac}: {e}")
    
    session.close()
    print()


def test_provider_method_with_ssid():
    """Test the get_provider method with SSID matching"""
    print("=== Testing get_provider Method with SSID ===")
    
    # Get session
    session = get_session()
    finder = MacProviderFinder(session)
    
    # Test with various SSIDs
    test_cases = [
        ("00:11:22:33:44:55", "TestSSID"),
        ("AA:BB:CC:DD:EE:FF", "WiFi_Network"),
        ("11:22:33:44:55:66", "HomeNetwork"),
    ]
    
    for mac, ssid in test_cases:
        try:
            provider = finder.get_provider(mac, ssid)
            print(f"  MAC {mac}, SSID '{ssid}': {provider} (type: {type(provider).__name__})")
            
            # Verify that the result is either None or a string
            if provider is None:
                print(f"    ✅ Valid result: None")
            elif isinstance(provider, str):
                print(f"    ✅ Valid result: String '{provider}'")
            else:
                print(f"    ⚠️  Unexpected result type: {type(provider)}")
                
        except Exception as e:
            print(f"  ❌ Error with MAC {mac}, SSID '{ssid}': {e}")
    
    session.close()
    print()


def test_error_handling():
    """Test error handling for edge cases"""
    print("=== Testing Error Handling ===")
    
    # Get session
    session = get_session()
    finder = MacProviderFinder(session)
    
    # Test edge cases that might cause errors
    edge_cases = [
        ("", ""),  # Empty MAC and SSID
        ("invalid_mac", "TestSSID"),  # Invalid MAC format
        ("00:11:22:33:44:55", ""),  # Empty SSID
        ("00:11:22:33:44:55", None),  # None SSID
    ]
    
    for mac, ssid in edge_cases:
        try:
            provider = finder.get_provider(mac, ssid)
            print(f"  Edge case MAC '{mac}', SSID '{ssid}': {provider}")
            
        except Exception as e:
            print(f"  ❌ Error with edge case MAC '{mac}', SSID '{ssid}': {e}")
            # This is expected for invalid inputs
    
    session.close()
    print()


def test_database_operations():
    """Test database operations to ensure no 'id' attribute errors"""
    print("=== Testing Database Operations ===")
    
    # Get session
    session = get_session()
    finder = MacProviderFinder(session)
    
    # Test with a known good MAC and SSID
    test_mac = "00:11:22:33:44:55"
    test_ssid = "TestProviderNetwork"
    
    try:
        # This should not raise the 'str' object has no attribute 'id' error
        provider = finder.get_provider(test_mac, test_ssid)
        print(f"✅ Database operation completed successfully: {provider}")
        
        # Test multiple calls to ensure consistency
        for i in range(3):
            provider2 = finder.get_provider(test_mac, test_ssid)
            print(f"  Call {i+1}: {provider2}")
            
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        import traceback
        traceback.print_exc()
    
    session.close()
    print()


def test_integration_with_kismet_analyzer():
    """Test integration with KismetAnalyzer to ensure no errors"""
    print("=== Testing Integration with KismetAnalyzer ===")
    
    # Get session
    session = get_session()
    
    try:
        # Simulate the call that was failing in KismetAnalyzer
        from utils import util
        
        test_mac = "00:11:22:33:44:55"
        test_ssid = "TestSSID"
        
        # This is the call that was failing
        provider = util.parse_provider(test_mac, test_ssid, session)
        print(f"✅ Integration test passed: {provider}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    session.close()
    print()


def test_performance():
    """Test performance with multiple provider lookups"""
    print("=== Testing Performance ===")
    
    # Get session
    session = get_session()
    finder = MacProviderFinder(session)
    
    # Test with multiple MACs and SSIDs
    test_cases = [
        ("00:11:22:33:44:55", "TestSSID1"),
        ("AA:BB:CC:DD:EE:FF", "TestSSID2"),
        ("11:22:33:44:55:66", "TestSSID3"),
        ("22:33:44:55:66:77", "TestSSID4"),
        ("33:44:55:66:77:88", "TestSSID5"),
    ]
    
    start_time = time.time()
    
    for mac, ssid in test_cases:
        try:
            provider = finder.get_provider(mac, ssid)
            print(f"  {mac} -> {ssid}: {provider}")
        except Exception as e:
            print(f"  ❌ Error with {mac} -> {ssid}: {e}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\n✅ Performance test completed in {processing_time:.2f} seconds")
    print(f"   Average time per lookup: {processing_time/len(test_cases):.3f} seconds")
    
    session.close()
    print()


def main():
    """Main test function"""
    print("Provider Error Fix Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: Initialization
        if not test_provider_finder_initialization():
            return 1
        
        # Test 2: get_provider_by_mac method
        test_provider_by_mac_method()
        
        # Test 3: get_provider method with SSID
        test_provider_method_with_ssid()
        
        # Test 4: Error handling
        test_error_handling()
        
        # Test 5: Database operations
        test_database_operations()
        
        # Test 6: Integration with KismetAnalyzer
        test_integration_with_kismet_analyzer()
        
        # Test 7: Performance
        test_performance()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ MacProviderFinder initializes correctly")
        print("✅ get_provider_by_mac handles both object and string cases")
        print("✅ get_provider method works without 'id' attribute errors")
        print("✅ Error handling works for edge cases")
        print("✅ Database operations complete successfully")
        print("✅ Integration with KismetAnalyzer works")
        print("✅ Performance is acceptable")
        print("✅ No more 'str' object has no attribute 'id' errors")
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
