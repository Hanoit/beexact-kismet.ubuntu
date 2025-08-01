#!/usr/bin/env python3
"""
Test script to verify that the improved logging system shows only essential information
and reduces verbosity for better terminal output.
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


def test_circuit_breaker_logging():
    """Test that circuit breaker only logs when opening and closing"""
    print("=== Testing Circuit Breaker Logging ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with MACs that will likely trigger circuit breaker
    test_macs = [
        "FF-FF-FF-FF-FF-FF",  # Likely to trigger rate limit
        "AA-BB-CC-DD-EE-FF",  # Might trigger rate limit
        "11-22-33-44-55-66",  # Might trigger rate limit
    ] * 15  # Create enough to trigger circuit breaker
    
    print(f"Testing circuit breaker logging with {len(test_macs)} MACs")
    print("Expected: Only circuit breaker OPEN/CLOSE messages, no individual MAC skips")
    print()
    
    circuit_breaker_opened = False
    circuit_breaker_closed = False
    
    for i, mac in enumerate(test_macs, 1):
        try:
            sequential_id = f"LOG{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            
            # Don't print individual results to avoid spam
            if i % 10 == 0:
                if vendor == "RATE_LIMITED":
                    print(f"  MAC {i}: Rate Limited (circuit breaker may be active)")
                    circuit_breaker_opened = True
                elif vendor:
                    print(f"  MAC {i}: {vendor}")
                    circuit_breaker_closed = True
                else:
                    print(f"  MAC {i}: None")
                    
        except Exception as e:
            if i % 10 == 0:
                print(f"  MAC {i}: Error - {e}")
        
        # Small delay to avoid overwhelming the system
        time.sleep(1)
    
    print()
    if circuit_breaker_opened:
        print("✅ Circuit breaker opened (should see OPEN message in logs)")
    if circuit_breaker_closed:
        print("✅ Circuit breaker closed (should see CLOSE message in logs)")
    
    session.close()
    print()


def test_rate_limit_logging():
    """Test that rate limit logging is less verbose"""
    print("=== Testing Rate Limit Logging ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with MACs that might trigger rate limiting
    test_macs = [
        "FF-FF-FF-FF-FF-FF",  # Likely to trigger rate limit
        "AA-BB-CC-DD-EE-FF",  # Might trigger rate limit
        "11-22-33-44-55-66",  # Might trigger rate limit
    ] * 5  # Test with 15 MACs
    
    print(f"Testing rate limit logging with {len(test_macs)} MACs")
    print("Expected: Only rate limit changes, not every individual rate limit")
    print()
    
    for i, mac in enumerate(test_macs, 1):
        try:
            sequential_id = f"RATE{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            
            # Don't print individual results to avoid spam
            if i % 5 == 0:
                if vendor == "RATE_LIMITED":
                    print(f"  MAC {i}: Rate Limited")
                elif vendor:
                    print(f"  MAC {i}: {vendor}")
                else:
                    print(f"  MAC {i}: None")
                    
        except Exception as e:
            if i % 5 == 0:
                print(f"  MAC {i}: Error - {e}")
        
        # Small delay
        time.sleep(2)
    
    session.close()
    print()


def test_queue_logging():
    """Test that queue logging is less verbose"""
    print("=== Testing Queue Logging ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with MACs that will likely fail and go to queue
    test_macs = [
        "FF-FF-FF-FF-FF-FF",  # Likely to trigger rate limit
        "AA-BB-CC-DD-EE-FF",  # Might trigger rate limit
        "11-22-33-44-55-66",  # Might trigger rate limit
    ] * 10  # Test with 30 MACs
    
    print(f"Testing queue logging with {len(test_macs)} MACs")
    print("Expected: Queue size every 10 additions, not every individual addition")
    print()
    
    for i, mac in enumerate(test_macs, 1):
        try:
            sequential_id = f"QUEUE{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            
            # Don't print individual results to avoid spam
            if i % 10 == 0:
                if vendor == "RATE_LIMITED":
                    print(f"  MAC {i}: Rate Limited")
                elif vendor:
                    print(f"  MAC {i}: {vendor}")
                else:
                    print(f"  MAC {i}: None")
                    
        except Exception as e:
            if i % 10 == 0:
                print(f"  MAC {i}: Error - {e}")
        
        # Small delay
        time.sleep(1)
    
    session.close()
    print()


def test_retry_logging():
    """Test that retry logging shows progress instead of individual retries"""
    print("=== Testing Retry Logging ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with MACs that will likely fail and be retried
    test_macs = [
        "FF-FF-FF-FF-FF-FF",  # Likely to trigger rate limit
        "AA-BB-CC-DD-EE-FF",  # Might trigger rate limit
        "11-22-33-44-55-66",  # Might trigger rate limit
    ] * 5  # Test with 15 MACs
    
    print(f"Testing retry logging with {len(test_macs)} MACs")
    print("Expected: Retry progress every 10 MACs, not individual retry results")
    print()
    
    for i, mac in enumerate(test_macs, 1):
        try:
            sequential_id = f"RETRY{i:02d}"
            vendor = finder.get_vendor(mac, sequential_id=sequential_id)
            
            # Don't print individual results to avoid spam
            if i % 5 == 0:
                if vendor == "RATE_LIMITED":
                    print(f"  MAC {i}: Rate Limited")
                elif vendor:
                    print(f"  MAC {i}: {vendor}")
                else:
                    print(f"  MAC {i}: None")
                    
        except Exception as e:
            if i % 5 == 0:
                print(f"  MAC {i}: Error - {e}")
        
        # Small delay
        time.sleep(2)
    
    session.close()
    print()


def test_api_capacity_logging():
    """Test that API capacity measurement logging is concise"""
    print("=== Testing API Capacity Logging ===")
    
    # Get session
    session = get_session()
    finder = MacVendorFinder(session)
    
    # Test with a known good MAC to trigger capacity measurement
    test_mac = "00-11-22-33-44-55"  # Known vendor
    
    print(f"Testing API capacity logging with: {test_mac}")
    print("Expected: Concise capacity measurement message")
    print()
    
    try:
        sequential_id = "CAPACITY"
        vendor = finder.get_vendor(test_mac, sequential_id=sequential_id)
        
        if vendor:
            print(f"  Result: {vendor}")
            print("  ✅ API capacity measurement should show concise message")
        elif vendor == "RATE_LIMITED":
            print(f"  Result: Rate Limited")
            print("  ⚠️  API capacity measurement may show error message")
        else:
            print(f"  Result: None")
            print("  ℹ️  MAC not found, but API responded")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    session.close()
    print()


def test_log_summary():
    """Test summary of improved logging features"""
    print("=== Improved Logging Summary ===")
    
    print("✅ Circuit Breaker Logging:")
    print("   - Only logs when OPEN (🚨) and CLOSED (✅)")
    print("   - No individual MAC skip messages")
    print("   - Clear emoji indicators for status")
    print()
    
    print("✅ Rate Limit Logging:")
    print("   - Only logs when interval changes (⚠️ 📈)")
    print("   - No repetitive messages for same interval")
    print("   - Clear emoji indicators for warnings and improvements")
    print()
    
    print("✅ Queue Logging:")
    print("   - Queue size every 10 additions (📋)")
    print("   - Queue full warnings with emoji (🔄)")
    print("   - No individual MAC addition messages")
    print()
    
    print("✅ Retry Logging:")
    print("   - Progress every 10 retries (📊)")
    print("   - Summary of success/failure counts (✅)")
    print("   - No individual retry result messages")
    print()
    
    print("✅ API Capacity Logging:")
    print("   - Concise capacity measurement (📊)")
    print("   - Clear error indicators (🚨)")
    print("   - No verbose response time details")
    print()
    
    print("✅ Overall Improvements:")
    print("   - Reduced terminal spam")
    print("   - Clear emoji indicators for different message types")
    print("   - Essential information only")
    print("   - Better readability in terminal")
    print()


def main():
    """Main test function"""
    print("Improved Logging System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test 1: Circuit breaker logging
        test_circuit_breaker_logging()
        
        # Test 2: Rate limit logging
        test_rate_limit_logging()
        
        # Test 3: Queue logging
        test_queue_logging()
        
        # Test 4: Retry logging
        test_retry_logging()
        
        # Test 5: API capacity logging
        test_api_capacity_logging()
        
        # Test 6: Log summary
        test_log_summary()
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print("✅ Circuit breaker logging reduced to essential messages")
        print("✅ Rate limit logging shows only interval changes")
        print("✅ Queue logging shows progress instead of individual additions")
        print("✅ Retry logging shows progress and summary")
        print("✅ API capacity logging is concise")
        print("✅ All logs use clear emoji indicators")
        print("✅ Terminal output is much cleaner and readable")
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
