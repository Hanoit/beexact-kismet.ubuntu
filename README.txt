# Running the Export Kismet Files Scripts

## Setting Up the Environment

Before running the export, configure the settings as follows:

1. Open the `.env` file.
2. Set the parameters according to your environment:

### `.env` File Documentation

```plaintext
# Directory where Kismet files are saved
WATCH_DIRECTORY="."

# How often the directory is checked for new files (in seconds)
CHECK_INTERVAL=300  

# Number of CPU cores to dedicate for processing
NUM_WORKERS=6

# Flip the coordinates if needed (0 = False, 1 = True)
FLIP_XY=1

# API Key for MacVendor API
API_KEY_MACVENDOR=

# Directory where the output CSV files will be saved
OUT_DIRECTORY="."

# Directory where the database files are located
DB_DIRECTORY="."

# Show basic processing progress in the console (0 = False, 1 = True)
BASIC_VERBOSE=1

# Show detailed processing progress in the console (0 = False, 1 = True)
ADVANCE_VERBOSE=0


## Running the Script
To start the export, run the following command:

	```sh
	python kismet_export.py
	```
	
### Kismet File Columns Description
The Kismet file includes the following columns:

| Name             | Type  |
|------------------|-------|
| first_time       | INT   |
| last_time        | INT   |
| devkey           | TEXT  |
| phyname          | TEXT  |
| devmac           | TEXT  |
| strongest_signal | INT   |
| min_lat          | REAL  |
| min_lon          | REAL  |
| max_lat          | REAL  |
| max_lon          | REAL  |
| avg_lat          | REAL  |
| avg_lon          | REAL  |
| bytes_data       | INT   |
| type             | TEXT  |
| device           | BLOB  |

Refer to the example file spec_kismet_example.json for a sample format.

For more details, consult this URLS:

[API Documentation](https://kismetwireless.net/docs/api/devices/)

[Kismet REST Documentation](https://kismet-rest.readthedocs.io/en/latest/devices.html#)

[Kismet Logging Documentation](https://github.com/kismetwireless/kismet-docs/blob/master/devel/log_kismet.md)

	
### How to Run the Manage DB Script
The manage_database.py script provides a flexible way to manage your database operations from the command line.

##Loading Data into the Database
To load data from a file into the mac_vendors table, use:

```sh
python manage_database.py load --file mac-vendor.txt --table vendor --delimiter ',' --operation_type insert
```

## Exporting Data from the Database
To export data from the mac_vendors table to a CSV file, use:

```sh
python manage_database.py export --output mac_vendors.csv --table vendor --delimiter ','
```

## Arguments Description
operation: Operation to perform: load or export.
--file: Path to the input file (for loading data).
--output: Path to the output file (for exporting data).
--table: Specify the table to operate on: vendor, provider, or ssid (required).
--delimiter: Delimiter used in the file (default is ,).
--operation_type: Operation type to perform: insert, delete, or update.

# How to Compile the Project

## 1. Create a Virtual Environment and Install Dependencies

	```sh
	python -m venv venv
	venv\Scripts\activate  # On Windows
	source venv/bin/activate  # On macOS/Linux
	```

## 2. Install Required Dependencies

	```sh
	pip install -r requirements.txt
	```
	
3. Compile the Project to an Executable (.exe)
	Use PyInstaller with the specification file:
	```

	```sh
	pyinstaller main.spec
	```

### Troubleshooting Compilation Errors
If you encounter issues during compilation, try the following:

	```sh
	pip uninstall arcgis
	pip uninstall pyinstaller
	pip install arcgis
	pip install pyinstaller
	Resolving win32ctypes.pywin32.pywintypes.error: (225, 'LoadLibraryExW', 'Operation did not complete successfully because the file contains a virus or potentially unwanted software.')
	```


	Start -> Settings -> Privacy & Security -> Virus & threat protection
	manage settings -> exclusions -> add or remove exclusions
	add your project folder

## 4. Copy the .env File
Copy the .env file to the root directory where the Export Kismet to CSV.exe executable is located.
