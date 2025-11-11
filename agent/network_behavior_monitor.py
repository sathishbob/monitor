"""
Network Behavior Details Monitor

Tracks network patterns, repository access, bandwidth usage,
and download/upload patterns for proper usage monitoring.
"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class NetworkBehaviorMonitor:
    """Monitor network behavior and data transfer patterns."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.network_transfers: deque = deque(maxlen=5000)
        self.repository_access: List[Dict[str, Any]] = []
        self.bandwidth_usage: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'upload_bytes': 0,
            'download_bytes': 0
        })

        logger.info("Network behavior monitor initialized")

    def track_network_transfer(self, user_id: str, direction: str,
                               bytes_transferred: int, protocol: str = None,
                               destination: str = None, file_type: str = None) -> Dict[str, Any]:
        """Track network data transfer."""
        timestamp = datetime.now(timezone.utc)

        transfer_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'direction': direction,  # upload, download
            'bytes': bytes_transferred,
            'megabytes': bytes_transferred / (1024 * 1024),
            'protocol': protocol,
            'destination': destination,
            'file_type': file_type
        }

        self.network_transfers.append(transfer_data)

        if direction == 'upload':
            self.bandwidth_usage[user_id]['upload_bytes'] += bytes_transferred
        elif direction == 'download':
            self.bandwidth_usage[user_id]['download_bytes'] += bytes_transferred

        if self.es_manager:
            self.es_manager.push_data(transfer_data, 'network_transfer')

        return transfer_data

    def track_repository_access(self, user_id: str, repo_url: str,
                               operation: str, success: bool = True) -> Dict[str, Any]:
        """Track access to code repositories (GitHub, GitLab, etc.)."""
        timestamp = datetime.now(timezone.utc)

        parsed = urlparse(repo_url)
        platform = parsed.netloc.replace('www.', '')

        repo_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'repository_url': repo_url,
            'platform': platform,
            'operation': operation,  # clone, pull, push, fork
            'success': success
        }

        self.repository_access.append(repo_data)

        if self.es_manager:
            self.es_manager.push_data(repo_data, 'repository_access')

        return repo_data

    def track_vpn_usage(self, user_id: str, vpn_connected: bool,
                       vpn_server: str = None) -> Dict[str, Any]:
        """Track VPN usage."""
        timestamp = datetime.now(timezone.utc)

        vpn_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'connected': vpn_connected,
            'server': vpn_server
        }

        if self.es_manager:
            self.es_manager.push_data(vpn_data, 'vpn_usage')

        return vpn_data

    def detect_bandwidth_intensive_activity(self, user_id: str,
                                           threshold_mbps: float = 10.0) -> bool:
        """Detect if user is doing bandwidth-intensive activities."""
        recent_usage = sum(
            t['bytes'] for t in self.network_transfers
            if t.get('user_id') == user_id
        )

        # Check if exceeds threshold
        return (recent_usage / (1024 * 1024)) > threshold_mbps

    def get_user_network_summary(self, user_id: str) -> Dict[str, Any]:
        """Get network behavior summary for user."""
        usage = self.bandwidth_usage.get(user_id, {})

        user_repos = [r for r in self.repository_access if r.get('user_id') == user_id]

        return {
            'user_id': user_id,
            'total_upload_mb': usage.get('upload_bytes', 0) / (1024 * 1024),
            'total_download_mb': usage.get('download_bytes', 0) / (1024 * 1024),
            'repository_operations': len(user_repos),
            'unique_repositories': len(set(r['repository_url'] for r in user_repos)),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['NetworkBehaviorMonitor']
