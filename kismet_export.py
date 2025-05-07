from database.SessionKismetDB import get_session
from services.DirectoryFilesProcessor import DirectoryFilesProcessor
from services.WatchingDirectory import WatchingDirectory
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Initialize the database session
        session = get_session()
        # Initialize the file processor
        processor = DirectoryFilesProcessor(session)
        # Initialize and start the directory watcher
        watch_dir = WatchingDirectory(processor)
        logger.info("Starting to watch directory...")
        watch_dir.start_watching()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
