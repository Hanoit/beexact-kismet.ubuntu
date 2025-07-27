"""
File Queue Processor
Handles file processing in a queue to ensure sequential processing and better performance
"""
import os
import time
import threading
import queue
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class FileQueueProcessor:
    """
    Queue-based file processor that handles files sequentially
    """
    
    def __init__(self, processor, max_queue_size: int = 10):
        """
        Initialize the file queue processor
        
        Args:
            processor: The file processor instance
            max_queue_size: Maximum number of files in queue
        """
        self.__processor = processor
        self.__file_queue = queue.Queue(maxsize=max_queue_size)
        self.__processing_thread = None
        self.__stop_event = threading.Event()
        self.__current_file = None
        self.__processing_stats = {
            'total_queued': 0,
            'total_processed': 0,
            'total_errors': 0,
            'current_queue_size': 0
        }
        
        # Start processing thread
        self.__start_processing_thread()
        
        logger.info(f"FileQueueProcessor initialized with max queue size: {max_queue_size}")
    
    def __start_processing_thread(self):
        """Start the background processing thread"""
        self.__processing_thread = threading.Thread(
            target=self.__process_queue_worker,
            daemon=True,
            name="FileQueueProcessor"
        )
        self.__processing_thread.start()
        logger.info("File queue processing thread started")
    
    def add_file_to_queue(self, file_path: str) -> bool:
        """
        Add a file to the processing queue
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            True if file was added to queue, False if queue is full
        """
        try:
            # Check if file is already in queue
            if self.__is_file_in_queue(file_path):
                logger.info(f"File {os.path.basename(file_path)} already in queue, skipping")
                return False
            
            # Add to queue with timeout
            self.__file_queue.put(file_path, timeout=1.0)
            self.__processing_stats['total_queued'] += 1
            self.__processing_stats['current_queue_size'] = self.__file_queue.qsize()
            
            logger.info(f"Added file to queue: {os.path.basename(file_path)} "
                       f"(queue size: {self.__file_queue.qsize()})")
            return True
            
        except queue.Full:
            logger.warning(f"Queue is full, cannot add file: {os.path.basename(file_path)}")
            return False
        except Exception as e:
            logger.error(f"Error adding file to queue: {e}")
            return False
    
    def __is_file_in_queue(self, file_path: str) -> bool:
        """Check if a file is already in the queue"""
        filename = os.path.basename(file_path)
        
        # Check current file being processed
        if self.__current_file and os.path.basename(self.__current_file) == filename:
            return True
        
        # Check files in queue
        try:
            # Create a temporary list of queue items
            temp_queue = []
            while not self.__file_queue.empty():
                item = self.__file_queue.get_nowait()
                temp_queue.append(item)
                if os.path.basename(item) == filename:
                    # Put items back in queue
                    for temp_item in temp_queue:
                        self.__file_queue.put(temp_item)
                    return True
            
            # Put items back in queue
            for temp_item in temp_queue:
                self.__file_queue.put(temp_item)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if file is in queue: {e}")
            return False
    
    def __process_queue_worker(self):
        """Background worker that processes files from the queue"""
        logger.info("File queue worker started")
        
        while not self.__stop_event.is_set():
            try:
                # Get file from queue with timeout
                file_path = self.__file_queue.get(timeout=1.0)
                self.__current_file = file_path
                filename = os.path.basename(file_path)
                
                logger.info(f"Processing file from queue: {filename}")
                
                # Process the file
                start_time = time.time()
                try:
                    self.__processor.process_file(file_path)
                    processing_time = time.time() - start_time
                    
                    self.__processing_stats['total_processed'] += 1
                    logger.info(f"✅ Successfully processed {filename} in {processing_time:.2f} seconds")
                    
                except Exception as e:
                    processing_time = time.time() - start_time
                    self.__processing_stats['total_errors'] += 1
                    logger.error(f"❌ Error processing {filename} after {processing_time:.2f} seconds: {e}")
                
                finally:
                    self.__current_file = None
                    self.__processing_stats['current_queue_size'] = self.__file_queue.qsize()
                    self.__file_queue.task_done()
                
            except queue.Empty:
                # No files in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Unexpected error in queue worker: {e}")
                time.sleep(1)  # Wait before retrying
        
        logger.info("File queue worker stopped")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status
        
        Returns:
            Dictionary with queue statistics
        """
        return {
            'queue_size': self.__file_queue.qsize(),
            'max_queue_size': self.__file_queue.maxsize,
            'current_file': os.path.basename(self.__current_file) if self.__current_file else None,
            'is_processing': self.__current_file is not None,
            'stats': self.__processing_stats.copy()
        }
    
    def wait_for_queue_empty(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all files in queue to be processed
        
        Args:
            timeout: Maximum time to wait (None for infinite)
            
        Returns:
            True if queue is empty, False if timeout
        """
        try:
            self.__file_queue.join()
            return True
        except Exception as e:
            logger.error(f"Error waiting for queue: {e}")
            return False
    
    def stop(self):
        """Stop the queue processor"""
        logger.info("Stopping file queue processor...")
        self.__stop_event.set()
        
        if self.__processing_thread and self.__processing_thread.is_alive():
            self.__processing_thread.join(timeout=5.0)
        
        logger.info("File queue processor stopped")
    
    def get_processing_summary(self) -> str:
        """
        Get a summary of processing statistics
        
        Returns:
            Formatted summary string
        """
        stats = self.__processing_stats
        status = self.get_queue_status()
        
        summary = f"""
📊 FILE QUEUE PROCESSING SUMMARY
{'=' * 50}
📁 Queue Status:
   • Current queue size: {status['queue_size']}/{status['max_queue_size']}
   • Currently processing: {status['current_file'] or 'None'}
   • Is processing: {'Yes' if status['is_processing'] else 'No'}

📈 Processing Statistics:
   • Total files queued: {stats['total_queued']:,}
   • Total files processed: {stats['total_processed']:,}
   • Total errors: {stats['total_errors']:,}
   • Success rate: {(stats['total_processed'] / max(stats['total_queued'], 1) * 100):.1f}%
"""
        return summary 