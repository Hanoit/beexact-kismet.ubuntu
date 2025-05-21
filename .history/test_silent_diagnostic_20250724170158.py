#!/usr/bin/env python3
"""
Test script to verify silent diagnostic reporting
"""
import os
from dotenv import load_dotenv
from utils.KismetDiagnostic import KismetDiagnostic

# Load environment variables
load_dotenv()

def test_silent_diagnostic():
    """Test that diagnostic reports are saved silently to log files"""
    
    # Test file path
    test_file = "/opt/kismetFiles/Kismet-20250403-13-58-41.kismet"
    
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} does not exist")
        return
    
    print("Testing Silent Diagnostic Reporting...")
    print("=" * 50)
    print("This should only show this message and the log file path.")
    print("The diagnostic report should NOT be printed to console.")
    print()
    
    # Create diagnostic utility
    diagnostic = KismetDiagnostic("/opt/kismetFiles", "Kismet-20250403-13-58-41.kismet")
    
    # Test silent logging
    processing_results = {
        'processed': 29,
        'exported': 29,
        'processing_time': 8.88,
        'total_devices': 1202,
        'wifi_aps': 112,
        'wifi_aps_with_signal': 101
    }
    
    print("Generating diagnostic report (should be silent)...")
    diagnostic.log_diagnostic_report(test_file, processing_results)
    
    print("✅ Diagnostic report generated silently!")
    print(f"📁 Log file: {diagnostic.diagnostic_log.logFilePath}")
    
    # Check if log file was created
    if os.path.exists(diagnostic.diagnostic_log.logFilePath):
        file_size = os.path.getsize(diagnostic.diagnostic_log.logFilePath)
        print(f"📊 Log file size: {file_size:,} bytes")
        print("✅ Test completed successfully!")
    else:
        print("❌ Log file was not created!")

if __name__ == '__main__':
    test_silent_diagnostic() 