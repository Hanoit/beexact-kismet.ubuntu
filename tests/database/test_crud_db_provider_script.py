import os
import subprocess
import sys


def run_manage_db_provider_script():
    try:
        script_path = os.path.join('..', 'manage_db.py')
        # Define the command to run your manage_db.py script
        command = [
            sys.executable,  # This ensures you use the same Python interpreter as your environment
            script_path,  # The script you want to test
            'load',  # Operation
            '--file',  # Argument name
            '../data/providers.csv',  # Path to the test CSV file
            '--table',  # Argument name
            'provider',  # Table to operate on
            '--operation_type',  # Argument name
            'insert'  # Operation type
        ]

        # Run the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        # Print the standard output and error
        print("Standard Output:\n", result.stdout)
        print("Standard Error:\n", result.stderr)

        # Check the return code to determine success
        if result.returncode != 0:
            print("Test failed!")
            return False

        print("Test passed!")
        return True

    except Exception as e:
        print(f"An error occurred while running the test: {e}")
        return False


if __name__ == '__main__':
    run_manage_db_provider_script()
