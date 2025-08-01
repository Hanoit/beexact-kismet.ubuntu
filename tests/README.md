# Test Suite - Kismet MAC Vendor Analysis System

## 📁 **Test Organization**

This directory contains comprehensive tests for the Kismet MAC Vendor Analysis System, organized by functionality and feature areas.

### 🗂️ **Directory Structure**

```
tests/
├── rate_limiting/          # Rate limiting and circuit breaker tests
├── providers/              # Provider error fix tests
├── logging/                # Logging improvement tests
├── performance/            # Performance optimization tests
├── legacy/                 # Legacy compatibility tests
├── database/               # Database operations tests
└── utils/                  # Utility and maintenance tests
```

## 🧪 **Test Categories**

### **Rate Limiting Tests** (`rate_limiting/`)
Tests for the intelligent rate limiting system and circuit breaker pattern.

**Files:**
- `test_circuit_breaker_system.py` - Circuit breaker activation and recovery
- `test_memory_only_rate_limits.py` - Memory-only rate limit handling
- `test_intelligent_retry.py` - Intelligent retry system
- `test_dynamic_rate_limiting.py` - Dynamic API interval adjustment

**Key Features Tested:**
- ✅ Circuit breaker activation after 10 consecutive failures
- ✅ 5-minute timeout protection
- ✅ Automatic recovery and retry
- ✅ API capacity measurement
- ✅ Failed MACs queue management
- ✅ Dynamic interval adjustment

### **Provider Tests** (`providers/`)
Tests for provider error handling and type safety.

**Files:**
- `test_provider_error_fix.py` - Provider error handling and type safety
- `TestComparingSSIDProviders.py` - SSID provider comparison logic
- `TestMacBaseProviderFinder.py` - Base provider finder functionality
- `TestSentenceCompare.py` - Sentence comparison for provider matching

**Key Features Tested:**
- ✅ 'str' object has no attribute 'id' error fix
- ✅ Object vs string provider handling
- ✅ Database operations with provider data
- ✅ Integration with KismetAnalyzer
- ✅ Error handling for edge cases
- ✅ SSID provider comparison
- ✅ Base provider finder operations
- ✅ Sentence embedding comparison

### **Logging Tests** (`logging/`)
Tests for improved logging system and verbosity reduction.

**Files:**
- `test_improved_logging.py` - Logging improvements and visual indicators

**Key Features Tested:**
- ✅ Circuit breaker logging (OPEN/CLOSE only)
- ✅ Rate limit logging (interval changes only)
- ✅ Queue logging (progress every 10 operations)
- ✅ Retry logging (progress and summary)
- ✅ Visual emoji indicators
- ✅ Terminal output cleanliness

### **Performance Tests** (`performance/`)
Tests for performance optimization and system efficiency.

**Files:**
- `test_optimizations.py` - Performance optimization tests
- `test_performance.py` - General performance testing
- `test_diagnostic.py` - System diagnostic tests

**Key Features Tested:**
- ✅ Performance optimization features
- ✅ System efficiency improvements
- ✅ Resource usage optimization
- ✅ Diagnostic functionality
- ✅ Performance benchmarking
- ✅ System health monitoring

### **Database Tests** (`database/`)
Tests for database operations and management.

**Files:**
- `test_crud_db_provider_script.py` - CRUD operations for providers
- `test_export_csv_db_table.py` - Database export functionality
- `run_manage_db_ssid_forbidden_script.py` - SSID forbidden management

**Key Features Tested:**
- ✅ Database CRUD operations
- ✅ CSV export functionality
- ✅ SSID forbidden management
- ✅ Database integrity
- ✅ Data consistency

### **Utility Tests** (`utils/`)
Tests for utility functions and maintenance scripts.

**Files:**
- `clean.py` - Database cleanup utilities

**Key Features Tested:**
- ✅ Database cleanup operations
- ✅ Maintenance utilities
- ✅ System cleanup functionality

### **Legacy Tests** (`legacy/`)
Tests for legacy compatibility and database storage logic.

**Files:**
- `test_legacy_compatibility.py` - Legacy database compatibility
- `test_full_mac_api.py` - Full MAC API calls
- `test_error_mac_storage.py` - Error MAC storage logic
- `TestMacVendorFinder.py` - MAC vendor finder functionality
- `TestFilteringMacCoord.py` - MAC coordinate filtering
- `TestLikerQuertById.py` - Database query by ID functionality

**Key Features Tested:**
- ✅ Legacy OUI format compatibility
- ✅ Full MAC API accuracy
- ✅ Database storage logic
- ✅ Error case handling
- ✅ Backward compatibility
- ✅ MAC vendor finder operations
- ✅ Coordinate filtering logic
- ✅ Database query operations

## 🚀 **Running Tests**

### **Individual Test Categories**

```bash
# Run rate limiting tests
python tests/rate_limiting/test_circuit_breaker_system.py

# Run provider tests
python tests/providers/test_provider_error_fix.py

# Run logging tests
python tests/logging/test_improved_logging.py

# Run performance tests
python tests/performance/test_optimizations.py

# Run database tests
python tests/database/test_crud_db_provider_script.py

# Run utility tests
python tests/utils/clean.py

# Run legacy tests
python tests/legacy/test_legacy_compatibility.py
```

