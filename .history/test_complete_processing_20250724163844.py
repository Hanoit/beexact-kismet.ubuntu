#!/usr/bin/env python3
"""
Test script to simulate complete file processing with diagnostic reports
"""
import os
import time
from dotenv import load_dotenv
from services.DirectoryFilesProcessor import DirectoryFilesProcessor
from database.SessionKismetDB import get_session
from utils.KismetDiagnostic import KismetDiagnostic

# Load environment variables
load_dotenv()

def test_complete_processing():
    """Test complete file processing with diagnostic reports"""
    
    # Test file path
    test_file = "/opt/kismetFiles/Kismet-20250403-13-58-41-1.kismet"
    
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} does not exist")
        return
    
    print("Testing Complete File Processing with Diagnostic Reports...")
    print("=" * 70)
    
    try:
        # Initialize database session and processor
        session = get_session()
        processor = DirectoryFilesProcessor(session)
        
        # Process the file (this will generate diagnostic reports)
        print("Starting file processing...")
        processor.process_file(test_file)
        
        print("\n" + "=" * 70)
        print("✅ File processing completed successfully!")
        print("=" * 70)
        
        # Show what files were created
        filename = os.path.basename(test_file)
        base_name = os.path.splitext(filename)[0]
        
        print("\n📁 Generated files:")
        print(f"   • {base_name}.csv - Exported data")
        print(f"   • {base_name}.log - Processing log")
        print(f"   • {base_name}_DIAGNOSTIC.log - Diagnostic report")
        print(f"   • {base_name}_NOT_VENDOR.log - Missing vendor log")
        print(f"   • {base_name}_NOT_PROVIDER.log - Missing provider log")
        
        # Check if files exist
        output_dir = "/opt/kismetFiles"
        files_to_check = [
            f"{base_name}.csv",
            f"{base_name}.log", 
            f"{base_name}_DIAGNOSTIC.log",
            f"{base_name}_NOT_VENDOR.log",
            f"{base_name}_NOT_PROVIDER.log"
        ]
        
        print("\n📋 File status:")
        for file in files_to_check:
            file_path = os.path.join(output_dir, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   ✅ {file} ({size:,} bytes)")
            else:
                print(f"   ❌ {file} (not found)")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_complete_processing() 