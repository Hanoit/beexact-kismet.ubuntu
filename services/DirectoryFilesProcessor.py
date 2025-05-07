import os
import uuid
from models.DBKismetModels import ProcessedFileTable
from utils.Log import Log
from services.KismetAnalyzer import KismetAnalyzer
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class DirectoryFilesProcessor:
    def __init__(self, session_factory):
        self.__output_directory = os.getenv("OUT_DIRECTORY", ".")
        self.__Session = session_factory

    def is_file_processed(self, filename):
        session = self.__Session()
        try:
            entry = session.query(ProcessedFileTable).filter_by(filename=filename).first()
            return entry is not None and entry.status
        except Exception as e:
            raise e
        finally:
            session.close()

    def process_file(self, file_path):
        log_outfile = os.path.splitext(os.path.basename(file_path))[0]
        log = Log(log_directory=self.__output_directory, log_filename=f"{log_outfile}.log",
                  log_header=f"Kismet Files Processing {log_outfile} Log")
        try:
            logger.info(f"processing file {file_path}")
            analyzer = KismetAnalyzer(file_path, self.__Session, log)
            analyzer.load_devices(strongest=True)
            analyzer.export_csv(self.__output_directory)
            self.mark_file_processed(os.path.basename(file_path))
        except Exception as e:
            self.mark_file_error(os.path.basename(file_path), str(e))
            log.write_log_error(f"Error processing {file_path}: {e}")
            raise e

    def mark_file_processed(self, filename):
        session = self.__Session()
        try:
            entry = session.query(ProcessedFileTable).filter_by(filename=filename).first()
            if not entry:
                entry = ProcessedFileTable(id=str(uuid.uuid4()), filename=filename, status=True)
            else:
                entry.status = True
                entry.error_message = None
            session.add(entry)
            session.commit()
        except Exception as e:
            raise e
        finally:
            session.close()

    def mark_file_error(self, filename, error_message):
        session = self.__Session()
        try:
            entry = session.query(ProcessedFileTable).filter_by(filename=filename).first()
            if not entry:
                entry = ProcessedFileTable(id=str(uuid.uuid4()), filename=filename, status=False,
                                           error_message=error_message)
            else:
                entry.status = False
                entry.error_message = error_message
            session.add(entry)
            session.commit()
        except Exception as e:
            raise e
        finally:
            session.close()