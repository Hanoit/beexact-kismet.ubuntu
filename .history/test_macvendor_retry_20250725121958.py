#!/usr/bin/env python3
"""
Test script to verify MacVendorFinder retry mechanism
"""
import os
import sys
import time
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.MacVendorFinder import fetch_vendor_from_api
import logging

# Set up logging to see the retry messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()


def test_retry_mechanism():
    """Test the retry mechanism with known MAC addresses"""
    
    # Test MAC addresses (some might return 504 errors)
    test_macs = [
        "DE-B3-70",  # This one was showing 504 errors in your log
        "DE-C2-C9",  # Another one from your log
        "DE-CB-AC",  # Another one from your log
        "00-11-22",  # Test with a different MAC
        "AA-BB-CC",  # Test with another MAC
    ]
    
    print("🧪 Testing MacVendorFinder retry mechanism...")
    print("=" * 60)
    
    for i, mac in enumerate(test_macs, 1):
        print(f"\n📡 Testing MAC {i}/{len(test_macs)}: {mac}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            vendor = fetch_vendor_from_api(mac)
            elapsed = time.time() - start_time
            
            if vendor:
                print(f"✅ Success: {vendor} (took {elapsed:.2f}s)")
            else:
                print(f"⚠️  No vendor found (took {elapsed:.2f}s)")
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Error after {elapsed:.2f}s: {e}")
        
        # Small delay between tests to avoid overwhelming the API
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")


if __name__ == "__main__":
    test_retry_mechanism() 
