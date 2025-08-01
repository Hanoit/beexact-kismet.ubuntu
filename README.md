# BeExact Kismet Processor

A comprehensive Kismet file processing system with intelligent MAC vendor lookup, provider identification, and sequential file processing.

## Features

- 🔍 **Intelligent MAC Vendor Lookup**: Dynamic rate limiting and retry mechanisms
- 📊 **Provider Identification**: Advanced SSID matching with sentence embeddings
- 📁 **Sequential File Processing**: Configurable queue system with automatic overflow handling
- 🛡️ **Error Handling**: Circuit breaker patterns and comprehensive error recovery
- 📈 **Progress Tracking**: Real-time progress bars and detailed logging
- 🔄 **File Monitoring**: Automatic detection and processing of new Kismet files

## Quick Start

### Prerequisites

- Python 3.8+
- SQLite database
- Internet connection for MAC vendor API

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables (see Configuration section)
4. Run the processor:
   ```bash
   python main.py
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following settings:

```bash
# Database Configuration
DATABASE_URL=sqlite:///kismet.db

# Output Directory
OUTPUT_DIRECTORY=/opt/kismetFiles

# File Processing Configuration
PROCESS_WITHOUT_LOCATION=1
FLIP_COORDINATES=0

# File Queue Configuration
FILE_QUEUE_MAX_SIZE=20  # Max: 30 files

# MacVendor API Configuration
MACVENDOR_API_INTERVAL=3.0
MACVENDOR_API_TIMEOUT=20.0
MACVENDOR_MAX_QUEUE_SIZE=50
MACVENDOR_MAX_CONSECUTIVE_FAILURES=10
MACVENDOR_CIRCUIT_BREAKER_TIMEOUT=300

# Logging Configuration
LOG_LEVEL=INFO
```

### Queue Configuration

The system supports configurable file queue sizes:

- **Default**: 20 files
- **Maximum**: 30 files (enforced limit)
- **Overflow Handling**: Excess files are automatically moved back to the folder for later processing

See [QUEUE_CONFIGURATION.md](QUEUE_CONFIGURATION.md) for detailed configuration options.

## Usage

### Basic Usage

1. Place Kismet files in the monitored directory
2. The system automatically detects and processes files sequentially
3. Processed files are exported to CSV format
4. Diagnostic reports are generated for each file

### Advanced Features

- **Sequential Processing**: Files are processed one at a time to prevent resource saturation
- **Intelligent Retry**: Failed MAC lookups are automatically retried with dynamic rate limiting
- **Progress Tracking**: Real-time progress bars show processing status
- **Error Recovery**: Comprehensive error handling with circuit breaker patterns

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/rate_limiting/
python -m pytest tests/providers/
python -m pytest tests/logging/
```

See [tests/README.md](tests/README.md) for detailed testing information.

## Documentation

- [RELEASE_NOTES.md](RELEASE_NOTES.md) - Complete release documentation
- [QUEUE_CONFIGURATION.md](QUEUE_CONFIGURATION.md) - Queue configuration guide
- [tests/README.md](tests/README.md) - Testing documentation

## Architecture

### Core Components

- **WatchingDirectory**: Monitors for new Kismet files
- **FileQueueProcessor**: Manages sequential file processing with configurable queue
- **KismetAnalyzer**: Processes individual Kismet files
- **MacVendorFinder**: Handles MAC vendor lookups with intelligent retry
- **MacProviderFinder**: Identifies providers using SSID matching

### Processing Flow

1. **File Detection**: WatchingDirectory detects new .kismet files
2. **Queue Management**: Files are added to configurable queue (max 30 files)
3. **Sequential Processing**: Files are processed one at a time
4. **Overflow Handling**: Excess files are moved back to folder for later processing
5. **Export**: Processed data is exported to CSV format

## Support

For issues and questions, please refer to the documentation or create an issue in the repository.
