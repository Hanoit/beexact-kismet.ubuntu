"""
Kismet Diagnostic Utility
Generates detailed diagnostic reports for Kismet file processing
"""
import sqlite3
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from utils.Log import Log
import logging

logger = logging.getLogger(__name__)


class KismetDiagnostic:
    """
    Diagnostic utility for analyzing Kismet files and generating detailed reports
    """
    
    def __init__(self, log_directory: str, filename: str):
        """
        Initialize the diagnostic utility
        
        Args:
            log_directory: Directory where log files will be saved
            filename: Name of the Kismet file being processed
        """
        self.log_directory = log_directory
        self.filename = filename
        self.log_filename = f"{os.path.splitext(filename)[0]}_DIAGNOSTIC.log"
        self.diagnostic_log = Log(
            log_directory=log_directory,
            log_filename=self.log_filename,
            log_header=f"KISMET DIAGNOSTIC REPORT - {filename}"
        )
        self.start_time = time.time()
        
    def analyze_file_structure(self, file_path: str) -> Dict:
        """
        Analyze the structure of a Kismet file
        
        Args:
            file_path: Path to the Kismet file
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'file_exists': False,
            'file_size': 0,
            'tables': [],
            'total_devices': 0,
            'device_types': {},
            'location_stats': {},
            'signal_stats': {},
            'processing_mode': 'unknown'
        }
        
        try:
            if not os.path.exists(file_path):
                self.diagnostic_log.write_log(f"ERROR: File {file_path} does not exist")
                return analysis
                
            analysis['file_exists'] = True
            analysis['file_size'] = os.path.getsize(file_path)
            
            # Connect to database
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            analysis['tables'] = tables
            
            if 'devices' not in tables:
                self.diagnostic_log.write_log("ERROR: No 'devices' table found in Kismet file")
                conn.close()
                return analysis
                
            # Analyze devices table
            cursor.execute("SELECT COUNT(*) FROM devices")
            analysis['total_devices'] = cursor.fetchone()[0]
            
            # Device types analysis
            cursor.execute("SELECT type, COUNT(*) FROM devices GROUP BY type ORDER BY COUNT(*) DESC")
            device_types = cursor.fetchall()
            analysis['device_types'] = {row[0]: row[1] for row in device_types}
            
            # Location analysis
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN avg_lat <> 0 OR avg_lon <> 0 THEN 1 ELSE 0 END) as with_location,
                    SUM(CASE WHEN avg_lat = 0 AND avg_lon = 0 THEN 1 ELSE 0 END) as without_location
                FROM devices
            """)
            location_stats = cursor.fetchone()
            analysis['location_stats'] = {
                'total': location_stats[0],
                'with_location': location_stats[1],
                'without_location': location_stats[2],
                'location_percentage': (location_stats[1] / location_stats[0] * 100) if location_stats[0] > 0 else 0
            }
            
            # Signal analysis
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN strongest_signal <> 0 THEN 1 ELSE 0 END) as with_signal,
                    SUM(CASE WHEN strongest_signal = 0 THEN 1 ELSE 0 END) as without_signal,
                    AVG(strongest_signal) as avg_signal,
                    MIN(strongest_signal) as min_signal,
                    MAX(strongest_signal) as max_signal
                FROM devices
                WHERE strongest_signal <> 0
            """)
            signal_stats = cursor.fetchone()
            analysis['signal_stats'] = {
                'total': signal_stats[0],
                'with_signal': signal_stats[1],
                'without_signal': signal_stats[2],
                'avg_signal': signal_stats[3],
                'min_signal': signal_stats[4],
                'max_signal': signal_stats[5],
                'signal_percentage': (signal_stats[1] / signal_stats[0] * 100) if signal_stats[0] > 0 else 0
            }
            
            # Determine processing mode
            if analysis['location_stats']['with_location'] == 0:
                analysis['processing_mode'] = 'without_location'
            else:
                analysis['processing_mode'] = 'with_location'
                
            conn.close()
            
        except Exception as e:
            self.diagnostic_log.write_log_error(f"Error analyzing file structure: {e}")
            
        return analysis
    
    def test_sql_queries(self, file_path: str) -> Dict:
        """
        Test the SQL queries used in processing
        
        Args:
            file_path: Path to the Kismet file
            
        Returns:
            Dictionary with query test results
        """
        results = {
            'original_query': 0,
            'modified_query': 0,
            'wifi_aps_total': 0,
            'wifi_aps_with_signal': 0,
            'wifi_aps_with_location': 0
        }
        
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Test original query (with location requirement)
            original_sql = """
                WITH RankedDevices AS (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (PARTITION BY devmac ORDER BY strongest_signal DESC) as rn
                    FROM devices
                    WHERE type = 'Wi-Fi AP'
                )
                SELECT * 
                FROM RankedDevices 
                WHERE rn = 1 
                  AND strongest_signal <> 0 
                  AND (avg_lat <> 0 OR avg_lon <> 0);
            """
            cursor.execute(original_sql)
            results['original_query'] = len(cursor.fetchall())
            
            # Test modified query (without location requirement)
            modified_sql = """
                WITH RankedDevices AS (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (PARTITION BY devmac ORDER BY strongest_signal DESC) as rn
                    FROM devices
                    WHERE type = 'Wi-Fi AP'
                )
                SELECT * 
                FROM RankedDevices 
                WHERE rn = 1 
                  AND strongest_signal <> 0;
            """
            cursor.execute(modified_sql)
            results['modified_query'] = len(cursor.fetchall())
            
            # Get Wi-Fi AP statistics
            cursor.execute("SELECT COUNT(*) FROM devices WHERE type = 'Wi-Fi AP'")
            results['wifi_aps_total'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM devices WHERE type = 'Wi-Fi AP' AND strongest_signal <> 0")
            results['wifi_aps_with_signal'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM devices WHERE type = 'Wi-Fi AP' AND (avg_lat <> 0 OR avg_lon <> 0)")
            results['wifi_aps_with_location'] = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as e:
            self.diagnostic_log.write_log_error(f"Error testing SQL queries: {e}")
            
        return results
    
    def generate_diagnostic_report(self, file_path: str, processing_results: Dict = None) -> str:
        """
        Generate a comprehensive diagnostic report
        
        Args:
            file_path: Path to the Kismet file
            processing_results: Results from processing (optional)
            
        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"KISMET FILE DIAGNOSTIC REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"File: {self.filename}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Processing Time: {time.time() - self.start_time:.2f} seconds")
        report_lines.append("")
        
        # File structure analysis
        report_lines.append("FILE STRUCTURE ANALYSIS:")
        report_lines.append("-" * 40)
        analysis = self.analyze_file_structure(file_path)
        
        if analysis['file_exists']:
            report_lines.append(f"✓ File exists: {file_path}")
            report_lines.append(f"✓ File size: {analysis['file_size']:,} bytes ({analysis['file_size'] / 1024 / 1024:.2f} MB)")
            report_lines.append(f"✓ Tables found: {', '.join(analysis['tables'])}")
            report_lines.append(f"✓ Total devices: {analysis['total_devices']:,}")
            report_lines.append("")
            
            # Device types
            report_lines.append("DEVICE TYPES:")
            report_lines.append("-" * 20)
            for device_type, count in analysis['device_types'].items():
                percentage = (count / analysis['total_devices'] * 100) if analysis['total_devices'] > 0 else 0
                report_lines.append(f"  {device_type}: {count:,} ({percentage:.1f}%)")
            report_lines.append("")
            
            # Location statistics
            report_lines.append("LOCATION STATISTICS:")
            report_lines.append("-" * 25)
            loc_stats = analysis['location_stats']
            report_lines.append(f"  Total devices: {loc_stats['total']:,}")
            report_lines.append(f"  With location: {loc_stats['with_location']:,} ({loc_stats['location_percentage']:.1f}%)")
            report_lines.append(f"  Without location: {loc_stats['without_location']:,} ({100 - loc_stats['location_percentage']:.1f}%)")
            report_lines.append("")
            
            # Signal statistics
            report_lines.append("SIGNAL STATISTICS:")
            report_lines.append("-" * 20)
            sig_stats = analysis['signal_stats']
            report_lines.append(f"  Total devices: {sig_stats['total']:,}")
            report_lines.append(f"  With signal: {sig_stats['with_signal']:,} ({sig_stats['signal_percentage']:.1f}%)")
            report_lines.append(f"  Without signal: {sig_stats['without_signal']:,} ({100 - sig_stats['signal_percentage']:.1f}%)")
            if sig_stats['avg_signal']:
                report_lines.append(f"  Average signal: {sig_stats['avg_signal']:.1f} dBm")
                report_lines.append(f"  Signal range: {sig_stats['min_signal']:.1f} to {sig_stats['max_signal']:.1f} dBm")
            report_lines.append("")
            
            # Processing mode
            report_lines.append("PROCESSING MODE:")
            report_lines.append("-" * 15)
            if analysis['processing_mode'] == 'without_location':
                report_lines.append("⚠️  NO LOCATION DATA DETECTED")
                report_lines.append("   Processing will use devices without GPS coordinates")
                report_lines.append("   Consider enabling GPS in Kismet for better results")
            else:
                report_lines.append("✓ Location data available")
                report_lines.append("   Processing will use GPS coordinates for filtering")
            report_lines.append("")
            
            # SQL query test results
            report_lines.append("SQL QUERY ANALYSIS:")
            report_lines.append("-" * 20)
            query_results = self.test_sql_queries(file_path)
            report_lines.append(f"  Wi-Fi APs total: {query_results['wifi_aps_total']:,}")
            report_lines.append(f"  Wi-Fi APs with signal: {query_results['wifi_aps_with_signal']:,}")
            report_lines.append(f"  Wi-Fi APs with location: {query_results['wifi_aps_with_location']:,}")
            report_lines.append(f"  Original query results: {query_results['original_query']:,}")
            report_lines.append(f"  Modified query results: {query_results['modified_query']:,}")
            report_lines.append("")
            
            # Processing results (if available)
            if processing_results:
                report_lines.append("PROCESSING RESULTS:")
                report_lines.append("-" * 20)
                
                # Show clear processing summary
                total_devices = analysis['total_devices']
                wifi_aps = query_results['wifi_aps_total']
                wifi_aps_with_signal = query_results['wifi_aps_with_signal']
                processed = processing_results.get('processed', 0)
                exported = processing_results.get('exported', 0)
                processing_time = processing_results.get('processing_time', 0)
                
                report_lines.append(f"  📊 PROCESSING SUMMARY:")
                report_lines.append(f"     • Total devices in file: {total_devices:,}")
                report_lines.append(f"     • Wi-Fi APs found: {wifi_aps:,}")
                report_lines.append(f"     • Wi-Fi APs with signal: {wifi_aps_with_signal:,}")
                report_lines.append(f"     • Devices processed: {processed:,}")
                report_lines.append(f"     • Devices exported to CSV: {exported:,}")
                report_lines.append(f"     • Processing time: {processing_time:.2f} seconds")
                report_lines.append("")
                
                # Show processing efficiency
                if wifi_aps_with_signal > 0:
                    processing_efficiency = (exported / wifi_aps_with_signal) * 100
                    report_lines.append(f"  📈 PROCESSING EFFICIENCY:")
                    report_lines.append(f"     • Processing rate: {processing_efficiency:.1f}% ({exported}/{wifi_aps_with_signal})")
                    report_lines.append(f"     • Devices per second: {exported/processing_time:.1f}" if processing_time > 0 else "     • Devices per second: N/A")
                    report_lines.append("")
                
                # Show what was filtered out
                if wifi_aps_with_signal > exported:
                    filtered_out = wifi_aps_with_signal - exported
                    report_lines.append(f"  🔍 FILTERING RESULTS:")
                    report_lines.append(f"     • Devices filtered out: {filtered_out:,}")
                    report_lines.append(f"     • Filtering reasons: SSID forbidden, encryption mismatch, etc.")
                    report_lines.append("")
                
                # Show final status
                if exported > 0:
                    report_lines.append(f"  ✅ SUCCESS: {exported:,} devices exported to CSV file")
                else:
                    report_lines.append(f"  ⚠️  WARNING: No devices exported (check filtering criteria)")
                report_lines.append("")
            
            # Recommendations
            report_lines.append("RECOMMENDATIONS:")
            report_lines.append("-" * 15)
            if analysis['processing_mode'] == 'without_location':
                report_lines.append("• Enable GPS in Kismet for better location accuracy")
                report_lines.append("• Consider using external GPS device")
                report_lines.append("• Verify GPS configuration in Kismet")
            if query_results['wifi_aps_total'] == 0:
                report_lines.append("• No Wi-Fi APs found - check capture settings")
                report_lines.append("• Verify wireless interface configuration")
            if query_results['wifi_aps_with_signal'] == 0:
                report_lines.append("• No Wi-Fi APs with signal data - check antenna/positioning")
            report_lines.append("• Review Kismet configuration for optimal capture")
            
        else:
            report_lines.append(f"✗ File not found: {file_path}")
            
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def log_diagnostic_report(self, file_path: str, processing_results: Dict = None):
        """
        Generate and log the diagnostic report
        
        Args:
            file_path: Path to the Kismet file
            processing_results: Results from processing (optional)
        """
        try:
            report = self.generate_diagnostic_report(file_path, processing_results)
            
            # Log to diagnostic file only (no console output)
            self.diagnostic_log.write_log(report)
            
            logger.info(f"Diagnostic report saved to: {self.diagnostic_log.logFilePath}")
            
        except Exception as e:
            logger.error(f"Error generating diagnostic report: {e}")
            self.diagnostic_log.write_log_error(f"Error generating diagnostic report: {e}")
    
    def get_summary(self, file_path: str) -> Dict:
        """
        Get a quick summary of the file for logging
        
        Args:
            file_path: Path to the Kismet file
            
        Returns:
            Summary dictionary
        """
        analysis = self.analyze_file_structure(file_path)
        query_results = self.test_sql_queries(file_path)
        
        return {
            'filename': self.filename,
            'file_size_mb': analysis['file_size'] / 1024 / 1024 if analysis['file_exists'] else 0,
            'total_devices': analysis['total_devices'],
            'wifi_aps': query_results['wifi_aps_total'],
            'wifi_aps_with_signal': query_results['wifi_aps_with_signal'],
            'wifi_aps_with_location': query_results['wifi_aps_with_location'],
            'processing_mode': analysis['processing_mode'],
            'location_percentage': analysis['location_stats'].get('location_percentage', 0),
            'signal_percentage': analysis['signal_stats'].get('signal_percentage', 0)
        } 