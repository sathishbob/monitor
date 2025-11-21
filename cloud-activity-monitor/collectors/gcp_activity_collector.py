"""
GCP Cloud Audit Logs Activity Collector

Collects user activity data from GCP Cloud Audit Logs across all projects.
Tracks admin activities, data access, and system events.
"""

import logging
from google.cloud import logging as cloud_logging
from google.oauth2 import service_account
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GCPActivityCollector:
    """Collects user activity from GCP Cloud Audit Logs."""

    # Event categories for classification
    ACTION_CATEGORIES = {
        'Create': ['create', 'insert', 'add', 'run', 'deploy', 'enable'],
        'Read': ['get', 'list', 'describe', 'read', 'export', 'download'],
        'Update': ['update', 'patch', 'modify', 'change', 'set', 'attach'],
        'Delete': ['delete', 'remove', 'disable', 'stop', 'terminate']
    }

    # Service name mappings
    SERVICE_MAPPINGS = {
        'compute.googleapis.com': 'ComputeEngine',
        'storage.googleapis.com': 'CloudStorage',
        'container.googleapis.com': 'GKE',
        'sqladmin.googleapis.com': 'CloudSQL',
        'bigquery.googleapis.com': 'BigQuery',
        'iam.googleapis.com': 'IAM',
        'cloudresourcemanager.googleapis.com': 'ResourceManager',
        'logging.googleapis.com': 'Logging',
        'monitoring.googleapis.com': 'Monitoring'
    }

    def __init__(self, project_config: Dict[str, Any]):
        """Initialize GCP activity collector."""
        self.project_name = project_config['name']
        self.project_id = project_config['project_id']
        self.credentials_file = project_config.get('credentials_file')

        # Initialize credentials
        if self.credentials_file:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file
            )
        else:
            self.credentials = None

        logger.info(f"Initialized GCP activity collector for: {self.project_name}")

    def collect_activities(self, lookback_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Collect Cloud Audit Log entries from GCP.

        Args:
            lookback_minutes: How many minutes back to look for events

        Returns:
            List of processed activity events
        """
        all_activities = []

        try:
            logger.info(f"Collecting Cloud Audit Logs from {self.project_name}")

            # Initialize logging client
            if self.credentials:
                client = cloud_logging.Client(
                    project=self.project_id,
                    credentials=self.credentials
                )
            else:
                client = cloud_logging.Client(project=self.project_id)

            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=lookback_minutes)

            # Build filter for audit logs
            # Audit logs are in these log types:
            # - cloudaudit.googleapis.com/activity (Admin Activity)
            # - cloudaudit.googleapis.com/data_access (Data Access)
            # - cloudaudit.googleapis.com/system_event (System Events)
            filter_str = f'''
                logName=~"projects/{self.project_id}/logs/cloudaudit.googleapis.com%2F"
                AND timestamp >= "{start_time.isoformat()}"
                AND timestamp <= "{end_time.isoformat()}"
            '''

            # List log entries
            entries = client.list_entries(filter_=filter_str, page_size=1000)

            for entry in entries:
                processed_event = self._process_log_entry(entry)
                if processed_event:
                    all_activities.append(processed_event)

            logger.info(f"Collected {len(all_activities)} audit log entries from {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting from {self.project_name}: {e}")

        return all_activities

    def _process_log_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Process a Cloud Audit Log entry into standardized format."""
        try:
            # Get the protoPayload which contains audit info
            payload = entry.payload

            if not hasattr(payload, 'get'):
                return None

            # Extract key fields
            service_name = payload.get('serviceName', 'unknown')
            method_name = payload.get('methodName', 'unknown')
            resource_name = payload.get('resourceName', 'unknown')

            # Extract authentication info
            auth_info = payload.get('authenticationInfo', {})
            principal_email = auth_info.get('principalEmail', 'unknown')

            # Extract request metadata
            request_metadata = payload.get('requestMetadata', {})
            caller_ip = request_metadata.get('callerIp', 'unknown')
            caller_supplied_user_agent = request_metadata.get('callerSuppliedUserAgent', 'unknown')

            # Extract status
            status = payload.get('status', {})
            error_code = status.get('code', 0)
            error_message = status.get('message', None)
            success = error_code == 0

            # Extract resource info
            resource_location = payload.get('resourceLocation', {})

            # Determine service and action
            service = self._map_service_name(service_name)
            action_category = self._categorize_action(method_name)

            # Extract method parts for event name
            event_name = method_name.split('.')[-1] if '.' in method_name else method_name

            # Build standardized event
            processed = {
                'timestamp': entry.timestamp.isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': self._extract_region(resource_location, resource_name),
                'user_identity': {
                    'type': 'User' if '@' in principal_email else 'ServiceAccount',
                    'user_name': principal_email,
                    'user_id': principal_email,
                    'principal_email': principal_email
                },
                'event_name': event_name,
                'method_name': method_name,
                'event_source': service_name,
                'service': service,
                'action_category': action_category,
                'resources_affected': [{
                    'type': 'resource',
                    'id': resource_name,
                    'location': resource_location
                }],
                'source_ip': caller_ip,
                'user_agent': caller_supplied_user_agent,
                'success': success,
                'error_code': error_code if not success else None,
                'error_message': error_message,
                'severity': entry.severity,
                'log_name': entry.log_name
            }

            return processed

        except Exception as e:
            logger.error(f"Error processing log entry: {e}")
            return None

    def _map_service_name(self, service_name: str) -> str:
        """Map GCP service name to friendly name."""
        return self.SERVICE_MAPPINGS.get(service_name, service_name.split('.')[0].upper())

    def _extract_region(self, resource_location: Dict[str, Any], resource_name: str) -> str:
        """Extract region from resource location or resource name."""
        # Try from resource location
        if resource_location:
            region = resource_location.get('currentLocations', [])
            if region:
                return region[0] if isinstance(region, list) else str(region)

        # Try to parse from resource name
        # Format: projects/PROJECT/zones/ZONE/... or projects/PROJECT/regions/REGION/...
        if '/zones/' in resource_name:
            parts = resource_name.split('/zones/')
            if len(parts) > 1:
                zone = parts[1].split('/')[0]
                return zone
        elif '/regions/' in resource_name:
            parts = resource_name.split('/regions/')
            if len(parts) > 1:
                region = parts[1].split('/')[0]
                return region

        return 'global'

    def _categorize_action(self, method_name: str) -> str:
        """Categorize action as Create, Read, Update, or Delete."""
        method_lower = method_name.lower()

        for category, keywords in self.ACTION_CATEGORIES.items():
            for keyword in keywords:
                if keyword in method_lower:
                    return category
        return 'Other'

    def get_user_summary(self, activities: List[Dict[str, Any]],
                        time_period: str = '1h') -> List[Dict[str, Any]]:
        """
        Generate per-user summary metrics from activities.

        Args:
            activities: List of activity events
            time_period: Time period for aggregation

        Returns:
            List of user summary metrics
        """
        user_metrics = {}

        for activity in activities:
            user_name = activity['user_identity']['user_name']

            if user_name not in user_metrics:
                user_metrics[user_name] = {
                    'user_name': user_name,
                    'user_type': activity['user_identity']['type'],
                    'total_actions': 0,
                    'successful_actions': 0,
                    'failed_actions': 0,
                    'services_used': set(),
                    'action_types': {},
                    'regions': set(),
                    'source_ips': set(),
                    'resources_accessed': set(),
                    'events': []
                }

            metrics = user_metrics[user_name]
            metrics['total_actions'] += 1

            if activity['success']:
                metrics['successful_actions'] += 1
            else:
                metrics['failed_actions'] += 1

            metrics['services_used'].add(activity['service'])
            metrics['regions'].add(activity['region'])
            metrics['source_ips'].add(activity['source_ip'])

            # Count action types
            action_cat = activity['action_category']
            metrics['action_types'][action_cat] = metrics['action_types'].get(action_cat, 0) + 1

            # Track resources
            for resource in activity['resources_affected']:
                metrics['resources_accessed'].add(resource['id'])

            # Keep event for timeline
            metrics['events'].append({
                'timestamp': activity['timestamp'],
                'event_name': activity['event_name'],
                'service': activity['service'],
                'success': activity['success']
            })

        # Convert sets to lists and counts
        summaries = []
        for user_name, metrics in user_metrics.items():
            summary = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'user_name': user_name,
                'user_type': metrics['user_type'],
                'time_period': time_period,
                'metrics': {
                    'total_actions': metrics['total_actions'],
                    'successful_actions': metrics['successful_actions'],
                    'failed_actions': metrics['failed_actions'],
                    'services_used': list(metrics['services_used']),
                    'service_count': len(metrics['services_used']),
                    'action_types': metrics['action_types'],
                    'regions': list(metrics['regions']),
                    'source_ips': list(metrics['source_ips']),
                    'unique_resources_accessed': len(metrics['resources_accessed']),
                    'error_rate': metrics['failed_actions'] / metrics['total_actions'] if metrics['total_actions'] > 0 else 0
                },
                'recent_events': metrics['events'][-10:]
            }
            summaries.append(summary)

        return summaries


__all__ = ['GCPActivityCollector']
