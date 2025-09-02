import os
import uuid
import time
import psutil
from models.DBKismetModels import ProcessedFileTable
from utils.Log import Log
from utils.KismetDiagnostic import KismetDiagnostic
from services.KismetAnalyzer import KismetAnalyzer
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('.env')

# ADAPTIVE CONFIGURATION FOR PERFORMANCE
CHUNK_SIZE = int(os.getenv('KISMET_CHUNK_SIZE', '10000'))
# Variables NUM_WORKERS y PROCESS_WORKERS eliminadas - no se usaban para paralelismo real
ENABLE_PERFORMANCE_MONITOR = os.getenv('ENABLE_PERFORMANCE_MONITOR', 'false').lower() == 'true'


class DirectoryFilesProcessor:

    def __init__(self, session_factory):
        self.__output_directory = os.getenv("OUT_DIRECTORY", ".")
        self.__Session = session_factory
        
        # Log performance configuration
        logger.info("DirectoryFilesProcessor Configuration - ADAPTIVA:")
        logger.info(f"  - Chunk Size: {CHUNK_SIZE:,} devices per chunk")
        logger.info(f"  - CPU cores: {multiprocessing.cpu_count()}")
        logger.info(f"  - Performance Monitor: {'Enabled' if ENABLE_PERFORMANCE_MONITOR else 'Disabled'}")

    def is_file_processed(self, filename):
        session = self.__Session()
        try:
            entry = session.query(ProcessedFileTable).filter_by(filename=filename).first()
            return entry is not None and entry.status
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_system_stats(self):
        """Get system statistics for performance monitoring"""
        if not ENABLE_PERFORMANCE_MONITOR:
            return {}
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024 ** 3),
                'disk_free_gb': disk.free / (1024 ** 3),
                'disk_percent': (disk.used / disk.total) * 100
            }
        except Exception as e:
            logger.warning(f"Error getting system stats: {e}")
            return {}

    def log_performance_stats(self, stats, stage=""):
        """Log performance statistics if enabled"""
        if not ENABLE_PERFORMANCE_MONITOR or not stats:
            return
        
        logger.info(f"📊 System Performance {stage}:")
        logger.info(f"  - CPU: {stats.get('cpu_percent', 0):.1f}%")
        logger.info(f"  - Memory: {stats.get('memory_percent', 0):.1f}% (Available: {stats.get('memory_available_gb', 0):.1f}GB)")
        logger.info(f"  - Disk: {stats.get('disk_percent', 0):.1f}% (Free: {stats.get('disk_free_gb', 0):.1f}GB)")

    def process_file(self, file_path: str) -> bool:
        """
        Process a single Kismet file with performance monitoring.
        
        Args:
            file_path (str): Path to the Kismet file to process
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            start_time = time.time()
            filename = os.path.basename(file_path)
            
            # Monitoreo inicial del sistema
            initial_stats = self.get_system_stats()
            self.log_performance_stats(initial_stats, "BEFORE PROCESSING")
            
            logger.info(f"🚀 Processing file {file_path}")
            logger.info("📋 Generating pre-processing diagnostic report...")
            
            # Generate pre-processing diagnostic
            diagnostic = KismetDiagnostic(self.__output_directory, filename)
            diagnostic.log_diagnostic_report(file_path)
            
            # Create log for KismetAnalyzer
            log_outfile = os.path.splitext(filename)[0]
            log = Log(log_directory=self.__output_directory, log_filename=f"{log_outfile}.log",
                     log_header=f"Kismet Files Processing {log_outfile} Log")
            
            # Process the file with performance monitoring
            logger.info("⚙️  Initializing KismetAnalyzer with optimized settings...")
            analyzer = KismetAnalyzer(file_path, self.__Session, log)
            
            # Monitoreo durante carga de dispositivos
            load_start = time.time()
            devices = analyzer.load_devices(strongest=True)
            load_time = time.time() - load_start
            
            # Log loading statistics
            device_count = len(devices) if devices else 0
            if device_count > 0:
                logger.info(f"📱 Loaded {device_count:,} devices in {load_time:.2f}s ({device_count/load_time:.0f} devices/sec)")
            
            # Monitoring during export
            export_start = time.time()
            analyzer.export_csv(self.__output_directory)
            export_time = time.time() - export_start
            
            if hasattr(analyzer, 'devices') and analyzer.devices:
                exported_count = len(analyzer.devices)
                logger.info(f"💾 Exported {exported_count:,} devices in {export_time:.2f}s ({exported_count/export_time:.0f} devices/sec)")
            
            # Mark file as processed
            self.mark_file_processed(filename)
            
            # Monitoreo final del sistema
            final_stats = self.get_system_stats()
            self.log_performance_stats(final_stats, "AFTER PROCESSING")
            
            # Generate post-processing diagnostic
            total_time = time.time() - start_time
            logger.info("📋 Generating post-processing diagnostic report...")
            processing_results = {
                'processed': len(devices) if devices else 0,
                'exported': len(analyzer.devices) if hasattr(analyzer, 'devices') and analyzer.devices else 0,
                'processing_time': total_time,
                'load_time': load_time,
                'export_time': export_time,
                'total_devices': diagnostic.get_summary(file_path)['total_devices'],
                'wifi_aps': diagnostic.get_summary(file_path)['wifi_aps'],
                'wifi_aps_with_signal': diagnostic.get_summary(file_path)['wifi_aps_with_signal']
            }
            diagnostic.log_diagnostic_report(file_path, processing_results)
            
            # Log completion summary
            logger.info("="*50)
            logger.info("📊 FILE PROCESSING COMPLETED SUCCESSFULLY")
            logger.info("="*50)
            logger.info(f"📁 File: {filename}")
            logger.info(f"📊 Total devices in file: {processing_results['total_devices']:,}")
            logger.info(f"📡 Wi-Fi APs found: {processing_results['wifi_aps']:,}")
            logger.info(f"📶 Wi-Fi APs with signal: {processing_results['wifi_aps_with_signal']:,}")
            logger.info(f"⚙️  Devices processed: {processing_results['processed']:,}")
            logger.info(f"💾 Devices exported to CSV: {processing_results['exported']:,}")
            logger.info(f"⏱️  Total processing time: {processing_results['processing_time']:.2f} seconds")
            logger.info(f"📥 Device load time: {processing_results['load_time']:.2f} seconds")
            logger.info(f"📤 CSV export time: {processing_results['export_time']:.2f} seconds")
            
            if processing_results['wifi_aps_with_signal'] > 0:
                efficiency = (processing_results['exported'] / processing_results['wifi_aps_with_signal']) * 100
                logger.info(f"📈 Processing efficiency: {efficiency:.1f}%")
            
            if processing_results['exported'] > 0:
                logger.info(f"✅ SUCCESS: {processing_results['exported']:,} devices exported to CSV")
            else:
                logger.warning(f"⚠️  WARNING: No devices exported (check filtering criteria)")
            
            logger.info("="*50)
            
            return True
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False

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
