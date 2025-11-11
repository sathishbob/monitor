"""
Resource Access Patterns Monitor

Tracks database connections, API usage, cloud services, and external integrations
to understand advanced skill usage and optimize resource allocation.
"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ResourceAccessMonitor:
    """Monitor resource access patterns and external service usage."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.db_connections: deque = deque(maxlen=5000)
        self.api_calls: deque = deque(maxlen=5000)
        self.cloud_operations: List[Dict[str, Any]] = []
        self.user_resource_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'db_connections': 0,
            'api_calls': 0,
            'cloud_operations': 0,
            'external_services': set()
        })

        logger.info("Resource access monitor initialized")

    def track_database_connection(self, user_id: str, db_type: str,
                                  db_name: str, operation: str,
                                  duration: float = None, success: bool = True) -> Dict[str, Any]:
        """Track database connection and operation."""
        timestamp = datetime.now(timezone.utc)

        db_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'database_type': db_type,  # postgresql, mysql, mongodb, etc.
            'database_name': db_name,
            'operation': operation,  # connect, query, insert, update, delete
            'duration_seconds': duration,
            'success': success
        }

        self.db_connections.append(db_data)
        self.user_resource_usage[user_id]['db_connections'] += 1

        if self.es_manager:
            self.es_manager.push_data(db_data, 'database_access')

        return db_data

    def track_api_call(self, user_id: str, api_endpoint: str,
                      method: str, status_code: int,
                      response_time: float = None) -> Dict[str, Any]:
        """Track API endpoint calls."""
        timestamp = datetime.now(timezone.utc)

        api_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'api_endpoint': api_endpoint,
            'http_method': method,
            'status_code': status_code,
            'response_time_ms': response_time,
            'success': 200 <= status_code < 300
        }

        self.api_calls.append(api_data)
        self.user_resource_usage[user_id]['api_calls'] += 1

        if self.es_manager:
            self.es_manager.push_data(api_data, 'api_call')

        return api_data

    def track_cloud_operation(self, user_id: str, provider: str,
                             service: str, operation: str,
                             resource_id: str = None, success: bool = True) -> Dict[str, Any]:
        """Track cloud service operations."""
        timestamp = datetime.now(timezone.utc)

        cloud_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'cloud_provider': provider,  # aws, azure, gcp
            'service': service,  # ec2, s3, lambda, etc.
            'operation': operation,
            'resource_id': resource_id,
            'success': success
        }

        self.cloud_operations.append(cloud_data)
        self.user_resource_usage[user_id]['cloud_operations'] += 1
        self.user_resource_usage[user_id]['external_services'].add(f"{provider}:{service}")

        if self.es_manager:
            self.es_manager.push_data(cloud_data, 'cloud_operation')

        return cloud_data

    def track_remote_connection(self, user_id: str, connection_type: str,
                               target_host: str, duration: float = None) -> Dict[str, Any]:
        """Track remote server connections (SSH, RDP, etc.)."""
        timestamp = datetime.now(timezone.utc)

        conn_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'connection_type': connection_type,  # ssh, rdp, vnc
            'target_host': target_host,
            'duration_seconds': duration
        }

        if self.es_manager:
            self.es_manager.push_data(conn_data, 'remote_connection')

        return conn_data

    def get_user_resource_summary(self, user_id: str) -> Dict[str, Any]:
        """Get resource access summary for user."""
        usage = self.user_resource_usage.get(user_id, {})

        return {
            'user_id': user_id,
            'total_db_connections': usage.get('db_connections', 0),
            'total_api_calls': usage.get('api_calls', 0),
            'total_cloud_operations': usage.get('cloud_operations', 0),
            'unique_external_services': len(usage.get('external_services', set())),
            'services_used': list(usage.get('external_services', set())),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['ResourceAccessMonitor']
