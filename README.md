# BeExact Kismet Processor

A comprehensive Kismet file processing system with intelligent MAC vendor lookup, provider identification, and sequential file processing with advanced performance improvements.

## 🚀 **Main Features**

- 🔍 **Intelligent MAC Vendor Lookup**: Dynamic rate limiting system with premium API (25 RPS, 100K requests/day)
- 📊 **Provider Identification**: Advanced SSID matching with sentence embeddings
- 📁 **Sequential File Processing**: Configurable queue system with automatic overflow handling
- 🛡️ **Error Handling**: Circuit breaker patterns and comprehensive error recovery
- 📈 **Progress Tracking**: Real-time progress bars and detailed logging
- 🔄 **File Monitoring**: Automatic detection and processing of new Kismet files
- ⚡ **Performance Optimizations**: Batch processing, optimized DB sessions, parallel API
- 🗄️ **Robust Database**: Exponential backoff retries, concurrency handling

## 📋 **Prerequisites**

- Python 3.8+
- SQLite database
- Internet connection for MAC vendor API
- Configured `.env` file (see Configuration section)

## 🛠️ **Installation**

1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables** (see Configuration section)
4. **Run the processor:**
   ```bash
   python kismet_export.py
   ```

## ⚙️ **.env File Configuration**

### 📁 **Directory Configuration**
```bash
# Directory where Kismet files are monitored
WATCH_DIRECTORY=/opt/kismetFiles

# Directory where output CSV files are saved
OUT_DIRECTORY=/opt/kismetFiles
```

### 🌐 **MacVendors API Configuration (OPTIMIZED)**
```bash
# Plan type (free/premium)
MACVENDOR_PLAN_TYPE=premium

# API limits for premium plan
MACVENDOR_REQUESTS_PER_SECOND=25       # 25 RPS maximum
MACVENDOR_REQUESTS_PER_DAY=100000      # 100K requests/day

# Optimized timeouts
MACVENDOR_API_TIMEOUT=8.0              # Timeout per request
MACVENDOR_API_INTERVAL=0.04            # Interval between requests (40ms)

# API Key (JWT Token)
API_KEY_MACVENDOR=your_api_key_here
```

### ⚡ **Batch Processing Configuration**
```bash
# Batch size for parallel requests
MACVENDOR_BATCH_SIZE=25                # Matches 25 RPS

# Workers for parallel processing
MACVENDOR_MAX_WORKERS=25               # Maximum parallelism

# Timeout for complete batches
MACVENDOR_BATCH_TIMEOUT=35.0           # 35 seconds per batch

# Cache for MACs not found (months)
MACS_NOT_FOUND_CACHE_MONTHS=6
```

### 📂 **File Processing Configuration**
```bash
# Maximum file queue size
FILE_QUEUE_MAX_SIZE=20

# Check interval for new files (seconds)
CHECK_INTERVAL=300

# Chunk size for device processing
KISMET_CHUNK_SIZE=10000
```

### 📊 **Monitoring and Performance Configuration**
```bash
# Enable system performance monitor
ENABLE_PERFORMANCE_MONITOR=true

# Enable progress bars
ENABLE_PROGRESS_BAR=1

# Save intermediate results
SAVE_INTERMEDIATE_RESULTS=1

# Target speed (devices per second)
TARGET_DEVICES_PER_SECOND=25
```

### 🗺️ **Geographic Processing Configuration**
```bash
# Process devices without location
PROCESS_WITHOUT_LOCATION=1

# Swap X/Y coordinates if needed
FLIP_XY=0

# Coordinate systems
COORDINATE_EPSG=4326                   # WGS84 (geographic)
PROJECTED_EPSG=3857                    # Web Mercator (projected)

# Precision and filters
COORDINATE_PRECISION=6
COORDINATE_DECIMAL_PLACES=4
DISTANCE_FILTER_METERS=50
```

### 🗄️ **Database Configuration**
```bash
# Database path
DB_PATH=kismet.db

# Retry configuration for DB locks
DB_RETRY_ATTEMPTS=3
DB_RETRY_DELAY=0.1
```

### 📝 **Logging Configuration**
```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Advanced verbosity (0=disabled, 1=enabled)
ADVANCE_VERBOSE=0

# Basic verbosity (0=disabled, 1=enabled)
BASIC_VERBOSE=0
```

### 🧠 **Sentence Transformers Configuration**
```bash
# Enable sentence transformer for provider matching
ENABLE_SENTENCE_TRANSFORMER=1
```

## 🎯 **Implemented Improvements (v2.5.0)**

### ⚡ **Performance Optimizations**
- **Batch Processing**: MAC vendors processed in batches of 25 (matches API limit)
- **Optimized DB Sessions**: One session per batch instead of per device
- **Parallel API**: 25 simultaneous requests leveraging premium plan
- **Early Filtering**: Filters applied before creating heavy objects
- **Smart Caching**: MACs not found cached for 6 months

### 🛡️ **Robust Error Handling**
- **Exponential Backoff Retries**: For database locks
- **Configurable Timeouts**: Separate timeouts for connection and read
- **Future Cancellation**: Graceful handling of batch timeouts
- **Detailed Logging**: Complete diagnostics for debugging

