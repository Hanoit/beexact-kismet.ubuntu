import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class EventHandler(FileSystemEventHandler):
    def __init__(self, processor, stability_time=5):
        self.__processor = processor
        self.__stability_time = stability_time

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            # Check if the file has a .kismet extension
            if filename.lower().endswith('.kismet'):
                if not self.__processor.is_file_processed(filename):
                    logger.info(f"New file detected: {filename}")
                    if self.__wait_for_file_stability(event.src_path):
                        logger.info(f"Processing file: {filename}")
                        self.__processor.process_file(event.src_path)
                    else:
                        logger.warning(f"File {filename} is not stable after waiting. Skipping processing.")

    def __wait_for_file_stability(self, file_path):
        previous_size = -1
        stable_count = 0

        while stable_count < self.__stability_time:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == previous_size:
                    stable_count += 1
                else:
                    stable_count = 0  # Reset count if file size changes
                    previous_size = current_size
                time.sleep(1)  # Check every second
            except FileNotFoundError:
                logger.error(f"File {file_path} not found during stability check.")
                return False
            except Exception as e:
                logger.error(f"Error while checking file stability for {file_path}: {e}")
                return False

        return True


class WatchingDirectory:
    def __init__(self, processor):
        self.__check_interval = int(os.getenv("CHECK_INTERVAL", 300))
        self.__directory = os.getenv("WATCH_DIRECTORY", ".")
        self.__processor = processor

    def start_watching(self):
        event_handler = EventHandler(self.__processor)
        observer = Observer()
        observer.schedule(event_handler, path=self.__directory, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(self.__check_interval)
        except KeyboardInterrupt:
            logger.info("Stopping directory watch...")
            observer.stop()
        observer.join()