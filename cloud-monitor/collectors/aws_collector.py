"""
AWS Resource Collector - Multi-Account Cloud Monitoring

This module collects usage metrics from AWS resources across multiple accounts
and regions, including EC2, RDS, S3, Lambda, and more.
"""

import logging
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class AWSCollector:
    """Collects resource usage metrics from AWS accounts."""

    def __init__(self, account_config: Dict[str, Any]):
        """
        Initialize AWS collector for a specific account.

        Args:
            account_config: Account configuration with credentials and regions
        """
        self.account_name = account_config['name']
        self.access_key = account_config['access_key_id']
        self.secret_key = account_config['secret_access_key']
        self.regions = account_config.get('regions', ['us-east-1'])

        logger.info(f"Initialized AWS collector for account: {self.account_name}")

    def get_session(self, region: str):
        """Create boto3 session for specified region."""
        return boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=region
        )

    def collect_all_metrics(self) -> List[Dict[str, Any]]:
        """Collect all metrics from all regions."""
        all_metrics = []

        for region in self.regions:
            try:
                logger.info(f"Collecting metrics from {self.account_name} - {region}")

                # Collect metrics from each service
                all_metrics.extend(self.collect_ec2_metrics(region))
                all_metrics.extend(self.collect_rds_metrics(region))
                all_metrics.extend(self.collect_s3_metrics(region))
                all_metrics.extend(self.collect_lambda_metrics(region))
                all_metrics.extend(self.collect_elb_metrics(region))
                all_metrics.extend(self.collect_ebs_metrics(region))
                all_metrics.extend(self.collect_dynamodb_metrics(region))

            except Exception as e:
                logger.error(f"Error collecting metrics from {region}: {e}")

        return all_metrics

    def collect_ec2_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect EC2 instance metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')
            cloudwatch = session.client('cloudwatch')

            # Get all EC2 instances
            response = ec2.describe_instances()

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    state = instance['State']['Name']

                    # Get CloudWatch metrics
                    cpu_metric = self._get_cloudwatch_metric(
                        cloudwatch, 'AWS/EC2', 'CPUUtilization',
                        [{'Name': 'InstanceId', 'Value': instance_id}]
                    )

                    metric_data = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'cloud_provider': 'aws',
                        'account': self.account_name,
                        'region': region,
                        'service': 'EC2',
                        'resource_type': 'instance',
                        'resource_id': instance_id,
                        'resource_name': self._get_tag_value(instance.get('Tags', []), 'Name'),
                        'instance_type': instance_type,
                        'state': state,
                        'cpu_utilization': cpu_metric,
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    }

                    metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} EC2 metrics from {region}")

        except Exception as e:
            logger.error(f"Error collecting EC2 metrics from {region}: {e}")

        return metrics

    def collect_rds_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect RDS database metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            rds = session.client('rds')
            cloudwatch = session.client('cloudwatch')

            # Get all RDS instances
            response = rds.describe_db_instances()

            for db in response['DBInstances']:
                db_id = db['DBInstanceIdentifier']

                cpu_metric = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/RDS', 'CPUUtilization',
                    [{'Name': 'DBInstanceIdentifier', 'Value': db_id}]
                )

                connections = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/RDS', 'DatabaseConnections',
                    [{'Name': 'DBInstanceIdentifier', 'Value': db_id}]
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'region': region,
                    'service': 'RDS',
                    'resource_type': 'database',
                    'resource_id': db_id,
                    'engine': db['Engine'],
                    'instance_class': db['DBInstanceClass'],
                    'status': db['DBInstanceStatus'],
                    'allocated_storage_gb': db['AllocatedStorage'],
                    'cpu_utilization': cpu_metric,
                    'connection_count': connections
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} RDS metrics from {region}")

        except Exception as e:
            logger.error(f"Error collecting RDS metrics from {region}: {e}")

        return metrics

    def collect_s3_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect S3 bucket metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            s3 = session.client('s3')
            cloudwatch = session.client('cloudwatch')

            # Get all S3 buckets
            response = s3.list_buckets()

            for bucket in response['Buckets']:
                bucket_name = bucket['Name']

                # Get bucket size and object count
                size_metric = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/S3', 'BucketSizeBytes',
                    [
                        {'Name': 'BucketName', 'Value': bucket_name},
                        {'Name': 'StorageType', 'Value': 'StandardStorage'}
                    ]
                )

                object_count = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/S3', 'NumberOfObjects',
                    [
                        {'Name': 'BucketName', 'Value': bucket_name},
                        {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                    ]
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'region': region,
                    'service': 'S3',
                    'resource_type': 'bucket',
                    'resource_id': bucket_name,
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'size_bytes': size_metric,
                    'size_gb': size_metric / (1024**3) if size_metric else 0,
                    'object_count': object_count
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} S3 metrics")

        except Exception as e:
            logger.error(f"Error collecting S3 metrics: {e}")

        return metrics

    def collect_lambda_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect Lambda function metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            lambda_client = session.client('lambda')
            cloudwatch = session.client('cloudwatch')

            # Get all Lambda functions
            response = lambda_client.list_functions()

            for function in response['Functions']:
                function_name = function['FunctionName']

                invocations = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/Lambda', 'Invocations',
                    [{'Name': 'FunctionName', 'Value': function_name}],
                    statistic='Sum'
                )

                errors = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/Lambda', 'Errors',
                    [{'Name': 'FunctionName', 'Value': function_name}],
                    statistic='Sum'
                )

                duration = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/Lambda', 'Duration',
                    [{'Name': 'FunctionName', 'Value': function_name}],
                    statistic='Average'
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'region': region,
                    'service': 'Lambda',
                    'resource_type': 'function',
                    'resource_id': function_name,
                    'runtime': function['Runtime'],
                    'memory_mb': function['MemorySize'],
                    'timeout_seconds': function['Timeout'],
                    'invocations': invocations or 0,
                    'errors': errors or 0,
                    'error_rate': (errors / invocations * 100) if invocations and errors else 0,
                    'avg_duration_ms': duration
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} Lambda metrics from {region}")

        except Exception as e:
            logger.error(f"Error collecting Lambda metrics from {region}: {e}")

        return metrics

    def collect_elb_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect Elastic Load Balancer metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            elb = session.client('elbv2')
            cloudwatch = session.client('cloudwatch')

            # Get all load balancers
            response = elb.describe_load_balancers()

            for lb in response['LoadBalancers']:
                lb_name = lb['LoadBalancerName']
                lb_arn = lb['LoadBalancerArn']

                request_count = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/ApplicationELB', 'RequestCount',
                    [{'Name': 'LoadBalancer', 'Value': lb_arn.split('/')[-1]}],
                    statistic='Sum'
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'region': region,
                    'service': 'ELB',
                    'resource_type': 'load_balancer',
                    'resource_id': lb_name,
                    'type': lb['Type'],
                    'scheme': lb['Scheme'],
                    'state': lb['State']['Code'],
                    'request_count': request_count or 0
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} ELB metrics from {region}")

        except Exception as e:
            logger.error(f"Error collecting ELB metrics from {region}: {e}")

        return metrics

    def collect_ebs_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect EBS volume metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            # Get all EBS volumes
            response = ec2.describe_volumes()

            for volume in response['Volumes']:
                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'region': region,
                    'service': 'EBS',
                    'resource_type': 'volume',
                    'resource_id': volume['VolumeId'],
                    'size_gb': volume['Size'],
                    'volume_type': volume['VolumeType'],
                    'state': volume['State'],
                    'iops': volume.get('Iops', 0)
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} EBS metrics from {region}")

        except Exception as e:
            logger.error(f"Error collecting EBS metrics from {region}: {e}")

        return metrics

    def collect_dynamodb_metrics(self, region: str) -> List[Dict[str, Any]]:
        """Collect DynamoDB table metrics."""
        metrics = []

        try:
            session = self.get_session(region)
            dynamodb = session.client('dynamodb')
            cloudwatch = session.client('cloudwatch')

            # Get all DynamoDB tables
            response = dynamodb.list_tables()

            for table_name in response['TableNames']:
                table_info = dynamodb.describe_table(TableName=table_name)['Table']

                read_capacity = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/DynamoDB', 'ConsumedReadCapacityUnits',
                    [{'Name': 'TableName', 'Value': table_name}],
                    statistic='Sum'
                )

                write_capacity = self._get_cloudwatch_metric(
                    cloudwatch, 'AWS/DynamoDB', 'ConsumedWriteCapacityUnits',
                    [{'Name': 'TableName', 'Value': table_name}],
                    statistic='Sum'
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'aws',
                    'account': self.account_name,
                    'region': region,
                    'service': 'DynamoDB',
                    'resource_type': 'table',
                    'resource_id': table_name,
                    'item_count': table_info.get('ItemCount', 0),
                    'table_size_bytes': table_info.get('TableSizeBytes', 0),
                    'consumed_read_capacity': read_capacity or 0,
                    'consumed_write_capacity': write_capacity or 0
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} DynamoDB metrics from {region}")

        except Exception as e:
            logger.error(f"Error collecting DynamoDB metrics from {region}: {e}")

        return metrics

    def _get_cloudwatch_metric(self, cloudwatch, namespace: str, metric_name: str,
                               dimensions: List[Dict], statistic: str = 'Average',
                               period: int = 300) -> Optional[float]:
        """Get CloudWatch metric value."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=10)

            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[statistic]
            )

            if response['Datapoints']:
                return response['Datapoints'][-1][statistic]

            return None

        except Exception as e:
            logger.debug(f"Error getting CloudWatch metric {metric_name}: {e}")
            return None

    def _get_tag_value(self, tags: List[Dict], key: str) -> Optional[str]:
        """Get value of a specific tag."""
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return None


__all__ = ['AWSCollector']
