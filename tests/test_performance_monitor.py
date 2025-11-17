"""
Unit tests for Performance Monitor Module.

This test module provides comprehensive test coverage for the PerformanceMonitor class,
including metrics collection, threshold checking, alert generation, and edge cases.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

# Import test data from conftest
from .conftest import CPU_USAGE_DATA

# Import the module to test
from agent.performance_monitor import PerformanceMonitor


class TestPerformanceMonitorInitialization:
    """Test PerformanceMonitor initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        monitor = PerformanceMonitor()

        assert monitor.max_history_size == 1000
        assert monitor.cpu_history == []
        assert monitor.memory_history == []
        assert monitor.disk_history == []
        assert monitor.network_history == []
        assert monitor.active_alerts == []
        assert monitor.cpu_threshold == 80.0
        assert monitor.memory_threshold == 85.0
        assert monitor.disk_threshold == 90.0

    def test_initialization_with_custom_history_size(self):
        """Test initialization with custom history size."""
        monitor = PerformanceMonitor(max_history_size=500)

        assert monitor.max_history_size == 500


class TestCPUMetricsCollection:
    """Test CPU metrics collection."""

    def test_collect_cpu_metrics_success(self, mock_psutil):
        """Test successful CPU metrics collection."""
        monitor = PerformanceMonitor()
        cpu_metrics = monitor._collect_cpu_metrics()

        assert 'utilization_percent' in cpu_metrics
        assert 'utilization_per_core' in cpu_metrics
        assert 'frequency_mhz' in cpu_metrics
        assert 'core_count_physical' in cpu_metrics
        assert 'core_count_logical' in cpu_metrics

        assert cpu_metrics['utilization_percent'] == 45.2
        assert len(cpu_metrics['utilization_per_core']) > 0
        assert cpu_metrics['frequency_mhz'] == 2400.0

    def test_collect_cpu_metrics_no_frequency(self):
        """Test CPU metrics when frequency info is unavailable."""
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.cpu_count', return_value=4), \
             patch('psutil.cpu_freq', return_value=None):

            monitor = PerformanceMonitor()
            cpu_metrics = monitor._collect_cpu_metrics()

            assert cpu_metrics['frequency_mhz'] is None
            assert cpu_metrics['frequency_min_mhz'] is None
            assert cpu_metrics['frequency_max_mhz'] is None

    def test_collect_cpu_metrics_error_handling(self):
        """Test CPU metrics collection error handling."""
        with patch('psutil.cpu_percent', side_effect=Exception("CPU error")):
            monitor = PerformanceMonitor()
            cpu_metrics = monitor._collect_cpu_metrics()

            assert cpu_metrics == {}


class TestMemoryMetricsCollection:
    """Test memory metrics collection."""

    def test_collect_memory_metrics_success(self, mock_psutil):
        """Test successful memory metrics collection."""
        monitor = PerformanceMonitor()
        memory_metrics = monitor._collect_memory_metrics()

        assert 'ram_total_gb' in memory_metrics
        assert 'ram_available_gb' in memory_metrics
        assert 'ram_used_gb' in memory_metrics
        assert 'ram_percent' in memory_metrics
        assert 'swap_total_gb' in memory_metrics
        assert 'swap_used_gb' in memory_metrics
        assert 'swap_percent' in memory_metrics

        assert memory_metrics['ram_percent'] == 50.0
        assert memory_metrics['swap_percent'] == 25.0

    def test_collect_memory_metrics_calculations(self, mock_psutil):
        """Test memory metrics GB conversions."""
        monitor = PerformanceMonitor()
        memory_metrics = monitor._collect_memory_metrics()

        # 16GB total
        assert memory_metrics['ram_total_gb'] == pytest.approx(16.0, rel=0.1)
        # 8GB available
        assert memory_metrics['ram_available_gb'] == pytest.approx(8.0, rel=0.1)

    def test_collect_memory_metrics_error_handling(self):
        """Test memory metrics collection error handling."""
        with patch('psutil.virtual_memory', side_effect=Exception("Memory error")):
            monitor = PerformanceMonitor()
            memory_metrics = monitor._collect_memory_metrics()

            assert memory_metrics == {}


