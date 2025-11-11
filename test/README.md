# Test Directory

This directory contains all test-related files for the Lab Server Monitoring Agent.

## Test Files

### 1. `test_installation.py`
**Purpose**: Comprehensive installation and dependency verification test
**Usage**: 
```bash
python3 test/test_installation.py
```

**Tests**:
- Module imports (required and platform-specific)
- Basic functionality of monitoring agent classes
- Elasticsearch connection
- Platform-specific features (Windows GUI, Linux X11)

**Output**: Detailed test results with pass/fail status for each component

### 2. `test_security.py`
**Purpose**: Security feature testing for the monitoring agent's Flask API
**Usage**:
```bash
python3 test/test_security.py <base_url> <api_key>
```

**Example**:
```bash
python3 test/test_security.py http://localhost:5000 my-api-key
```

**Tests**:
- Health endpoint (no auth required)
- Commands endpoint (with/without authentication)
- Execute endpoint (with/without authentication)
- Dangerous command blocking
- Unauthorized command blocking
- Rate limiting

**Output**: Security test results with detailed status for each endpoint

### 3. `test_es_connection.py`
**Purpose**: Simple Elasticsearch connection and index creation test
**Usage**:
```bash
python3 test/test_es_connection.py [host] [index_name]
```

**Examples**:
```bash
# Test default connection
python3 test/test_es_connection.py

# Test custom host and index
python3 test/test_es_connection.py https://es.example.com:9200 my_index
```

**Tests**:
- Elasticsearch connection
- Index existence check
- Index creation (if needed)
- Test document insertion

**Output**: Connection status and index operation results

## Running All Tests

You can run all tests in sequence:

```bash
# 1. Test installation and dependencies
python3 test/test_installation.py

# 2. Test Elasticsearch connection (adjust host as needed)
python3 test/test_es_connection.py

# 3. Test security features (requires running agent with API key)
python3 test/test_security.py http://localhost:5000 your-api-key
```

## Test Prerequisites

### For Installation Test
- Python 3.8+ installed
- All dependencies from `requirements.txt` installed

### For Security Test
- Monitoring agent running with Flask API enabled
- API key configured
- Agent accessible at the specified URL

### For Elasticsearch Test
- Elasticsearch server running
- Network access to Elasticsearch host

## Notes

- All tests are designed to be non-destructive
- Test files can be run independently
- Security tests require a running agent instance
- Installation test is comprehensive and should be run first
- Elasticsearch test is useful for troubleshooting connection issues
