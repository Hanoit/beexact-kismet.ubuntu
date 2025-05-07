import os
from datetime import datetime
from utils.Exceptions import Exceptions, getTraceBack


class Log:
    __numberErrors = 0

    def __init__(self, log_directory=None, log_filename=None, log_header="LOG"):
        """Initialize the Log class with specified directory, filename, and header."""
        self.log_directory = log_directory or os.path.dirname(os.path.abspath(__file__))
        self.log_filename = log_filename or f"LOG_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        self.log_header = log_header
        self.logFilePath = os.path.join(self.log_directory, self.log_filename)
        self.create_log_file()

    def get_errors_count(self):
        """Return the number of errors logged."""
        return self.__numberErrors

    def write_log(self, message):
        """Register events in the system log file."""
        try:
            with open(self.logFilePath, "a", encoding='utf-8') as log:
                log.write(message + "\n")
        except Exception as exception:
            raise Exceptions(getTraceBack()) from exception

    def write_log_error(self, error_message):
        """Register error events in the system log file."""
        try:
            self.write_log(error_message)
            self.__numberErrors += 1
        except Exception as e:
            raise Exceptions(getTraceBack()) from e

    def remove_log(self):
        """Remove the log file."""
        try:
            if os.path.isfile(self.logFilePath):
                os.remove(self.logFilePath)
        except Exception as e:
            raise Exceptions(getTraceBack()) from e

    def create_log_file(self):
        """Create the log file with the specified header."""
        try:
            if os.path.isfile(self.logFilePath):
                os.remove(self.logFilePath)

            with open(self.logFilePath, "w", encoding='utf-8') as log:
                log.write(f"{self.log_header}\n")
                log.write(f"Log file created... \n{datetime.today()}\n")
        except Exception as e:
            raise Exceptions(getTraceBack()) from e
