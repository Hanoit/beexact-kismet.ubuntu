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

### 🚀 **Automated Installation (Recommended)**

The easiest way to install and compile the Kismet Processor on Ubuntu:

```bash
# Make the installation script executable
chmod +x install_dependencies_ubuntu.sh

# Run the automated installation
./install_dependencies_ubuntu.sh
```

**What the automated installation does:**
- ✅ Installs all system dependencies
- ✅ Creates Python virtual environment
- ✅ Installs Python packages
- ✅ Compiles the application with PyInstaller
- ✅ Creates desktop application
- ✅ Sets up launcher scripts
- ✅ Copies configuration files

**What the script creates:**
- 🖥️ **Desktop Application**: Integrated with Ubuntu applications menu
- 📜 **Launcher Scripts**: `run_kismet_compiled.sh` and `run_kismet_source.sh`
- 🎯 **Compiled Executable**: Standalone application in `dist/` folder
- ⚙️ **Configuration Template**: Pre-configured `.env` file
- 🔗 **Desktop Shortcut**: Ready-to-use desktop icon

**After automated installation, you can run the app:**
- 📱 **Desktop App**: Search for "BeExact Kismet Processor" in applications
- 🖱️ **Double-click**: `BeExact_Kismet_Processor.desktop`
- 📜 **Script**: `./run_kismet_compiled.sh` (compiled version)
- 🐍 **Script**: `./run_kismet_source.sh` (development version)

**Installation Requirements:**
- Ubuntu 18.04+ (tested on 20.04, 22.04)
- 4GB+ RAM (for compilation)
- 2GB+ free disk space
- Internet connection (for dependencies and API)
- sudo privileges (for system packages)

### 📋 **Manual Installation**

If you prefer manual installation or are not using Ubuntu:

1. **Clone the repository**
2. **Install system dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3-dev python3-pip python3-venv build-essential
   
   # Install geospatial dependencies
   sudo apt install -y libcairo2-dev libgirepository1.0-dev
   ```

3. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure environment variables** (see Configuration section)

6. **Run the processor:**
   ```bash
   python kismet_export.py
   ```

### 📦 **Compilation (Optional)**

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Clean previous builds
rm -rf build/ dist/

# Compile the application
pyinstaller main.spec

# Run compiled version
cd dist/export_kismet_to_csv/
./export_kismet_to_csv
```

## 🚀 **Quick Start Guide**

### **Option 1: One-Command Installation (Ubuntu)**
```bash
# Download and run the automated installer
curl -O https://raw.githubusercontent.com/your-repo/install_dependencies_ubuntu.sh
chmod +x install_dependencies_ubuntu.sh
./install_dependencies_ubuntu.sh
```

### **Option 2: Fast Development Setup**
```bash
# Clone and setup for development
git clone <repository-url>
cd beexact-kismet-processor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python kismet_export.py
```

### **Option 3: Docker Installation (Coming Soon)**
```bash
# Using Docker for isolated environment
docker build -t kismet-processor .
docker run -v /opt/kismetFiles:/data kismet-processor
```

## 🎯 **Installation Comparison**

| Feature | Automated Script | Manual Installation |
|---------|------------------|-------------------|
| **Time Required** | ~10-15 minutes | ~30-45 minutes |
| **Technical Knowledge** | Beginner | Intermediate |
| **Desktop Integration** | ✅ Full integration | ❌ Manual setup |
| **Compiled Executable** | ✅ Automatic | ⚙️ Manual compilation |
| **Error Handling** | ✅ Built-in fixes | 🛠️ Manual debugging |
| **Customization** | ⚙️ Standard setup | ✅ Full control |
| **Updates** | 🔄 Re-run script | 🛠️ Manual process |

## 🎯 **Installation Scenarios**

### **Scenario 1: Production Server (Ubuntu) - RECOMMENDED**
- **Use**: `./install_dependencies_ubuntu.sh`
- **Best for**: End users, production deployment, demo setups
- **Benefits**: 
  - ✅ Complete setup in one command
  - ✅ Desktop application ready
  - ✅ Compiled executable included
  - ✅ Error handling built-in

### **Scenario 2: Development Environment**
- **Use**: Manual installation with virtual environment
- **Best for**: Developers, code contributors, customization
- **Benefits**: 
  - ✅ Easy debugging and modification
  - ✅ Faster development iteration
  - ✅ Custom dependency versions
  - ✅ Source code access

### **Scenario 3: Portable Application**
- **Use**: Pre-compiled executable distribution
- **Best for**: Field deployment, offline usage
- **Benefits**: 
  - ✅ No Python dependencies needed
  - ✅ Single folder deployment
  - ✅ Works on any Ubuntu system
  - ✅ Minimal setup required

### **Scenario 4: CI/CD Pipeline**
- **Use**: `pip install -r requirements.txt`
- **Best for**: Automated builds, testing, containerization
- **Benefits**: 
  - ✅ Reproducible builds
  - ✅ Automated testing
  - ✅ Docker-friendly
  - ✅ Version control integration

## 🔧 **Installation Troubleshooting**

### **Common Issues and Solutions:**

#### **Issue: `python3-gi-dev not found`**
```bash
# Solution: Install correct package names
sudo apt install -y libgirepository1.0-dev python3-gi
```

#### **Issue: `PyGObject compilation failed`**
```bash
# Solution: Install system dependencies first
sudo apt install -y python3-dev libcairo2-dev pkg-config
```

#### **Issue: `Repository errors (PostgreSQL/MongoDB)`**
```bash
# Solution: Clean problematic repositories
sudo rm -f /etc/apt/sources.list.d/pgdg.list
sudo rm -f /etc/apt/sources.list.d/pgadmin4.list
sudo apt update
```

#### **Issue: `Permission denied` on script execution**
```bash
# Solution: Make script executable
chmod +x install_dependencies_ubuntu.sh
```

#### **Issue: Virtual environment not activating**
```bash
# Solution: Install python3-venv
sudo apt install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
```

### **Verification Commands:**
```bash
# Check Python version
python3 --version

# Check if virtual environment is active
which python

# Verify main dependencies
python3 -c "import pandas, geopandas, sentence_transformers; print('✅ All dependencies OK')"

# Test application startup
python kismet_export.py --help
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