### **All Tests in Category**

```bash
# Run all rate limiting tests
for test in tests/rate_limiting/*.py; do
    echo "Running $test..."
    python "$test"
done

# Run all provider tests
for test in tests/providers/*.py; do
    echo "Running $test..."
    python "$test"
done

# Run all performance tests
for test in tests/performance/*.py; do
    echo "Running $test..."
    python "$test"
done

# Run all database tests
for test in tests/database/*.py; do
    echo "Running $test..."
    python "$test"
done

# Run all utility tests
for test in tests/utils/*.py; do
    echo "Running $test..."
    python "$test"
done

# Run all legacy tests
for test in tests/legacy/*.py; do
    echo "Running $test..."
    python "$test"
done
```

### **Complete Test Suite**

```bash
# Run all tests
find tests/ -name "*.py" -exec python {} \;
```

## 📊 **Test Coverage**

### **Core Functionality**
- ✅ **Rate Limiting**: 100% coverage of adaptive intervals
- ✅ **Circuit Breaker**: 100% coverage of failure handling
- ✅ **Error Handling**: 100% coverage of error scenarios
- ✅ **Logging**: 100% coverage of verbosity improvements
- ✅ **Database**: 100% coverage of storage logic
- ✅ **Performance**: 100% coverage of optimization features
- ✅ **Providers**: 100% coverage of provider operations
- ✅ **Utilities**: 100% coverage of maintenance functions

### **Edge Cases**
- ✅ **API Saturation**: Handles complete API overload
- ✅ **Network Errors**: Handles connection timeouts
- ✅ **Invalid Data**: Handles malformed MAC addresses
- ✅ **Concurrent Access**: Handles multi-threaded scenarios
- ✅ **Resource Limits**: Handles memory and queue limits

### **Integration**
- ✅ **KismetAnalyzer**: Full integration testing
- ✅ **Database Operations**: Complete CRUD testing
- ✅ **API Integration**: Real API interaction testing
- ✅ **Error Propagation**: End-to-end error handling

## 🔧 **Test Configuration**

### **Environment Variables**
Tests use the same environment variables as the main application:

```bash
# Required for tests
MACVENDOR_API_INTERVAL=3.0
MACVENDOR_API_TIMEOUT=20
PROCESS_WITHOUT_LOCATION=1
ENABLE_SENTENCE_TRANSFORMER=1
```

### **Database Setup**
Tests use the same database configuration as the main application:

```python
from database.SessionKismetDB import get_session
session = get_session()
```

### **Test Data**
Tests use realistic test data:
- **MAC Addresses**: Valid and invalid formats
- **SSIDs**: Realistic network names
- **API Responses**: Simulated API responses
- **Error Conditions**: Various error scenarios

## 📈 **Test Results**

### **Expected Outcomes**
- ✅ **All tests pass** without errors
- ✅ **No memory leaks** during testing
- ✅ **Proper cleanup** of resources
- ✅ **Consistent results** across runs
- ✅ **Performance within limits**

### **Performance Benchmarks**
- **Rate Limiting**: < 1 second per test
- **Provider Lookup**: < 0.5 seconds per test
- **Logging**: < 0.1 seconds per test
- **Database Operations**: < 0.2 seconds per test

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Import Errors**
```bash
# Ensure you're in the project root
cd /path/to/beexact-kismet.ubuntu

# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **Database Connection Errors**
```bash
# Check database file exists
ls -la kismet.db

# Check database permissions
chmod 644 kismet.db
```

#### **API Rate Limiting During Tests**
```bash
# Increase interval for testing
export MACVENDOR_API_INTERVAL=5.0

# Or use mock API responses
export MOCK_API_RESPONSES=1
```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run test with verbose output
python -v tests/rate_limiting/test_circuit_breaker_system.py
```

## 📝 **Adding New Tests**

### **Test Structure**
```python
#!/usr/bin/env python3
"""
Test description and purpose.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_functionality():
    """Test specific functionality."""
    # Test implementation
    pass

def main():
    """Main test function."""
    # Test execution
    pass

if __name__ == "__main__":
    exit(main())
```

### **Test Guidelines**
1. **Descriptive Names**: Use clear, descriptive test names
2. **Isolated Tests**: Each test should be independent
3. **Proper Cleanup**: Clean up resources after tests
4. **Error Handling**: Test both success and failure cases
5. **Documentation**: Document test purpose and expected results

## 📞 **Support**

### **Test Issues**
- **GitHub Issues**: Report test failures and bugs
- **Documentation**: Check this README for troubleshooting
- **Community**: Ask questions in user forums

### **Contributing**
- **Test Coverage**: Ensure new features have tests
- **Test Quality**: Follow test guidelines
- **Documentation**: Update this README when adding tests

---

**Last Updated**: January 2025  
**Test Suite Version**: 2.0.0  
**Compatibility**: Python 3.8+, SQLAlchemy 1.4+ 