#!/usr/bin/env python3
"""
Diagnostic script to analyze Kismet file content
"""
import sqlite3
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_kismet_file(file_path):
    """Analyze the content of a Kismet file to understand the data structure"""
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return
    
    print(f"Analyzing Kismet file: {file_path}")
    print("=" * 60)
    
    try:
        # Connect to the Kismet database
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables found: {[table[0] for table in tables]}")
        print()
        
        # Analyze devices table
        if ('devices',) in tables:
            print("DEVICES TABLE ANALYSIS:")
            print("-" * 30)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM devices")
            total_devices = cursor.fetchone()[0]
            print(f"Total devices: {total_devices}")
            
            # Get device types
            cursor.execute("SELECT type, COUNT(*) FROM devices GROUP BY type")
            device_types = cursor.fetchall()
            print(f"Device types: {device_types}")
            
            # Get devices with location
            cursor.execute("SELECT COUNT(*) FROM devices WHERE avg_lat <> 0 OR avg_lon <> 0")
            devices_with_location = cursor.fetchone()[0]
            print(f"Devices with location: {devices_with_location}")
            
            # Get devices with signal
            cursor.execute("SELECT COUNT(*) FROM devices WHERE strongest_signal <> 0")
            devices_with_signal = cursor.fetchone()[0]
            print(f"Devices with signal: {devices_with_signal}")
            
            # Get Wi-Fi APs
            cursor.execute("SELECT COUNT(*) FROM devices WHERE type = 'Wi-Fi AP'")
            wifi_aps = cursor.fetchone()[0]
            print(f"Wi-Fi APs: {wifi_aps}")
            
            # Get Wi-Fi APs with location and signal
            cursor.execute("""
                SELECT COUNT(*) FROM devices 
                WHERE type = 'Wi-Fi AP' 
                AND strongest_signal <> 0 
                AND (avg_lat <> 0 OR avg_lon <> 0)
            """)
            wifi_aps_with_location_signal = cursor.fetchone()[0]
            print(f"Wi-Fi APs with location and signal: {wifi_aps_with_location_signal}")
            
            # Show sample data
            print("\nSAMPLE DATA:")
            print("-" * 30)
            cursor.execute("""
                SELECT devmac, type, strongest_signal, avg_lat, avg_lon, phyname
                FROM devices 
                LIMIT 10
            """)
            sample_data = cursor.fetchall()
            for row in sample_data:
                print(f"MAC: {row[0]}, Type: {row[1]}, Signal: {row[2]}, Lat: {row[3]}, Lon: {row[4]}, Phy: {row[5]}")
            
            # Show Wi-Fi APs specifically
            print("\nWI-FI APs SAMPLE:")
            print("-" * 30)
            cursor.execute("""
                SELECT devmac, strongest_signal, avg_lat, avg_lon, phyname
                FROM devices 
                WHERE type = 'Wi-Fi AP'
                LIMIT 10
            """)
            wifi_sample = cursor.fetchall()
            for row in wifi_sample:
                print(f"MAC: {row[0]}, Signal: {row[1]}, Lat: {row[2]}, Lon: {row[3]}, Phy: {row[4]}")
            
            # Check for devices with different types
            print("\nALL DEVICE TYPES WITH COUNTS:")
            print("-" * 30)
            cursor.execute("""
                SELECT type, COUNT(*) as count, 
                       SUM(CASE WHEN strongest_signal <> 0 THEN 1 ELSE 0 END) as with_signal,
                       SUM(CASE WHEN avg_lat <> 0 OR avg_lon <> 0 THEN 1 ELSE 0 END) as with_location
                FROM devices 
                GROUP BY type
                ORDER BY count DESC
            """)
            type_analysis = cursor.fetchall()
            for row in type_analysis:
                print(f"Type: {row[0]}, Total: {row[1]}, With Signal: {row[2]}, With Location: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        return

def test_sql_query(file_path):
    """Test the exact SQL query used in the application"""
    
    print(f"\nTESTING SQL QUERY:")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Test the exact query from KismetAnalyzer
        sql = """
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
        
        cursor.execute(sql)
        result = cursor.fetchall()
        print(f"Query result count: {len(result)}")
        
        if len(result) > 0:
            print("First few results:")
            for i, row in enumerate(result[:5]):
                print(f"Row {i+1}: MAC={row[4]}, Signal={row[5]}, Lat={row[10]}, Lon={row[11]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error testing SQL query: {e}")

if __name__ == '__main__':
    # Get file path from command line or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Use the file mentioned in the logs
        file_path = "/opt/kismetFiles/Kismet-20250403-13-58-41-1.kismet"
    
    analyze_kismet_file(file_path)
    test_sql_query(file_path) 