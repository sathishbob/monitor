"""
Performance Monitor Module - System Performance Metrics Collection

This module provides comprehensive system performance monitoring capabilities for lab servers.
It collects real-time metrics on CPU, memory, disk, network, and process performance to
ensure optimal server operation and identify potential performance bottlenecks.

Key Features:
- Real-time CPU usage monitoring (per-core and overall)
- Memory utilization tracking (RAM, swap, virtual memory)
- Disk I/O performance and storage capacity monitoring
- Network interface statistics and bandwidth usage
- Process-level performance analysis
- Performance trend analysis and alerting
- Resource usage optimization recommendations

The module integrates with the Elasticsearch backend to store historical performance data
for trend analysis, capacity planning, and performance optimization.
"""

import logging
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# Set up module-level logging
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    System performance monitoring and metrics collection.
    
    This class provides comprehensive monitoring of system resources including CPU,
    memory, disk, network, and process performance. It collects real-time metrics
    and stores them for historical analysis and trend identification.
    
    The monitor supports:
    - Real-time resource usage tracking
    - Performance bottleneck identification
    - Capacity planning and resource optimization
    - Performance trend analysis over time
    - Alert generation for resource thresholds
    - Integration with external monitoring systems
    
    All metrics are collected using the psutil library for cross-platform compatibility
    and stored in Elasticsearch for long-term analysis and reporting.
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize the performance monitor.
        
        Args:
            max_history_size (int): Maximum number of historical measurements to retain in memory
        """
        # Configuration for data retention and monitoring
        self.max_history_size = max_history_size
        
        # Performance metrics storage
        # CPU performance history with timestamp and utilization data
        self.cpu_history: List[Dict[str, Any]] = []
        # Memory usage history including RAM, swap, and virtual memory
        self.memory_history: List[Dict[str, Any]] = []
        # Disk performance history with I/O statistics and capacity
        self.disk_history: List[Dict[str, Any]] = []
        # Network performance history with interface statistics
        self.network_history: List[Dict[str, Any]] = []
        
        # Performance thresholds and alerting
        # CPU utilization threshold for performance alerts (percentage)
        self.cpu_threshold = 80.0
        # Memory utilization threshold for performance alerts (percentage)
        self.memory_threshold = 85.0
        # Disk usage threshold for capacity alerts (percentage)
        self.disk_threshold = 90.0
        
        # Alert tracking and management
        # List of active performance alerts
        self.active_alerts: List[Dict[str, Any]] = []
        # Performance optimization recommendations
        self.optimization_recommendations: List[str] = []
        
        logger.info("Performance monitor initialized with max history size: %d", max_history_size)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect comprehensive system performance metrics.
        
        This method gathers real-time performance data from all monitored system
        components including CPU, memory, disk, and network resources.
        
        Returns:
            Dict[str, Any]: Complete performance metrics snapshot with timestamp
        """
        try:
            # Get current timestamp for metrics collection
            timestamp = datetime.now(timezone.utc)
            
            # Collect CPU performance metrics
            cpu_metrics = self._collect_cpu_metrics()
            
            # Collect memory utilization metrics
            memory_metrics = self._collect_memory_metrics()
            
            # Collect disk performance metrics
            disk_metrics = self._collect_disk_metrics()
            
            # Collect network performance metrics
            network_metrics = self._collect_network_metrics()
            
            # Compile comprehensive metrics snapshot
            metrics = {
                'timestamp': timestamp.isoformat(),
                'cpu': cpu_metrics,
                'memory': memory_metrics,
                'disk': disk_metrics,
                'network': network_metrics,
                'system_info': {
                    'platform': psutil.sys.platform,
                    'python_version': psutil.sys.version,
                    'psutil_version': psutil.version_info
                }
            }
            
            # Store metrics in historical records
            self._store_metrics(metrics)
            
            # Check for performance thresholds and generate alerts
            self._check_performance_thresholds(metrics)
            
            logger.debug("Performance metrics collected successfully")
            return metrics
            
        except Exception as e:
            logger.error("Error collecting performance metrics: %s", e)
            return {}
    
    def _collect_cpu_metrics(self) -> Dict[str, Any]:
        """
        Collect CPU performance metrics.
        
        Returns:
            Dict[str, Any]: CPU utilization, frequency, and per-core statistics
        """
        try:
            # Get overall CPU utilization percentage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get per-core CPU utilization
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Get CPU frequency information
            cpu_freq = psutil.cpu_freq()
            
            # Get CPU count information
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            return {
                'utilization_percent': cpu_percent,
                'utilization_per_core': cpu_per_core,
                'frequency_mhz': cpu_freq.current if cpu_freq else None,
                'frequency_min_mhz': cpu_freq.min if cpu_freq else None,
                'frequency_max_mhz': cpu_freq.max if cpu_freq else None,
                'core_count_physical': cpu_count,
                'core_count_logical': cpu_count_logical,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
        except Exception as e:
            logger.error("Error collecting CPU metrics: %s", e)
            return {}
    
    def _collect_memory_metrics(self) -> Dict[str, Any]:
        """
        Collect memory utilization metrics.
        
        Returns:
            Dict[str, Any]: RAM, swap, and virtual memory statistics
        """
        try:
            # Get virtual memory statistics
            virtual_memory = psutil.virtual_memory()
            
            # Get swap memory statistics
            swap_memory = psutil.swap_memory()
            
            return {
                'ram_total_gb': virtual_memory.total / (1024**3),
                'ram_available_gb': virtual_memory.available / (1024**3),
                'ram_used_gb': virtual_memory.used / (1024**3),
                'ram_percent': virtual_memory.percent,
                'swap_total_gb': swap_memory.total / (1024**3),
                'swap_used_gb': swap_memory.used / (1024**3),
                'swap_percent': swap_memory.percent
            }
            
        except Exception as e:
            logger.error("Error collecting memory metrics: %s", e)
            return {}
    
    def _collect_disk_metrics(self) -> Dict[str, Any]:
        """
        Collect disk performance and capacity metrics.
        
        Returns:
            Dict[str, Any]: Disk usage, I/O statistics, and capacity information
        """
        try:
            # Get disk partition information
            disk_partitions = psutil.disk_partitions()
            
            # Get disk usage for all partitions
            disk_usage = {}
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = {
                        'mountpoint': partition.mountpoint,
                        'filesystem': partition.fstype,
                        'total_gb': usage.total / (1024**3),
                        'used_gb': usage.used / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'percent': usage.percent
                    }
                except PermissionError:
                    # Skip partitions without read access
                    continue
            
            # Get disk I/O statistics
            disk_io = psutil.disk_io_counters()
            
            return {
                'partitions': disk_usage,
                'io_read_bytes': disk_io.read_bytes if disk_io else 0,
                'io_write_bytes': disk_io.write_bytes if disk_io else 0,
                'io_read_count': disk_io.read_count if disk_io else 0,
                'io_write_count': disk_io.write_count if disk_io else 0
            }
            
        except Exception as e:
            logger.error("Error collecting disk metrics: %s", e)
            return {}
    
    def _collect_network_metrics(self) -> Dict[str, Any]:
        """
        Collect network interface and bandwidth metrics.
        
        Returns:
            Dict[str, Any]: Network interface statistics and bandwidth usage
        """
        try:
            # Get network interface statistics
            net_io = psutil.net_io_counters()
            
            # Get network interface addresses
            net_addresses = psutil.net_if_addrs()
            
            # Get network interface status
            net_status = psutil.net_if_stats()
            
            return {
                'bytes_sent': net_io.bytes_sent if net_io else 0,
                'bytes_recv': net_io.bytes_recv if net_io else 0,
                'packets_sent': net_io.packets_sent if net_io else 0,
                'packets_recv': net_io.packets_recv if net_io else 0,
                'interfaces': {
                    interface: {
                        'addresses': [addr.address for addr in addresses],
                        'status': net_status.get(interface, {}).isup if interface in net_status else False
                    }
                    for interface, addresses in net_addresses.items()
                }
            }
            
        except Exception as e:
            logger.error("Error collecting network metrics: %s", e)
            return {}
    
    def _store_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Store performance metrics in historical records.
        
        Args:
            metrics (Dict[str, Any]): Performance metrics to store
        """
        try:
            # Store CPU metrics
            if 'cpu' in metrics:
                self.cpu_history.append(metrics['cpu'])
                if len(self.cpu_history) > self.max_history_size:
                    self.cpu_history.pop(0)
            
            # Store memory metrics
            if 'memory' in metrics:
                self.memory_history.append(metrics['memory'])
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)
            
            # Store disk metrics
            if 'disk' in metrics:
                self.disk_history.append(metrics['disk'])
                if len(self.disk_history) > self.max_history_size:
                    self.disk_history.pop(0)
            
            # Store network metrics
            if 'network' in metrics:
                self.network_history.append(metrics['network'])
                if len(self.network_history) > self.max_history_size:
                    self.network_history.pop(0)
                    
        except Exception as e:
            logger.error("Error storing performance metrics: %s", e)
    
    def _check_performance_thresholds(self, metrics: Dict[str, Any]) -> None:
        """
        Check performance metrics against thresholds and generate alerts.
        
        Args:
            metrics (Dict[str, Any]): Current performance metrics
        """
        try:
            # Check CPU utilization threshold
            if 'cpu' in metrics and 'utilization_percent' in metrics['cpu']:
                cpu_util = metrics['cpu']['utilization_percent']
                if cpu_util > self.cpu_threshold:
                    self._create_alert('CPU', f"High CPU utilization: {cpu_util:.1f}%", 'warning')
            
            # Check memory utilization threshold
            if 'memory' in metrics and 'ram_percent' in metrics['memory']:
                mem_util = metrics['memory']['ram_percent']
                if mem_util > self.memory_threshold:
                    self._create_alert('Memory', f"High memory utilization: {mem_util:.1f}%", 'warning')
            
            # Check disk usage threshold
            if 'disk' in metrics and 'partitions' in metrics['disk']:
                for device, partition in metrics['disk']['partitions'].items():
                    if partition['percent'] > self.disk_threshold:
                        self._create_alert('Disk', f"High disk usage on {device}: {partition['percent']:.1f}%", 'warning')
                        
        except Exception as e:
            logger.error("Error checking performance thresholds: %s", e)
    
    def _create_alert(self, alert_type: str, message: str, severity: str) -> None:
        """
        Create a performance alert.
        
        Args:
            alert_type (str): Type of performance alert
            message (str): Alert message description
            severity (str): Alert severity level
        """
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }
        
        self.active_alerts.append(alert)
        logger.warning("Performance alert: %s - %s", alert_type, message)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current performance status.
        
        Returns:
            Dict[str, Any]: Performance summary with current metrics and alerts
        """
        try:
            # Get latest metrics if available
            latest_cpu = self.cpu_history[-1] if self.cpu_history else {}
            latest_memory = self.memory_history[-1] if self.memory_history else {}
            latest_disk = self.disk_history[-1] if self.disk_history else {}
            latest_network = self.network_history[-1] if self.network_history else {}
            
            return {
                'current_metrics': {
                    'cpu': latest_cpu,
                    'memory': latest_memory,
                    'disk': latest_disk,
                    'network': latest_network
                },
                'active_alerts': self.active_alerts,
                'optimization_recommendations': self.optimization_recommendations,
                'history_sizes': {
                    'cpu': len(self.cpu_history),
                    'memory': len(self.memory_history),
                    'disk': len(self.disk_history),
                    'network': len(self.network_history)
                }
            }
            
        except Exception as e:
            logger.error("Error generating performance summary: %s", e)
            return {}
    
    def clear_history(self) -> None:
        """Clear all historical performance data."""
        self.cpu_history.clear()
        self.memory_history.clear()
        self.disk_history.clear()
        self.network_history.clear()
        self.active_alerts.clear()
        self.optimization_recommendations.clear()
        logger.info("Performance monitor history cleared")


__all__ = ["PerformanceMonitor"]
