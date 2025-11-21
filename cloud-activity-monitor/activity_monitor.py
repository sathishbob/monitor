"""
Cloud User Activity Monitoring System

Main orchestrator for collecting user activities from AWS, GCP, and Azure,
detecting anomalies, generating metrics, and pushing data to Elasticsearch.
"""

import logging
import time
import yaml
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collectors.aws_activity_collector import AWSActivityCollector
from collectors.gcp_activity_collector import GCPActivityCollector
from collectors.azure_activity_collector import AzureActivityCollector
from processors.anomaly_detector import AnomalyDetector

# Import ES manager from parent project
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.es_manager import ElasticsearchManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('activity-monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ActivityMonitor:
    """Main orchestrator for cloud user activity monitoring."""

    def __init__(self, config_path: str = 'config/activity-config.yaml'):
        """
        Initialize activity monitor with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.collectors = self._initialize_collectors()
        self.anomaly_detector = AnomalyDetector(self.config)
        self.es_manager = self._initialize_elasticsearch()

        self.monitoring_interval = self.config.get('monitoring', {}).get('interval_minutes', 5) * 60
        self.lookback_minutes = self.config.get('monitoring', {}).get('lookback_minutes', 5)

        logger.info("Activity Monitor initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_path = os.path.expandvars(config_path)

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Expand environment variables
            config = self._expand_env_vars(config)

            logger.info(f"Loaded configuration from {config_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return os.path.expandvars(obj)
        return obj

    def _initialize_collectors(self) -> Dict[str, List]:
        """Initialize activity collectors for all enabled cloud providers."""
        collectors = {'aws': [], 'gcp': [], 'azure': []}

        # Initialize AWS collectors
        if self.config.get('aws', {}).get('enabled', False):
            for account_config in self.config['aws'].get('accounts', []):
                try:
                    collector = AWSActivityCollector(account_config)
                    collectors['aws'].append(collector)
                    logger.info(f"Initialized AWS collector for {account_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize AWS collector: {e}")

        # Initialize GCP collectors
        if self.config.get('gcp', {}).get('enabled', False):
            for project_config in self.config['gcp'].get('projects', []):
                try:
                    collector = GCPActivityCollector(project_config)
                    collectors['gcp'].append(collector)
                    logger.info(f"Initialized GCP collector for {project_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize GCP collector: {e}")

        # Initialize Azure collectors
        if self.config.get('azure', {}).get('enabled', False):
            for subscription_config in self.config['azure'].get('subscriptions', []):
                try:
                    collector = AzureActivityCollector(subscription_config)
                    collectors['azure'].append(collector)
                    logger.info(f"Initialized Azure collector for {subscription_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize Azure collector: {e}")

        total_collectors = sum(len(c) for c in collectors.values())
        logger.info(f"Initialized {total_collectors} activity collectors")

        return collectors

    def _initialize_elasticsearch(self) -> ElasticsearchManager:
        """Initialize Elasticsearch manager for data storage."""
        try:
            es_config = self.config.get('elasticsearch', {})

            es_manager = ElasticsearchManager(
                host=es_config.get('host', 'localhost:9200'),
                index=es_config.get('index', 'cloud-user-activities'),
                user=es_config.get('username'),
                password=es_config.get('password'),
                api_key=es_config.get('api_key'),
                insecure=not es_config.get('ssl', False)
            )

            logger.info("Elasticsearch manager initialized")
            return es_manager

        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {e}")
            return None

    def collect_activities(self) -> List[Dict[str, Any]]:
        """Collect user activities from all cloud providers."""
        all_activities = []

        # Collect from AWS
        for collector in self.collectors['aws']:
            try:
                activities = collector.collect_activities(self.lookback_minutes)
                all_activities.extend(activities)
                logger.info(f"Collected {len(activities)} activities from AWS account {collector.account_name}")
            except Exception as e:
                logger.error(f"Error collecting AWS activities: {e}")

        # Collect from GCP
        for collector in self.collectors['gcp']:
            try:
                activities = collector.collect_activities(self.lookback_minutes)
                all_activities.extend(activities)
                logger.info(f"Collected {len(activities)} activities from GCP project {collector.project_name}")
            except Exception as e:
                logger.error(f"Error collecting GCP activities: {e}")

        # Collect from Azure
        for collector in self.collectors['azure']:
            try:
                activities = collector.collect_activities(self.lookback_minutes)
                all_activities.extend(activities)
                logger.info(f"Collected {len(activities)} activities from Azure subscription {collector.subscription_name}")
            except Exception as e:
                logger.error(f"Error collecting Azure activities: {e}")

        logger.info(f"Total activities collected: {len(all_activities)}")
        return all_activities

    def generate_user_summaries(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate per-user summary metrics."""
        all_summaries = []

        # Group activities by cloud provider and account
        grouped = {}
        for activity in activities:
            key = (activity['cloud_provider'], activity['account'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(activity)

        # Generate summaries for each group
        for (cloud_provider, account), group_activities in grouped.items():
            # Find appropriate collector
            collector = None

            if cloud_provider == 'aws':
                collector = next((c for c in self.collectors['aws'] if c.account_name == account), None)
            elif cloud_provider == 'gcp':
                collector = next((c for c in self.collectors['gcp'] if c.project_name == account), None)
            elif cloud_provider == 'azure':
                collector = next((c for c in self.collectors['azure'] if c.subscription_name == account), None)

            if collector:
                try:
                    summaries = collector.get_user_summary(group_activities)
                    all_summaries.extend(summaries)
                except Exception as e:
                    logger.error(f"Error generating summaries for {cloud_provider}/{account}: {e}")

        logger.info(f"Generated {len(all_summaries)} user summaries")
        return all_summaries

    def process_activities(self, activities: List[Dict[str, Any]],
                          user_summaries: List[Dict[str, Any]]):
        """Process activities: detect anomalies and store in Elasticsearch."""

        # Detect anomalies
        if self.config.get('anomaly_detection', {}).get('enabled', True):
            try:
                anomalies = self.anomaly_detector.detect_anomalies(activities, user_summaries)
                logger.info(f"Detected {len(anomalies)} anomalies")

                # Store anomalies in Elasticsearch
                if self.es_manager and anomalies:
                    for anomaly in anomalies:
                        self.es_manager.push_data(anomaly, 'anomaly')

                # Send email alerts for critical anomalies
                critical_anomalies = [a for a in anomalies if a['severity'] == 'critical']
                if critical_anomalies and self.config.get('alerting', {}).get('enabled', False):
                    self._send_anomaly_alerts(critical_anomalies)

            except Exception as e:
                logger.error(f"Error processing anomalies: {e}")

        # Store activities in Elasticsearch
        if self.es_manager:
            try:
                success_count = 0

                # Store individual activities
                for activity in activities:
                    if self.es_manager.push_data(activity, 'user_activity'):
                        success_count += 1

                logger.info(f"Stored {success_count}/{len(activities)} activities in Elasticsearch")

                # Store user summaries
                summary_count = 0
                for summary in user_summaries:
                    if self.es_manager.push_data(summary, 'user_summary'):
                        summary_count += 1

                logger.info(f"Stored {summary_count}/{len(user_summaries)} user summaries in Elasticsearch")

            except Exception as e:
                logger.error(f"Error storing data in Elasticsearch: {e}")
        else:
            logger.warning("Elasticsearch not configured, skipping data storage")

    def _send_anomaly_alerts(self, anomalies: List[Dict[str, Any]]):
        """Send email alerts for anomalies."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_config = self.config.get('alerting', {}).get('smtp', {})
            recipients = self.config.get('alerting', {}).get('recipients', [])

            if not recipients:
                logger.warning("No email recipients configured")
                return

            # Build email content
            subject = f"[ALERT] Cloud User Activity Anomalies Detected - {len(anomalies)} anomalies"

            body_parts = ["The following anomalies were detected in cloud user activities:\n\n"]

            for anomaly in anomalies:
                body_parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                body_parts.append(f"Severity: {anomaly['severity'].upper()}")
                body_parts.append(f"Type: {anomaly['anomaly_type']}")
                body_parts.append(f"User: {anomaly['user_name']}")
                body_parts.append(f"Cloud: {anomaly['cloud_provider'].upper()}")
                body_parts.append(f"Account: {anomaly['account']}")
                body_parts.append(f"Description: {anomaly['description']}")
                body_parts.append(f"Time: {anomaly['timestamp']}")
                body_parts.append("")

            body = "\n".join(body_parts)

            # Send email
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('username')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                if smtp_config.get('use_tls'):
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)

            logger.info(f"Sent anomaly alert email to {len(recipients)} recipients")

        except Exception as e:
            logger.error(f"Failed to send anomaly alerts: {e}")

    def run(self):
        """Run the monitoring loop continuously."""
        logger.info("Starting activity monitoring loop")

        iteration = 0
        while True:
            try:
                iteration += 1
                logger.info(f"=== Monitoring iteration {iteration} started ===")

                # Collect activities
                start_time = time.time()
                activities = self.collect_activities()

                # Generate user summaries
                user_summaries = []
                if activities:
                    user_summaries = self.generate_user_summaries(activities)
                    self.process_activities(activities, user_summaries)
                else:
                    logger.warning("No activities collected in this iteration")

                duration = time.time() - start_time
                logger.info(f"=== Iteration {iteration} completed in {duration:.2f}s ===")

                # Wait for next iteration
                logger.info(f"Sleeping for {self.monitoring_interval} seconds...")
                time.sleep(self.monitoring_interval)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying

        logger.info("Activity monitoring stopped")

    def run_once(self):
        """Run a single monitoring iteration (useful for testing)."""
        logger.info("Running single monitoring iteration")

        activities = self.collect_activities()

        if activities:
            user_summaries = self.generate_user_summaries(activities)
            self.process_activities(activities, user_summaries)
            logger.info(f"Processed {len(activities)} activities and {len(user_summaries)} user summaries")
        else:
            logger.warning("No activities collected")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Cloud User Activity Monitoring System')
    parser.add_argument(
        '--config',
        default='config/activity-config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = ActivityMonitor(config_path=args.config)

    # Run
    if args.once:
        monitor.run_once()
    else:
        monitor.run()


if __name__ == '__main__':
    main()
