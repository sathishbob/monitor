"""
Alert Manager - Threshold-based Email Alerting for Cloud Resources

Monitors cloud resource metrics against configured thresholds and sends
email notifications when thresholds are exceeded.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages threshold-based alerting for cloud resources."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize alert manager with configuration.

        Args:
            config: Configuration dict with alerting and threshold settings
        """
        self.enabled = config.get('alerting', {}).get('enabled', True)
        self.smtp_config = config.get('alerting', {}).get('smtp', {})
        self.recipients = config.get('alerting', {}).get('recipients', [])
        self.thresholds = config.get('thresholds', {})

        # Alert history to prevent duplicate alerts
        self.alert_history = {}
        self.cooldown_minutes = 60  # Don't resend same alert within 1 hour

        logger.info("Alert Manager initialized")

    def check_and_alert(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check metrics against thresholds and generate alerts.

        Args:
            metrics: List of resource metrics to check

        Returns:
            List of alert dictionaries that were triggered
        """
        if not self.enabled:
            return []

        triggered_alerts = []

        for metric in metrics:
            alerts = self._check_thresholds(metric)
            for alert in alerts:
                # Check if this alert was recently sent
                if not self._is_duplicate_alert(alert):
                    triggered_alerts.append(alert)
                    self._send_email_alert(alert)
                    self._record_alert(alert)

        logger.info(f"Triggered {len(triggered_alerts)} alerts")
        return triggered_alerts

    def _check_thresholds(self, metric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a single metric against all relevant thresholds."""
        alerts = []
        service = metric.get('service', '').lower()

        # Check compute thresholds
        if service in ['ec2', 'computeengine', 'virtualmachines']:
            alerts.extend(self._check_compute_thresholds(metric))

        # Check storage thresholds
        elif service in ['s3', 'cloudstorage', 'blobstorage']:
            alerts.extend(self._check_storage_thresholds(metric))

        # Check database thresholds
        elif service in ['rds', 'cloudsql', 'sqldatabase']:
            alerts.extend(self._check_database_thresholds(metric))

        # Check serverless thresholds
        elif service in ['lambda', 'cloudfunctions', 'functions']:
            alerts.extend(self._check_serverless_thresholds(metric))

        # Check network thresholds
        elif service in ['elb', 'cloudloadbalancing', 'loadbalancer']:
            alerts.extend(self._check_network_thresholds(metric))

        return alerts

    def _check_compute_thresholds(self, metric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check compute resource thresholds."""
        alerts = []
        compute_thresholds = self.thresholds.get('compute', {})

        # CPU utilization
        cpu = metric.get('cpu_utilization')
        cpu_threshold = compute_thresholds.get('cpu_utilization_percent', 80)
        if cpu and cpu > cpu_threshold:
            alerts.append({
                'severity': 'WARNING' if cpu < 90 else 'CRITICAL',
                'metric_type': 'cpu_utilization',
                'current_value': cpu,
                'threshold': cpu_threshold,
                'resource': metric,
                'message': f"CPU utilization ({cpu:.1f}%) exceeds threshold ({cpu_threshold}%)"
            })

        # Memory utilization
        memory = metric.get('memory_utilization')
        memory_threshold = compute_thresholds.get('memory_utilization_percent', 85)
        if memory and memory > memory_threshold:
            alerts.append({
                'severity': 'WARNING' if memory < 95 else 'CRITICAL',
                'metric_type': 'memory_utilization',
                'current_value': memory,
                'threshold': memory_threshold,
                'resource': metric,
                'message': f"Memory utilization ({memory:.1f}%) exceeds threshold ({memory_threshold}%)"
            })

        return alerts

    def _check_storage_thresholds(self, metric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check storage resource thresholds."""
        alerts = []
        storage_thresholds = self.thresholds.get('storage', {})

        # Bucket size
        size_gb = metric.get('size_gb', 0)
        size_threshold = storage_thresholds.get('bucket_size_gb', 1000)
        if size_gb > size_threshold:
            alerts.append({
                'severity': 'WARNING',
                'metric_type': 'storage_size',
                'current_value': size_gb,
                'threshold': size_threshold,
                'resource': metric,
                'message': f"Storage size ({size_gb:.1f} GB) exceeds threshold ({size_threshold} GB)"
            })

        # Object count
        object_count = metric.get('object_count', 0)
        count_threshold = storage_thresholds.get('bucket_object_count', 1000000)
        if object_count > count_threshold:
            alerts.append({
                'severity': 'INFO',
                'metric_type': 'object_count',
                'current_value': object_count,
                'threshold': count_threshold,
                'resource': metric,
                'message': f"Object count ({object_count:,}) exceeds threshold ({count_threshold:,})"
            })

        return alerts

    def _check_database_thresholds(self, metric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check database resource thresholds."""
        alerts = []
        db_thresholds = self.thresholds.get('database', {})

        # CPU utilization
        cpu = metric.get('cpu_utilization')
        cpu_threshold = db_thresholds.get('cpu_utilization_percent', 75)
        if cpu and cpu > cpu_threshold:
            alerts.append({
                'severity': 'WARNING' if cpu < 85 else 'CRITICAL',
                'metric_type': 'db_cpu_utilization',
                'current_value': cpu,
                'threshold': cpu_threshold,
                'resource': metric,
                'message': f"Database CPU ({cpu:.1f}%) exceeds threshold ({cpu_threshold}%)"
            })

        # Connection count
        connections = metric.get('connection_count')
        conn_threshold = db_thresholds.get('connection_count', 500)
        if connections and connections > conn_threshold:
            alerts.append({
                'severity': 'WARNING',
                'metric_type': 'db_connections',
                'current_value': connections,
                'threshold': conn_threshold,
                'resource': metric,
                'message': f"Database connections ({connections}) exceeds threshold ({conn_threshold})"
            })

        return alerts

    def _check_serverless_thresholds(self, metric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check serverless function thresholds."""
        alerts = []
        serverless_thresholds = self.thresholds.get('serverless', {})

        # Error rate
        error_rate = metric.get('error_rate', 0)
        error_threshold = serverless_thresholds.get('error_rate_percent', 5)
        if error_rate > error_threshold:
            alerts.append({
                'severity': 'WARNING' if error_rate < 10 else 'CRITICAL',
                'metric_type': 'function_error_rate',
                'current_value': error_rate,
                'threshold': error_threshold,
                'resource': metric,
                'message': f"Function error rate ({error_rate:.1f}%) exceeds threshold ({error_threshold}%)"
            })

        # Invocation count (hourly)
        invocations = metric.get('invocations', 0)
        inv_threshold = serverless_thresholds.get('invocation_count_per_hour', 100000)
        if invocations > inv_threshold:
            alerts.append({
                'severity': 'INFO',
                'metric_type': 'function_invocations',
                'current_value': invocations,
                'threshold': inv_threshold,
                'resource': metric,
                'message': f"Function invocations ({invocations:,}) exceeds threshold ({inv_threshold:,})"
            })

        return alerts

    def _check_network_thresholds(self, metric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check network resource thresholds."""
        alerts = []
        network_thresholds = self.thresholds.get('network', {})

        # Request count
        requests = metric.get('request_count', 0)
        request_threshold = network_thresholds.get('load_balancer_requests_per_minute', 10000)
        if requests > request_threshold:
            alerts.append({
                'severity': 'INFO',
                'metric_type': 'lb_requests',
                'current_value': requests,
                'threshold': request_threshold,
                'resource': metric,
                'message': f"Load balancer requests ({requests:,}) exceeds threshold ({request_threshold:,})"
            })

        return alerts

    def _send_email_alert(self, alert: Dict[str, Any]) -> bool:
        """Send email notification for an alert."""
        if not self.recipients:
            logger.warning("No email recipients configured")
            return False

        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('username')
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"[{alert['severity']}] Cloud Resource Alert - {alert['metric_type']}"

            # Email body
            resource = alert['resource']
            body = f"""
Cloud Resource Alert

Severity: {alert['severity']}
Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Alert Message:
{alert['message']}

Resource Details:
- Provider: {resource.get('cloud_provider', 'N/A')}
- Account/Project: {resource.get('account', 'N/A')}
- Region: {resource.get('region', 'N/A')}
- Service: {resource.get('service', 'N/A')}
- Resource ID: {resource.get('resource_id', 'N/A')}
- Resource Type: {resource.get('resource_type', 'N/A')}

Metric Information:
- Current Value: {alert['current_value']}
- Threshold: {alert['threshold']}

Action Required:
Please investigate this resource and take appropriate action to resolve the threshold violation.

---
This is an automated alert from the Cloud Monitoring System.
"""

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls', True):
                    server.starttls()

                server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )

                server.send_message(msg)

            logger.info(f"Sent email alert for {alert['metric_type']}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    def _is_duplicate_alert(self, alert: Dict[str, Any]) -> bool:
        """Check if this alert was recently sent to avoid spam."""
        resource = alert['resource']
        alert_key = f"{resource.get('cloud_provider')}:{resource.get('account')}:{resource.get('resource_id')}:{alert['metric_type']}"

        if alert_key in self.alert_history:
            last_sent = self.alert_history[alert_key]
            time_since = (datetime.now(timezone.utc) - last_sent).total_seconds() / 60

            if time_since < self.cooldown_minutes:
                logger.debug(f"Suppressing duplicate alert: {alert_key}")
                return True

        return False

    def _record_alert(self, alert: Dict[str, Any]):
        """Record that an alert was sent."""
        resource = alert['resource']
        alert_key = f"{resource.get('cloud_provider')}:{resource.get('account')}:{resource.get('resource_id')}:{alert['metric_type']}"
        self.alert_history[alert_key] = datetime.now(timezone.utc)


__all__ = ['AlertManager']
