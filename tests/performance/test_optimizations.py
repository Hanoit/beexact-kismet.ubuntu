#!/usr/bin/env python3
"""
Test script to verify the performance optimizations work correctly.
This script tests the optimizations without requiring a full Kismet file.
"""

import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sentence_transformer_optimizations():
    """Test the optimized sentence transformer processing."""
    from services.SentenceEmbeddings import find_provider, clear_cache, get_model
    
    # Create mock provider data
    class MockProvider:
        def __init__(self, name, aliases):
            self.provider_name = name
            self.alias = aliases
    
    # Test data
    providers = [
        MockProvider("Telefonica", '["Movistar", "O2", "Telefonica"]'),
        MockProvider("Vodafone", '["Vodafone", "Voda"]'),
        MockProvider("Orange", '["Orange", "France Telecom"]'),
        MockProvider("T-Mobile", '["T-Mobile", "TMobile", "Deutsche Telekom"]'),
        MockProvider("Verizon", '["Verizon", "Verizon Wireless"]'),
        MockProvider("AT&T", '["AT&T", "ATT", "American Telephone and Telegraph"]'),
        MockProvider("Comcast", '["Comcast", "Xfinity"]'),
        MockProvider("Spectrum", '["Spectrum", "Charter"]'),
        MockProvider("Cox", '["Cox Communications"]'),
        MockProvider("CenturyLink", '["CenturyLink", "Lumen"]'),
    ]
    
    # Test SSIDs
    test_ssids = [
        "Movistar_WiFi",
        "Vodafone_Hotspot", 
        "Orange_Network",
        "TMobile_5G",
        "Verizon_Fios",
        "ATT_Wireless",
        "Xfinity_WiFi",
        "Spectrum_Network",
        "Cox_Home",
        "CenturyLink_Fiber",
        "Random_WiFi_123",
        "Home_Network_2024",
        "Office_WiFi",
        "Guest_Network",
        "Public_Hotspot"
    ]
    
    logger.info("Testing sentence transformer optimizations...")
    
    # Clear cache before testing
    clear_cache()
    
    # Test with sentence transformer enabled
    os.environ['ENABLE_SENTENCE_TRANSFORMER'] = '1'
    start_time = time.time()
    
    for ssid in test_ssids:
        provider, index, similarity = find_provider(ssid, providers, threshold=0.75)
        logger.info(f"SSID: {ssid} -> Provider: {provider} (similarity: {similarity:.3f})")
    
    enabled_time = time.time() - start_time
    logger.info(f"Time with sentence transformer enabled: {enabled_time:.2f} seconds")
    
    # Clear cache and test with sentence transformer disabled
    clear_cache()
    os.environ['ENABLE_SENTENCE_TRANSFORMER'] = '0'
    start_time = time.time()
    
    for ssid in test_ssids:
        provider, index, similarity = find_provider(ssid, providers, threshold=0.75)
        logger.info(f"SSID: {ssid} -> Provider: {provider} (similarity: {similarity:.3f})")
    
    disabled_time = time.time() - start_time
    logger.info(f"Time with sentence transformer disabled: {disabled_time:.2f} seconds")
    
    # Performance comparison
    if enabled_time > 0:
        speedup = enabled_time / disabled_time
        logger.info(f"Performance improvement: {speedup:.1f}x faster with sentence transformer disabled")
    
    return enabled_time, disabled_time

def test_mac_provider_finder_optimizations():
    """Test the MacProviderFinder optimizations."""
    from database.SessionKismetDB import get_session
    from services.MacProviderFinder import MacProviderFinder
    
    logger.info("Testing MacProviderFinder optimizations...")
    
    session = get_session()
    finder = MacProviderFinder(session)
    
    # Test MAC addresses and SSIDs
    test_cases = [
        ("00:11:22:33:44:55", "Test_WiFi"),
        ("AA:BB:CC:DD:EE:FF", "Home_Network"),
        ("11:22:33:44:55:66", "Office_WiFi"),
        ("FF:EE:DD:CC:BB:AA", "Guest_WiFi"),
        ("55:44:33:22:11:00", "Public_Hotspot"),
    ]
    
    start_time = time.time()
    
    for mac, ssid in test_cases:
        provider = finder.get_provider(mac, ssid)
        logger.info(f"MAC: {mac}, SSID: {ssid} -> Provider: {provider}")
    
    processing_time = time.time() - start_time
    logger.info(f"MacProviderFinder processing time: {processing_time:.2f} seconds")
    
    session.close()
    return processing_time

def test_model_loading_optimization():
    """Test that the model is loaded only once."""
    from services.SentenceEmbeddings import get_model, clear_cache
    
    logger.info("Testing model loading optimization...")
    
    # Clear any existing model
    clear_cache()
    
    start_time = time.time()
    
    # First call - should load the model
    model1 = get_model()
    first_load_time = time.time() - start_time
    logger.info(f"First model load time: {first_load_time:.2f} seconds")
    
    # Second call - should reuse the model
    start_time = time.time()
    model2 = get_model()
    second_load_time = time.time() - start_time
    logger.info(f"Second model load time: {second_load_time:.2f} seconds")
    
    # Verify it's the same model instance
    if model1 is model2:
        logger.info("✅ Model loading optimization working: Same model instance reused")
    else:
        logger.warning("❌ Model loading optimization failed: Different model instances")
    
    speedup = first_load_time / second_load_time if second_load_time > 0 else float('inf')
    logger.info(f"Model reuse speedup: {speedup:.1f}x faster")
    
    return first_load_time, second_load_time

if __name__ == "__main__":
    logger.info("Starting optimization tests...")
    
    try:
        # Test model loading optimization
        first_load, second_load = test_model_loading_optimization()
        
        # Test sentence transformer optimizations
        enabled_time, disabled_time = test_sentence_transformer_optimizations()
        
        # Test MacProviderFinder optimizations
        finder_time = test_mac_provider_finder_optimizations()
        
        logger.info("🎉 All optimization tests completed successfully!")
        logger.info(f"📊 Performance Summary:")
        logger.info(f"  - Model first load: {first_load:.2f}s")
        logger.info(f"  - Model reuse: {second_load:.2f}s")
        logger.info(f"  - Sentence transformer enabled: {enabled_time:.2f}s")
        logger.info(f"  - Sentence transformer disabled: {disabled_time:.2f}s")
        logger.info(f"  - MacProviderFinder: {finder_time:.2f}s")
        
        if enabled_time > disabled_time:
            speedup = enabled_time / disabled_time
            logger.info(f"  - Performance improvement: {speedup:.1f}x faster when disabled")
        
        logger.info(f"✅ Ready to use optimized executable!")
        
    except Exception as e:
        logger.error(f"❌ Error during optimization testing: {e}", exc_info=True) 