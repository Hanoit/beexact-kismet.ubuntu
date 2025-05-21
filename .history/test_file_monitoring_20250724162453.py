#!/usr/bin/env python3
"""
Test script to simulate file copying and test the file monitoring system
"""
import os
import time
import threading
import tempfile
import shutil
from dotenv import load_dotenv
import logging
from services.WatchingDirectory import WatchingDirectory, EventHandler
from services.DirectoryFilesProcessor import DirectoryFilesProcessor
from database.SessionKismetDB import get_session
from utils.file_monitor import FileStabilityMonitor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_file_copy(source_file, dest_file, copy_duration=10):
    """
    Simulate copying a file over a specified duration
    """
    logger.info(f"Starting simulated file copy: {source_file} -> {dest_file}")
    
    # Get source file size
    source_size = os.path.getsize(source_file)
    
    # Create destination file
    with open(dest_file, 'wb') as dest:
        with open(source_file, 'rb') as source:
            copied = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while copied < source_size:
                # Calculate how much to copy in this iteration
                remaining = source_size - copied
                current_chunk = min(chunk_size, remaining)
                
                # Copy chunk
                chunk = source.read(current_chunk)
                dest.write(chunk)
                dest.flush()  # Ensure data is written to disk
                
                copied += current_chunk
                
                # Calculate sleep time to simulate slow copy
                progress = copied / source_size
                elapsed = time.time() - start_time
                target_time = copy_duration * progress
                
                if elapsed < target_time:
                    sleep_time = target_time - elapsed
                    time.sleep(sleep_time)
                
                logger.debug(f"Copy progress: {progress:.1%} ({copied}/{source_size} bytes)")
    
    logger.info(f"File copy completed: {dest_file}")

def test_file_monitoring():
    """
    Test the file monitoring system
    """
    logger.info("Starting file monitoring test...")
    
    # Load environment variables
    load_dotenv()
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary directory: {temp_dir}")
        
        # Create a test kismet file
        test_file = os.path.join(temp_dir, "test.kismet")
        with open(test_file, 'w') as f:
            f.write("Test kismet file content")
        
        # Initialize database session and processor
        session = get_session()
        processor = DirectoryFilesProcessor(session)
        
        # Create event handler
        event_handler = EventHandler(processor)
        
        # Test file stability monitor
        monitor = FileStabilityMonitor(stability_time=3, max_wait_time=60)
        
        # Test with a file that doesn't change
        logger.info("Testing with stable file...")
        if monitor.wait_for_stability(test_file):
            logger.info("✓ Stable file test passed")
        else:
            logger.error("✗ Stable file test failed")
        
        # Test file accessibility
        logger.info("Testing file accessibility...")
        if monitor.wait_for_accessibility(test_file, timeout=10):
            logger.info("✓ File accessibility test passed")
        else:
            logger.error("✗ File accessibility test failed")
        
        # Test with simulated file copy
        logger.info("Testing with simulated file copy...")
        copied_file = os.path.join(temp_dir, "copied.kismet")
        
        # Start file copy in background thread
        copy_thread = threading.Thread(
            target=simulate_file_copy,
            args=(test_file, copied_file, 5)  # 5 second copy
        )
        copy_thread.start()
        
        # Wait a moment for copy to start
        time.sleep(0.5)
        
        # Test stability during copy
        logger.info("Testing stability during file copy...")
        if monitor.wait_for_stability(copied_file):
            logger.info("✓ File copy stability test passed")
        else:
            logger.info("✗ File copy stability test failed (expected for incomplete file)")
        
        # Wait for copy to complete
        copy_thread.join()
        
        # Test stability after copy
        logger.info("Testing stability after file copy...")
        if monitor.wait_for_stability(copied_file):
            logger.info("✓ Post-copy stability test passed")
        else:
            logger.error("✗ Post-copy stability test failed")

if __name__ == '__main__':
    start_time = time.time()
    test_file_monitoring()
    logger.info(f"Test completed in {time.time() - start_time:.2f} seconds") 