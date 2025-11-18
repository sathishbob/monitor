"""
Multi-Cloud Cost Tracker

Collects cost and billing data from AWS, GCP, and Azure.
Provides daily, monthly, and service-level cost breakdowns.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import boto3
from google.cloud import billing_v1
from azure.mgmt.costmanagement import CostManagementClient
from azure.identity import ClientSecretCredential
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class AWSCostTracker:
    """Tracks AWS costs using Cost Explorer API."""

    def __init__(self, account_config: Dict[str, Any]):
        """Initialize AWS cost tracker."""
        self.account_name = account_config['name']
        self.access_key = account_config['access_key_id']
        self.secret_key = account_config['secret_access_key']
        self.region = account_config.get('regions', ['us-east-1'])[0]

        logger.info(f"Initialized AWS cost tracker for: {self.account_name}")

    def get_session(self):
        """Create boto3 session."""
        return boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

    def collect_cost_data(self) -> List[Dict[str, Any]]:
        """Collect cost data from AWS Cost Explorer."""
        all_costs = []

        try:
            session = self.get_session()
            ce_client = session.client('ce')

            # Get costs for last 30 days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)

            # Daily costs for last 30 days
            all_costs.extend(self.get_daily_costs(ce_client, start_date, end_date))

            # Service-level costs for current month
            all_costs.extend(self.get_service_costs(ce_client))

            # Regional costs
            all_costs.extend(self.get_regional_costs(ce_client))

        except Exception as e:
            logger.error(f"Error collecting AWS costs: {e}")

        return all_costs

    def get_daily_costs(self, ce_client, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily cost breakdown."""
        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )

            costs = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']

                # Calculate total for the day
                total_cost = sum(
                    float(group['Metrics']['UnblendedCost']['Amount'])
                    for group in result['Groups']
                )

                # Get service breakdown
                service_costs = {}
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0:
                        service_costs[service] = cost

                costs.append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'cost_type': 'daily',
                    'date': date,
                    'total_cost_usd': round(total_cost, 2),
                    'currency': 'USD',
                    'service_breakdown': service_costs
                })

            return costs

        except Exception as e:
            logger.error(f"Error getting daily costs: {e}")
            return []

    def get_service_costs(self, ce_client) -> List[Dict[str, Any]]:
        """Get service-level cost breakdown for current month."""
        try:
            # Get current month
            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_of_month.strftime('%Y-%m-%d'),
                    'End': now.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )

            service_costs = {}
            total_cost = 0

            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0:
                        service_costs[service] = round(cost, 2)
                        total_cost += cost

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'cost_type': 'monthly_by_service',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': round(total_cost, 2),
                'currency': 'USD',
                'service_breakdown': service_costs
            }]

        except Exception as e:
            logger.error(f"Error getting service costs: {e}")
            return []

    def get_regional_costs(self, ce_client) -> List[Dict[str, Any]]:
        """Get regional cost breakdown for current month."""
        try:
            # Get current month
            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_of_month.strftime('%Y-%m-%d'),
                    'End': now.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'REGION'}
                ]
            )

            regional_costs = {}
            total_cost = 0

            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    region = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0:
                        regional_costs[region] = round(cost, 2)
                        total_cost += cost

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'cost_type': 'monthly_by_region',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': round(total_cost, 2),
                'currency': 'USD',
                'regional_breakdown': regional_costs
            }]

        except Exception as e:
            logger.error(f"Error getting regional costs: {e}")
            return []


class GCPCostTracker:
    """Tracks GCP costs using Cloud Billing API."""

    def __init__(self, project_config: Dict[str, Any]):
        """Initialize GCP cost tracker."""
        self.project_name = project_config['name']
        self.project_id = project_config['project_id']
        self.billing_account_id = project_config.get('billing_account_id')
        self.credentials_file = project_config.get('credentials_file')

        if self.credentials_file:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file
            )
        else:
            self.credentials = None

        logger.info(f"Initialized GCP cost tracker for: {self.project_name}")

    def collect_cost_data(self) -> List[Dict[str, Any]]:
        """Collect cost data from GCP Cloud Billing."""
        all_costs = []

        try:
            # Note: GCP Cloud Billing API provides data with some delay
            # Typically previous day's data is available

            all_costs.extend(self.get_monthly_costs())
            all_costs.extend(self.get_service_costs())

        except Exception as e:
            logger.error(f"Error collecting GCP costs: {e}")

        return all_costs

    def get_monthly_costs(self) -> List[Dict[str, Any]]:
        """Get monthly cost summary."""
        try:
            # GCP Billing data is typically retrieved via BigQuery export
            # This is a simplified version

            # For now, return placeholder data
            # In production, you would query the BigQuery billing export table
            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'cost_type': 'monthly',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': 0.0,
                'currency': 'USD',
                'note': 'GCP costs require BigQuery billing export setup'
            }]

        except Exception as e:
            logger.error(f"Error getting monthly costs: {e}")
            return []

    def get_service_costs(self) -> List[Dict[str, Any]]:
        """Get service-level cost breakdown."""
        try:
            # Query BigQuery billing export table
            # This requires billing export to be set up in GCP

            # For now, return placeholder
            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'cost_type': 'monthly_by_service',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': 0.0,
                'currency': 'USD',
                'service_breakdown': {},
                'note': 'GCP costs require BigQuery billing export setup'
            }]

        except Exception as e:
            logger.error(f"Error getting service costs: {e}")
            return []


