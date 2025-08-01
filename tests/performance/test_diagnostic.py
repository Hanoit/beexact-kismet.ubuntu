#!/usr/bin/env python3
"""
Test script for Kismet diagnostic functionality
"""
import os
import sys
from dotenv import load_dotenv
from utils.KismetDiagnostic import KismetDiagnostic

# Load environment variables
load_dotenv()

def test_diagnostic():
    """Test the diagnostic functionality"""
    
    # Test file path
    test_file = "/opt/kismetFiles/Kismet-20250403-13-58-41-1.kismet"
    
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} does not exist")
        return
    
    print("Testing Kismet Diagnostic Utility...")
    print("=" * 50)
    
    # Create diagnostic utility
    diagnostic = KismetDiagnostic("/opt/kismetFiles", "Kismet-20250403-13-58-41-1.kismet")
    
    # Test file analysis
    print("1. Testing file structure analysis...")
    analysis = diagnostic.analyze_file_structure(test_file)
    print(f"   File exists: {analysis['file_exists']}")
    print(f"   File size: {analysis['file_size']:,} bytes")
    print(f"   Total devices: {analysis['total_devices']:,}")
    print(f"   Processing mode: {analysis['processing_mode']}")
    print()
    
    # Test SQL queries
    print("2. Testing SQL queries...")
    query_results = diagnostic.test_sql_queries(test_file)
    print(f"   Wi-Fi APs total: {query_results['wifi_aps_total']:,}")
    print(f"   Wi-Fi APs with signal: {query_results['wifi_aps_with_signal']:,}")
    print(f"   Wi-Fi APs with location: {query_results['wifi_aps_with_location']:,}")
    print(f"   Original query results: {query_results['original_query']:,}")
    print(f"   Modified query results: {query_results['modified_query']:,}")
    print()
    
    # Test summary
    print("3. Testing summary...")
    summary = diagnostic.get_summary(test_file)
    print(f"   Filename: {summary['filename']}")
    print(f"   File size: {summary['file_size_mb']:.2f} MB")
    print(f"   Total devices: {summary['total_devices']:,}")
    print(f"   Wi-Fi APs: {summary['wifi_aps']:,}")
    print(f"   Location percentage: {summary['location_percentage']:.1f}%")
    print(f"   Signal percentage: {summary['signal_percentage']:.1f}%")
    print()
    
    # Test diagnostic report
    print("4. Testing diagnostic report generation...")
    processing_results = {
        'processed': 101,
        'exported': 95,
        'processing_time': 2.5
    }
    
    report = diagnostic.generate_diagnostic_report(test_file, processing_results)
    print("Diagnostic report generated successfully!")
    print(f"Report length: {len(report)} characters")
    print()
    
    # Test logging
    print("5. Testing diagnostic logging...")
    diagnostic.log_diagnostic_report(test_file, processing_results)
    print("Diagnostic report logged successfully!")
    print(f"Log file: {diagnostic.diagnostic_log.logFilePath}")
    
    print("\n" + "=" * 50)
    print("All diagnostic tests completed successfully!")

if __name__ == '__main__':
    test_diagnostic() 