 File Queue Configuration

## Overview

The file queue system now supports configurable queue sizes with automatic handling of excess files.

## Configuration

### Environment Variable

Add the following to your `.env` file:

```bash
# File Queue Configuration
FILE_QUEUE_MAX_SIZE=20
```

### Parameters

- **FILE_QUEUE_MAX_SIZE**: Maximum number of files that can be queued for processing
  - **Default**: 20 files
  - **Maximum**: 30 files (enforced limit)
  - **Type**: Integer

### Examples

```bash
# Default configuration (20 files)
FILE_QUEUE_MAX_SIZE=20

# Maximum configuration (30 files)
FILE_QUEUE_MAX_SIZE=30

# Invalid configuration (will be set to 30)
FILE_QUEUE_MAX_SIZE=50
```

## Behavior

### Normal Operation
- Files are detected and added to the queue
- Files are processed sequentially (one at a time)
- Queue size is monitored and logged

### Queue Full Scenario
When the queue reaches its maximum capacity:

1. **Warning Logged**: System warns that queue is full
2. **File Moved Back**: Excess files are moved back to the original folder
3. **Later Processing**: Files will be detected again when the queue has space
4. **Statistics Tracked**: Number of files moved back is tracked

### Example Log Output

```
INFO:services.FileQueueProcessor:FileQueueProcessor initialized with max queue size: 20
INFO:services.FileQueueProcessor:⚠️  Queue is at maximum capacity (30 files). Excess files will be moved back to folder.

# When queue is full:
WARNING:services.FileQueueProcessor:⚠️  Queue is full (20 files). Cannot add Kismet-20250331-07-57-08-1 (21).kismet
INFO:services.FileQueueProcessor:✅ File Kismet-20250331-07-57-08-1 (21).kismet moved back to folder for later processing
INFO:services.FileQueueProcessor:📁 Moved Kismet-20250331-07-57-08-1 (21).kismet back to folder for later processing
INFO:services.FileQueueProcessor:📊 Files moved back so far: 1

# Queue status:
INFO:services.WatchingDirectory:📊 Queue Status: 20 files queued (100.0%), processing: Kismet-20250331-07-57-08-1 (1).kismet
INFO:services.WatchingDirectory:📁 Files moved back to folder: 1
```

## Benefits

1. **Configurable Capacity**: Adjust queue size based on system resources
2. **No File Loss**: Excess files are safely moved back to folder
3. **Automatic Recovery**: Files are re-detected when queue space is available
4. **Clear Monitoring**: Detailed logging of queue status and file movements
5. **Resource Protection**: Prevents system overload with maximum limit

## Recommendations

- **Development**: Use 10-15 files for testing
- **Production**: Use 20-25 files for normal operation
- **High Volume**: Use 30 files maximum for high-volume scenarios
- **Low Resources**: Use 10-15 files for systems with limited resources 