class AzureCostTracker:
    """Tracks Azure costs using Cost Management API."""

    def __init__(self, subscription_config: Dict[str, Any]):
        """Initialize Azure cost tracker."""
        self.subscription_name = subscription_config['name']
        self.subscription_id = subscription_config['subscription_id']
        self.tenant_id = subscription_config['tenant_id']
        self.client_id = subscription_config['client_id']
        self.client_secret = subscription_config['client_secret']

        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        logger.info(f"Initialized Azure cost tracker for: {self.subscription_name}")

    def collect_cost_data(self) -> List[Dict[str, Any]]:
        """Collect cost data from Azure Cost Management."""
        all_costs = []

        try:
            all_costs.extend(self.get_monthly_costs())
            all_costs.extend(self.get_service_costs())
            all_costs.extend(self.get_resource_group_costs())

        except Exception as e:
            logger.error(f"Error collecting Azure costs: {e}")

        return all_costs

    def get_monthly_costs(self) -> List[Dict[str, Any]]:
        """Get monthly cost summary."""
        try:
            cost_client = CostManagementClient(self.credential)

            # Define scope
            scope = f"/subscriptions/{self.subscription_id}"

            # Get current month
            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Define query
            query_definition = {
                "type": "ActualCost",
                "timeframe": "MonthToDate",
                "dataset": {
                    "granularity": "None",
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    }
                }
            }

            result = cost_client.query.usage(scope, query_definition)

            total_cost = 0.0
            if result.rows:
                total_cost = float(result.rows[0][0])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'cost_type': 'monthly',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': round(total_cost, 2),
                'currency': 'USD'
            }]

        except Exception as e:
            logger.error(f"Error getting Azure monthly costs: {e}")
            return []

    def get_service_costs(self) -> List[Dict[str, Any]]:
        """Get service-level cost breakdown."""
        try:
            cost_client = CostManagementClient(self.credential)

            scope = f"/subscriptions/{self.subscription_id}"

            # Query by service
            query_definition = {
                "type": "ActualCost",
                "timeframe": "MonthToDate",
                "dataset": {
                    "granularity": "None",
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {
                            "type": "Dimension",
                            "name": "ServiceName"
                        }
                    ]
                }
            }

            result = cost_client.query.usage(scope, query_definition)

            service_costs = {}
            total_cost = 0.0

            if result.rows:
                for row in result.rows:
                    cost = float(row[0])
                    service_name = row[1] if len(row) > 1 else 'Unknown'

                    if cost > 0:
                        service_costs[service_name] = round(cost, 2)
                        total_cost += cost

            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'cost_type': 'monthly_by_service',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': round(total_cost, 2),
                'currency': 'USD',
                'service_breakdown': service_costs
            }]

        except Exception as e:
            logger.error(f"Error getting Azure service costs: {e}")
            return []

    def get_resource_group_costs(self) -> List[Dict[str, Any]]:
        """Get cost breakdown by resource group."""
        try:
            cost_client = CostManagementClient(self.credential)

            scope = f"/subscriptions/{self.subscription_id}"

            # Query by resource group
            query_definition = {
                "type": "ActualCost",
                "timeframe": "MonthToDate",
                "dataset": {
                    "granularity": "None",
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {
                            "type": "Dimension",
                            "name": "ResourceGroup"
                        }
                    ]
                }
            }

            result = cost_client.query.usage(scope, query_definition)

            rg_costs = {}
            total_cost = 0.0

            if result.rows:
                for row in result.rows:
                    cost = float(row[0])
                    rg_name = row[1] if len(row) > 1 else 'Unknown'

                    if cost > 0:
                        rg_costs[rg_name] = round(cost, 2)
                        total_cost += cost

            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'cost_type': 'monthly_by_resource_group',
                'month': start_of_month.strftime('%Y-%m'),
                'total_cost_usd': round(total_cost, 2),
                'currency': 'USD',
                'resource_group_breakdown': rg_costs
            }]

        except Exception as e:
            logger.error(f"Error getting resource group costs: {e}")
            return []


__all__ = ['AWSCostTracker', 'GCPCostTracker', 'AzureCostTracker']
