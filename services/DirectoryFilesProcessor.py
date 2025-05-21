import os
import uuid
import time
from models.DBKismetModels import ProcessedFileTable
from utils.Log import Log
from utils.KismetDiagnostic import KismetDiagnostic
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
        start_time = time.time()
        filename = os.path.basename(file_path)
        log_outfile = os.path.splitext(filename)[0]
        
        # Create processing log
        log = Log(log_directory=self.__output_directory, log_filename=f"{log_outfile}.log",
                  log_header=f"Kismet Files Processing {log_outfile} Log")
        
        # Create diagnostic utility
        diagnostic = KismetDiagnostic(self.__output_directory, filename)
        
        try:
            logger.info(f"Processing file {file_path}")
            
            # Generate pre-processing diagnostic report
            logger.info("Generating pre-processing diagnostic report...")
            diagnostic.log_diagnostic_report(file_path)
            
            # Process the file
            analyzer = KismetAnalyzer(file_path, self.__Session, log)
            devices = analyzer.load_devices(strongest=True)
            analyzer.export_csv(self.__output_directory)
            
            # Calculate processing results
            processing_time = time.time() - start_time
            devices_processed = len(devices) if devices else 0
            devices_exported = len(analyzer.devices) if hasattr(analyzer, 'devices') and analyzer.devices else 0
            
            processing_results = {
                'processed': devices_processed,
                'exported': devices_exported,
                'processing_time': processing_time,
                'total_devices': diagnostic.get_summary(file_path)['total_devices'],
                'wifi_aps': diagnostic.get_summary(file_path)['wifi_aps'],
                'wifi_aps_with_signal': diagnostic.get_summary(file_path)['wifi_aps_with_signal']
            }
            
            # Generate post-processing diagnostic report
            logger.info("Generating post-processing diagnostic report...")
            diagnostic.log_diagnostic_report(file_path, processing_results)
            
            # Mark file as processed
            self.mark_file_processed(filename)
            
            # Log clear summary
            logger.info("=" * 60)
            logger.info("📊 PROCESSING COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"📁 File: {filename}")
            logger.info(f"📊 Total devices in file: {processing_results['total_devices']:,}")
            logger.info(f"📡 Wi-Fi APs found: {processing_results['wifi_aps']:,}")
            logger.info(f"📶 Wi-Fi APs with signal: {processing_results['wifi_aps_with_signal']:,}")
            logger.info(f"⚙️  Devices processed: {processing_results['processed']:,}")
            logger.info(f"💾 Devices exported to CSV: {processing_results['exported']:,}")
            logger.info(f"⏱️  Processing time: {processing_results['processing_time']:.2f} seconds")
            
            if processing_results['wifi_aps_with_signal'] > 0:
                efficiency = (processing_results['exported'] / processing_results['wifi_aps_with_signal']) * 100
                logger.info(f"📈 Processing efficiency: {efficiency:.1f}%")
            
            if processing_results['exported'] > 0:
                logger.info(f"✅ SUCCESS: {processing_results['exported']:,} devices exported to CSV")
            else:
                logger.warning(f"⚠️  WARNING: No devices exported (check filtering criteria)")
            
            logger.info("=" * 60)
            
        except Exception as e:
            self.mark_file_error(filename, str(e))
            log.write_log_error(f"Error processing {file_path}: {e}")
            
            # Generate error diagnostic report
            diagnostic.log_diagnostic_report(file_path, {'error': str(e)})
            
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