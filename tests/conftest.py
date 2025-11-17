"""
Shared test fixtures and configuration for all tests.

This module provides common fixtures, mocks, and utilities that can be
used across all test modules. It includes mocked dependencies, test data
generators, and helper functions.
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


# =============================================================================
# Elasticsearch Fixtures
# =============================================================================

@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.info.return_value = {
        'version': {'number': '8.11.0'},
        'cluster_name': 'test_cluster'
    }
    mock_client.indices.exists.return_value = True
    mock_client.indices.create.return_value = {'acknowledged': True}
    mock_client.index.return_value = {
        '_id': 'test_doc_id',
        'result': 'created',
        '_version': 1
    }
    mock_client.search.return_value = {
        'hits': {
            'total': {'value': 0},
            'hits': []
        }
    }
    return mock_client


@pytest.fixture
def es_config():
    """Elasticsearch configuration for tests."""
    return {
        'host': 'localhost:9200',
        'index': 'test_lab_monitoring',
        'user': 'test_user',
        'password': 'test_password',
        'timeout': 10,
        'max_retries': 3
    }


@pytest.fixture
def sample_es_document():
    """Sample Elasticsearch document."""
    return {
        'timestamp': datetime.now().isoformat(),
        'server_id': 'test_server_01',
        'event_type': 'performance_metrics',
        'data': {
            'cpu': {'utilization_percent': 45.2},
            'memory': {'ram_percent': 60.5},
            'disk': {'io_read_bytes': 1024000}
        }
    }


# =============================================================================
# Performance Monitor Fixtures
# =============================================================================

@pytest.fixture
def mock_psutil():
    """Mock psutil library."""
    with patch('psutil.cpu_percent', return_value=45.2), \
         patch('psutil.cpu_count', return_value=8), \
         patch('psutil.cpu_freq', return_value=MagicMock(current=2400.0, min=800.0, max=3600.0)), \
         patch('psutil.virtual_memory', return_value=MagicMock(
             total=16 * 1024**3,
             available=8 * 1024**3,
             percent=50.0,
             used=8 * 1024**3
         )), \
         patch('psutil.swap_memory', return_value=MagicMock(
             total=4 * 1024**3,
             used=1 * 1024**3,
             percent=25.0
         )), \
         patch('psutil.disk_usage', return_value=MagicMock(
             total=500 * 1024**3,
             used=200 * 1024**3,
             free=300 * 1024**3,
             percent=40.0
         )), \
         patch('psutil.net_io_counters', return_value=MagicMock(
             bytes_sent=1024000,
             bytes_recv=2048000,
             packets_sent=1000,
             packets_recv=2000
         )):
        yield


@pytest.fixture
def sample_performance_data():
    """Sample performance monitoring data."""
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu': {
            'utilization_percent': 45.2,
            'utilization_per_core': [40, 50, 45, 48, 42, 46, 44, 47],
            'frequency_mhz': 2400.0,
            'frequency_min_mhz': 800.0,
            'frequency_max_mhz': 3600.0
        },
        'memory': {
            'ram_total_gb': 16.0,
            'ram_available_gb': 8.0,
            'ram_used_gb': 8.0,
            'ram_percent': 50.0,
            'swap_total_gb': 4.0,
            'swap_used_gb': 1.0,
            'swap_percent': 25.0
        },
        'disk': {
            'total_gb': 500.0,
            'used_gb': 200.0,
            'free_gb': 300.0,
            'percent': 40.0,
            'io_read_bytes': 1024000,
            'io_write_bytes': 512000
        },
        'network': {
            'bytes_sent': 1024000,
            'bytes_recv': 2048000,
            'packets_sent': 1000,
            'packets_recv': 2000
        }
    }


# =============================================================================
# Command Monitor Fixtures
# =============================================================================

@pytest.fixture
def sample_commands():
    """Sample command data."""
    return [
        {
            'command': 'ls -la',
            'user': 'testuser',
            'timestamp': datetime.now().isoformat(),
            'dangerous': False,
            'risk_score': 0.1
        },
        {
            'command': 'sudo rm -rf /',
            'user': 'testuser',
            'timestamp': datetime.now().isoformat(),
            'dangerous': True,
            'risk_score': 0.95
        },
        {
            'command': 'python script.py',
            'user': 'testuser',
            'timestamp': datetime.now().isoformat(),
            'dangerous': False,
            'risk_score': 0.2
        }
    ]


@pytest.fixture
def dangerous_command_patterns():
    """Dangerous command patterns for testing."""
    return [
        'rm -rf',
        'dd if=',
        'mkfs',
        ':(){ :|:& };:',
        'chmod -R 777',
        'wget.*|.*bash',
        'curl.*|.*sh'
    ]


# =============================================================================
# User Activity Fixtures
# =============================================================================

@pytest.fixture
def sample_user_activity():
    """Sample user activity data."""
    return {
        'timestamp': datetime.now().isoformat(),
        'user_id': 'user123',
        'session_id': 'session_abc',
        'activity_type': 'keyboard',
        'application': 'vscode',
        'window_title': 'main.py - VSCode',
        'duration_seconds': 120,
        'productive': True
    }


@pytest.fixture
def mock_window_info():
    """Mock window information."""
    return {
        'window_id': 12345,
        'title': 'Test Window - Application',
        'process_name': 'test_app',
        'pid': 9876,
        'geometry': {'x': 100, 'y': 100, 'width': 800, 'height': 600}
    }


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def temp_directory():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_directory):
    """Create sample files for testing."""
    files = []
    for i in range(5):
        file_path = temp_directory / f"test_file_{i}.txt"
        file_path.write_text(f"Test content {i}")
        files.append(file_path)
    return files


# =============================================================================
# Engagement Scoring Fixtures
# =============================================================================

@pytest.fixture
def sample_engagement_data():
    """Sample engagement scoring data."""
    return {
        'user_id': 'user123',
        'timestamp': datetime.now().isoformat(),
        'session_duration': 3600,
        'commands_count': 50,
        'unique_commands': 25,
        'error_rate': 0.05,
        'productivity_score': 0.85,
        'engagement_level': 'high'
    }


@pytest.fixture
def sample_learning_progress():
    """Sample learning progress data."""
    return {
        'user_id': 'user123',
        'skill': 'Python',
        'level': 'intermediate',
        'progress_percent': 65,
        'completed_exercises': 30,
        'total_exercises': 50,
        'last_activity': datetime.now().isoformat()
    }


# =============================================================================
# Data Aggregator Fixtures
# =============================================================================

@pytest.fixture
def sample_aggregation_data():
    """Sample data for aggregation."""
    base_time = datetime.now()
    return [
        {
            'timestamp': (base_time - timedelta(minutes=i)).isoformat(),
            'metric': 'cpu_usage',
            'value': 40 + i,
            'server_id': 'server1'
        }
        for i in range(10)
    ]


# =============================================================================
# AI Model Fixtures
# =============================================================================

@pytest.fixture
def mock_sklearn_model():
    """Mock sklearn model."""
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.75]
    mock_model.predict_proba.return_value = [[0.25, 0.75]]
    mock_model.score.return_value = 0.92
    return mock_model


@pytest.fixture
def sample_training_data():
    """Sample training data for ML models."""
    return {
        'X': [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],
        'y': [0, 1, 0, 1]
    }


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        'server_id': 'test_server',
        'elasticsearch': {
            'host': 'localhost:9200',
            'index': 'test_monitoring',
            'user': 'test',
            'password': 'test123'
        },
        'monitoring': {
            'interval': 60,
            'performance': True,
            'commands': True,
            'user_activity': True
        },
        'logging': {
            'level': 'DEBUG',
            'file': '/tmp/test.log'
        }
    }


@pytest.fixture
def config_file(temp_directory, sample_config):
    """Create temporary config file."""
    config_path = temp_directory / "config.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


# =============================================================================
# Time-related Fixtures
# =============================================================================

@pytest.fixture
def fixed_datetime():
    """Fixed datetime for consistent testing."""
    return datetime(2025, 1, 1, 12, 0, 0)


@pytest.fixture
def time_range():
    """Time range for testing."""
    end = datetime.now()
    start = end - timedelta(hours=24)
    return {'start': start, 'end': end}


# =============================================================================
# Utility Functions
# =============================================================================

def assert_valid_timestamp(timestamp_str):
    """Assert that timestamp is valid ISO format."""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


def assert_dict_contains_keys(data, required_keys):
    """Assert dictionary contains all required keys."""
    assert all(key in data for key in required_keys), \
        f"Missing keys: {set(required_keys) - set(data.keys())}"


# =============================================================================
# Parametrize Data
# =============================================================================

# CPU usage test data
CPU_USAGE_DATA = [
    (0.0, "idle"),
    (25.5, "low"),
    (50.0, "medium"),
    (75.8, "high"),
    (95.2, "critical"),
    (100.0, "maximum")
]

# Memory usage test data
MEMORY_USAGE_DATA = [
    (512 * 1024**2, "512MB"),
    (2 * 1024**3, "2GB"),
    (8 * 1024**3, "8GB"),
    (16 * 1024**3, "16GB"),
    (32 * 1024**3, "32GB")
]

# Risk score test data
RISK_SCORES = [
    (0.0, "safe"),
    (0.3, "low_risk"),
    (0.5, "medium_risk"),
    (0.7, "high_risk"),
    (0.9, "critical_risk")
]
