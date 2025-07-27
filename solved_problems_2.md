# 🛠️ Troubleshooting - BeeExact Kismet on Ubuntu

## Identified Issues and Implemented Solutions

### 1. `.env` File Not Found
**Issue**: The configuration file was named `_.env` instead of `.env`  
**Solution**: Copied `_.env` to `.env` so `python-dotenv` can load it correctly  
**Command**: `cp _.env .env`

### 2. Inadequate Detection of Complete Files
**Issue**: The system only checked file size, not whether it was fully written  
**Solution**: Implemented `FileStabilityMonitor` that checks:
- File size stability
- Last modified time stability
- File accessibility (not locked)
- Configurable timeouts to avoid infinite waits

### 3. Processing Files Without GPS Coordinates
**Issue**: Kismet files had GPS coordinates set to zero, preventing device processing  
**Solution**:
- Added `PROCESS_WITHOUT_LOCATION=1` to `.env`
- Modified SQL queries to include devices without coordinates
- Updated validations in `ExtDeviceModel.py`

### 4. MacVendor API 404 Errors
**Issue**: API returned 404 for unknown MACs and changed JSON format  
**Solution**:
- Improved JSON response parsing (new format)
- Changed 404 warnings to debug logs (normal behavior)
- Implemented rate limiting (100ms between requests)

### 5. Diagnostic Reports Flooding the Terminal
**Issue**: Diagnostic reports overwhelmed the terminal  
**Solution**: Reports are now silently saved to log files

### 6. Sequential Processing System
**Issue**: Files were processed immediately upon detection, causing overload  
**Solution**: Implemented queue-based sequential processing system

---

## New File Processing Queue System

### Key Features

#### 📁 **FileQueueProcessor**
- **Sequential processing**: Files are processed one at a time
- **Configurable queue**: Maximum queue size (default: 10 files)
- **Duplicate detection**: Prevents reprocessing of the same file
- **Real-time statistics**: Monitors queue and performance
- **Robust error handling**: Continues processing remaining files even on failure

#### 🔄 **Processing Flow**
1. **Detection**: `WatchingDirectory` detects new `.kismet` file  
2. **Verification**: `FileStabilityMonitor` ensures file is complete  
3. **Enqueuing**: File is added to the processing queue  
4. **Processing**: Worker thread processes files sequentially  
5. **Reporting**: Generates logs and diagnostic reports

#### 📊 **Monitoring and Statistics**
```python
# Queue status
- Current size: X/Y files
- File being processed: filename.kismet
- Total processed: X
- Total errors: Y
- Success rate: Z%

```

### Configuration

#### Environment Variables
# .env
WATCH_DIRECTORY="/opt/kismetFiles"
OUT_DIRECTORY="/opt/kismetFiles"
PROCESS_WITHOUT_LOCATION=1
CHECK_INTERVAL=300
```
#### Queue Parameters
```python
# In FileQueueProcessor
max_queue_size=10  # Maximum number of files in the queue
stability_time=5   # Seconds to check for file stability
max_wait_time=300  # Maximum timeout for stability
```

### Advantages of the New System

#### ⚡ **Improved Performance**
- **Sequential processing**: Avoids system overload
- **Detection of fully copied files**: Processes only complete files
- **Efficient memory usage**: One file at a time

#### 🛡️ **Robustness**
- **Error recovery**: If a file fails, the system continues with the next one
- **Duplicate verification**: Prevents redundant processing
- **Configurable timeouts**: Avoids infinite blocking

#### 📈 **Monitoring**
- **Real-time statistics**: Queue status and performance
- **Detailed logs**: Full trace of the processing steps
- **Diagnostic reports**: Pre- and post-processing analysis

### Generated Files

For each processed file, the system generates:
1. `{filename}.csv` – Exported data
2. `{filename}.log` – Processing log
3. `{filename}_DIAGNOSTIC.log` – Detailed diagnostic report
4. `{filename}_NOT_VENDOR.log` – MACs without manufacturer
5. `{filename}_NOT_PROVIDER.log` – MACs without provider

### System Usage

#### Automatic Startup
```bash
# The system starts automatically with:
python3 kismet_export.py
```

#### Real-time Monitoring
```bash
# Logs display queue status
tail -f /opt/kismetFiles/*.log
```

#### Status Check
```python
# Get queue summary
watcher = WatchingDirectory(processor)
summary = watcher.get_queue_summary()
print(summary)
```

### Recommendations

#### 🚀 **Optimization**
- Adjust `max_queue_size` based on system capacity
- Configure `stability_time` based on network speed
- Monitor logs to detect error patterns

#### 🔧 **Maintenance**
- Periodically check log files
- Clean up old processed files
- Verify available disk space for output files

#### 📊 **Monitoring**
- Use diagnostic reports to optimize filters
- Review processing success rates
- Tune configuration based on usage patterns

## Project Structure

```
beexact-kismet.ubuntu/
├── services/
│   ├── WatchingDirectory.py      # Directory monitoring
│   ├── FileQueueProcessor.py     # Queue system
│   ├── DirectoryFilesProcessor.py # File processing
│   └── KismetAnalyzer.py         # Data analysis
├── utils/
│   ├── file_monitor.py           # File stability checker
│   └── KismetDiagnostic.py       # Diagnostic reports
├── database/
│   └── SessionKismetDB.py        # Database management
└── models/
    └── ExtDeviceModel.py         # Device model
```

## Useful Commands

```bash
# Check configuration
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('WATCH_DIRECTORY:', os.getenv('WATCH_DIRECTORY'))"

# Test queue system
python3 test_file_queue.py

# View real-time logs
tail -f /opt/kismetFiles/*.log

# Check processed files
ls -la /opt/kismetFiles/*.csv
```

## Troubleshooting

### Common Issues

#### Files not processed
- Ensure `WATCH_DIRECTORY` exists and has proper permissions
- Confirm `PROCESS_WITHOUT_LOCATION=1` is set
- Check logs for specific errors

#### Queue full
- Increase `max_queue_size` in `FileQueueProcessor`
- Ensure processing is not blocked
- Check disk space

#### API Errors
- 404 errors are normal for unknown MAC addresses
- Verify internet connectivity
- Check for rate limiting if many errors appear

### Key Logs

```bash
# File detection logs
grep "New .kismet file detected" /opt/kismetFiles/*.log

# File processing logs
grep "Processing file" /opt/kismetFiles/*.log

# Processing errors
grep "ERROR" /opt/kismetFiles/*.log

# Queue statistics
grep "Queue Status" /opt/kismetFiles/*.log
```