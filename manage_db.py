import argparse
from database.DataDBManager import DataManager
from database.SessionKismetDB import get_session
from models.DBKismetModels import MACVendorTable, MACBaseProviderTable, SSIDForbiddenTable
from utils import util


def load_data(file_path, table_class, delimiter=',', operation='all'):
    """Load data from a file into the specified table."""
    session = get_session()
    manager = DataManager(table_class, session, delimiter)
    manager.process_file(file_path, operation)


def export_data_to_csv(output_file, table_class, delimiter=','):
    """Export data from the specified table to a CSV file."""
    session = get_session()
    util.export_tableDB_to_csv(session, table_class, output_file, delimiter)


def main():
    try:
        parser = argparse.ArgumentParser(description='Manage MAC vendor database operations.')
        parser.add_argument('operation', type=str, choices=['load', 'export'],
                            help='Operation to perform: load or export.')
        parser.add_argument('--file', type=str, help='The path to the input file (for loading data).')
        parser.add_argument('--output', type=str, help='The path to the output file (for exporting data).')
        parser.add_argument('--table', type=str, choices=['vendor', 'provider', 'ssid'], required=True,
                            help='Specify which table to operate on: vendor, provider, or ssid.')
        parser.add_argument('--delimiter', type=str, default=',', help='Delimiter used in the file.')
        parser.add_argument('--operation_type', type=str, choices=[util.Operation().insert, util.Operation().delete,
                                                                   util.Operation().update],
                            default=util.Operation().all,
                            help='Operation type to perform: insert, delete, or all (only applicable for load '
                                 'operation).')

        args = parser.parse_args()

        table_class_map = {
            'vendor': MACVendorTable,
            'provider': MACBaseProviderTable,
            'ssid': SSIDForbiddenTable
        }

        table_class = table_class_map[args.table]

        if args.operation == 'load':
            if not args.file:
                print("Please specify a file to load data from.")
                return
            load_data(args.file, table_class, args.delimiter, args.operation_type)
        elif args.operation == 'export':
            if not args.output:
                print("Please specify an output file to export data to.")
                return
            export_data_to_csv(args.output, table_class, args.delimiter)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
