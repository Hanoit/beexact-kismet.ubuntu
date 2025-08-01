# Kismet MAC Vendor Analysis System

## 🎯 **Overview**

A comprehensive system for analyzing Kismet wireless network data with intelligent MAC vendor lookup, provider identification, and enhanced rate limiting capabilities. This system processes Kismet log files and extracts detailed information about wireless devices including vendor information, provider details, and location data.

## ✨ **Key Features**

### **🚀 Intelligent Rate Limiting**
- **Adaptive API Intervals**: Automatically adjusts from 3s to 60s based on API responses
- **Circuit Breaker Pattern**: Prevents infinite loops during API saturation
- **Memory-Only Handling**: Rate limits handled entirely in memory for better performance
- **Immediate Retry Queue**: Failed MACs retried with measured API capacity

### **🔍 Enhanced MAC Analysis**
- **Full MAC API Calls**: Uses complete MAC addresses for better accuracy
- **Legacy Compatibility**: Maintains backward compatibility with existing databases
- **Provider Identification**: Intelligent SSID-based provider matching
- **Error Handling**: Robust error handling for network and API issues

### **📊 Clean Logging System**
- **Visual Indicators**: Clear emoji indicators for different message types
- **Progress Tracking**: Shows progress every 10 operations
- **Reduced Verbosity**: 80% reduction in terminal spam
- **Essential Information**: Only logs important events and status changes

## 🛠️ **Installation & Setup**

### **1. Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd beexact-kismet.ubuntu

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Configuration**
Create a `.env` file with the following settings:

```bash
# Core Settings
WATCH_DIRECTORY="."              # Directory to monitor for Kismet files
CHECK_INTERVAL=300               # Check interval in seconds
NUM_WORKERS=6                    # Number of processing threads
FLIP_XY=1                        # Flip coordinates if needed

# API Configuration
API_KEY_MACVENDOR=               # Optional: MacVendor API key
MACVENDOR_API_INTERVAL=3.0       # Initial API interval (seconds)
MACVENDOR_API_TIMEOUT=20         # API timeout (seconds)

# Output Settings
OUT_DIRECTORY="."                # CSV output directory
DB_DIRECTORY="."                 # Database directory

# Processing Options
PROCESS_WITHOUT_LOCATION=1       # Process devices without location data
ENABLE_SENTENCE_TRANSFORMER=1    # Enable advanced provider matching

# Logging
BASIC_VERBOSE=1                  # Basic progress logging
ADVANCE_VERBOSE=0                # Detailed logging (use sparingly)
```

## 🚀 **Usage**

### **1. Start the Export Process**
```bash
# Start the Kismet file processing
python kismet_export.py
```

The system will:
- ✅ Monitor the specified directory for new Kismet files
- ✅ Process files automatically with intelligent rate limiting
- ✅ Extract vendor and provider information
- ✅ Generate CSV reports with detailed device information

### **2. Database Management**
```bash
# Load vendor data into database
python manage_db.py load --file mac-vendor.txt --table vendor --delimiter ',' --operation_type insert

# Export data from database
python manage_db.py export --output mac_vendors.csv --table vendor --delimiter ','
```

### **3. File Processing**
The system processes Kismet files with the following columns:

| Column           | Type  | Description                    |
|------------------|-------|--------------------------------|
| first_time       | INT   | First detection timestamp      |
| last_time        | INT   | Last detection timestamp       |
| devkey           | TEXT  | Device key                     |
| phyname          | TEXT  | Physical interface name        |
| devmac           | TEXT  | Device MAC address            |
| strongest_signal | INT   | Strongest signal strength      |
| min_lat          | REAL  | Minimum latitude              |
| min_lon          | REAL  | Minimum longitude             |
| max_lat          | REAL  | Maximum latitude              |
| max_lon          | REAL  | Maximum longitude             |
| avg_lat          | REAL  | Average latitude              |
| avg_lon          | REAL  | Average longitude             |
| bytes_data       | INT   | Data bytes transferred        |
| type             | TEXT  | Device type                   |
| device           | BLOB  | Device JSON data              |

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Run all tests
find tests/ -name "*.py" -exec python {} \;