class TestDiskMetricsCollection:
    """Test disk metrics collection."""

    def test_collect_disk_metrics_success(self, mock_psutil):
        """Test successful disk metrics collection."""
        monitor = PerformanceMonitor()
        disk_metrics = monitor._collect_disk_metrics()

        assert 'partitions' in disk_metrics
        assert 'io_read_bytes' in disk_metrics
        assert 'io_write_bytes' in disk_metrics
        assert 'io_read_count' in disk_metrics
        assert 'io_write_count' in disk_metrics

        assert disk_metrics['io_read_bytes'] == 1024000
        assert disk_metrics['io_write_bytes'] > 0

    def test_collect_disk_metrics_multiple_partitions(self):
        """Test disk metrics with multiple partitions."""
        # Mock multiple disk partitions
        partition1 = MagicMock()
        partition1.device = '/dev/sda1'
        partition1.mountpoint = '/'
        partition1.fstype = 'ext4'

        partition2 = MagicMock()
        partition2.device = '/dev/sdb1'
        partition2.mountpoint = '/data'
        partition2.fstype = 'xfs'

        usage = MagicMock()
        usage.total = 500 * 1024**3
        usage.used = 200 * 1024**3
        usage.free = 300 * 1024**3
        usage.percent = 40.0

        with patch('psutil.disk_partitions', return_value=[partition1, partition2]), \
             patch('psutil.disk_usage', return_value=usage), \
             patch('psutil.disk_io_counters', return_value=MagicMock(
                 read_bytes=1000, write_bytes=2000, read_count=10, write_count=20
             )):

            monitor = PerformanceMonitor()
            disk_metrics = monitor._collect_disk_metrics()

            assert len(disk_metrics['partitions']) == 2
            assert '/dev/sda1' in disk_metrics['partitions']
            assert '/dev/sdb1' in disk_metrics['partitions']

    def test_collect_disk_metrics_permission_error(self):
        """Test disk metrics when partition access is denied."""
        partition = MagicMock()
        partition.device = '/dev/sda1'
        partition.mountpoint = '/restricted'
        partition.fstype = 'ext4'

        with patch('psutil.disk_partitions', return_value=[partition]), \
             patch('psutil.disk_usage', side_effect=PermissionError("Access denied")), \
             patch('psutil.disk_io_counters', return_value=None):

            monitor = PerformanceMonitor()
            disk_metrics = monitor._collect_disk_metrics()

            # Should skip the partition and continue
            assert 'partitions' in disk_metrics
            assert '/dev/sda1' not in disk_metrics['partitions']

    def test_collect_disk_metrics_no_io_stats(self):
        """Test disk metrics when I/O statistics are unavailable."""
        partition = MagicMock()
        partition.device = '/dev/sda1'
        partition.mountpoint = '/'
        partition.fstype = 'ext4'

        with patch('psutil.disk_partitions', return_value=[partition]), \
             patch('psutil.disk_usage', return_value=MagicMock(
                 total=1000, used=500, free=500, percent=50.0
             )), \
             patch('psutil.disk_io_counters', return_value=None):

            monitor = PerformanceMonitor()
            disk_metrics = monitor._collect_disk_metrics()

            assert disk_metrics['io_read_bytes'] == 0
            assert disk_metrics['io_write_bytes'] == 0


class TestNetworkMetricsCollection:
    """Test network metrics collection."""

    def test_collect_network_metrics_success(self, mock_psutil):
        """Test successful network metrics collection."""
        monitor = PerformanceMonitor()
        network_metrics = monitor._collect_network_metrics()

        assert 'bytes_sent' in network_metrics
        assert 'bytes_recv' in network_metrics
        assert 'packets_sent' in network_metrics
        assert 'packets_recv' in network_metrics
        assert 'interfaces' in network_metrics

        assert network_metrics['bytes_sent'] == 1024000
        assert network_metrics['bytes_recv'] == 2048000

    def test_collect_network_metrics_no_io(self):
        """Test network metrics when I/O counters are unavailable."""
        with patch('psutil.net_io_counters', return_value=None), \
             patch('psutil.net_if_addrs', return_value={}), \
             patch('psutil.net_if_stats', return_value={}):

            monitor = PerformanceMonitor()
            network_metrics = monitor._collect_network_metrics()

            assert network_metrics['bytes_sent'] == 0
            assert network_metrics['bytes_recv'] == 0

    def test_collect_network_metrics_error_handling(self):
        """Test network metrics collection error handling."""
        with patch('psutil.net_io_counters', side_effect=Exception("Network error")):
            monitor = PerformanceMonitor()
            network_metrics = monitor._collect_network_metrics()

            assert network_metrics == {}


