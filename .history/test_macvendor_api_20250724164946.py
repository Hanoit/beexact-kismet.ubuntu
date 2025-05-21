#!/usr/bin/env python3
"""
Test script to diagnose MacVendor API issues
"""
import os
import requests
from dotenv import load_dotenv
from utils import util

# Load environment variables
load_dotenv()

def test_macvendor_api():
    """Test the MacVendor API with different MAC formats"""
    
    # Test MAC addresses from the error logs
    test_macs = [
        "00:8C:88:12:34:56",
        "02:02:6F:12:34:56", 
        "02:0A:F5:12:34:56",
        "02:08:22:12:34:56",
        "02:16:78:12:34:56"
    ]
    
    print("Testing MacVendor API...")
    print("=" * 50)
    
    # Get API key
    api_token = os.getenv('API_KEY_MACVENDOR')
    print(f"API Token: {'Present' if api_token else 'Not found'}")
    print()
    
    for mac in test_macs:
        print(f"Testing MAC: {mac}")
        
        # Test different MAC formats
        formats = [
            ("Original", mac),
            ("3 parts with dash", util.format_mac_id(mac, position=3, separator="-")),
            ("3 parts with colon", util.format_mac_id(mac, position=3, separator=":")),
            ("6 parts with dash", util.format_mac_id(mac, position=6, separator="-")),
            ("6 parts with colon", util.format_mac_id(mac, position=6, separator=":"))
        ]
        
        for format_name, formatted_mac in formats:
            print(f"  {format_name}: {formatted_mac}")
            
            # Test API call
            if api_token:
                url = f"https://api.macvendors.com/v1/lookup/{formatted_mac}"
                headers = {
                    'Authorization': f'Bearer {api_token}',
                    'Accept': 'application/json'
                }
            else:
                url = f"https://api.macvendors.com/{formatted_mac}"
                headers = {}
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"    Status: {response.status_code}")
                print(f"    Response: {response.text[:100]}...")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        vendor = data.get('organization_name', 'No vendor name in response')
                        print(f"    ✅ Vendor: {vendor}")
                    except:
                        print(f"    ✅ Raw response: {response.text}")
                elif response.status_code == 404:
                    print(f"    ❌ Not found")
                else:
                    print(f"    ⚠️  Error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
            
            print()
        
        print("-" * 30)
    
    # Test API documentation
    print("API Documentation Test:")
    print("=" * 30)
    
    # Test a known working MAC (Apple)
    test_apple_mac = "00:1B:63:12:34:56"
    apple_mac_id = util.format_mac_id(test_apple_mac, position=3, separator="-")
    
    print(f"Testing known Apple MAC: {test_apple_mac} -> {apple_mac_id}")
    
    if api_token:
        url = f"https://api.macvendors.com/v1/lookup/{apple_mac_id}"
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json'
        }
    else:
        url = f"https://api.macvendors.com/{apple_mac_id}"
        headers = {}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                vendor = data.get('organization_name', 'No vendor name')
                print(f"✅ Apple vendor: {vendor}")
            except:
                print(f"✅ Raw response: {response.text}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_api_rate_limits():
    """Test API rate limits"""
    print("\n" + "=" * 50)
    print("Testing API Rate Limits...")
    print("=" * 50)
    
    api_token = os.getenv('API_KEY_MACVENDOR')
    
    # Test multiple rapid requests
    test_mac = "00:1B:63:12:34:56"
    mac_id = util.format_mac_id(test_mac, position=3, separator="-")
    
    print(f"Making 5 rapid requests for MAC: {mac_id}")
    
    for i in range(5):
        if api_token:
            url = f"https://api.macvendors.com/v1/lookup/{mac_id}"
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Accept': 'application/json'
            }
        else:
            url = f"https://api.macvendors.com/{mac_id}"
            headers = {}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Request {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                print("⚠️  Rate limit exceeded!")
                break
                
        except Exception as e:
            print(f"Request {i+1}: Exception {e}")

if __name__ == '__main__':
    test_macvendor_api()
    test_api_rate_limits() 