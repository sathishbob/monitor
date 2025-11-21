"""
Azure Activity Log Collector

Collects user activity data from Azure Activity Logs across all subscriptions.
Tracks administrative operations, resource modifications, and authentication events.
"""

import logging
from azure.identity import ClientSecretCredential
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.resource import SubscriptionClient
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AzureActivityCollector:
    """Collects user activity from Azure Activity Logs."""

    # Event categories for classification
    ACTION_CATEGORIES = {
        'Create': ['write', 'register', 'create', 'deploy'],
        'Read': ['read', 'get', 'list'],
        'Update': ['update', 'patch', 'modify'],
        'Delete': ['delete', 'remove', 'unregister']
    }

    def __init__(self, subscription_config: Dict[str, Any]):
        """Initialize Azure activity collector."""
        self.subscription_name = subscription_config['name']
        self.subscription_id = subscription_config['subscription_id']
        self.tenant_id = subscription_config['tenant_id']
        self.client_id = subscription_config['client_id']
        self.client_secret = subscription_config['client_secret']

        # Create credential
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        # Initialize Monitor client
        self.monitor_client = MonitorManagementClient(
            credential=self.credential,
            subscription_id=self.subscription_id
        )

        logger.info(f"Initialized Azure activity collector for: {self.subscription_name}")

    def collect_activities(self, lookback_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Collect Activity Log events from Azure.

        Args:
            lookback_minutes: How many minutes back to look for events

        Returns:
            List of processed activity events
        """
        all_activities = []

        try:
            logger.info(f"Collecting Activity Logs from {self.subscription_name}")

            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=lookback_minutes)

            # Format filter string
            # Azure Activity Logs filter format: eventTimestamp ge 'YYYY-MM-DD' and eventTimestamp le 'YYYY-MM-DD'
            filter_str = (
                f"eventTimestamp ge '{start_time.isoformat()}' and "
                f"eventTimestamp le '{end_time.isoformat()}'"
            )

            # Get activity logs
            activity_logs = self.monitor_client.activity_logs.list(
                filter=filter_str
            )

            for log in activity_logs:
                processed_event = self._process_activity_log(log)
                if processed_event:
                    all_activities.append(processed_event)

            logger.info(f"Collected {len(all_activities)} activity logs from {self.subscription_name}")

        except Exception as e:
            logger.error(f"Error collecting from {self.subscription_name}: {e}")

        return all_activities

    def _process_activity_log(self, log) -> Optional[Dict[str, Any]]:
        """Process an Activity Log entry into standardized format."""
        try:
            # Extract timestamp
            event_timestamp = log.event_timestamp

            # Extract caller (user identity)
            caller = log.caller or 'System'

            # Extract operation details
            operation_name = log.operation_name.localized_value if hasattr(log.operation_name, 'localized_value') else str(log.operation_name)
            operation_id = log.operation_id or 'unknown'

            # Extract category (Administrative, ServiceHealth, Alert, etc.)
            category = log.category.localized_value if hasattr(log.category, 'localized_value') else str(log.category)

            # Extract resource information
            resource_id = log.resource_id or 'unknown'
            resource_group = log.resource_group_name or 'unknown'
            resource_provider = log.resource_provider_name.localized_value if hasattr(log.resource_provider_name, 'localized_value') else str(log.resource_provider_name)
            resource_type = log.resource_type.localized_value if hasattr(log.resource_type, 'localized_value') else str(log.resource_type)

            # Extract status and sub-status
            status = log.status.localized_value if hasattr(log.status, 'localized_value') else str(log.status)
            sub_status = log.sub_status.localized_value if hasattr(log.sub_status, 'localized_value') else ''

            # Determine success
            success = status.lower() in ['succeeded', 'success', 'accepted']

            # Extract HTTP request info
            http_request = log.http_request
            client_ip = 'unknown'
            user_agent = 'unknown'
            if http_request:
                client_ip = getattr(http_request, 'client_ip_address', 'unknown') or 'unknown'
                # User agent might not be available in all cases

            # Extract claims (includes detailed auth info)
            claims = log.claims or {}

            # Determine user type
            user_type = 'User'
            if 'http://schemas.microsoft.com/identity/claims/objectidentifier' in claims:
                user_type = 'User'
            elif 'appid' in claims:
                user_type = 'ServicePrincipal'

            # Extract region
            region = self._extract_region(resource_id)

            # Determine service from resource provider
            service = self._map_service_name(resource_provider)

            # Categorize action
            action_category = self._categorize_action(operation_name)

            # Extract event name
            event_name = operation_name.split('/')[-1] if '/' in operation_name else operation_name

            # Build standardized event
            processed = {
                'timestamp': event_timestamp.isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': region,
                'user_identity': {
                    'type': user_type,
                    'user_name': caller,
                    'user_id': claims.get('http://schemas.microsoft.com/identity/claims/objectidentifier', caller),
                    'caller': caller,
                    'claims': claims
                },
                'event_name': event_name,
                'operation_name': operation_name,
                'operation_id': operation_id,
                'event_source': resource_provider,
                'service': service,
                'category': category,
                'action_category': action_category,
                'resources_affected': [{
                    'type': resource_type,
                    'id': resource_id,
                    'resource_group': resource_group,
                    'provider': resource_provider
                }],
                'source_ip': client_ip,
                'user_agent': user_agent,
                'success': success,
                'status': status,
                'sub_status': sub_status,
                'error_code': None if success else sub_status,
                'error_message': None if success else status,
                'level': str(log.level) if log.level else 'Informational'
            }

            return processed

        except Exception as e:
            logger.error(f"Error processing activity log: {e}")
            return None

    def _extract_region(self, resource_id: str) -> str:
        """Extract region from resource ID."""
        # Azure resource ID format:
        # /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/{provider}/{type}/{name}
        # Some resources include /locations/{location}/
        if '/locations/' in resource_id:
            parts = resource_id.split('/locations/')
            if len(parts) > 1:
                location = parts[1].split('/')[0]
                return location
        return 'global'

    def _map_service_name(self, resource_provider: str) -> str:
        """Map Azure resource provider to friendly service name."""
        mappings = {
            'Microsoft.Compute': 'VirtualMachines',
            'Microsoft.Storage': 'Storage',
            'Microsoft.Sql': 'SQLDatabase',
            'Microsoft.Network': 'Networking',
            'Microsoft.Web': 'AppService',
            'Microsoft.ContainerService': 'AKS',
            'Microsoft.KeyVault': 'KeyVault',
            'Microsoft.DocumentDB': 'CosmosDB',
            'Microsoft.Cache': 'RedisCache',
            'Microsoft.Authorization': 'Authorization',
            'Microsoft.Resources': 'ResourceManagement',
            'Microsoft.Insights': 'Monitoring'
        }
        return mappings.get(resource_provider, resource_provider.replace('Microsoft.', ''))

    def _categorize_action(self, operation_name: str) -> str:
        """Categorize action as Create, Read, Update, or Delete."""
        operation_lower = operation_name.lower()

        for category, keywords in self.ACTION_CATEGORIES.items():
            for keyword in keywords:
                if keyword in operation_lower:
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
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
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


__all__ = ['AzureActivityCollector']
