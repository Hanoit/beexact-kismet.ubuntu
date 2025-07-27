import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import logging
from utils.file_monitor import FileStabilityMonitor
from services.FileQueueProcessor import FileQueueProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class EventHandler(FileSystemEventHandler):
    def __init__(self, processor, stability_time=5):
        self.__processor = processor
        self.__queue_processor = FileQueueProcessor(processor, max_queue_size=10)
        self.__stability_monitor = FileStabilityMonitor(
            stability_time=stability_time,
            max_wait_time=300,  # 5 minutes max wait
            check_interval=1.0
        )

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            # Check if the file has a .kismet extension
            if filename.lower().endswith('.kismet'):
                logger.info(f"New .kismet file detected: {filename}")
                
                # Check if file is already processed
                if self.__processor.is_file_processed(filename):
                    logger.info(f"File {filename} already processed, skipping")
                    return
                
                # Wait for file to be completely written and accessible
                logger.info(f"Waiting for file {filename} to be completely written...")
                
                # First wait for file stability
                if self.__stability_monitor.wait_for_stability(event.src_path):
                    # Then wait for file accessibility
                    if self.__stability_monitor.wait_for_accessibility(event.src_path, timeout=30):
                        logger.info(f"File {filename} is stable and accessible, adding to processing queue...")
                        
                        # Add file to processing queue instead of processing immediately
                        if self.__queue_processor.add_file_to_queue(event.src_path):
                            logger.info(f"✅ File {filename} added to processing queue")
                        else:
                            logger.warning(f"⚠️  Could not add file {filename} to queue (queue full or already queued)")
                    else:
                        logger.warning(f"File {filename} is not accessible after stability check. Skipping processing.")
                else:
                    logger.warning(f"File {filename} is not stable after waiting. Skipping processing.")
            else:
                logger.debug(f"Non-kismet file detected: {filename}")




class WatchingDirectory:
    def __init__(self, processor):
        self.__check_interval = int(os.getenv("CHECK_INTERVAL", 300))
        self.__directory = os.getenv("WATCH_DIRECTORY", ".")
        self.__processor = processor
        self.__queue_processor = None
        
        # Validate directory exists
        if not os.path.exists(self.__directory):
            raise FileNotFoundError(f"Watch directory '{self.__directory}' does not exist")
        
        logger.info(f"Initialized WatchingDirectory with:")
        logger.info(f"  - Watch directory: {self.__directory}")
        logger.info(f"  - Check interval: {self.__check_interval} seconds")

    def start_watching(self):
        logger.info(f"Starting to watch directory: {self.__directory}")
        
        event_handler = EventHandler(self.__processor)
        self.__queue_processor = event_handler._EventHandler__queue_processor
        observer = Observer()
        
        try:
            observer.schedule(event_handler, path=self.__directory, recursive=False)
            observer.start()
            logger.info("Directory watcher started successfully")
            
            # Log initial status
            self.__log_queue_status()
            
            try:
                while True:
                    time.sleep(self.__check_interval)
                    # Log queue status periodically
                    self.__log_queue_status()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping directory watch...")
            except Exception as e:
                logger.error(f"Unexpected error in watching loop: {e}")
            finally:
                # Stop queue processor
                if self.__queue_processor:
                    self.__queue_processor.stop()
                
                observer.stop()
                observer.join()
                logger.info("Directory watcher stopped")
                
        except Exception as e:
            logger.error(f"Error starting directory watcher: {e}")
            raise
    
    def __log_queue_status(self):
        """Log current queue status"""
        if self.__queue_processor:
            status = self.__queue_processor.get_queue_status()
            if status['is_processing'] or status['queue_size'] > 0:
                logger.info(f"📊 Queue Status: {status['queue_size']} files queued, "
                           f"processing: {status['current_file'] or 'None'}")
    
    def get_queue_summary(self) -> str:
        """Get queue processing summary"""
        if self.__queue_processor:
            return self.__queue_processor.get_processing_summary()
        return "Queue processor not available"