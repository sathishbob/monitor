"""
Multi-Cloud Monitoring System

Main orchestrator for collecting metrics from AWS, GCP, and Azure,
checking thresholds, sending alerts, and pushing data to Elasticsearch.
"""

import logging
import time
import yaml
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collectors.aws_collector import AWSCollector
from collectors.gcp_collector import GCPCollector
from collectors.azure_collector import AzureCollector
from alerting.alert_manager import AlertManager

# Import ES manager from parent project
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.es_manager import ElasticsearchManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud-monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CloudMonitor:
    """Main orchestrator for multi-cloud monitoring."""

    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize cloud monitor with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.collectors = self._initialize_collectors()
        self.alert_manager = AlertManager(self.config)
        self.es_manager = self._initialize_elasticsearch()

        self.monitoring_interval = self.config.get('monitoring_interval', 300)

        logger.info("Cloud Monitor initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            # Expand environment variables in config path
            config_path = os.path.expandvars(config_path)

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Expand environment variables in config values
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
        """Initialize collectors for all enabled cloud providers."""
        collectors = {'aws': [], 'gcp': [], 'azure': []}

        # Initialize AWS collectors
        if self.config.get('aws', {}).get('enabled', False):
            for account_config in self.config['aws'].get('accounts', []):
                try:
                    collector = AWSCollector(account_config)
                    collectors['aws'].append(collector)
                    logger.info(f"Initialized AWS collector for {account_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize AWS collector: {e}")

        # Initialize GCP collectors
        if self.config.get('gcp', {}).get('enabled', False):
            for project_config in self.config['gcp'].get('projects', []):
                try:
                    collector = GCPCollector(project_config)
                    collectors['gcp'].append(collector)
                    logger.info(f"Initialized GCP collector for {project_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize GCP collector: {e}")

        # Initialize Azure collectors
        if self.config.get('azure', {}).get('enabled', False):
            for subscription_config in self.config['azure'].get('subscriptions', []):
                try:
                    collector = AzureCollector(subscription_config)
                    collectors['azure'].append(collector)
                    logger.info(f"Initialized Azure collector for {subscription_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize Azure collector: {e}")

        total_collectors = sum(len(c) for c in collectors.values())
        logger.info(f"Initialized {total_collectors} cloud collectors")

        return collectors

    def _initialize_elasticsearch(self) -> ElasticsearchManager:
        """Initialize Elasticsearch manager for data storage."""
        try:
            es_config = self.config.get('elasticsearch', {})

            es_manager = ElasticsearchManager(
                host=es_config.get('host', 'localhost:9200'),
                index=es_config.get('index', 'cloud-usage-metrics'),
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

    def collect_metrics(self) -> List[Dict[str, Any]]:
        """Collect metrics from all cloud providers."""
        all_metrics = []

        # Collect from AWS
        for collector in self.collectors['aws']:
            try:
                metrics = collector.collect_all_metrics()
                all_metrics.extend(metrics)
                logger.info(f"Collected {len(metrics)} metrics from AWS account {collector.account_name}")
            except Exception as e:
                logger.error(f"Error collecting AWS metrics: {e}")

        # Collect from GCP
        for collector in self.collectors['gcp']:
            try:
                metrics = collector.collect_all_metrics()
                all_metrics.extend(metrics)
                logger.info(f"Collected {len(metrics)} metrics from GCP project {collector.project_name}")
            except Exception as e:
                logger.error(f"Error collecting GCP metrics: {e}")

        # Collect from Azure
        for collector in self.collectors['azure']:
            try:
                metrics = collector.collect_all_metrics()
                all_metrics.extend(metrics)
                logger.info(f"Collected {len(metrics)} metrics from Azure subscription {collector.subscription_name}")
            except Exception as e:
                logger.error(f"Error collecting Azure metrics: {e}")

        logger.info(f"Total metrics collected: {len(all_metrics)}")
        return all_metrics

    def process_metrics(self, metrics: List[Dict[str, Any]]):
        """Process metrics: check thresholds and store in Elasticsearch."""

        # Check thresholds and send alerts
        try:
            alerts = self.alert_manager.check_and_alert(metrics)
            logger.info(f"Processed {len(alerts)} alerts")
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")

        # Store metrics in Elasticsearch
        if self.es_manager:
            try:
                success_count = 0
                for metric in metrics:
                    if self.es_manager.push_data(metric, 'cloud_usage'):
                        success_count += 1

                logger.info(f"Stored {success_count}/{len(metrics)} metrics in Elasticsearch")

            except Exception as e:
                logger.error(f"Error storing metrics in Elasticsearch: {e}")
        else:
            logger.warning("Elasticsearch not configured, skipping metric storage")

    def run(self):
        """Run the monitoring loop continuously."""
        logger.info("Starting cloud monitoring loop")

        iteration = 0
        while True:
            try:
                iteration += 1
                logger.info(f"=== Monitoring iteration {iteration} started ===")

                # Collect metrics
                start_time = time.time()
                metrics = self.collect_metrics()

                # Process metrics
                if metrics:
                    self.process_metrics(metrics)
                else:
                    logger.warning("No metrics collected in this iteration")

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

        logger.info("Cloud monitoring stopped")

    def run_once(self):
        """Run a single monitoring iteration (useful for testing)."""
        logger.info("Running single monitoring iteration")

        metrics = self.collect_metrics()

        if metrics:
            self.process_metrics(metrics)
            logger.info(f"Processed {len(metrics)} metrics successfully")
        else:
            logger.warning("No metrics collected")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Cloud Monitoring System')
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = CloudMonitor(config_path=args.config)

    # Run
    if args.once:
        monitor.run_once()
    else:
        monitor.run()


if __name__ == '__main__':
    main()