### 🏗️ **Improved Architecture**
- **Centralized Configuration**: Everything in single `.env` file
- **Clean Code**: Removed unused variables
- **SOLID Principles**: Clear separation of responsibilities
- **Type Safety**: Type checks for robustness

### 📈 **Monitoring and Observability**
- **Performance Metrics**: CPU, memory, processing speed
- **Progress Bars**: Visual indicators with `tqdm`
- **Structured Logging**: Clear messages with emojis for easy identification
- **Diagnostics**: Pre and post processing reports

## 🚀 **Usage**

### **Basic Execution**
```bash
# Start the main processor
python kismet_export.py
```

### **Database Management**
```bash
# Load vendor data
python manage_db.py load --file data/mac_vendorsv1.csv --table vendor --delimiter ','

# Export data to CSV
python manage_db.py export --output vendors_export.csv --table vendor --delimiter ','
```

### **Arguments Description**
- **operation**: Operation to perform: load or export.
- **--file**: Path to the input file (for loading data).
- **--output**: Path to the output file (for exporting data).
- **--table**: Specify the table to operate on: vendor, provider, or ssid (required).
- **--delimiter**: Delimiter used in the file (default is ,).
- **--operation_type**: Operation type to perform: insert, delete, or update.

## 📦 **How to Compile the Project**

### **1. Create a Virtual Environment and Install Dependencies**

```sh
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On macOS/Linux
```

### **2. Install Required Dependencies**

```sh
pip install -r requirements.txt
```

### **3. Compile the Project to an Executable (.exe)**
Use PyInstaller with the specification file:

```sh
pyinstaller main.spec
```

### **4. Copy the .env File**
Copy the .env file to the root directory where the Export Kismet to CSV.exe executable is located.

### **Troubleshooting Compilation Errors**
If you encounter issues during compilation, try the following:

```sh
pip uninstall arcgis
pip uninstall pyinstaller
pip install arcgis
pip install pyinstaller
```

#### **Resolving win32ctypes.pywin32.pywintypes.error**
If you get the error: `(225, 'LoadLibraryExW', 'Operation did not complete successfully because the file contains a virus or potentially unwanted software.')`

**Solution:**
1. Start → Settings → Privacy & Security → Virus & threat protection
2. Manage settings → exclusions → add or remove exclusions
3. Add your project folder to exclusions

## 📊 **Kismet File Structure**

Processed Kismet files include the following columns:

| Name             | Type  | Description                    |
|------------------|-------|--------------------------------|
| first_time       | INT   | First detection time           |
| last_time        | INT   | Last detection time            |
| devkey           | TEXT  | Unique device key              |
| phyname          | TEXT  | Physical interface name        |
| devmac           | TEXT  | Device MAC address             |
| strongest_signal | INT   | Strongest recorded signal      |
| min_lat          | REAL  | Minimum latitude               |
| min_lon          | REAL  | Minimum longitude              |
| max_lat          | REAL  | Maximum latitude               |
| max_lon          | REAL  | Maximum longitude              |
| avg_lat          | REAL  | Average latitude               |
| avg_lon          | REAL  | Average longitude              |
| bytes_data       | INT   | Transferred data bytes         |
| type             | TEXT  | Device type                    |
| device           | BLOB  | Device JSON data               |

## 🔗 **References**

- [API Documentation](https://kismetwireless.net/docs/api/devices/)
- [Kismet REST Documentation](https://kismet-rest.readthedocs.io/en/latest/devices.html#)
- [Kismet Logging Documentation](https://github.com/kismetwireless/kismet-docs/blob/master/devel/log_kismet.md)

## 🧪 **Testing**

The project includes a comprehensive test suite:

```bash
# Run rate limiting tests
python -m pytest tests/rate_limiting/

# Run performance tests
python -m pytest tests/performance/

# Run all tests
python -m pytest tests/
```

## 🏆 **Performance**

### **Optimized Metrics:**
- **Processing**: 20-25 devices/second (target achieved)
- **API Requests**: 25 RPS without saturation
- **Database**: No locks with automatic retries
- **Memory**: Optimized usage with batch processing

### **Recommended Configuration:**
- CPU: 4+ cores for parallel processing
- RAM: 8GB+ for large Kismet files
- Connection: Stable for MAC vendor API

## 🆘 **Troubleshooting**

### **Common Errors:**

1. **`coord_epsg referenced before assignment`**
   - ✅ **Fixed**: EPSG variables moved outside conditional blocks

2. **`database is locked`**
   - ✅ **Fixed**: Automatic retries with exponential backoff

3. **`API rate limit exceeded`**
   - ✅ **Fixed**: Dynamic rate limiting with premium plan

4. **`Slow processing performance`**
   - ✅ **Fixed**: Batch processing and DB optimizations

### **Debug Logs:**
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python kismet_export.py
```

---

**Version**: 2.5.0  
**Last Updated**: January 2025  
**Maintainer**: BeExact Team