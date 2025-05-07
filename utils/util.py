import csv
import datetime
import re
import uuid
from sqlalchemy import inspect
from services.MacVendorFinder import MacVendorFinder
from services.MacProviderFinder import MacProviderFinder
from typing import NamedTuple
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Operation(NamedTuple):
    insert: str = 'insert'
    update: str = 'update'
    delete: str = 'delete'
    all: str = 'all'


def does_list_ssid_matches(dev, list_ssid):
    """
    Checks if any word in the device SSID matches any SSID in the given list.

    :param dev: JSON string from the Kismet database column "device"
    :param list_ssid: List of SSID strings or regex patterns to match against

    :return: True if any SSID matches, false otherwise
    :rtype: boolean
    """
    device_ssid = dev.get('kismet.device.base.name', '')
    if not device_ssid:
        return False

    # Split the device_ssid into words
    device_words = set(device_ssid.lower().split())

    # Compile regex patterns and extract simple SSIDs
    regex_patterns = [re.compile(ssid, re.IGNORECASE) for ssid in list_ssid if any(c in ssid for c in ".^$*+?{}[]|()")]
    simple_ssids = {ssid.lower() for ssid in list_ssid if ssid not in regex_patterns}

    # Check if any word in device_ssid is in simple_ssids or matches any regex
    if device_words & simple_ssids:
        return True

    for pattern in regex_patterns:
        if any(pattern.search(word) for word in device_words):
            return True

    return False


def parse_signal(dev):
    try:
        signal = dev['kismet.device.base.signal']
        if signal:
            return signal['kismet.common.signal.last_signal']
        else:
            raise ValueError("The 'signal' is empty.")
    except Exception as e:
        raise e


def parse_seen(dev):
    try:
        first_seen = dev['kismet.device.base.first_time']
        return first_seen
    except Exception as e:
        raise e


def format_separator(mac_address, separator):
    formatted_mac = mac_address.replace(':', separator)
    return formatted_mac


def format_mac_id(mac_address, position=None, separator=":"):
    parts = mac_address.split(':')
    if len(parts) > 1:
        formatted_mac = f'{separator}'.join(parts[:position] if position is not None else parts)
        if separator != ":":
            return format_separator(formatted_mac, separator)
        else:
            return formatted_mac
    else:
        raise ValueError("This is not a mac address")


def parse_date_utc(value):
    try:
        return datetime.datetime.utcfromtimestamp(value)
    except Exception as e:
        raise e


def format_unix_timestamp_to_string(unix_timestamp, format_type='default'):
    """
    Converts a UNIX timestamp to a formatted date string.

    :param unix_timestamp: The UNIX timestamp to convert.
    :param format_type: The type of format to return the date string in.
    :return: A string representing the date and time in the specified format.
    """
    formatted_date = None
    if format_type == 'default':
        # Default format MM/DD/YYYY HH:MM
        formatted_date = unix_timestamp.strftime('%m/%d/%Y %H:%M')
    else:
        formatted_date = unix_timestamp.strftime(format_type)

    return formatted_date


def parse_vendor(mac_address, session):
    finder = MacVendorFinder(session)
    return finder.get_vendor(mac_address)


def parse_provider(mac_address, ssid, session):
    finder = MacProviderFinder(session)
    return finder.get_provider(mac_address, ssid)


def is_valid_uuid(value, version=4):
    """Validate if a string is a valid UUID."""
    try:
        uuid_obj = uuid.UUID(value, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == value


def validate_file(file_path):
    """Validate if the file is a CSV or TXT file."""
    return file_path.endswith('.csv') or file_path.endswith('.txt')


def is_uuid_column_orm(table_class, column_name):
    """Check if a column in the ORM class is a UUID."""
    column_type = table_class.__table__.c[column_name].type
    return isinstance(column_type, PGUUID)


def get_table_columns(session_factory, table_class):
    session = session_factory()
    try:
        """Get the primary key, column names, and check if it's a UUID from the ORM class."""
        inspector = inspect(session.get_bind())

        # Get primary key from ORM
        primary_key = next(iter(table_class.__table__.primary_key.columns)).name

        # Get all column names from ORM
        columns = [column.name for column in table_class.__table__.columns]

        # Check if the primary key is a UUID based on the ORM class definition
        is_uuid_primary_key = is_uuid_column_orm(table_class, primary_key)

        return primary_key, columns, is_uuid_primary_key
    except Exception as e:
        raise e
    finally:
        session.close()


def export_tableDB_to_csv(session_factory, table_class, output_file, delimiter=','):
    session = session_factory()
    try:
        """Export table data to a CSV file."""
        data = session.query(table_class).all()
        with open(f"../data/{output_file}", mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Write header
            header = [column.name for column in table_class.__table__.columns]
            writer.writerow(header)
            # Write data rows
            for row in data:
                writer.writerow([getattr(row, column) for column in header])
        logger.info(f"Data exported successfully to {output_file}.")
    except Exception as e:
        raise e
    finally:
        session.close()


