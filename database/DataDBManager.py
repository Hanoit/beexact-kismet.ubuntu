import csv

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from utils import util
import uuid
from utils.util import Operation


class DataManager:
    """Class to handle data loading, updating, and deletion."""

    def __init__(self, table_class, session_factory, delimiter=','):
        self.__table_class = table_class
        self.__delimiter = delimiter
        self.__Session = session_factory

    def process_file(self, file_path, operation=Operation().all):

        """Process a file to insert, update, or delete records in the table."""
        if not util.validate_file(file_path):
            print("Invalid file. Only CSV or TXT files are supported.")
            return

        try:
            primary_key, column_names, is_uuid_primary_key = util.get_table_columns(self.__Session, self.__table_class)
            file_data = self.read_file(file_path, primary_key, column_names, operation, is_uuid_primary_key)

            if operation in [Operation().insert, Operation().all]:
                self._insert_or_update_records(file_data, primary_key)
            if operation in [Operation().delete, Operation().all]:
                self._delete_records(file_data, primary_key)

            print(f"Data processed successfully for table {self.__table_class.__tablename__}.")
        except Exception as e:
            raise e

    def read_file(self, file_path, primary_key, column_names, operation, is_uuid_primary_key):
        """Read the file and return a dictionary of IDs and field values."""
        file_data = {}
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=self.__delimiter)

            # Check if the file columns match the table columns (except for UUID primary keys on insert)
            file_column_set = set(reader.fieldnames)
            expected_columns = set(column_names)
            if is_uuid_primary_key and operation == Operation().insert:
                # Exclude primary key from expected columns if it's a UUID and operation is insert
                expected_columns.discard(primary_key)

            # Ensure the file has the same columns as expected, except for the UUID primary key if inserting
            if file_column_set != expected_columns:
                raise ValueError("File columns do not match the expected table columns.")

            for row in reader:
                if is_uuid_primary_key and operation == Operation().insert:
                    # Generate UUID for primary key if it's auto-generated
                    formatted_id = str(uuid.uuid4())
                else:
                    formatted_id = row[primary_key]

                # Construct field values from the row, excluding the primary key if it's auto-generated
                field_values = {col: row[col] for col in column_names if col in row}
                if is_uuid_primary_key and operation == Operation().insert:
                    field_values.pop(primary_key, None)

                file_data[formatted_id] = field_values

        return file_data

    def _insert_or_update_records(self, file_data, primary_key):
        session = self.__Session()
        try:
            """Insert or update records in the database."""
            for formatted_id, field_values in file_data.items():
                # Convert formatted_id to UUID if the primary key is a UUID
                table_class = self.__table_class
                column_type = table_class.__table__.c[primary_key].type
                if isinstance(column_type, PGUUID):
                    formatted_id = uuid.UUID(formatted_id)

                existing_entry = session.query(self.__table_class).filter(
                    getattr(table_class, primary_key) == formatted_id).first()

                if existing_entry:
                    # Update the entry if it exists
                    for column_name, value in field_values.items():
                        setattr(existing_entry, column_name, value)
                else:
                    # Insert the entry if it exists
                    field_values[primary_key] = formatted_id
                    new_entry = self.__table_class(**field_values)
                    session.add(new_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _delete_records(self, file_data, primary_key):
        session = self.__Session()
        try:
            """Delete records not present in the file."""
            existing_ids = {str(entry[0]) for entry in session.query(getattr(self.__table_class, primary_key)).all()}
            ids_to_delete = existing_ids - set(file_data.keys())
            if ids_to_delete:
                session.query(self.__table_class).filter(
                    getattr(self.__table_class, primary_key).in_(ids_to_delete)).delete(synchronize_session=False)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
