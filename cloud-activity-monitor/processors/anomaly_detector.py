"""
Anomaly Detector for Cloud User Activities

Detects unusual patterns in user behavior:
- Unusual access times
- High error rates
- New IP addresses
- Mass operations
- Service access changes
- API rate spikes
"""

import logging
from datetime import datetime, timezone, time
from typing import Dict, List, Any, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalous user activity patterns."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize anomaly detector with configuration."""
        self.config = config.get('anomaly_detection', {})

        # Anomaly thresholds
        self.error_rate_threshold = self.config.get('error_rate_threshold', 0.20)  # 20% errors
        self.action_spike_multiplier = self.config.get('action_spike_multiplier', 3.0)  # 3x normal
        self.unusual_hour_start = self.config.get('unusual_hour_start', 22)  # 10 PM
        self.unusual_hour_end = self.config.get('unusual_hour_end', 6)  # 6 AM
        self.mass_delete_threshold = self.config.get('mass_delete_threshold', 10)  # 10+ deletes

        # Historical data for baseline (in-memory for now)
        self.user_baselines = {}

        logger.info("Anomaly detector initialized")

    def detect_anomalies(self, activities: List[Dict[str, Any]],
                        user_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in user activities.

        Args:
            activities: Raw activity events
            user_summaries: Aggregated user metrics

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Detect anomalies per user
        for summary in user_summaries:
            user_name = summary['user_name']
            metrics = summary['metrics']

            # Check for high error rate
            error_anomaly = self._detect_high_error_rate(summary)
            if error_anomaly:
                anomalies.append(error_anomaly)

            # Check for unusual access times
            time_anomaly = self._detect_unusual_access_time(summary, activities)
            if time_anomaly:
                anomalies.append(time_anomaly)

            # Check for new IP addresses
            ip_anomaly = self._detect_new_ip(summary, user_name)
            if ip_anomaly:
                anomalies.append(ip_anomaly)

            # Check for mass delete operations
            delete_anomaly = self._detect_mass_delete(summary)
            if delete_anomaly:
                anomalies.append(delete_anomaly)

            # Check for activity spike
            spike_anomaly = self._detect_activity_spike(summary, user_name)
            if spike_anomaly:
                anomalies.append(spike_anomaly)

            # Check for new service access
            service_anomaly = self._detect_new_service(summary, user_name)
            if service_anomaly:
                anomalies.append(service_anomaly)

        # Update baselines
        self._update_baselines(user_summaries)

        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies

    def _detect_high_error_rate(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Detect unusually high error rate."""
        metrics = summary['metrics']
        error_rate = metrics.get('error_rate', 0)

        if error_rate > self.error_rate_threshold:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'anomaly_type': 'high_error_rate',
                'severity': 'warning' if error_rate < 0.5 else 'critical',
                'cloud_provider': summary['cloud_provider'],
                'account': summary['account'],
                'user_name': summary['user_name'],
                'description': f"User has {error_rate*100:.1f}% error rate ({metrics['failed_actions']}/{metrics['total_actions']} failed)",
                'metrics': {
                    'error_rate': error_rate,
                    'failed_actions': metrics['failed_actions'],
                    'total_actions': metrics['total_actions']
                }
            }
        return None

    def _detect_unusual_access_time(self, summary: Dict[str, Any],
                                    activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect activity during unusual hours."""
        user_name = summary['user_name']
        cloud_provider = summary['cloud_provider']
        account = summary['account']

        # Filter activities for this user
        user_activities = [
            a for a in activities
            if a['user_identity']['user_name'] == user_name
            and a['cloud_provider'] == cloud_provider
            and a['account'] == account
        ]

        unusual_hour_count = 0
        for activity in user_activities:
            timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour

            # Check if in unusual hour range
            if self.unusual_hour_start > self.unusual_hour_end:
                # Range crosses midnight (e.g., 22-6)
                if hour >= self.unusual_hour_start or hour < self.unusual_hour_end:
                    unusual_hour_count += 1
            else:
                # Normal range (e.g., 2-6)
                if self.unusual_hour_start <= hour < self.unusual_hour_end:
                    unusual_hour_count += 1

        if unusual_hour_count > 0:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'anomaly_type': 'unusual_access_time',
                'severity': 'info',
                'cloud_provider': cloud_provider,
                'account': account,
                'user_name': user_name,
                'description': f"User performed {unusual_hour_count} actions during unusual hours ({self.unusual_hour_start}:00-{self.unusual_hour_end}:00)",
                'metrics': {
                    'unusual_hour_actions': unusual_hour_count,
                    'total_actions': len(user_activities)
                }
            }
        return None

    def _detect_new_ip(self, summary: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        """Detect access from new IP addresses."""
        current_ips = set(summary['metrics'].get('source_ips', []))

        # Get historical IPs for this user
        baseline = self.user_baselines.get(user_name, {})
        historical_ips = baseline.get('known_ips', set())

        # Find new IPs
        new_ips = current_ips - historical_ips

        if new_ips and historical_ips:  # Only alert if we have baseline
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'anomaly_type': 'new_ip_address',
                'severity': 'warning',
                'cloud_provider': summary['cloud_provider'],
                'account': summary['account'],
                'user_name': user_name,
                'description': f"User accessed from {len(new_ips)} new IP address(es): {', '.join(new_ips)}",
                'metrics': {
                    'new_ips': list(new_ips),
                    'known_ips': list(historical_ips)
                }
            }
        return None

    def _detect_mass_delete(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Detect mass delete operations."""
        metrics = summary['metrics']
        action_types = metrics.get('action_types', {})
        delete_count = action_types.get('Delete', 0)

        if delete_count >= self.mass_delete_threshold:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'anomaly_type': 'mass_delete',
                'severity': 'critical',
                'cloud_provider': summary['cloud_provider'],
                'account': summary['account'],
                'user_name': summary['user_name'],
                'description': f"User performed {delete_count} delete operations",
                'metrics': {
                    'delete_count': delete_count,
                    'total_actions': metrics['total_actions']
                }
            }
        return None

    def _detect_activity_spike(self, summary: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        """Detect sudden spike in activity."""
        current_actions = summary['metrics']['total_actions']

        # Get historical average for this user
        baseline = self.user_baselines.get(user_name, {})
        avg_actions = baseline.get('avg_actions', 0)

        # Only alert if we have baseline and current is significantly higher
        if avg_actions > 0 and current_actions > avg_actions * self.action_spike_multiplier:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'anomaly_type': 'activity_spike',
                'severity': 'warning',
                'cloud_provider': summary['cloud_provider'],
                'account': summary['account'],
                'user_name': user_name,
                'description': f"User activity is {current_actions/avg_actions:.1f}x higher than normal ({current_actions} vs avg {avg_actions:.0f})",
                'metrics': {
                    'current_actions': current_actions,
                    'average_actions': avg_actions,
                    'spike_multiplier': current_actions / avg_actions
                }
            }
        return None

    def _detect_new_service(self, summary: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        """Detect access to new services."""
        current_services = set(summary['metrics'].get('services_used', []))

        # Get historical services for this user
        baseline = self.user_baselines.get(user_name, {})
        historical_services = baseline.get('known_services', set())

        # Find new services
        new_services = current_services - historical_services

        if new_services and historical_services:  # Only alert if we have baseline
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'anomaly_type': 'new_service_access',
                'severity': 'info',
                'cloud_provider': summary['cloud_provider'],
                'account': summary['account'],
                'user_name': user_name,
                'description': f"User accessed {len(new_services)} new service(s): {', '.join(new_services)}",
                'metrics': {
                    'new_services': list(new_services),
                    'known_services': list(historical_services)
                }
            }
        return None

    def _update_baselines(self, user_summaries: List[Dict[str, Any]]):
        """Update user activity baselines."""
        for summary in user_summaries:
            user_name = summary['user_name']
            metrics = summary['metrics']

            if user_name not in self.user_baselines:
                self.user_baselines[user_name] = {
                    'avg_actions': metrics['total_actions'],
                    'known_ips': set(metrics.get('source_ips', [])),
                    'known_services': set(metrics.get('services_used', [])),
                    'sample_count': 1
                }
            else:
                baseline = self.user_baselines[user_name]

                # Update running average
                baseline['sample_count'] += 1
                baseline['avg_actions'] = (
                    (baseline['avg_actions'] * (baseline['sample_count'] - 1) + metrics['total_actions'])
                    / baseline['sample_count']
                )

                # Add new IPs and services to known set
                baseline['known_ips'].update(metrics.get('source_ips', []))
                baseline['known_services'].update(metrics.get('services_used', []))


__all__ = ['AnomalyDetector']
