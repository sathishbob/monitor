"""
AWS Resource Inventory Collector - Comprehensive Resource Counting

Counts all resources across ALL AWS services in multiple accounts and regions.
Focuses on resource inventory, not performance metrics.
"""

import logging
import boto3
from datetime import datetime, timezone
from typing import Dict, List, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AWSInventoryCollector:
    """Collects resource counts from AWS accounts across all services."""

    def __init__(self, account_config: Dict[str, Any]):
        """Initialize AWS inventory collector."""
        self.account_name = account_config['name']
        self.access_key = account_config['access_key_id']
        self.secret_key = account_config['secret_access_key']
        self.regions = account_config.get('regions', ['us-east-1'])

        logger.info(f"Initialized AWS inventory collector for: {self.account_name}")

    def get_session(self, region: str):
        """Create boto3 session for specified region."""
        return boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=region
        )

    def collect_all_inventory(self) -> List[Dict[str, Any]]:
        """Collect resource counts from all regions and all services."""
        all_inventory = []

        for region in self.regions:
            try:
                logger.info(f"Collecting inventory from {self.account_name} - {region}")

                # Compute services
                all_inventory.extend(self.count_ec2_instances(region))
                all_inventory.extend(self.count_ec2_volumes(region))
                all_inventory.extend(self.count_ec2_snapshots(region))
                all_inventory.extend(self.count_amis(region))
                all_inventory.extend(self.count_key_pairs(region))
                all_inventory.extend(self.count_elastic_ips(region))

                # Container services
                all_inventory.extend(self.count_ecs_clusters(region))
                all_inventory.extend(self.count_ecs_services(region))
                all_inventory.extend(self.count_eks_clusters(region))
                all_inventory.extend(self.count_ecr_repositories(region))

                # Database services
                all_inventory.extend(self.count_rds_instances(region))
                all_inventory.extend(self.count_rds_clusters(region))
                all_inventory.extend(self.count_dynamodb_tables(region))
                all_inventory.extend(self.count_elasticache_clusters(region))
                all_inventory.extend(self.count_redshift_clusters(region))

                # Storage services
                all_inventory.extend(self.count_s3_buckets(region))
                all_inventory.extend(self.count_efs_filesystems(region))
                all_inventory.extend(self.count_fsx_filesystems(region))

                # Networking services
                all_inventory.extend(self.count_vpcs(region))
                all_inventory.extend(self.count_subnets(region))
                all_inventory.extend(self.count_security_groups(region))
                all_inventory.extend(self.count_load_balancers(region))
                all_inventory.extend(self.count_target_groups(region))
                all_inventory.extend(self.count_nat_gateways(region))
                all_inventory.extend(self.count_internet_gateways(region))
                all_inventory.extend(self.count_route_tables(region))
                all_inventory.extend(self.count_network_acls(region))
                all_inventory.extend(self.count_vpc_endpoints(region))

                # Serverless services
                all_inventory.extend(self.count_lambda_functions(region))
                all_inventory.extend(self.count_api_gateways(region))
                all_inventory.extend(self.count_step_functions(region))

                # Analytics & Big Data
                all_inventory.extend(self.count_emr_clusters(region))
                all_inventory.extend(self.count_kinesis_streams(region))
                all_inventory.extend(self.count_glue_jobs(region))

                # Application Integration
                all_inventory.extend(self.count_sqs_queues(region))
                all_inventory.extend(self.count_sns_topics(region))
                all_inventory.extend(self.count_eventbridge_rules(region))

                # Developer Tools
                all_inventory.extend(self.count_codecommit_repos(region))
                all_inventory.extend(self.count_codebuild_projects(region))
                all_inventory.extend(self.count_codepipeline_pipelines(region))

                # Security & Identity
                all_inventory.extend(self.count_iam_users(region))
                all_inventory.extend(self.count_iam_roles(region))
                all_inventory.extend(self.count_iam_policies(region))
                all_inventory.extend(self.count_kms_keys(region))
                all_inventory.extend(self.count_secrets(region))

                # Management & Governance
                all_inventory.extend(self.count_cloudwatch_alarms(region))
                all_inventory.extend(self.count_cloudformation_stacks(region))
                all_inventory.extend(self.count_config_rules(region))

                # Content Delivery
                all_inventory.extend(self.count_cloudfront_distributions(region))

                # Machine Learning
                all_inventory.extend(self.count_sagemaker_endpoints(region))
                all_inventory.extend(self.count_sagemaker_models(region))

            except Exception as e:
                logger.error(f"Error collecting inventory from {region}: {e}")

        return all_inventory

    def count_ec2_instances(self, region: str) -> List[Dict[str, Any]]:
        """Count EC2 instances by state and type."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_instances()

            # Count by state
            state_counts = {}
            type_counts = {}
            total = 0

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    total += 1
                    state = instance['State']['Name']
                    instance_type = instance['InstanceType']

                    state_counts[state] = state_counts.get(state, 0) + 1
                    type_counts[instance_type] = type_counts.get(instance_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'EC2',
                'resource_type': 'instances',
                'total_count': total,
                'running_count': state_counts.get('running', 0),
                'stopped_count': state_counts.get('stopped', 0),
                'state_breakdown': state_counts,
                'type_breakdown': type_counts
            }]

        except Exception as e:
            logger.error(f"Error counting EC2 instances in {region}: {e}")
            return []

    def count_ec2_volumes(self, region: str) -> List[Dict[str, Any]]:
        """Count EBS volumes."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_volumes()
            volumes = response['Volumes']

            total_size_gb = sum(v['Size'] for v in volumes)
            attached = sum(1 for v in volumes if v['State'] == 'in-use')
            available = sum(1 for v in volumes if v['State'] == 'available')

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'EBS',
                'resource_type': 'volumes',
                'total_count': len(volumes),
                'attached_count': attached,
                'available_count': available,
                'total_size_gb': total_size_gb
            }]

        except Exception as e:
            logger.error(f"Error counting EBS volumes in {region}: {e}")
            return []

    def count_rds_instances(self, region: str) -> List[Dict[str, Any]]:
        """Count RDS database instances."""
        try:
            session = self.get_session(region)
            rds = session.client('rds')

            response = rds.describe_db_instances()
            instances = response['DBInstances']

            engine_counts = {}
            for db in instances:
                engine = db['Engine']
                engine_counts[engine] = engine_counts.get(engine, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'RDS',
                'resource_type': 'db_instances',
                'total_count': len(instances),
                'engine_breakdown': engine_counts
            }]

        except Exception as e:
            logger.error(f"Error counting RDS instances in {region}: {e}")
            return []

    def count_s3_buckets(self, region: str) -> List[Dict[str, Any]]:
        """Count S3 buckets (global service, count once)."""
        if region != 'us-east-1':  # Only count in one region to avoid duplicates
            return []

        try:
            session = self.get_session(region)
            s3 = session.client('s3')

            response = s3.list_buckets()
            buckets = response['Buckets']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': 'global',
                'service': 'S3',
                'resource_type': 'buckets',
                'total_count': len(buckets)
            }]

        except Exception as e:
            logger.error(f"Error counting S3 buckets: {e}")
            return []

    def count_lambda_functions(self, region: str) -> List[Dict[str, Any]]:
        """Count Lambda functions."""
        try:
            session = self.get_session(region)
            lambda_client = session.client('lambda')

            functions = []
            paginator = lambda_client.get_paginator('list_functions')
            for page in paginator.paginate():
                functions.extend(page['Functions'])

            runtime_counts = {}
            for func in functions:
                runtime = func['Runtime']
                runtime_counts[runtime] = runtime_counts.get(runtime, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'Lambda',
                'resource_type': 'functions',
                'total_count': len(functions),
                'runtime_breakdown': runtime_counts
            }]

        except Exception as e:
            logger.error(f"Error counting Lambda functions in {region}: {e}")
            return []

    def count_dynamodb_tables(self, region: str) -> List[Dict[str, Any]]:
        """Count DynamoDB tables."""
        try:
            session = self.get_session(region)
            dynamodb = session.client('dynamodb')

            response = dynamodb.list_tables()
            table_names = response['TableNames']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'DynamoDB',
                'resource_type': 'tables',
                'total_count': len(table_names)
            }]

        except Exception as e:
            logger.error(f"Error counting DynamoDB tables in {region}: {e}")
            return []

    def count_vpcs(self, region: str) -> List[Dict[str, Any]]:
        """Count VPCs."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_vpcs()
            vpcs = response['Vpcs']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'vpcs',
                'total_count': len(vpcs)
            }]

        except Exception as e:
            logger.error(f"Error counting VPCs in {region}: {e}")
            return []

    def count_load_balancers(self, region: str) -> List[Dict[str, Any]]:
        """Count Application and Network Load Balancers."""
        try:
            session = self.get_session(region)
            elbv2 = session.client('elbv2')

            response = elbv2.describe_load_balancers()
            lbs = response['LoadBalancers']

            type_counts = {}
            for lb in lbs:
                lb_type = lb['Type']
                type_counts[lb_type] = type_counts.get(lb_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'ELB',
                'resource_type': 'load_balancers',
                'total_count': len(lbs),
                'type_breakdown': type_counts
            }]

        except Exception as e:
            logger.error(f"Error counting load balancers in {region}: {e}")
            return []

    def count_ecs_clusters(self, region: str) -> List[Dict[str, Any]]:
        """Count ECS clusters."""
        try:
            session = self.get_session(region)
            ecs = session.client('ecs')

            response = ecs.list_clusters()
            clusters = response['clusterArns']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'ECS',
                'resource_type': 'clusters',
                'total_count': len(clusters)
            }]

        except Exception as e:
            logger.error(f"Error counting ECS clusters in {region}: {e}")
            return []

    def count_eks_clusters(self, region: str) -> List[Dict[str, Any]]:
        """Count EKS clusters."""
        try:
            session = self.get_session(region)
            eks = session.client('eks')

            response = eks.list_clusters()
            clusters = response['clusters']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'EKS',
                'resource_type': 'clusters',
                'total_count': len(clusters)
            }]

        except Exception as e:
            logger.error(f"Error counting EKS clusters in {region}: {e}")
            return []

    # Placeholder methods for additional services (implement similarly)
    def count_ec2_snapshots(self, region: str) -> List[Dict[str, Any]]:
        """Count EBS snapshots owned by this account."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')
            response = ec2.describe_snapshots(OwnerIds=['self'])
            return [{'timestamp': datetime.now(timezone.utc).isoformat(), 'cloud_provider': 'aws',
                    'account': self.account_name, 'region': region, 'service': 'EBS',
                    'resource_type': 'snapshots', 'total_count': len(response['Snapshots'])}]
        except Exception as e:
            logger.error(f"Error counting snapshots in {region}: {e}")
            return []

    def count_amis(self, region: str) -> List[Dict[str, Any]]:
        """Count AMIs owned by this account."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')
            response = ec2.describe_images(Owners=['self'])
            return [{'timestamp': datetime.now(timezone.utc).isoformat(), 'cloud_provider': 'aws',
                    'account': self.account_name, 'region': region, 'service': 'EC2',
                    'resource_type': 'amis', 'total_count': len(response['Images'])}]
        except Exception as e:
            logger.error(f"Error counting AMIs in {region}: {e}")
            return []

    def count_key_pairs(self, region: str) -> List[Dict[str, Any]]:
        """Count EC2 key pairs."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')
            response = ec2.describe_key_pairs()
            return [{'timestamp': datetime.now(timezone.utc).isoformat(), 'cloud_provider': 'aws',
                    'account': self.account_name, 'region': region, 'service': 'EC2',
                    'resource_type': 'key_pairs', 'total_count': len(response['KeyPairs'])}]
        except Exception as e:
            return []

    def count_elastic_ips(self, region: str) -> List[Dict[str, Any]]:
        """Count Elastic IPs."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')
            response = ec2.describe_addresses()
            return [{'timestamp': datetime.now(timezone.utc).isoformat(), 'cloud_provider': 'aws',
                    'account': self.account_name, 'region': region, 'service': 'EC2',
                    'resource_type': 'elastic_ips', 'total_count': len(response['Addresses'])}]
        except Exception as e:
            return []

    # Container Services
    def count_ecs_services(self, region: str) -> List[Dict[str, Any]]:
        """Count ECS services across all clusters."""
        try:
            session = self.get_session(region)
            ecs = session.client('ecs')

            # Get all clusters
            clusters_response = ecs.list_clusters()
            cluster_arns = clusters_response.get('clusterArns', [])

            total_services = 0
            for cluster_arn in cluster_arns:
                services_response = ecs.list_services(cluster=cluster_arn)
                total_services += len(services_response.get('serviceArns', []))

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'ECS',
                'resource_type': 'services',
                'total_count': total_services,
                'cluster_count': len(cluster_arns)
            }]
        except Exception as e:
            logger.error(f"Error counting ECS services in {region}: {e}")
            return []

    def count_ecr_repositories(self, region: str) -> List[Dict[str, Any]]:
        """Count ECR repositories."""
        try:
            session = self.get_session(region)
            ecr = session.client('ecr')

            repositories = []
            paginator = ecr.get_paginator('describe_repositories')
            for page in paginator.paginate():
                repositories.extend(page['repositories'])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'ECR',
                'resource_type': 'repositories',
                'total_count': len(repositories)
            }]
        except Exception as e:
            logger.error(f"Error counting ECR repositories in {region}: {e}")
            return []

    # Database Services
    def count_rds_clusters(self, region: str) -> List[Dict[str, Any]]:
        """Count RDS Aurora clusters."""
        try:
            session = self.get_session(region)
            rds = session.client('rds')

            response = rds.describe_db_clusters()
            clusters = response['DBClusters']

            engine_counts = {}
            for cluster in clusters:
                engine = cluster['Engine']
                engine_counts[engine] = engine_counts.get(engine, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'RDS',
                'resource_type': 'clusters',
                'total_count': len(clusters),
                'engine_breakdown': engine_counts
            }]
        except Exception as e:
            logger.error(f"Error counting RDS clusters in {region}: {e}")
            return []

    def count_elasticache_clusters(self, region: str) -> List[Dict[str, Any]]:
        """Count ElastiCache clusters (Redis and Memcached)."""
        try:
            session = self.get_session(region)
            elasticache = session.client('elasticache')

            response = elasticache.describe_cache_clusters()
            clusters = response['CacheClusters']

            engine_counts = {}
            for cluster in clusters:
                engine = cluster['Engine']
                engine_counts[engine] = engine_counts.get(engine, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'ElastiCache',
                'resource_type': 'clusters',
                'total_count': len(clusters),
                'engine_breakdown': engine_counts
            }]
        except Exception as e:
            logger.error(f"Error counting ElastiCache clusters in {region}: {e}")
            return []

    def count_redshift_clusters(self, region: str) -> List[Dict[str, Any]]:
        """Count Redshift data warehouse clusters."""
        try:
            session = self.get_session(region)
            redshift = session.client('redshift')

            response = redshift.describe_clusters()
            clusters = response['Clusters']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'Redshift',
                'resource_type': 'clusters',
                'total_count': len(clusters)
            }]
        except Exception as e:
            logger.error(f"Error counting Redshift clusters in {region}: {e}")
            return []

    # Storage Services
    def count_efs_filesystems(self, region: str) -> List[Dict[str, Any]]:
        """Count EFS file systems."""
        try:
            session = self.get_session(region)
            efs = session.client('efs')

            response = efs.describe_file_systems()
            filesystems = response['FileSystems']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'EFS',
                'resource_type': 'filesystems',
                'total_count': len(filesystems)
            }]
        except Exception as e:
            logger.error(f"Error counting EFS filesystems in {region}: {e}")
            return []

    def count_fsx_filesystems(self, region: str) -> List[Dict[str, Any]]:
        """Count FSx file systems (Windows, Lustre, etc.)."""
        try:
            session = self.get_session(region)
            fsx = session.client('fsx')

            response = fsx.describe_file_systems()
            filesystems = response['FileSystems']

            type_counts = {}
            for fs in filesystems:
                fs_type = fs['FileSystemType']
                type_counts[fs_type] = type_counts.get(fs_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'FSx',
                'resource_type': 'filesystems',
                'total_count': len(filesystems),
                'type_breakdown': type_counts
            }]
        except Exception as e:
            logger.error(f"Error counting FSx filesystems in {region}: {e}")
            return []

    # Networking Services
    def count_subnets(self, region: str) -> List[Dict[str, Any]]:
        """Count subnets."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_subnets()
            subnets = response['Subnets']

            # Count by VPC
            vpc_counts = {}
            for subnet in subnets:
                vpc_id = subnet['VpcId']
                vpc_counts[vpc_id] = vpc_counts.get(vpc_id, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'subnets',
                'total_count': len(subnets),
                'vpc_breakdown': vpc_counts
            }]
        except Exception as e:
            logger.error(f"Error counting subnets in {region}: {e}")
            return []

    def count_security_groups(self, region: str) -> List[Dict[str, Any]]:
        """Count security groups."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_security_groups()
            security_groups = response['SecurityGroups']

            # Count by VPC
            vpc_counts = {}
            for sg in security_groups:
                vpc_id = sg.get('VpcId', 'EC2-Classic')
                vpc_counts[vpc_id] = vpc_counts.get(vpc_id, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'security_groups',
                'total_count': len(security_groups),
                'vpc_breakdown': vpc_counts
            }]
        except Exception as e:
            logger.error(f"Error counting security groups in {region}: {e}")
            return []

    def count_target_groups(self, region: str) -> List[Dict[str, Any]]:
        """Count target groups for load balancers."""
        try:
            session = self.get_session(region)
            elbv2 = session.client('elbv2')

            response = elbv2.describe_target_groups()
            target_groups = response['TargetGroups']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'ELB',
                'resource_type': 'target_groups',
                'total_count': len(target_groups)
            }]
        except Exception as e:
            logger.error(f"Error counting target groups in {region}: {e}")
            return []

    def count_nat_gateways(self, region: str) -> List[Dict[str, Any]]:
        """Count NAT gateways."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_nat_gateways()
            nat_gateways = response['NatGateways']

            # Filter out deleted ones
            active = [ng for ng in nat_gateways if ng['State'] != 'deleted']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'nat_gateways',
                'total_count': len(active)
            }]
        except Exception as e:
            logger.error(f"Error counting NAT gateways in {region}: {e}")
            return []

    def count_internet_gateways(self, region: str) -> List[Dict[str, Any]]:
        """Count internet gateways."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_internet_gateways()
            igws = response['InternetGateways']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'internet_gateways',
                'total_count': len(igws)
            }]
        except Exception as e:
            logger.error(f"Error counting internet gateways in {region}: {e}")
            return []

    def count_route_tables(self, region: str) -> List[Dict[str, Any]]:
        """Count route tables."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_route_tables()
            route_tables = response['RouteTables']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'route_tables',
                'total_count': len(route_tables)
            }]
        except Exception as e:
            logger.error(f"Error counting route tables in {region}: {e}")
            return []

    def count_network_acls(self, region: str) -> List[Dict[str, Any]]:
        """Count network ACLs."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_network_acls()
            nacls = response['NetworkAcls']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'network_acls',
                'total_count': len(nacls)
            }]
        except Exception as e:
            logger.error(f"Error counting network ACLs in {region}: {e}")
            return []

    def count_vpc_endpoints(self, region: str) -> List[Dict[str, Any]]:
        """Count VPC endpoints."""
        try:
            session = self.get_session(region)
            ec2 = session.client('ec2')

            response = ec2.describe_vpc_endpoints()
            endpoints = response['VpcEndpoints']

            type_counts = {}
            for endpoint in endpoints:
                ep_type = endpoint['VpcEndpointType']
                type_counts[ep_type] = type_counts.get(ep_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'VPC',
                'resource_type': 'vpc_endpoints',
                'total_count': len(endpoints),
                'type_breakdown': type_counts
            }]
        except Exception as e:
            logger.error(f"Error counting VPC endpoints in {region}: {e}")
            return []

    # Serverless Services
    def count_api_gateways(self, region: str) -> List[Dict[str, Any]]:
        """Count API Gateway REST APIs."""
        try:
            session = self.get_session(region)
            apigateway = session.client('apigateway')

            response = apigateway.get_rest_apis()
            apis = response['items']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'APIGateway',
                'resource_type': 'rest_apis',
                'total_count': len(apis)
            }]
        except Exception as e:
            logger.error(f"Error counting API Gateways in {region}: {e}")
            return []

    def count_step_functions(self, region: str) -> List[Dict[str, Any]]:
        """Count Step Functions state machines."""
        try:
            session = self.get_session(region)
            stepfunctions = session.client('stepfunctions')

            response = stepfunctions.list_state_machines()
            state_machines = response['stateMachines']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'StepFunctions',
                'resource_type': 'state_machines',
                'total_count': len(state_machines)
            }]
        except Exception as e:
            logger.error(f"Error counting Step Functions in {region}: {e}")
            return []

    # Analytics & Big Data
    def count_emr_clusters(self, region: str) -> List[Dict[str, Any]]:
        """Count EMR clusters."""
        try:
            session = self.get_session(region)
            emr = session.client('emr')

            # Get active and terminated clusters
            response = emr.list_clusters()
            clusters = response['Clusters']

            state_counts = {}
            for cluster in clusters:
                state = cluster['Status']['State']
                state_counts[state] = state_counts.get(state, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'EMR',
                'resource_type': 'clusters',
                'total_count': len(clusters),
                'state_breakdown': state_counts
            }]
        except Exception as e:
            logger.error(f"Error counting EMR clusters in {region}: {e}")
            return []

    def count_kinesis_streams(self, region: str) -> List[Dict[str, Any]]:
        """Count Kinesis data streams."""
        try:
            session = self.get_session(region)
            kinesis = session.client('kinesis')

            response = kinesis.list_streams()
            stream_names = response['StreamNames']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'Kinesis',
                'resource_type': 'streams',
                'total_count': len(stream_names)
            }]
        except Exception as e:
            logger.error(f"Error counting Kinesis streams in {region}: {e}")
            return []

    def count_glue_jobs(self, region: str) -> List[Dict[str, Any]]:
        """Count AWS Glue ETL jobs."""
        try:
            session = self.get_session(region)
            glue = session.client('glue')

            response = glue.get_jobs()
            jobs = response['Jobs']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'Glue',
                'resource_type': 'jobs',
                'total_count': len(jobs)
            }]
        except Exception as e:
            logger.error(f"Error counting Glue jobs in {region}: {e}")
            return []

    # Application Integration
    def count_sqs_queues(self, region: str) -> List[Dict[str, Any]]:
        """Count SQS queues."""
        try:
            session = self.get_session(region)
            sqs = session.client('sqs')

            response = sqs.list_queues()
            queue_urls = response.get('QueueUrls', [])

            # Determine FIFO vs standard
            fifo_count = sum(1 for url in queue_urls if url.endswith('.fifo'))
            standard_count = len(queue_urls) - fifo_count

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'SQS',
                'resource_type': 'queues',
                'total_count': len(queue_urls),
                'fifo_count': fifo_count,
                'standard_count': standard_count
            }]
        except Exception as e:
            logger.error(f"Error counting SQS queues in {region}: {e}")
            return []

    def count_sns_topics(self, region: str) -> List[Dict[str, Any]]:
        """Count SNS topics."""
        try:
            session = self.get_session(region)
            sns = session.client('sns')

            response = sns.list_topics()
            topics = response.get('Topics', [])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'SNS',
                'resource_type': 'topics',
                'total_count': len(topics)
            }]
        except Exception as e:
            logger.error(f"Error counting SNS topics in {region}: {e}")
            return []

    def count_eventbridge_rules(self, region: str) -> List[Dict[str, Any]]:
        """Count EventBridge rules."""
        try:
            session = self.get_session(region)
            events = session.client('events')

            response = events.list_rules()
            rules = response['Rules']

            # Count enabled vs disabled
            enabled = sum(1 for rule in rules if rule['State'] == 'ENABLED')
            disabled = len(rules) - enabled

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'EventBridge',
                'resource_type': 'rules',
                'total_count': len(rules),
                'enabled_count': enabled,
                'disabled_count': disabled
            }]
        except Exception as e:
            logger.error(f"Error counting EventBridge rules in {region}: {e}")
            return []

    # Developer Tools
    def count_codecommit_repos(self, region: str) -> List[Dict[str, Any]]:
        """Count CodeCommit repositories."""
        try:
            session = self.get_session(region)
            codecommit = session.client('codecommit')

            response = codecommit.list_repositories()
            repos = response.get('repositories', [])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'CodeCommit',
                'resource_type': 'repositories',
                'total_count': len(repos)
            }]
        except Exception as e:
            logger.error(f"Error counting CodeCommit repos in {region}: {e}")
            return []

    def count_codebuild_projects(self, region: str) -> List[Dict[str, Any]]:
        """Count CodeBuild projects."""
        try:
            session = self.get_session(region)
            codebuild = session.client('codebuild')

            response = codebuild.list_projects()
            projects = response.get('projects', [])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'CodeBuild',
                'resource_type': 'projects',
                'total_count': len(projects)
            }]
        except Exception as e:
            logger.error(f"Error counting CodeBuild projects in {region}: {e}")
            return []

    def count_codepipeline_pipelines(self, region: str) -> List[Dict[str, Any]]:
        """Count CodePipeline pipelines."""
        try:
            session = self.get_session(region)
            codepipeline = session.client('codepipeline')

            response = codepipeline.list_pipelines()
            pipelines = response.get('pipelines', [])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'CodePipeline',
                'resource_type': 'pipelines',
                'total_count': len(pipelines)
            }]
        except Exception as e:
            logger.error(f"Error counting CodePipeline pipelines in {region}: {e}")
            return []

    # Security & Identity (IAM is global, count once)
    def count_iam_users(self, region: str) -> List[Dict[str, Any]]:
        """Count IAM users (global service)."""
        if region != 'us-east-1':  # Only count in one region
            return []

        try:
            session = self.get_session(region)
            iam = session.client('iam')

            users = []
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                users.extend(page['Users'])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': 'global',
                'service': 'IAM',
                'resource_type': 'users',
                'total_count': len(users)
            }]
        except Exception as e:
            logger.error(f"Error counting IAM users: {e}")
            return []

    def count_iam_roles(self, region: str) -> List[Dict[str, Any]]:
        """Count IAM roles (global service)."""
        if region != 'us-east-1':  # Only count in one region
            return []

        try:
            session = self.get_session(region)
            iam = session.client('iam')

            roles = []
            paginator = iam.get_paginator('list_roles')
            for page in paginator.paginate():
                roles.extend(page['Roles'])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': 'global',
                'service': 'IAM',
                'resource_type': 'roles',
                'total_count': len(roles)
            }]
        except Exception as e:
            logger.error(f"Error counting IAM roles: {e}")
            return []

    def count_iam_policies(self, region: str) -> List[Dict[str, Any]]:
        """Count customer-managed IAM policies (global service)."""
        if region != 'us-east-1':  # Only count in one region
            return []

        try:
            session = self.get_session(region)
            iam = session.client('iam')

            policies = []
            paginator = iam.get_paginator('list_policies')
            for page in paginator.paginate(Scope='Local'):  # Only customer-managed
                policies.extend(page['Policies'])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': 'global',
                'service': 'IAM',
                'resource_type': 'policies',
                'total_count': len(policies)
            }]
        except Exception as e:
            logger.error(f"Error counting IAM policies: {e}")
            return []

    def count_kms_keys(self, region: str) -> List[Dict[str, Any]]:
        """Count KMS customer-managed keys."""
        try:
            session = self.get_session(region)
            kms = session.client('kms')

            keys = []
            paginator = kms.get_paginator('list_keys')
            for page in paginator.paginate():
                keys.extend(page['Keys'])

            # Filter to only customer-managed keys
            customer_keys = []
            for key in keys:
                try:
                    key_metadata = kms.describe_key(KeyId=key['KeyId'])
                    if key_metadata['KeyMetadata']['KeyManager'] == 'CUSTOMER':
                        customer_keys.append(key)
                except:
                    pass

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'KMS',
                'resource_type': 'customer_keys',
                'total_count': len(customer_keys)
            }]
        except Exception as e:
            logger.error(f"Error counting KMS keys in {region}: {e}")
            return []

    def count_secrets(self, region: str) -> List[Dict[str, Any]]:
        """Count Secrets Manager secrets."""
        try:
            session = self.get_session(region)
            secretsmanager = session.client('secretsmanager')

            secrets = []
            paginator = secretsmanager.get_paginator('list_secrets')
            for page in paginator.paginate():
                secrets.extend(page['SecretList'])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'SecretsManager',
                'resource_type': 'secrets',
                'total_count': len(secrets)
            }]
        except Exception as e:
            logger.error(f"Error counting secrets in {region}: {e}")
            return []

    # Management & Governance
    def count_cloudwatch_alarms(self, region: str) -> List[Dict[str, Any]]:
        """Count CloudWatch alarms."""
        try:
            session = self.get_session(region)
            cloudwatch = session.client('cloudwatch')

            alarms = []
            paginator = cloudwatch.get_paginator('describe_alarms')
            for page in paginator.paginate():
                alarms.extend(page['MetricAlarms'])

            # Count by state
            state_counts = {}
            for alarm in alarms:
                state = alarm['StateValue']
                state_counts[state] = state_counts.get(state, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'CloudWatch',
                'resource_type': 'alarms',
                'total_count': len(alarms),
                'state_breakdown': state_counts
            }]
        except Exception as e:
            logger.error(f"Error counting CloudWatch alarms in {region}: {e}")
            return []

    def count_cloudformation_stacks(self, region: str) -> List[Dict[str, Any]]:
        """Count CloudFormation stacks."""
        try:
            session = self.get_session(region)
            cfn = session.client('cloudformation')

            response = cfn.list_stacks(
                StackStatusFilter=[
                    'CREATE_IN_PROGRESS', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS',
                    'ROLLBACK_COMPLETE', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE',
                    'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE'
                ]
            )
            stacks = response['StackSummaries']

            status_counts = {}
            for stack in stacks:
                status = stack['StackStatus']
                status_counts[status] = status_counts.get(status, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'CloudFormation',
                'resource_type': 'stacks',
                'total_count': len(stacks),
                'status_breakdown': status_counts
            }]
        except Exception as e:
            logger.error(f"Error counting CloudFormation stacks in {region}: {e}")
            return []

    def count_config_rules(self, region: str) -> List[Dict[str, Any]]:
        """Count AWS Config rules."""
        try:
            session = self.get_session(region)
            config = session.client('config')

            response = config.describe_config_rules()
            rules = response['ConfigRules']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'Config',
                'resource_type': 'rules',
                'total_count': len(rules)
            }]
        except Exception as e:
            logger.error(f"Error counting Config rules in {region}: {e}")
            return []

    # Content Delivery (CloudFront is global)
    def count_cloudfront_distributions(self, region: str) -> List[Dict[str, Any]]:
        """Count CloudFront distributions (global service)."""
        if region != 'us-east-1':  # Only count in one region
            return []

        try:
            session = self.get_session(region)
            cloudfront = session.client('cloudfront')

            response = cloudfront.list_distributions()
            distributions = response.get('DistributionList', {}).get('Items', [])

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': 'global',
                'service': 'CloudFront',
                'resource_type': 'distributions',
                'total_count': len(distributions)
            }]
        except Exception as e:
            logger.error(f"Error counting CloudFront distributions: {e}")
            return []

    # Machine Learning
    def count_sagemaker_endpoints(self, region: str) -> List[Dict[str, Any]]:
        """Count SageMaker endpoints."""
        try:
            session = self.get_session(region)
            sagemaker = session.client('sagemaker')

            response = sagemaker.list_endpoints()
            endpoints = response['Endpoints']

            status_counts = {}
            for endpoint in endpoints:
                status = endpoint['EndpointStatus']
                status_counts[status] = status_counts.get(status, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'SageMaker',
                'resource_type': 'endpoints',
                'total_count': len(endpoints),
                'status_breakdown': status_counts
            }]
        except Exception as e:
            logger.error(f"Error counting SageMaker endpoints in {region}: {e}")
            return []

    def count_sagemaker_models(self, region: str) -> List[Dict[str, Any]]:
        """Count SageMaker models."""
        try:
            session = self.get_session(region)
            sagemaker = session.client('sagemaker')

            response = sagemaker.list_models()
            models = response['Models']

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'aws',
                'account': self.account_name,
                'region': region,
                'service': 'SageMaker',
                'resource_type': 'models',
                'total_count': len(models)
            }]
        except Exception as e:
            logger.error(f"Error counting SageMaker models in {region}: {e}")
            return []


__all__ = ['AWSInventoryCollector']
