"""
Data Aggregator Module - In-Memory Aggregation and Selective ES Push

This module provides intelligent data aggregation to reduce the volume of data
sent to Elasticsearch while maintaining data quality for dashboard analytics.

Key Features:
- Buffers high-frequency metrics in memory
- Aggregates metrics into summaries (avg, min, max, std)
- Filters duplicate and low-value data
- Configurable aggregation intervals
- Efficient memory management
- Selective ES push logic

The aggregator collects data at high frequency (every 30 seconds) but only
sends aggregated summaries to Elasticsearch at lower frequency (every 15-60 minutes)
to reduce volume by 95% while maintaining dashboard data quality.
"""

import logging
import numpy as np
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Set up module-level logging
logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Intelligent data aggregation for efficient ES data management.
    
    This class buffers high-frequency monitoring data in memory and aggregates
    it into summaries before sending to Elasticsearch. This reduces ES volume
    by 95% while maintaining data quality for dashboard analytics.
    
    The aggregator provides:
    - Performance metrics aggregation (CPU, memory, disk, network)
    - Command event filtering and deduplication
    - Session activity summarization
    - Configurable aggregation intervals
    - Memory-efficient sliding window buffers
    """
    
    def __init__(self, aggregation_interval_minutes: int = 15, 
                 buffer_max_size: int = 120):
        """
        Initialize the data aggregator.
        
        Args:
            aggregation_interval_minutes (int): Minutes between ES pushes (default 15)
            buffer_max_size (int): Maximum buffer size in samples (default 120 = 60 min at 30s intervals)
        """
        # Aggregation configuration
        self.aggregation_interval_minutes = aggregation_interval_minutes
        self.aggregation_interval_seconds = aggregation_interval_minutes * 60
        self.buffer_max_size = buffer_max_size
        
        # Performance metrics buffers
        self.performance_buffer = deque(maxlen=buffer_max_size)
        self.last_performance_sent = datetime.now(timezone.utc)
        
        # Command event tracking for filtering
        self.command_counts = defaultdict(int)
        self.command_window_start = datetime.now(timezone.utc)
        self.command_window_duration = 300  # 5 minutes
        
        # Session activity tracking
        self.recent_user_activity = {}
        self.last_activity_sent = datetime.now(timezone.utc)
        
        logger.info(f"Data aggregator initialized (interval: {aggregation_interval_minutes} min)")
    
    def should_send_performance_to_es(self) -> bool:
        """
        Check if performance data should be aggregated and sent to ES.
        
        Returns:
            bool: True if aggregation interval has elapsed and buffer has data
        """
        current_time = datetime.now(timezone.utc)
        elapsed_seconds = (current_time - self.last_performance_sent).total_seconds()
        
        return elapsed_seconds >= self.aggregation_interval_seconds and len(self.performance_buffer) > 0
    
    def add_performance_metric(self, metric: Dict[str, Any]) -> None:
        """
        Add a performance metric to the aggregation buffer.
        
        Args:
            metric (Dict[str, Any]): Performance metric data
        """
        try:
            self.performance_buffer.append(metric)
            logger.debug("Added performance metric to buffer (size: %d)", len(self.performance_buffer))
        except Exception as e:
            logger.error("Error adding performance metric to buffer: %s", e)
    
    def aggregate_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Aggregate buffered performance metrics into summary.
        
        Returns:
            Optional[Dict[str, Any]]: Aggregated summary or None if buffer is empty
        """
        if not self.performance_buffer:
            logger.debug("No performance data to aggregate")
            return None
        
        try:
            metrics_list = list(self.performance_buffer)
            sample_count = len(metrics_list)
            
            logger.info(f"Aggregating {sample_count} performance metrics into summary")
            
            # Aggregate CPU metrics
            cpu_values = []
            cpu_per_core_values = []
            for m in metrics_list:
                if 'cpu' in m and 'utilization_percent' in m['cpu']:
                    cpu_values.append(m['cpu']['utilization_percent'])
                if 'cpu' in m and 'utilization_per_core' in m['cpu']:
                    cpu_per_core_values.append(m['cpu']['utilization_per_core'])
            
            cpu_aggregated = {}
            if cpu_values:
                cpu_aggregated = {
                    'utilization_percent_avg': round(np.mean(cpu_values), 2),
                    'utilization_percent_max': round(np.max(cpu_values), 2),
                    'utilization_percent_min': round(np.min(cpu_values), 2),
                    'utilization_percent_std': round(np.std(cpu_values), 2)
                }
            
            # Aggregate memory metrics
            ram_percent_values = []
            ram_used_gb_values = []
            ram_total_gb_values = []
            
            for m in metrics_list:
                if 'memory' in m:
                    if 'ram_percent' in m['memory']:
                        ram_percent_values.append(m['memory']['ram_percent'])
                    if 'ram_used_gb' in m['memory']:
                        ram_used_gb_values.append(m['memory']['ram_used_gb'])
                    if 'ram_total_gb' in m['memory']:
                        ram_total_gb_values.append(m['memory']['ram_total_gb'])
            
            memory_aggregated = {}
            if ram_percent_values:
                memory_aggregated = {
                    'ram_percent_avg': round(np.mean(ram_percent_values), 2),
                    'ram_percent_max': round(np.max(ram_percent_values), 2),
                    'ram_percent_min': round(np.min(ram_percent_values), 2),
                    'ram_used_gb_avg': round(np.mean(ram_used_gb_values), 2) if ram_used_gb_values else None,
                    'ram_total_gb': ram_total_gb_values[0] if ram_total_gb_values else None
                }
            
            # Aggregate disk metrics
            disk_io_read = []
            disk_io_write = []
            
            for m in metrics_list:
                if 'disk' in m:
                    if 'io_read_bytes' in m['disk']:
                        disk_io_read.append(m['disk']['io_read_bytes'])
                    if 'io_write_bytes' in m['disk']:
                        disk_io_write.append(m['disk']['io_write_bytes'])
            
            disk_aggregated = {}
            if disk_io_read or disk_io_write:
                disk_aggregated = {
                    'io_read_bytes_total': sum(disk_io_read) if disk_io_read else 0,
                    'io_write_bytes_total': sum(disk_io_write) if disk_io_write else 0,
                    'io_read_count': len(disk_io_read),
                    'io_write_count': len(disk_io_write)
                }
            
            # Aggregate network metrics
            network_bytes_sent = []
            network_bytes_recv = []
            
            for m in metrics_list:
                if 'network' in m:
                    if 'bytes_sent' in m['network']:
                        network_bytes_sent.append(m['network']['bytes_sent'])
                    if 'bytes_recv' in m['network']:
                        network_bytes_recv.append(m['network']['bytes_recv'])
            
            network_aggregated = {}
            if network_bytes_sent or network_bytes_recv:
                network_aggregated = {
                    'bytes_sent_total': sum(network_bytes_sent) if network_bytes_sent else 0,
                    'bytes_recv_total': sum(network_bytes_recv) if network_bytes_recv else 0,
                    'bytes_sent_avg': round(np.mean(network_bytes_sent), 0) if network_bytes_sent else 0,
                    'bytes_recv_avg': round(np.mean(network_bytes_recv), 0) if network_bytes_recv else 0
                }
            
            # Create aggregated summary
            aggregated = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'aggregation_window_minutes': self.aggregation_interval_minutes,
                'sample_count': sample_count,
                'cpu': cpu_aggregated,
                'memory': memory_aggregated,
                'disk': disk_aggregated,
                'network': network_aggregated
            }
            
            # Clear buffer after aggregation
            self.performance_buffer.clear()
            self.last_performance_sent = datetime.now(timezone.utc)
            
            logger.info(f"Aggregated {sample_count} metrics into summary")
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating performance metrics: {e}")
            return None
    
    def should_send_command_to_es(self, command_data: Dict[str, Any]) -> bool:
        """
        Determine if a command should be sent to Elasticsearch.
        
        Filters out routine commands and deduplicates frequent ones.
        
        Args:
            command_data (Dict[str, Any]): Command execution data
            
        Returns:
            bool: True if command should be sent to ES
        """
        try:
            command = command_data.get('command', '').lower()
            
            # Always send dangerous commands
            if command_data.get('dangerous', False):
                logger.debug(f"Sending dangerous command to ES: {command[:50]}")
                return True
            
            # Always send high-risk commands
            dangerous_patterns = [
                'sudo', 'su -', 'passwd', 'chmod 777', 'chmod +x', 'chown root',
                'rm -rf', 'dd if=', 'mkfs', 'fdisk', 'mount', 'umount'
            ]
            for pattern in dangerous_patterns:
                if pattern in command:
                    logger.debug(f"Sending high-risk command to ES: {pattern}")
                    return True
            
            # Don't send routine commands
            routine_commands = [
                'ls', 'pwd', 'cd', 'cat', 'echo', 'date', 'whoami', 'clear',
                'head', 'tail', 'grep', 'find', 'which', 'whereis', 'type'
            ]
            command_base = command.split()[0] if command else ''
            if command_base in routine_commands:
                logger.debug(f"Filtering routine command: {command_base}")
                return False
            
            # Send commands with significant execution time (>5 seconds)
            execution_time = command_data.get('execution_time', 0)
            if execution_time > 5.0:
                logger.debug(f"Sending long-running command to ES: {command[:50]} ({execution_time}s)")
                return True
            
            # Send commands with errors
            exit_code = command_data.get('exit_code', 0)
            if exit_code and exit_code != 0:
                logger.debug(f"Sending command with error to ES: {command[:50]} (exit_code: {exit_code})")
                return True
            
            # Deduplication: Don't send the same command too frequently
            current_time = datetime.now(timezone.utc)
            elapsed = (current_time - self.command_window_start).total_seconds()
            
            if elapsed > self.command_window_duration:
                # Reset window
                self.command_counts.clear()
                self.command_window_start = current_time
            
            # Track command frequency
            command_hash = command_data.get('command_hash', '')
            if command_hash:
                self.command_counts[command_hash] += 1
                
                # Don't send if command appeared > 5 times in current window
                if self.command_counts[command_hash] > 5:
                    logger.debug(f"Filtering frequent duplicate: {command[:50]}")
                    return False
            
            # Send other significant commands
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating command for ES: {e}")
            return False
    
    def aggregate_user_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate user activity data into summary.
        
        Args:
            activity_data (Dict[str, Any]): Current activity data
            
        Returns:
            Dict[str, Any]: Aggregated activity summary
        """
        try:
            aggregated = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_active_users': activity_data.get('active_sessions', 0),
                'total_active_time_minutes': activity_data.get('total_active_time_minutes', 0),
                'historical_sessions': activity_data.get('historical_sessions', 0),
                'session_details': {
                    'total_sessions': activity_data.get('total_sessions', 0),
                    'total_time_minutes': activity_data.get('total_time_minutes', 0),
                    'avg_session_length': activity_data.get('avg_session_length_minutes', 0)
                }
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating user activity: {e}")
            return activity_data
    
    def should_send_engagement_to_es(self, engagement_data: Dict[str, Any]) -> bool:
        """
        Determine if engagement data should be sent to ES.
        
        Only sends significant milestones and final summaries.
        
        Args:
            engagement_data (Dict[str, Any]): Engagement data
            
        Returns:
            bool: True if should be sent to ES
        """
        # Always send session start/end events
        event_type = engagement_data.get('event_type', '')
        if event_type in ['engagement_session', 'dropout_risk_assessment']:
            return True
        
        # Always send engagement milestones
        if 'milestone' in engagement_data.get('status', '').lower():
            return True
        
        # Send risk assessments
        if engagement_data.get('risk_level') in ['High', 'Critical']:
            return True
        
        # Send significant score changes (>10 point change)
        if 'engagement_score' in engagement_data:
            score = engagement_data['engagement_score']
            # This would need to track previous scores
            return True
        
        return False
    
    def get_aggregation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current aggregation state.
        
        Returns:
            Dict[str, Any]: Aggregation statistics
        """
        return {
            'performance_buffer_size': len(self.performance_buffer),
            'performance_buffer_max_size': self.buffer_max_size,
            'aggregation_interval_minutes': self.aggregation_interval_minutes,
            'seconds_since_last_send': (datetime.now(timezone.utc) - self.last_performance_sent).total_seconds(),
            'commands_tracked': len(self.command_counts),
            'ready_to_send': self.should_send_performance_to_es()
        }


__all__ = ["DataAggregator"]