class TestComprehensiveMetricsCollection:
    """Test complete metrics collection."""

    def test_collect_metrics_success(self, mock_psutil):
        """Test successful collection of all metrics."""
        monitor = PerformanceMonitor()
        metrics = monitor.collect_metrics()

        assert 'timestamp' in metrics
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'disk' in metrics
        assert 'network' in metrics
        assert 'system_info' in metrics

        # Verify timestamp format
        timestamp = datetime.fromisoformat(metrics['timestamp'].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)

    def test_collect_metrics_stores_history(self, mock_psutil):
        """Test that metrics are stored in history."""
        monitor = PerformanceMonitor()
        monitor.collect_metrics()

        assert len(monitor.cpu_history) == 1
        assert len(monitor.memory_history) == 1
        assert len(monitor.disk_history) == 1
        assert len(monitor.network_history) == 1

    def test_collect_metrics_history_limit(self, mock_psutil):
        """Test that history respects maximum size limit."""
        monitor = PerformanceMonitor(max_history_size=5)

        # Collect more metrics than max_history_size
        for _ in range(10):
            monitor.collect_metrics()

        assert len(monitor.cpu_history) == 5
        assert len(monitor.memory_history) == 5
        assert len(monitor.disk_history) == 5
        assert len(monitor.network_history) == 5

    def test_collect_metrics_error_handling(self):
        """Test metrics collection with errors."""
        with patch('psutil.cpu_percent', side_effect=Exception("Error")):
            monitor = PerformanceMonitor()
            metrics = monitor.collect_metrics()

            # Should return empty dict on total failure
            assert metrics == {}


class TestThresholdChecking:
    """Test performance threshold checking and alerts."""

    def test_cpu_threshold_exceeded(self, mock_psutil):
        """Test alert generation when CPU threshold is exceeded."""
        with patch('psutil.cpu_percent', return_value=95.0):
            monitor = PerformanceMonitor()
            monitor.cpu_threshold = 80.0

            metrics = monitor.collect_metrics()

            # Should have created an alert
            assert len(monitor.active_alerts) > 0
            assert any('CPU' in alert['type'] for alert in monitor.active_alerts)

    def test_memory_threshold_exceeded(self, mock_psutil):
        """Test alert generation when memory threshold is exceeded."""
        high_memory = MagicMock()
        high_memory.total = 16 * 1024**3
        high_memory.available = 1 * 1024**3
        high_memory.used = 15 * 1024**3
        high_memory.percent = 93.0

        with patch('psutil.virtual_memory', return_value=high_memory), \
             patch('psutil.swap_memory', return_value=MagicMock(
                 total=4*1024**3, used=1*1024**3, percent=25.0
             )), \
             patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.disk_partitions', return_value=[]), \
             patch('psutil.net_io_counters', return_value=None):

            monitor = PerformanceMonitor()
            monitor.memory_threshold = 85.0

            metrics = monitor.collect_metrics()

            # Should have created a memory alert
            assert len(monitor.active_alerts) > 0
            assert any('Memory' in alert['type'] for alert in monitor.active_alerts)

    def test_disk_threshold_exceeded(self):
        """Test alert generation when disk threshold is exceeded."""
        partition = MagicMock()
        partition.device = '/dev/sda1'
        partition.mountpoint = '/'
        partition.fstype = 'ext4'

        high_disk_usage = MagicMock()
        high_disk_usage.total = 100 * 1024**3
        high_disk_usage.used = 95 * 1024**3
        high_disk_usage.free = 5 * 1024**3
        high_disk_usage.percent = 95.0

        with patch('psutil.disk_partitions', return_value=[partition]), \
             patch('psutil.disk_usage', return_value=high_disk_usage), \
             patch('psutil.disk_io_counters', return_value=None), \
             patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory', return_value=MagicMock(
                 total=16*1024**3, available=8*1024**3, used=8*1024**3, percent=50.0
             )), \
             patch('psutil.swap_memory', return_value=MagicMock(
                 total=4*1024**3, used=1*1024**3, percent=25.0
             )), \
             patch('psutil.net_io_counters', return_value=None):

            monitor = PerformanceMonitor()
            monitor.disk_threshold = 90.0

            metrics = monitor.collect_metrics()

            # Should have created a disk alert
            assert len(monitor.active_alerts) > 0
            assert any('Disk' in alert['type'] for alert in monitor.active_alerts)

    def test_no_alerts_below_threshold(self, mock_psutil):
        """Test that no alerts are generated when below thresholds."""
        monitor = PerformanceMonitor()
        monitor.cpu_threshold = 90.0
        monitor.memory_threshold = 90.0
        monitor.disk_threshold = 95.0

        metrics = monitor.collect_metrics()

        # Should have no alerts (mock data is below thresholds)
        assert len(monitor.active_alerts) == 0


