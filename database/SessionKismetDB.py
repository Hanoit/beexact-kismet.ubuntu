from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models.DBKismetModels import get_base
from dotenv import load_dotenv
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

Base = get_base()


def get_session():
    try:
        current_dir = os.getenv("DB_DIRECTORY", ".")

        if current_dir == ".":
            try:
                current_dir = sys._MEIPASS
            except AttributeError:
                pass

        # Check if the output directory exists
        if not os.path.exists(current_dir):
            raise FileNotFoundError(f"The Database directory '{current_dir}' does not exist.")

        db_path = os.path.join(current_dir, "kismet.db")

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"The Database '{db_path}' does not exist.")

        logger.info(f"Connecting to database at '{db_path}'")
        engine = create_engine(f'sqlite:///{db_path}', connect_args={'timeout': 10}, pool_size=20, max_overflow=10)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        logger.info(f"Database connected'")
        return scoped_session(session_factory)
    except Exception as e:
        raise e