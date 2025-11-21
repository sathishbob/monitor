"""
AWS CloudTrail Activity Collector

Collects user activity data from AWS CloudTrail across all accounts and regions.
Tracks who did what, when, and from where.
"""

import logging
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AWSActivityCollector:
    """Collects user activity from AWS CloudTrail."""

    # Event categories for classification
    ACTION_CATEGORIES = {
        'Create': ['Create', 'Run', 'Launch', 'Start', 'Put', 'Upload', 'Register', 'Allocate'],
        'Read': ['Describe', 'Get', 'List', 'Lookup', 'Head', 'Download'],
        'Update': ['Update', 'Modify', 'Change', 'Edit', 'Set', 'Attach', 'Detach'],
        'Delete': ['Delete', 'Terminate', 'Stop', 'Remove', 'Deregister', 'Release']
    }

    def __init__(self, account_config: Dict[str, Any]):
        """Initialize AWS activity collector."""
        self.account_name = account_config['name']
        self.access_key = account_config['access_key_id']
        self.secret_key = account_config['secret_access_key']
        self.regions = account_config.get('regions', ['us-east-1'])

        logger.info(f"Initialized AWS activity collector for: {self.account_name}")

    def get_session(self, region: str):
        """Create boto3 session for specified region."""
        return boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=region
        )

    def collect_activities(self, lookback_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Collect CloudTrail events from all regions.

        Args:
            lookback_minutes: How many minutes back to look for events

        Returns:
            List of processed activity events
        """
        all_activities = []
        start_time = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
        end_time = datetime.now(timezone.utc)

        for region in self.regions:
            try:
                logger.info(f"Collecting CloudTrail events from {self.account_name} - {region}")
                activities = self._collect_from_region(region, start_time, end_time)
                all_activities.extend(activities)
                logger.info(f"Collected {len(activities)} events from {region}")
            except Exception as e:
                logger.error(f"Error collecting from {region}: {e}")

        logger.info(f"Total activities collected from {self.account_name}: {len(all_activities)}")
        return all_activities

    def _collect_from_region(self, region: str, start_time: datetime,
                            end_time: datetime) -> List[Dict[str, Any]]:
        """Collect CloudTrail events from a specific region."""
        session = self.get_session(region)
        cloudtrail = session.client('cloudtrail')

        activities = []

        try:
            # Use LookupEvents API to get recent events
            paginator = cloudtrail.get_paginator('lookup_events')

            for page in paginator.paginate(
                LookupAttributes=[],
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=50
            ):
                for event in page.get('Events', []):
                    processed_event = self._process_event(event, region)
                    if processed_event:
                        activities.append(processed_event)

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                logger.warning(f"No CloudTrail access in {region}")
            else:
                logger.error(f"CloudTrail error in {region}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error collecting from {region}: {e}")

        return activities

    def _process_event(self, event: Dict[str, Any], region: str) -> Optional[Dict[str, Any]]:
        """Process a CloudTrail event into standardized format."""
        try:
            # Parse CloudTrail event
            import json

            event_time = event.get('EventTime')
            event_name = event.get('EventName', 'Unknown')
            event_source = event.get('EventSource', 'unknown.amazonaws.com')
            username = event.get('Username', 'Unknown')

            # Parse CloudTrailEvent JSON string if present
            cloud_trail_event = {}
            if 'CloudTrailEvent' in event:
                try:
                    cloud_trail_event = json.loads(event['CloudTrailEvent'])
                except:
                    pass

            # Extract user identity
            user_identity = self._extract_user_identity(event, cloud_trail_event)

            # Extract source IP and user agent
            source_ip = cloud_trail_event.get('sourceIPAddress', 'Unknown')
            user_agent = cloud_trail_event.get('userAgent', 'Unknown')

            # Determine if event was successful
            error_code = cloud_trail_event.get('errorCode')
            error_message = cloud_trail_event.get('errorMessage')
            success = error_code is None

            # Extract resources affected
            resources = self._extract_resources(event, cloud_trail_event)

            # Determine service from event source
            service = event_source.split('.')[0].upper() if '.' in event_source else event_source.upper()

            # Categorize action
            action_category = self._categorize_action(event_name)

            # Build standardized event
            processed = {
                'timestamp': event_time.isoformat() if isinstance(event_time, datetime) else str(event_time),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'user_identity': user_identity,
                'event_name': event_name,
                'event_source': event_source,
                'service': service,
                'action_category': action_category,
                'resources_affected': resources,
                'source_ip': source_ip,
                'user_agent': user_agent,
                'success': success,
                'error_code': error_code,
                'error_message': error_message,
                'request_parameters': cloud_trail_event.get('requestParameters', {}),
                'read_only': event.get('ReadOnly', None)
            }

            return processed

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return None

    def _extract_user_identity(self, event: Dict[str, Any],
                               cloud_trail_event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user identity information from event."""
        user_identity = {}

        # Try to get from CloudTrailEvent first
        if 'userIdentity' in cloud_trail_event:
            ui = cloud_trail_event['userIdentity']
            user_identity = {
                'type': ui.get('type', 'Unknown'),
                'user_name': ui.get('userName', ui.get('principalId', 'Unknown')),
                'user_id': ui.get('principalId', 'Unknown'),
                'arn': ui.get('arn', 'Unknown'),
                'account_id': ui.get('accountId', 'Unknown'),
                'session_context': ui.get('sessionContext', {})
            }
        else:
            # Fallback to Username from event
            username = event.get('Username', 'Unknown')
            user_identity = {
                'type': 'Unknown',
                'user_name': username,
                'user_id': username,
                'arn': 'Unknown',
                'account_id': 'Unknown',
                'session_context': {}
            }

        return user_identity

    def _extract_resources(self, event: Dict[str, Any],
                           cloud_trail_event: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract affected resources from event."""
        resources = []

        # Get resources from CloudTrail event
        if 'resources' in cloud_trail_event:
            for resource in cloud_trail_event['resources']:
                resources.append({
                    'type': resource.get('type', 'Unknown'),
                    'id': resource.get('ARN', 'Unknown'),
                    'account_id': resource.get('accountId', 'Unknown')
                })

        # Also check Resources field in event
        if 'Resources' in event:
            for resource in event['Resources']:
                resources.append({
                    'type': resource.get('ResourceType', 'Unknown'),
                    'id': resource.get('ResourceName', 'Unknown'),
                    'account_id': 'Unknown'
                })

        return resources

    def _categorize_action(self, event_name: str) -> str:
        """Categorize action as Create, Read, Update, or Delete."""
        for category, prefixes in self.ACTION_CATEGORIES.items():
            for prefix in prefixes:
                if event_name.startswith(prefix):
                    return category
        return 'Other'

    def get_user_summary(self, activities: List[Dict[str, Any]],
                        time_period: str = '1h') -> List[Dict[str, Any]]:
        """
        Generate per-user summary metrics from activities.

        Args:
            activities: List of activity events
            time_period: Time period for aggregation (e.g., '1h', '1d')

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

        # Convert sets to lists and counts for JSON serialization
        summaries = []
        for user_name, metrics in user_metrics.items():
            summary = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
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
                'recent_events': metrics['events'][-10:]  # Last 10 events
            }
            summaries.append(summary)

        return summaries


__all__ = ['AWSActivityCollector']