class TestPerformanceSummary:
    """Test performance summary generation."""

    def test_get_performance_summary_empty(self):
        """Test performance summary with no data."""
        monitor = PerformanceMonitor()
        summary = monitor.get_performance_summary()

        assert 'current_metrics' in summary
        assert summary['current_metrics']['cpu'] == {}
        assert summary['current_metrics']['memory'] == {}
        assert summary['history_sizes']['cpu'] == 0

    def test_get_performance_summary_with_data(self, mock_psutil):
        """Test performance summary with collected data."""
        monitor = PerformanceMonitor()
        monitor.collect_metrics()

        summary = monitor.get_performance_summary()

        assert summary['current_metrics']['cpu'] != {}
        assert summary['current_metrics']['memory'] != {}
        assert summary['history_sizes']['cpu'] == 1
        assert summary['history_sizes']['memory'] == 1
        assert 'active_alerts' in summary

    def test_get_performance_summary_error_handling(self):
        """Test performance summary generation error handling."""
        monitor = PerformanceMonitor()
        # Corrupt the history to cause an error
        monitor.cpu_history = "not a list"

        summary = monitor.get_performance_summary()

        # Should return empty dict on error
        assert summary == {}


class TestHistoryManagement:
    """Test performance history management."""

    def test_clear_history(self, mock_psutil):
        """Test clearing all historical data."""
        monitor = PerformanceMonitor()

        # Collect some metrics
        monitor.collect_metrics()
        monitor.collect_metrics()

        # Create some alerts
        monitor._create_alert('Test', 'Test alert', 'warning')

        assert len(monitor.cpu_history) > 0
        assert len(monitor.active_alerts) > 0

        # Clear history
        monitor.clear_history()

        assert len(monitor.cpu_history) == 0
        assert len(monitor.memory_history) == 0
        assert len(monitor.disk_history) == 0
        assert len(monitor.network_history) == 0
        assert len(monitor.active_alerts) == 0

    def test_history_rotation(self, mock_psutil):
        """Test that old history is removed when limit is reached."""
        monitor = PerformanceMonitor(max_history_size=3)

        # Collect 5 metrics
        for _ in range(5):
            monitor.collect_metrics()

        # Should only keep last 3
        assert len(monitor.cpu_history) == 3
        assert len(monitor.memory_history) == 3


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.parametrize("history_size", [0, 1, 10, 1000, 10000])
    def test_various_history_sizes(self, history_size):
        """Test monitor with various history sizes."""
        monitor = PerformanceMonitor(max_history_size=history_size)
        assert monitor.max_history_size == history_size

    def test_store_metrics_with_missing_keys(self):
        """Test storing metrics with missing keys."""
        monitor = PerformanceMonitor()

        # Metrics with only CPU data
        partial_metrics = {'cpu': {'utilization_percent': 50.0}}
        monitor._store_metrics(partial_metrics)

        assert len(monitor.cpu_history) == 1
        assert len(monitor.memory_history) == 0

    def test_check_thresholds_with_missing_data(self):
        """Test threshold checking with incomplete metrics."""
        monitor = PerformanceMonitor()

        # Metrics with missing nested data
        incomplete_metrics = {
            'cpu': {},
            'memory': {},
            'disk': {}
        }

        # Should not raise an error
        monitor._check_performance_thresholds(incomplete_metrics)

    def test_create_alert_structure(self):
        """Test alert structure and fields."""
        monitor = PerformanceMonitor()
        monitor._create_alert('CPU', 'High CPU usage: 95%', 'critical')

        assert len(monitor.active_alerts) == 1
        alert = monitor.active_alerts[0]

        assert 'timestamp' in alert
        assert 'type' in alert
        assert 'message' in alert
        assert 'severity' in alert
        assert alert['type'] == 'CPU'
        assert alert['severity'] == 'critical'

    @pytest.mark.parametrize("cpu,description", CPU_USAGE_DATA[:3])
    def test_parametrized_cpu_usage(self, cpu, description):
        """Test with various CPU usage levels."""
        with patch('psutil.cpu_percent', return_value=cpu):
            monitor = PerformanceMonitor()
            cpu_metrics = monitor._collect_cpu_metrics()

            assert cpu_metrics['utilization_percent'] == cpu
