"""Unit tests for Data Aggregator Module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import numpy as np
from agent.data_aggregator import DataAggregator


class TestDataAggregatorInitialization:
    """Test DataAggregator initialization."""
    
    def test_initialization_defaults(self):
        aggregator = DataAggregator()
        
        assert aggregator.aggregation_interval_minutes == 15
        assert aggregator.buffer_max_size == 120
        assert len(aggregator.performance_buffer) == 0
    
    def test_initialization_custom_params(self):
        aggregator = DataAggregator(
            aggregation_interval_minutes=30,
            buffer_max_size=200
        )
        
        assert aggregator.aggregation_interval_minutes == 30
        assert aggregator.buffer_max_size == 200


class TestPerformanceMetricsBuffering:
    """Test performance metrics buffering."""
    
    def test_add_performance_metric(self):
        aggregator = DataAggregator()
        
        metric = {
            'cpu': {'utilization_percent': 50.0},
            'memory': {'ram_percent': 60.0}
        }
        
        aggregator.add_performance_metric(metric)
        
        assert len(aggregator.performance_buffer) == 1
    
    def test_buffer_max_size_enforcement(self):
        aggregator = DataAggregator(buffer_max_size=5)
        
        for i in range(10):
            aggregator.add_performance_metric({'value': i})
        
        assert len(aggregator.performance_buffer) == 5


class TestShouldSendLogic:
    """Test should send to ES logic."""
    
    def test_should_send_performance_false_no_data(self):
        aggregator = DataAggregator()
        
        result = aggregator.should_send_performance_to_es()
        
        assert result is False
    
    def test_should_send_performance_false_not_elapsed(self):
        aggregator = DataAggregator(aggregation_interval_minutes=60)
        aggregator.add_performance_metric({'test': 'data'})
        
        result = aggregator.should_send_performance_to_es()
        
        assert result is False
    
    def test_should_send_performance_true(self):
        aggregator = DataAggregator(aggregation_interval_minutes=0)
        aggregator.add_performance_metric({'test': 'data'})
        aggregator.last_performance_sent = datetime.now(timezone.utc) - timedelta(minutes=20)
        
        result = aggregator.should_send_performance_to_es()
        
        assert result is True


class TestPerformanceAggregation:
    """Test performance metrics aggregation."""
    
    def test_aggregate_empty_buffer(self):
        aggregator = DataAggregator()
        
        result = aggregator.aggregate_performance_metrics()
        
        assert result is None
    
    def test_aggregate_cpu_metrics(self):
        aggregator = DataAggregator()
        
        # Add CPU metrics
        aggregator.add_performance_metric({
            'cpu': {'utilization_percent': 50.0}
        })
        aggregator.add_performance_metric({
            'cpu': {'utilization_percent': 60.0}
        })
        aggregator.add_performance_metric({
            'cpu': {'utilization_percent': 70.0}
        })
        
        result = aggregator.aggregate_performance_metrics()
        
        assert result is not None
        assert 'cpu' in result
        assert result['cpu']['utilization_percent_avg'] == 60.0
        assert result['cpu']['utilization_percent_max'] == 70.0
        assert result['cpu']['utilization_percent_min'] == 50.0
    
    def test_aggregate_memory_metrics(self):
        aggregator = DataAggregator()
        
        aggregator.add_performance_metric({
            'memory': {'ram_percent': 50.0, 'ram_used_gb': 8.0, 'ram_total_gb': 16.0}
        })
        aggregator.add_performance_metric({
            'memory': {'ram_percent': 60.0, 'ram_used_gb': 9.6, 'ram_total_gb': 16.0}
        })
        
        result = aggregator.aggregate_performance_metrics()
        
        assert result is not None
        assert 'memory' in result
        assert result['memory']['ram_percent_avg'] == 55.0
    
    def test_aggregate_disk_metrics(self):
        aggregator = DataAggregator()
        
        aggregator.add_performance_metric({
            'disk': {'io_read_bytes': 1000, 'io_write_bytes': 2000}
        })
        aggregator.add_performance_metric({
            'disk': {'io_read_bytes': 1500, 'io_write_bytes': 2500}
        })
        
        result = aggregator.aggregate_performance_metrics()
        
        assert result is not None
        assert 'disk' in result
        assert result['disk']['io_read_bytes_total'] == 2500
        assert result['disk']['io_write_bytes_total'] == 4500
    
    def test_aggregate_network_metrics(self):
        aggregator = DataAggregator()
        
        aggregator.add_performance_metric({
            'network': {'bytes_sent': 1000, 'bytes_recv': 2000}
        })
        aggregator.add_performance_metric({
            'network': {'bytes_sent': 1500, 'bytes_recv': 2500}
        })
        
        result = aggregator.aggregate_performance_metrics()
        
        assert result is not None
        assert 'network' in result
        assert result['network']['bytes_sent_total'] == 2500
        assert result['network']['bytes_recv_total'] == 4500


class TestCommandTracking:
    """Test command event tracking."""
    
    def test_command_counts_initialized(self):
        aggregator = DataAggregator()
        
        assert isinstance(aggregator.command_counts, dict)


class TestEdgeCases:
    """Test edge cases."""
    
    def test_aggregate_with_missing_fields(self):
        aggregator = DataAggregator()
        
        # Add metric with only CPU
        aggregator.add_performance_metric({
            'cpu': {'utilization_percent': 50.0}
        })
        
        result = aggregator.aggregate_performance_metrics()
        
        assert result is not None
        assert 'cpu' in result
    
    def test_aggregate_with_empty_metrics(self):
        aggregator = DataAggregator()
        
        aggregator.add_performance_metric({})
        
        result = aggregator.aggregate_performance_metrics()
        
        # Should handle gracefully
        assert result is not None
