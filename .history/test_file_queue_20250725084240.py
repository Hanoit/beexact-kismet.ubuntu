#!/usr/bin/env python3
"""
Test script for file queue processing system
"""
import os
import time
import tempfile
import shutil
from dotenv import load_dotenv
from services.WatchingDirectory import WatchingDirectory
from services.DirectoryFilesProcessor import DirectoryFilesProcessor
from database.SessionKismetDB import get_session

# Load environment variables
load_dotenv()

def create_test_kismet_file(file_path: str, size_mb: int = 1):
    """Create a test Kismet file with specified size"""
    # Create a minimal SQLite database that looks like a Kismet file
    import sqlite3
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    
    # Create basic tables
    cursor.execute("""
        CREATE TABLE devices (
            first_time INTEGER,
            last_time INTEGER,
            devkey TEXT,
            phyname TEXT,
            devmac TEXT,
            strongest_signal INTEGER,
            min_lat REAL,
            min_lon REAL,
            max_lat REAL,
            max_lon REAL,
            avg_lat REAL,
            avg_lon REAL,
            bytes_data INTEGER,
            type TEXT,
            device BLOB
        )
    """)
    
    # Insert some test data
    test_data = [
        (1234567890, 1234567890, "key1", "IEEE802.11", "00:1B:63:12:34:56", -50, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1000, "Wi-Fi AP", b'{"test": "data"}'),
        (1234567890, 1234567890, "key2", "IEEE802.11", "00:50:56:12:34:56", -60, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1000, "Wi-Fi AP", b'{"test": "data"}'),
    ]
    
    cursor.executemany("""
        INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, test_data)
    
    conn.commit()
    conn.close()
    
    # Pad file to desired size
    current_size = os.path.getsize(file_path)
    target_size = size_mb * 1024 * 1024
    
    if current_size < target_size:
        with open(file_path, 'ab') as f:
            f.write(b'\x00' * (target_size - current_size))

def test_file_queue():
    """Test the file queue processing system"""
    
    print("Testing File Queue Processing System...")
    print("=" * 60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Initialize processor and watcher
        session = get_session()
        processor = DirectoryFilesProcessor(session)
        watcher = WatchingDirectory(processor)
        
        # Start watching in background
        import threading
        watch_thread = threading.Thread(target=watcher.start_watching, daemon=True)
        watch_thread.start()
        
        # Wait for watcher to start
        time.sleep(2)
        
        print("\n📁 Creating test files...")
        
        # Create multiple test files
        test_files = []
        for i in range(3):
            filename = f"test_file_{i+1}.kismet"
            file_path = os.path.join(temp_dir, filename)
            create_test_kismet_file(file_path, size_mb=1)
            test_files.append(file_path)
            print(f"  Created: {filename}")
        
        print(f"\n📊 Copying files to watch directory...")
        
        # Copy files to watch directory to trigger processing
        watch_dir = os.getenv("WATCH_DIRECTORY", "/opt/kismetFiles")
        
        for i, file_path in enumerate(test_files):
            dest_path = os.path.join(watch_dir, f"test_queue_{i+1}.kismet")
            shutil.copy2(file_path, dest_path)
            print(f"  Copied: test_queue_{i+1}.kismet")
            time.sleep(2)  # Wait between copies
        
        print(f"\n⏳ Waiting for processing to complete...")
        
        # Wait for processing to complete
        time.sleep(10)
        
        # Get queue summary
        summary = watcher.get_queue_summary()
        print(f"\n{summary}")
        
        print("\n✅ Test completed!")
        
        # Clean up test files
        print("\n🧹 Cleaning up test files...")
        for i in range(3):
            test_file = os.path.join(watch_dir, f"test_queue_{i+1}.kismet")
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"  Removed: test_queue_{i+1}.kismet")

if __name__ == '__main__':
    test_file_queue() 