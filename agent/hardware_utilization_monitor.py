"""
Hardware Utilization Monitor

Tracks GPU usage, peripherals, and specialized hardware
to justify investments and identify resource bottlenecks.
"""

import logging
import platform
import psutil
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class HardwareUtilizationMonitor:
    """Monitor hardware utilization and peripheral usage."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.gpu_usage_logs: List[Dict[str, Any]] = []
        self.peripheral_usage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.user_hardware_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'gpu_time': 0,
            'peripherals_used': set()
        })

        logger.info("Hardware utilization monitor initialized")

    def track_gpu_usage(self, user_id: str, gpu_id: int,
                       utilization_percent: float, memory_used_mb: float,
                       duration: float) -> Dict[str, Any]:
        """Track GPU usage."""
        timestamp = datetime.now(timezone.utc)

        gpu_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'gpu_id': gpu_id,
            'utilization_percent': utilization_percent,
            'memory_used_mb': memory_used_mb,
            'duration_seconds': duration
        }

        self.gpu_usage_logs.append(gpu_data)
        self.user_hardware_stats[user_id]['gpu_time'] += duration

        if self.es_manager:
            self.es_manager.push_data(gpu_data, 'gpu_usage')

        return gpu_data

    def track_peripheral_usage(self, user_id: str, peripheral_type: str,
                              peripheral_name: str, usage_duration: float = None) -> Dict[str, Any]:
        """Track peripheral device usage."""
        timestamp = datetime.now(timezone.utc)

        peripheral_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'peripheral_type': peripheral_type,  # graphics_tablet, webcam, microphone, etc.
            'peripheral_name': peripheral_name,
            'usage_duration': usage_duration
        }

        self.peripheral_usage[user_id].append(peripheral_data)
        self.user_hardware_stats[user_id]['peripherals_used'].add(peripheral_type)

        if self.es_manager:
            self.es_manager.push_data(peripheral_data, 'peripheral_usage')

        return peripheral_data

    def detect_monitors(self, user_id: str) -> Dict[str, Any]:
        """Detect number of monitors in use."""
        # Platform-specific monitor detection would go here
        # This is a placeholder implementation

        monitor_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'monitor_count': 1,  # Placeholder
            'primary_resolution': '1920x1080'  # Placeholder
        }

        if self.es_manager:
            self.es_manager.push_data(monitor_data, 'monitor_setup')

        return monitor_data

    def get_user_hardware_summary(self, user_id: str) -> Dict[str, Any]:
        """Get hardware utilization summary for user."""
        stats = self.user_hardware_stats.get(user_id, {})

        return {
            'user_id': user_id,
            'total_gpu_time_hours': stats.get('gpu_time', 0) / 3600,
            'peripherals_used': list(stats.get('peripherals_used', set())),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['HardwareUtilizationMonitor']
