import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import logging
from utils.file_monitor import FileStabilityMonitor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class EventHandler(FileSystemEventHandler):
    def __init__(self, processor, stability_time=5):
        self.__processor = processor
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
                        logger.info(f"File {filename} is stable and accessible, starting processing...")
                        try:
                            self.__processor.process_file(event.src_path)
                            logger.info(f"Successfully processed file: {filename}")
                        except Exception as e:
                            logger.error(f"Error processing file {filename}: {e}")
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
        
        # Validate directory exists
        if not os.path.exists(self.__directory):
            raise FileNotFoundError(f"Watch directory '{self.__directory}' does not exist")
        
        logger.info(f"Initialized WatchingDirectory with:")
        logger.info(f"  - Watch directory: {self.__directory}")
        logger.info(f"  - Check interval: {self.__check_interval} seconds")

    def start_watching(self):
        logger.info(f"Starting to watch directory: {self.__directory}")
        
        event_handler = EventHandler(self.__processor)
        observer = Observer()
        
        try:
            observer.schedule(event_handler, path=self.__directory, recursive=False)
            observer.start()
            logger.info("Directory watcher started successfully")
            
            try:
                while True:
                    time.sleep(self.__check_interval)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping directory watch...")
            except Exception as e:
                logger.error(f"Unexpected error in watching loop: {e}")
            finally:
                observer.stop()
                observer.join()
                logger.info("Directory watcher stopped")
                
        except Exception as e:
            logger.error(f"Error starting directory watcher: {e}")
            raise