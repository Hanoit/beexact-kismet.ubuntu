from __future__ import print_function
import json
import os
import sqlite3
import time
import csv
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from shapely.geometry import Point
from concurrent.futures import as_completed, ThreadPoolExecutor
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from services.SSIDForbidenRepository import SSIDForbiddenRepository
from utils import util
from utils.Log import Log
from models.ExtDeviceModel import ExtDeviceModel
from kismetanalyzer.util import does_ssid_matches
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('.env')


class KismetAnalyzer:
    def __init__(self, infile: str, session_factory, log):
        self.infile = infile
        self.devices = []
        self.__Session = session_factory
        self.__start_time = time.time()
        self.__total_rows = 0
        self.__log = log
        try:
            self.db = sqlite3.connect(self.infile)
        except Exception as e:
            raise RuntimeError(f"Failed to open kismet logfile: {e}")

    def process_row(self, row, list_SSID_forbidden, ssid, encryption, strongest, total_rows, current_index,
                    flip_coord):
        # Add unique sequential ID for tracking
        import threading
        sequential_id = f"R{current_index:06d}-T{threading.current_thread().ident % 10000:04d}"
        
        base = {
            'first_time': row[0],
            'last_time': row[1],
            'devkey': row[2],
            'phyname': row[3],
            'devmac': row[4],
            'strongest_signal': row[5],
            'min_lat': row[6],
            'min_lon': row[7],
            'max_lat': row[8],
            'max_lon': row[9],
            'avg_lat': row[10],
            'avg_lon': row[11],
            'bytes_data': row[12],
            'type': row[13],
            'sequential_id': sequential_id  # Add sequential ID to base
        }
        # Start a new session for each thread
        session: Session = self.__Session()
        try:
            dev_json_str = row[14].decode('utf-8')
            dev = json.loads(dev_json_str)

            if ssid and not does_ssid_matches(dev, ssid):
                return None

            if util.does_list_ssid_matches(dev, list_SSID_forbidden):
                return None

            # Create a new instance of ExtDeviceModel with the session
            extended_device = ExtDeviceModel(base=base, session=session)
            extended_device.from_json(dev, flip_coord, strongest=strongest)

            if encryption and encryption not in extended_device.encryption:
                return None

            if bool(int(os.getenv('ADVANCE_VERBOSE', 0))):
                logger.info(f"Processed record {current_index + 1}/{total_rows}\n "
                            f"Details: mac={extended_device.mac} - ssid={extended_device.ssid} - "
                            f"provider={extended_device.provider} - vendor={extended_device.vendor}")
            if bool(int(os.getenv('BASIC_VERBOSE', 0))):
                logger.info(f"Processed record {current_index + 1}/{total_rows}")

            return extended_device

        except ValueError as e:
            if str(e) == "Record does not location info":
                return None
            else:
                raise RuntimeError(f"An error occurred while processing the data \n {e}") from e
        except Exception as e:
            session.rollback()  # Ensure the session is rolled back on exception
            raise RuntimeError(f"An error occurred while processing the data\n {e}") from e
        finally:
            session.close()  # Close the session to free up resources

    def filter_near_coord(self, sql_result, flip_coord):
        # Check if we should process devices without location
        process_without_location = bool(int(os.getenv('PROCESS_WITHOUT_LOCATION', 1)))
        
        if not sql_result:
            return sql_result
            
        # Convert the SQL result into a DataFrame
        df = pd.DataFrame(sql_result, columns=[
            'first_time', 'last_time', 'devkey', 'phyname', 'devmac', 'strongest_signal',
            'min_lat', 'min_lon', 'max_lat', 'max_lon', 'avg_lat', 'avg_lon', 'bytes_data', 'type', 'device', 'unknow'
        ])
        
        # Check if all devices have zero coordinates
        all_zero_coords = (df['avg_lat'] == 0).all() and (df['avg_lon'] == 0).all()
        
        if all_zero_coords and process_without_location:
            logger.info("All devices have zero coordinates - skipping location-based filtering")
            # For devices without location, just keep the strongest signal per MAC
            df['mac_prefix'] = df['devmac'].str.replace(':', '').str[:8]
            filtered_df = df.loc[df.groupby('mac_prefix')['strongest_signal'].idxmax()]
            return filtered_df.drop(columns=['mac_prefix']).values.tolist()
        
        # Original location-based filtering logic
        if not flip_coord:
            # Create a GeoDataFrame with the geographic points
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.max_lon, df.max_lat), crs="EPSG:4326")
        else:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.max_lat, df.max_lon), crs="EPSG:4326")

        # Convertir a un CRS proyectado adecuado para medir distancias en metros
        gdf = gdf.to_crs(epsg=3857)

        # Group by the first 4 positions of the MAC address
        gdf['mac_prefix'] = df['devmac'].str.replace(':', '').str[:8]

        # Calculate the distance within each group using GeoPandas built-in functionality
        def filter_within_distance(group, max_distance=50):
            # Crear la matriz de distancias
            distance_matrix = group.geometry.apply(lambda geom: group.distance(geom)).values

            # Iterar sobre la matriz para eliminar los registros con señal más débil
            to_keep = set(range(len(group)))  # Indices de registros a mantener
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    if i in to_keep and j in to_keep:
                        if distance_matrix[i, j] <= max_distance:
                            # Comparar señales y eliminar el de señal más débil
                            if group.iloc[i]['strongest_signal'] > group.iloc[j]['strongest_signal']:
                                to_keep.discard(j)
                            else:
                                to_keep.discard(i)

            return group.iloc[list(to_keep)]

        # Apply the distance filter within each mac_prefix group
        filtered_gdf = gdf.groupby('mac_prefix').apply(filter_within_distance).reset_index(drop=True)

        # Convert back to original DataFrame format and return
        filtered_sql_result = filtered_gdf.drop(columns=['geometry', 'mac_prefix']).values.tolist()

        return filtered_sql_result

    def load_devices(self, ssid=None, encryption=None, strongest=False):
        try:
            count_sql = """
                   SELECT COUNT(*)
                   FROM devices
                   WHERE type = 'Wi-Fi AP';
            """

            cursor = self.db.cursor()
            cursor.execute(count_sql)
            total_records = cursor.fetchone()[0]
            logger.info(f"Total records before filtering: {total_records}")
            self.__log.write_log(f"Total records before filtering: {total_records}")
        except Exception as e:
            raise RuntimeError(f"Failed to count record from kismet file \n {e}") from e

        try:
            # Check if we should process devices without location
            process_without_location = bool(int(os.getenv('PROCESS_WITHOUT_LOCATION', 1)))
            
            if process_without_location:
                # Process devices even without location data
                sql = f"""
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
                logger.info("Processing devices without location data (PROCESS_WITHOUT_LOCATION=1)")
            else:
                # Original query - only devices with location
                sql = f"""
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
                logger.info("Processing only devices with location data (PROCESS_WITHOUT_LOCATION=0)")

            # Execute the query
            cursor = self.db.cursor()
            cursor.execute(sql)
            sql_result = cursor.fetchall()
            logger.info(f"Records after filtering: {len(sql_result)}")
            self.__log.write_log(f"Records after filtering: {len(sql_result)}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract data from database \n {e}") from e

        session = self.__Session()

        try:
            SSID_forbidden_repo = SSIDForbiddenRepository(session)
            list_SSID_forbidden = {ssid.ssid_name for ssid in SSID_forbidden_repo.get_all()}
        except Exception as e:
            raise RuntimeError(f"Failed to extract data from database \n {e}") from e
        finally:
            session.close()

        devs = []

        # Read the desired number of workers from the .env file
        desired_workers = int(os.getenv('NUM_WORKERS', 4))

        # Determine the maximum number of workers based on CPU count
        max_workers = min(desired_workers, os.cpu_count())

        self.__total_rows = len(sql_result)

        flip_coord = bool(os.getenv('FLIP_XY', 0))

        sql_result = self.filter_near_coord(sql_result, flip_coord)

        logger.info(f"Records after filtering by location and mac address: {len(sql_result)}")
        self.__log.write_log(f"Records after filtering by location and mac address: {len(sql_result)}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.process_row, row, list_SSID_forbidden, ssid, encryption, strongest,
                                self.__total_rows, index, flip_coord)
                for index, row in enumerate(sql_result)
            ]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing devices", ncols=100):
                result = future.result()
                if result:
                    devs.append(result)

        self.devices = devs
        return devs

    def export_csv(self, out_dir: str, delimiter=";"):

        # Check if the output directory exists
        if not os.path.exists(out_dir):
            raise FileNotFoundError(f"The output directory '{out_dir}' does not exist.")

        outfile = os.path.splitext(os.path.basename(self.infile))[0]
        out_path = os.path.join(out_dir, outfile)

        log_vendor_filename = f"{out_path}_NOT_VENDOR.log"
        log_vendor = Log(log_directory=out_dir, log_filename=log_vendor_filename)

        log_provider_filename = f"{out_path}_NOT_PROVIDER.log"
        log_provider = Log(log_directory=out_dir, log_filename=log_provider_filename)

        num_plotted = 0
        try:
            with open(f"{out_path}.csv", mode='w', encoding='utf-8', newline='') as csv_file:
                w = csv.writer(csv_file, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                w.writerow(['MAC_1', 'MAC_2', 'MAC_3', 'Provider', 'SSID', 'AuthMode', 'FirstSeen', 'Channel', 'RSSI',
                            'CurrentLatitude', 'CurrentLongitude', 'AltitudeMeters', 'AccuracyMeters', 'Type',
                            'MAC_ID_1', 'MAC_ID_2', 'Device', 'Vendor'])
                for dev in self.devices:
                    short_mac_id = util.format_mac_id(dev.mac, position=-3)
                    w.writerow([dev.mac, util.format_mac_id(dev.mac, position=None, separator=""),
                                util.format_mac_id(dev.mac, position=-2, separator=""), dev.provider, dev.ssid,
                                dev.encryption,
                                util.format_unix_timestamp_to_string(util.parse_date_utc(dev.firstSeen)),
                                dev.channel, dev.RSSI, dev.location.lat, dev.location.lon, dev.location.alt,
                                dev.accuracy_mt, dev.type, short_mac_id,
                                util.format_mac_id(dev.mac, position=-3, separator=""), dev.manufacturer, dev.vendor])
                    num_plotted += 1

                    if not dev.vendor:
                        # If vendor is not found, log the MAC address
                        log_vendor.write_log(f"{short_mac_id}")

                    if not dev.provider:
                        # If provider is not found, log the MAC address and SSID
                        log_provider.write_log(f"{short_mac_id}, {dev.ssid}")

            logger.info(f"Exported {num_plotted} devices to {outfile}.csv")
            self.__log.write_log(f"Exported {num_plotted} devices to {outfile}.csv")
            end_time = time.time()
            logger.info(f"Processed {self.__total_rows} devices in {end_time - self.__start_time:.2f} seconds.")
            self.__log.write_log(f"Processed {self.__total_rows} devices in {end_time - self.__start_time:.2f} seconds.")
        except IOError as e:
            raise IOError(f"IOError: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
