"""
File Queue Processor
Handles file processing in a queue to ensure sequential processing and better performance
"""
import os
import time
import threading
import queue
import shutil
import psutil
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# CONFIGURACIÓN ADAPTIVA DESDE .ENV - OPTIMIZADA
CHECK_INTERVAL = float(os.getenv('CHECK_INTERVAL', '300'))
ENABLE_PERFORMANCE_MONITOR = os.getenv('ENABLE_PERFORMANCE_MONITOR', 'false').lower() == 'true'
ENABLE_PROGRESS_BAR = os.getenv('ENABLE_PROGRESS_BAR', '1') == '1'
SAVE_INTERMEDIATE_RESULTS = os.getenv('SAVE_INTERMEDIATE_RESULTS', '1') == '1'

# Configure logging
logger = logging.getLogger(__name__)


class FileQueueProcessor:
    """
    File queue processor that handles sequential file processing with configurable queue size
    """
    
    def __init__(self, processor, max_queue_size: Optional[int]=None):
        """
        Initialize the FileQueueProcessor
        
        Args:
            processor: The processor to use for processing files
            max_queue_size: Maximum number of files that can be queued (defaults to env var or 20)
        """
        self.__processor = processor
        self.__output_directory = getattr(processor, '_DirectoryFilesProcessor__output_directory', None)
        
        # Get queue size from environment or use default
        if max_queue_size is None:
            env_queue_size = os.getenv('FILE_QUEUE_MAX_SIZE', '20')
            try:
                max_queue_size = int(env_queue_size)
            except ValueError:
                max_queue_size = 20
                logger.warning(f"Invalid FILE_QUEUE_MAX_SIZE value '{env_queue_size}', using default: 20")
        
        # Enforce maximum limit of 30 files
        if max_queue_size > 30:
            logger.warning(f"Queue size {max_queue_size} exceeds maximum limit of 30. Setting to 30.")
            max_queue_size = 30
        
        self.__max_queue_size = max_queue_size
        self.__file_queue = queue.Queue(maxsize=max_queue_size)
        self.__stop_event = threading.Event()
        self.__worker_thread = None
        self.__current_file = None
        self.__processing_stats = {
            'total_processed': 0,
            'total_errors': 0,
            'current_queue_size': 0,
            'files_moved_back': 0,
            'start_time': time.time(),
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'fastest_file_time': float('inf'),
            'slowest_file_time': 0.0,
            'fastest_file': '',
            'slowest_file': '',
            'throughput_files_per_hour': 0.0
        }
        self.__start_worker()
        
        # Log configuración adaptiva
        logger.info("FileQueueProcessor Configuration - ADAPTIVA Y OPTIMIZADA:")
        logger.info(f"  - Max Queue Size: {max_queue_size}")
        logger.info(f"  - Check Interval: {CHECK_INTERVAL:.0f}s")
        logger.info(f"  - Performance Monitor: {'Enabled' if ENABLE_PERFORMANCE_MONITOR else 'Disabled'}")
        logger.info(f"  - Progress Bar: {'Enabled' if ENABLE_PROGRESS_BAR else 'Disabled'}")
        logger.info(f"  - Save Intermediate: {'Enabled' if SAVE_INTERMEDIATE_RESULTS else 'Disabled'}")
        
        if max_queue_size == 30:
            logger.info("⚠️  Queue is at maximum capacity (30 files). Excess files will be moved back to folder.")
    
    def __start_worker(self):
        """Start the worker thread"""
        self.__worker_thread = threading.Thread(
            target=self.__process_queue_worker,
            daemon=True,
            name="FileQueueProcessor"
        )
        self.__worker_thread.start()
        logger.info("File queue worker thread started")
    
    def __update_processing_stats(self, filename: str, processing_time: float, success: bool):
        """Actualizar estadísticas avanzadas de procesamiento"""
        if success:
            self.__processing_stats['total_processed'] += 1
        else:
            self.__processing_stats['total_errors'] += 1
        
        # Actualizar tiempos
        self.__processing_stats['total_processing_time'] += processing_time
        
        # Calcular tiempo promedio
        total_files = self.__processing_stats['total_processed'] + self.__processing_stats['total_errors']
        if total_files > 0:
            self.__processing_stats['average_processing_time'] = self.__processing_stats['total_processing_time'] / total_files
        
        # Actualizar archivo más rápido
        if processing_time < self.__processing_stats['fastest_file_time']:
            self.__processing_stats['fastest_file_time'] = processing_time
            self.__processing_stats['fastest_file'] = filename
        
        # Actualizar archivo más lento
        if processing_time > self.__processing_stats['slowest_file_time']:
            self.__processing_stats['slowest_file_time'] = processing_time
            self.__processing_stats['slowest_file'] = filename
        
        # Calcular throughput (archivos por hora)
        elapsed_time = time.time() - self.__processing_stats['start_time']
        if elapsed_time > 0:
            self.__processing_stats['throughput_files_per_hour'] = (total_files / elapsed_time) * 3600
    
    def __move_file_back_to_folder(self, file_path: str) -> bool:
        """
        Move a file back to the original folder for later processing
        
        Args:
            file_path: Path to the file to move back
            
        Returns:
            bool: True if file was moved successfully, False otherwise
        """
        try:
            if not self.__output_directory:
                logger.error("Cannot move file back: output directory not configured")
                return False
            
            filename = os.path.basename(file_path)
            source_path = file_path
            destination_path = os.path.join(self.__output_directory, filename)
            
            # Check if file exists in source
            if not os.path.exists(source_path):
                logger.warning(f"File {filename} not found at source, cannot move back")
                return False
            
            # Move file back to original folder
            shutil.move(source_path, destination_path)
            self.__processing_stats['files_moved_back'] += 1
            
            logger.info(f"📁 Moved {filename} back to folder for later processing")
            logger.info(f"📊 Files moved back so far: {self.__processing_stats['files_moved_back']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {filename} back to folder: {e}")
            return False

    def add_file_to_queue(self, file_path: str) -> bool:
        """
        Add a file to the processing queue
        
        Args:
            file_path: Path to the file to add to queue
            
        Returns:
            bool: True if file was added successfully, False otherwise
        """
        try:
            filename = os.path.basename(file_path)
            
            # Check if queue is full
            if self.__file_queue.full():
                logger.warning(f"⚠️  Queue is full ({self.__max_queue_size} files). Cannot add {filename}")
                
                # Move file back to folder for later processing
                if self.__move_file_back_to_folder(file_path):
                    logger.info(f"✅ File {filename} moved back to folder for later processing")
                    return False  # File was moved back, not added to queue
                else:
                    logger.error(f"❌ Failed to move {filename} back to folder")
                    return False
            
            # Check if file is already in queue
            if file_path in [item for item in list(self.__file_queue.queue)]:
                logger.warning(f"File {filename} is already in queue")
                return False
            
            # Add file to queue
            self.__file_queue.put(file_path, timeout=1.0)
            self.__processing_stats['current_queue_size'] = self.__file_queue.qsize()
            
            logger.info(f"Added file to queue: {filename} (queue size: {self.__file_queue.qsize()})")
            return True
            
        except queue.Full:
            logger.warning(f"Queue is full, cannot add file: {filename}")
            # Try to move file back to folder
            self.__move_file_back_to_folder(file_path)
            return False
        except Exception as e:
            logger.error(f"Error adding file {filename} to queue: {e}")
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
                
                # Clear any previous output and add visual separator
                print("\n" + "="*50)
                logger.info(f"🚀 STARTING NEW FILE PROCESSING")
                logger.info(f"📁 File: {filename}")
                logger.info(f"⏰ Start time: {time.strftime('%H:%M:%S')}")
                logger.info(f"📊 Queue position: {self.__processing_stats['total_processed'] + 1}")
                logger.info(f"📋 Files remaining in queue: {self.__file_queue.qsize()}")
                
                # Clear console for clean progress display
                print("\n" * 2)  # Add extra space
                
                # Process the file with advanced statistics
                start_time = time.time()
                
                # Log performance monitoring si está habilitado
                if ENABLE_PERFORMANCE_MONITOR:
                    cpu_before = psutil.cpu_percent()
                    memory_before = psutil.virtual_memory().percent
                    logger.info(f"📊 System before processing - CPU: {cpu_before:.1f}% | Memory: {memory_before:.1f}%")
                
                try:
                    # Process the file - this will handle all internal logging
                    self.__processor.process_file(file_path)
                    processing_time = time.time() - start_time
                    
                    # Actualizar estadísticas avanzadas
                    self.__update_processing_stats(filename, processing_time, success=True)
                    
                    # Log performance después si está habilitado
                    if ENABLE_PERFORMANCE_MONITOR:
                        cpu_after = psutil.cpu_percent()
                        memory_after = psutil.virtual_memory().percent
                        logger.info(f"📊 System after processing - CPU: {cpu_after:.1f}% | Memory: {memory_after:.1f}%")
                    
                    # Clear any remaining progress output
                    print("\n" * 2)
                    
                    # Add completion separator
                    print("="*50)
                    logger.info(f"✅ FILE PROCESSING COMPLETED")
                    logger.info(f"📁 File: {filename}")
                    logger.info(f"⏰ End time: {time.strftime('%H:%M:%S')}")
                    logger.info(f"⏱️  Processing time: {processing_time:.2f} seconds")
                    logger.info(f"📊 Total processed: {self.__processing_stats['total_processed']}")
                    logger.info(f"📋 Files remaining in queue: {self.__file_queue.qsize()}")
                    print("\n")
                    
                except Exception as e:
                    processing_time = time.time() - start_time
                    self.__update_processing_stats(filename, processing_time, success=False)
                    
                    # Clear any remaining progress output
                    print("\n" * 2)
                    
                    # Add error separator
                    print("="*50)
                    logger.error(f"❌ FILE PROCESSING FAILED")
                    logger.error(f"📁 File: {filename}")
                    logger.error(f"⏰ Error time: {time.strftime('%H:%M:%S')}")
                    logger.error(f"⏱️  Processing time: {processing_time:.2f} seconds")
                    logger.error(f"💥 Error: {e}")
                    print("\n")
                
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
            Dict containing queue status information
        """
        return {
            'queue_size': self.__file_queue.qsize(),
            'max_queue_size': self.__max_queue_size,
            'is_processing': self.__current_file is not None,
            'current_file': os.path.basename(self.__current_file) if self.__current_file else "None",
            'total_processed': self.__processing_stats['total_processed'],
            'total_errors': self.__processing_stats['total_errors'],
            'files_moved_back': self.__processing_stats['files_moved_back'],
            'queue_utilization': f"{(self.__file_queue.qsize() / self.__max_queue_size) * 100:.1f}%"
        }
    
    def wait_for_queue_empty(self, timeout: Optional[float]=None) -> bool:
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
        
        if self.__worker_thread and self.__worker_thread.is_alive():
            self.__worker_thread.join(timeout=5.0)
        
        logger.info("File queue processor stopped")
    
    def get_processing_summary(self) -> str:
        """
        Get a summary of processing statistics
        
        Returns:
            String with processing summary
        """
        stats = self.__processing_stats
        queue_status = self.get_queue_status()
        
        # Calcular tiempo total de funcionamiento
        elapsed_time = time.time() - stats['start_time']
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        
        # Formatear tiempos de archivos más rápido/lento
        fastest_time = stats['fastest_file_time'] if stats['fastest_file_time'] != float('inf') else 0
        
        summary = f"""
📊 FILE QUEUE PROCESSING SUMMARY - ADAPTIVA Y OPTIMIZADA
{'='*60}
📁 Files Processed: {stats['total_processed']}
❌ Processing Errors: {stats['total_errors']}
📋 Current Queue: {queue_status['queue_size']}/{queue_status['max_queue_size']} ({queue_status['queue_utilization']})
📁 Files Moved Back: {stats['files_moved_back']}
⚙️  Currently Processing: {queue_status['current_file']}
⏰ Total Runtime: {elapsed_str}
⏱️  Total Processing Time: {stats['total_processing_time']:.1f}s
📊 Average Time per File: {stats['average_processing_time']:.1f}s
⚡ Fastest File: {stats['fastest_file']} ({fastest_time:.1f}s)
🐌 Slowest File: {stats['slowest_file']} ({stats['slowest_file_time']:.1f}s)
🚀 Throughput: {stats['throughput_files_per_hour']:.1f} files/hour
{'='*60}
"""
        return summary 
