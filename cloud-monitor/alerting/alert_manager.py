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
        cloud_provider = metric.get('cloud_provider', '').lower()

        # Get provider-specific thresholds
        provider_thresholds = self.thresholds.get(cloud_provider, {})

        # Check resource count thresholds
        total_count = metric.get('total_count')
        if total_count is not None:
            alerts.extend(self._check_resource_count_thresholds(metric, provider_thresholds))

        # Check cost thresholds
        if metric.get('cost_type'):
            alerts.extend(self._check_cost_thresholds(metric, provider_thresholds))

        return alerts

    def _check_resource_count_thresholds(self, metric: Dict[str, Any], provider_thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check resource count against thresholds."""
        alerts = []
        service = metric.get('service', '').lower()
        resource_type = metric.get('resource_type', '')
        total_count = metric.get('total_count', 0)
        region = metric.get('region', 'unknown')

        # Build threshold key: service_resourcetype_per_region or service_resourcetype_total
        # Examples: ec2_instances_per_region, s3_buckets_total, lambda_functions_per_region
        is_regional = region not in ['global', 'all-regions', 'all-zones']

        threshold_key = f"{service}_{resource_type}"
        if is_regional:
            threshold_key += "_per_region"
        else:
            threshold_key += "_total"

        threshold_value = provider_thresholds.get(threshold_key)

        if threshold_value is not None and total_count > threshold_value:
            # Determine severity based on how much threshold is exceeded
            excess_percent = ((total_count - threshold_value) / threshold_value) * 100

            if excess_percent > 50:
                severity = 'CRITICAL'
            elif excess_percent > 20:
                severity = 'WARNING'
            else:
                severity = 'INFO'

            # Get breakdown information if available
            breakdown_info = []
            if metric.get('status_breakdown'):
                breakdown_info.append(f"Status: {metric['status_breakdown']}")
            if metric.get('state_breakdown'):
                breakdown_info.append(f"State: {metric['state_breakdown']}")
            if metric.get('type_breakdown'):
                breakdown_info.append(f"Type: {metric['type_breakdown']}")

            breakdown_str = ", ".join(breakdown_info) if breakdown_info else ""

            message = f"{service.upper()} {resource_type} count ({total_count:,}) exceeds threshold ({threshold_value:,})"
            if region != 'global':
                message += f" in {region}"
            if breakdown_str:
                message += f" [{breakdown_str}]"

            alerts.append({
                'severity': severity,
                'metric_type': 'resource_count',
                'current_value': total_count,
                'threshold': threshold_value,
                'resource': metric,
                'message': message,
                'service': service,
                'resource_type': resource_type
            })

        return alerts

    def _check_cost_thresholds(self, metric: Dict[str, Any], provider_thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check cost against budget thresholds."""
        alerts = []
        cost_type = metric.get('cost_type', '')
        total_cost = metric.get('total_cost_usd', 0)

        # Check monthly budget
        if cost_type in ['monthly', 'monthly_by_service']:
            monthly_budget = provider_thresholds.get('monthly_budget_usd')

            if monthly_budget and total_cost > monthly_budget:
                excess_percent = ((total_cost - monthly_budget) / monthly_budget) * 100

                if excess_percent > 20:
                    severity = 'CRITICAL'
                elif excess_percent > 10:
                    severity = 'WARNING'
                else:
                    severity = 'INFO'

                message = f"Monthly cost (${total_cost:,.2f}) exceeds budget (${monthly_budget:,.2f})"

                # Add service breakdown if available
                if metric.get('service_breakdown'):
                    top_services = sorted(
                        metric['service_breakdown'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    message += f" - Top services: {dict(top_services)}"

                alerts.append({
                    'severity': severity,
                    'metric_type': 'cost_budget',
                    'current_value': total_cost,
                    'threshold': monthly_budget,
                    'resource': metric,
                    'message': message
                })

        # Check daily cost anomalies
        elif cost_type == 'daily':
            daily_budget = provider_thresholds.get('daily_budget_usd')

            if daily_budget and total_cost > daily_budget:
                message = f"Daily cost (${total_cost:,.2f}) exceeds expected (${daily_budget:,.2f})"

                alerts.append({
                    'severity': 'WARNING',
                    'metric_type': 'daily_cost_anomaly',
                    'current_value': total_cost,
                    'threshold': daily_budget,
                    'resource': metric,
                    'message': message
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