# Run specific test categories
python tests/rate_limiting/test_circuit_breaker_system.py
python tests/providers/test_provider_error_fix.py
python tests/logging/test_improved_logging.py
```

### **Test Coverage**
- ✅ **Rate Limiting**: Circuit breaker and adaptive intervals
- ✅ **Provider Handling**: Error handling and type safety
- ✅ **Logging**: Verbosity reduction and visual indicators
- ✅ **Legacy Compatibility**: Database storage logic
- ✅ **Integration**: End-to-end functionality

## 📚 **Documentation**

### **API References**
- [Kismet API Documentation](https://kismetwireless.net/docs/api/devices/)
- [Kismet REST Documentation](https://kismet-rest.readthedocs.io/en/latest/devices.html)
- [Kismet Logging Documentation](https://github.com/kismetwireless/kismet-docs/blob/master/devel/log_kismet.md)

### **Project Documentation**
- [RELEASE_NOTES.md](RELEASE_NOTES.md) - Comprehensive release documentation
- [FINAL_CORRECTIONS_SUMMARY.md](FINAL_CORRECTIONS_SUMMARY.md) - Technical implementation details
- [tests/README.md](tests/README.md) - Test suite documentation

## 🔧 **Advanced Usage**

### **Database Management Script**
The `manage_db.py` script provides flexible database operations:

#### **Arguments Description**
- `operation`: Operation to perform: `load` or `export`
- `--file`: Path to the input file (for loading data)
- `--output`: Path to the output file (for exporting data)
- `--table`: Specify the table: `vendor`, `provider`, or `ssid` (required)
- `--delimiter`: Delimiter used in the file, default is `,`
- `--operation_type`: Operation type: `insert`, `delete`, or `update`

#### **Examples**
```bash
# Load vendor data
python manage_db.py load --file mac-vendor.txt --table vendor --delimiter ',' --operation_type insert

# Export vendor data
python manage_db.py export --output mac_vendors.csv --table vendor --delimiter ','

# Load provider data
python manage_db.py load --file providers.txt --table provider --delimiter ';' --operation_type insert
```

## 🏗️ **Building & Deployment**

### **1. Development Setup**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Compile to Executable**
```bash
# Build executable using PyInstaller
pyinstaller main.spec
```

### **3. Troubleshooting Build Issues**

#### **Common PyInstaller Issues**
```bash
# Reinstall problematic packages
pip uninstall arcgis pyinstaller
pip install arcgis pyinstaller
```

#### **Windows Antivirus Issues**
If you encounter `win32ctypes.pywin32.pywintypes.error: (225, 'LoadLibraryExW')`:

1. **Windows Security Settings**:
   - Start → Settings → Privacy & Security → Virus & threat protection
   - Manage settings → Exclusions → Add or remove exclusions
   - Add your project folder to exclusions

2. **Alternative Solution**:
   - Temporarily disable real-time protection during build
   - Re-enable after successful compilation

### **4. Deployment**
```bash
# Copy .env file to executable directory
cp .env dist/export_kismet_to_csv/

# Copy required data files
cp -r data/ dist/export_kismet_to_csv/
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **API Rate Limiting**
- **Symptom**: Frequent 429 errors
- **Solution**: System automatically handles this with circuit breaker
- **Configuration**: Adjust `MACVENDOR_API_INTERVAL` if needed

#### **Database Errors**
- **Symptom**: 'str' object has no attribute 'id'
- **Solution**: Fixed in version 2.0.0
- **Prevention**: Use latest version with improved error handling

#### **Memory Issues**
- **Symptom**: High memory usage
- **Solution**: System now uses memory-only rate limiting
- **Monitoring**: Check queue size in logs

### **Performance Optimization**
- **Queue Size**: Limited to 50 failed MACs
- **Circuit Breaker**: 5-minute timeout prevents infinite loops
- **Logging**: Reduced verbosity for better performance
- **Database**: Only stores essential data

## 📞 **Support & Contributing**

### **Getting Help**
- **Documentation**: Check [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed information
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Community**: Join user forums for discussions and help

### **Contributing**
- **Code Quality**: Follow existing code patterns
- **Testing**: Add tests for new features
- **Documentation**: Update documentation for changes
- **Testing**: Run full test suite before submitting

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**License**: MIT License  
**Compatibility**: Python 3.8+, SQLAlchemy 1.4+
