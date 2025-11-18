"""
GCP Resource Inventory Collector - Comprehensive Resource Counting

Counts all resources across ALL GCP services in multiple projects.
Focuses on resource inventory, not performance metrics.
"""

import logging
from google.cloud import compute_v1, storage, sql_v1, container_v1
from google.cloud import functions_v1, pubsub_v1, bigquery, dns
from google.cloud import resourcemanager_v3, kms_v1, secretmanager_v1
from google.oauth2 import service_account
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class GCPInventoryCollector:
    """Collects resource counts from GCP projects across all services."""

    def __init__(self, project_config: Dict[str, Any]):
        """Initialize GCP inventory collector."""
        self.project_name = project_config['name']
        self.project_id = project_config['project_id']
        self.credentials_file = project_config.get('credentials_file')

        # Initialize credentials
        if self.credentials_file:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file
            )
        else:
            self.credentials = None

        logger.info(f"Initialized GCP inventory collector for: {self.project_name}")

    def collect_all_inventory(self) -> List[Dict[str, Any]]:
        """Collect resource counts from all GCP services."""
        all_inventory = []

        try:
            logger.info(f"Collecting inventory from {self.project_name}")

            # Compute services
            all_inventory.extend(self.count_compute_instances())
            all_inventory.extend(self.count_instance_templates())
            all_inventory.extend(self.count_instance_groups())
            all_inventory.extend(self.count_disks())
            all_inventory.extend(self.count_snapshots())
            all_inventory.extend(self.count_images())

            # Container services
            all_inventory.extend(self.count_gke_clusters())
            all_inventory.extend(self.count_gke_node_pools())

            # Database services
            all_inventory.extend(self.count_cloudsql_instances())
            all_inventory.extend(self.count_bigtable_instances())
            all_inventory.extend(self.count_spanner_instances())

            # Storage services
            all_inventory.extend(self.count_storage_buckets())
            all_inventory.extend(self.count_filestore_instances())

            # Networking services
            all_inventory.extend(self.count_vpc_networks())
            all_inventory.extend(self.count_subnets())
            all_inventory.extend(self.count_firewall_rules())
            all_inventory.extend(self.count_load_balancers())
            all_inventory.extend(self.count_target_pools())
            all_inventory.extend(self.count_vpn_gateways())
            all_inventory.extend(self.count_cloud_routers())
            all_inventory.extend(self.count_cloud_nat())

            # Serverless services
            all_inventory.extend(self.count_cloud_functions())
            all_inventory.extend(self.count_cloud_run_services())
            all_inventory.extend(self.count_app_engine_services())

            # Analytics & Big Data
            all_inventory.extend(self.count_bigquery_datasets())
            all_inventory.extend(self.count_bigquery_tables())
            all_inventory.extend(self.count_dataflow_jobs())
            all_inventory.extend(self.count_dataproc_clusters())
            all_inventory.extend(self.count_composer_environments())

            # Application Integration
            all_inventory.extend(self.count_pubsub_topics())
            all_inventory.extend(self.count_pubsub_subscriptions())

            # Developer Tools
            all_inventory.extend(self.count_cloud_build_triggers())
            all_inventory.extend(self.count_artifact_registry_repos())
            all_inventory.extend(self.count_source_repositories())

            # Security & Identity
            all_inventory.extend(self.count_service_accounts())
            all_inventory.extend(self.count_kms_keys())
            all_inventory.extend(self.count_secrets())

            # Management & Monitoring
            all_inventory.extend(self.count_logging_sinks())
            all_inventory.extend(self.count_monitoring_alert_policies())

            # Content Delivery
            all_inventory.extend(self.count_dns_zones())
            all_inventory.extend(self.count_cdn_backends())

        except Exception as e:
            logger.error(f"Error collecting GCP inventory: {e}")

        return all_inventory

    # Compute Services
    def count_compute_instances(self) -> List[Dict[str, Any]]:
        """Count Compute Engine instances."""
        try:
            instances_client = compute_v1.InstancesClient(credentials=self.credentials)
            zones_client = compute_v1.ZonesClient(credentials=self.credentials)

            # Get all zones
            zones_request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = zones_client.list(request=zones_request)

            total_count = 0
            status_counts = {}
            machine_type_counts = {}

            for zone in zones:
                zone_name = zone.name
                request = compute_v1.ListInstancesRequest(
                    project=self.project_id,
                    zone=zone_name
                )
                instances = instances_client.list(request=request)

                for instance in instances:
                    total_count += 1
                    status = instance.status
                    machine_type = instance.machine_type.split('/')[-1]

                    status_counts[status] = status_counts.get(status, 0) + 1
                    machine_type_counts[machine_type] = machine_type_counts.get(machine_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-zones',
                'service': 'ComputeEngine',
                'resource_type': 'instances',
                'total_count': total_count,
                'running_count': status_counts.get('RUNNING', 0),
                'stopped_count': status_counts.get('TERMINATED', 0),
                'status_breakdown': status_counts,
                'machine_type_breakdown': machine_type_counts
            }]

        except Exception as e:
            logger.error(f"Error counting Compute instances: {e}")
            return []

    def count_instance_templates(self) -> List[Dict[str, Any]]:
        """Count instance templates."""
        try:
            templates_client = compute_v1.InstanceTemplatesClient(credentials=self.credentials)
            request = compute_v1.ListInstanceTemplatesRequest(project=self.project_id)
            templates = templates_client.list(request=request)

            template_count = sum(1 for _ in templates)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'ComputeEngine',
                'resource_type': 'instance_templates',
                'total_count': template_count
            }]

        except Exception as e:
            logger.error(f"Error counting instance templates: {e}")
            return []

    def count_instance_groups(self) -> List[Dict[str, Any]]:
        """Count managed instance groups."""
        try:
            groups_client = compute_v1.InstanceGroupManagersClient(credentials=self.credentials)
            zones_client = compute_v1.ZonesClient(credentials=self.credentials)

            zones_request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = zones_client.list(request=zones_request)

            total_count = 0
            for zone in zones:
                zone_name = zone.name
                request = compute_v1.ListInstanceGroupManagersRequest(
                    project=self.project_id,
                    zone=zone_name
                )
                groups = groups_client.list(request=request)
                total_count += sum(1 for _ in groups)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-zones',
                'service': 'ComputeEngine',
                'resource_type': 'instance_groups',
                'total_count': total_count
            }]

        except Exception as e:
            logger.error(f"Error counting instance groups: {e}")
            return []

    def count_disks(self) -> List[Dict[str, Any]]:
        """Count persistent disks."""
        try:
            disks_client = compute_v1.DisksClient(credentials=self.credentials)
            zones_client = compute_v1.ZonesClient(credentials=self.credentials)

            zones_request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = zones_client.list(request=zones_request)

            total_count = 0
            total_size_gb = 0
            type_counts = {}

            for zone in zones:
                zone_name = zone.name
                request = compute_v1.ListDisksRequest(
                    project=self.project_id,
                    zone=zone_name
                )
                disks = disks_client.list(request=request)

                for disk in disks:
                    total_count += 1
                    total_size_gb += disk.size_gb
                    disk_type = disk.type_.split('/')[-1] if disk.type_ else 'unknown'
                    type_counts[disk_type] = type_counts.get(disk_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-zones',
                'service': 'ComputeEngine',
                'resource_type': 'disks',
                'total_count': total_count,
                'total_size_gb': total_size_gb,
                'type_breakdown': type_counts
            }]

        except Exception as e:
            logger.error(f"Error counting disks: {e}")
            return []

    def count_snapshots(self) -> List[Dict[str, Any]]:
        """Count disk snapshots."""
        try:
            snapshots_client = compute_v1.SnapshotsClient(credentials=self.credentials)
            request = compute_v1.ListSnapshotsRequest(project=self.project_id)
            snapshots = snapshots_client.list(request=request)

            snapshot_count = sum(1 for _ in snapshots)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'ComputeEngine',
                'resource_type': 'snapshots',
                'total_count': snapshot_count
            }]

        except Exception as e:
            logger.error(f"Error counting snapshots: {e}")
            return []

    def count_images(self) -> List[Dict[str, Any]]:
        """Count custom images."""
        try:
            images_client = compute_v1.ImagesClient(credentials=self.credentials)
            request = compute_v1.ListImagesRequest(project=self.project_id)
            images = images_client.list(request=request)

            image_count = sum(1 for _ in images)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'ComputeEngine',
                'resource_type': 'images',
                'total_count': image_count
            }]

        except Exception as e:
            logger.error(f"Error counting images: {e}")
            return []

    # Container Services
    def count_gke_clusters(self) -> List[Dict[str, Any]]:
        """Count GKE clusters."""
        try:
            cluster_client = container_v1.ClusterManagerClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = container_v1.ListClustersRequest(parent=parent)
            response = cluster_client.list_clusters(request=request)

            status_counts = {}
            for cluster in response.clusters:
                status = str(cluster.status)
                status_counts[status] = status_counts.get(status, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-zones',
                'service': 'GKE',
                'resource_type': 'clusters',
                'total_count': len(response.clusters),
                'status_breakdown': status_counts
            }]

        except Exception as e:
            logger.error(f"Error counting GKE clusters: {e}")
            return []

    def count_gke_node_pools(self) -> List[Dict[str, Any]]:
        """Count GKE node pools across all clusters."""
        try:
            cluster_client = container_v1.ClusterManagerClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = container_v1.ListClustersRequest(parent=parent)
            response = cluster_client.list_clusters(request=request)

            total_node_pools = 0
            total_nodes = 0

            for cluster in response.clusters:
                total_node_pools += len(cluster.node_pools)
                total_nodes += sum(pool.initial_node_count for pool in cluster.node_pools)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-zones',
                'service': 'GKE',
                'resource_type': 'node_pools',
                'total_count': total_node_pools,
                'total_nodes': total_nodes
            }]

        except Exception as e:
            logger.error(f"Error counting GKE node pools: {e}")
            return []

    # Database Services
    def count_cloudsql_instances(self) -> List[Dict[str, Any]]:
        """Count Cloud SQL instances."""
        try:
            sql_client = sql_v1.SqlInstancesServiceClient(credentials=self.credentials)
            request = sql_v1.SqlInstancesListRequest(project=self.project_id)
            instances = sql_client.list(request=request)

            total_count = 0
            db_version_counts = {}
            tier_counts = {}

            for instance in instances.items:
                total_count += 1
                db_version = instance.database_version
                tier = instance.settings.tier if instance.settings else 'unknown'

                db_version_counts[db_version] = db_version_counts.get(db_version, 0) + 1
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'CloudSQL',
                'resource_type': 'instances',
                'total_count': total_count,
                'db_version_breakdown': db_version_counts,
                'tier_breakdown': tier_counts
            }]

        except Exception as e:
            logger.error(f"Error counting Cloud SQL instances: {e}")
            return []

    def count_bigtable_instances(self) -> List[Dict[str, Any]]:
        """Count Bigtable instances."""
        try:
            from google.cloud import bigtable

            client = bigtable.Client(project=self.project_id, credentials=self.credentials)
            instances = client.list_instances()

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'Bigtable',
                'resource_type': 'instances',
                'total_count': len(instances[0])
            }]

        except Exception as e:
            logger.error(f"Error counting Bigtable instances: {e}")
            return []

    def count_spanner_instances(self) -> List[Dict[str, Any]]:
        """Count Spanner instances."""
        try:
            from google.cloud import spanner

            client = spanner.Client(project=self.project_id, credentials=self.credentials)
            instances = list(client.list_instances())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'Spanner',
                'resource_type': 'instances',
                'total_count': len(instances)
            }]

        except Exception as e:
            logger.error(f"Error counting Spanner instances: {e}")
            return []

    # Storage Services
    def count_storage_buckets(self) -> List[Dict[str, Any]]:
        """Count Cloud Storage buckets."""
        try:
            storage_client = storage.Client(
                project=self.project_id,
                credentials=self.credentials
            )
            buckets = list(storage_client.list_buckets())

            storage_class_counts = {}
            for bucket in buckets:
                storage_class = bucket.storage_class
                storage_class_counts[storage_class] = storage_class_counts.get(storage_class, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'CloudStorage',
                'resource_type': 'buckets',
                'total_count': len(buckets),
                'storage_class_breakdown': storage_class_counts
            }]

        except Exception as e:
            logger.error(f"Error counting storage buckets: {e}")
            return []

    def count_filestore_instances(self) -> List[Dict[str, Any]]:
        """Count Filestore instances."""
        try:
            from google.cloud import filestore_v1

            client = filestore_v1.CloudFilestoreManagerClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = filestore_v1.ListInstancesRequest(parent=parent)
            instances = client.list_instances(request=request)

            instance_count = sum(1 for _ in instances)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'Filestore',
                'resource_type': 'instances',
                'total_count': instance_count
            }]

        except Exception as e:
            logger.error(f"Error counting Filestore instances: {e}")
            return []

    # Networking Services
    def count_vpc_networks(self) -> List[Dict[str, Any]]:
        """Count VPC networks."""
        try:
            networks_client = compute_v1.NetworksClient(credentials=self.credentials)
            request = compute_v1.ListNetworksRequest(project=self.project_id)
            networks = networks_client.list(request=request)

            network_count = sum(1 for _ in networks)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'VPC',
                'resource_type': 'networks',
                'total_count': network_count
            }]

        except Exception as e:
            logger.error(f"Error counting VPC networks: {e}")
            return []

    def count_subnets(self) -> List[Dict[str, Any]]:
        """Count subnets."""
        try:
            subnets_client = compute_v1.SubnetworksClient(credentials=self.credentials)
            request = compute_v1.AggregatedListSubnetworksRequest(project=self.project_id)
            subnets = subnets_client.aggregated_list(request=request)

            total_count = 0
            for region, subnets_scoped_list in subnets:
                if subnets_scoped_list.subnetworks:
                    total_count += len(subnets_scoped_list.subnetworks)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'VPC',
                'resource_type': 'subnets',
                'total_count': total_count
            }]

        except Exception as e:
            logger.error(f"Error counting subnets: {e}")
            return []

    def count_firewall_rules(self) -> List[Dict[str, Any]]:
        """Count firewall rules."""
        try:
            firewalls_client = compute_v1.FirewallsClient(credentials=self.credentials)
            request = compute_v1.ListFirewallsRequest(project=self.project_id)
            firewalls = firewalls_client.list(request=request)

            firewall_count = sum(1 for _ in firewalls)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'VPC',
                'resource_type': 'firewall_rules',
                'total_count': firewall_count
            }]

        except Exception as e:
            logger.error(f"Error counting firewall rules: {e}")
            return []

    def count_load_balancers(self) -> List[Dict[str, Any]]:
        """Count load balancers."""
        try:
            forwarding_rules_client = compute_v1.ForwardingRulesClient(credentials=self.credentials)
            request = compute_v1.AggregatedListForwardingRulesRequest(project=self.project_id)
            forwarding_rules = forwarding_rules_client.aggregated_list(request=request)

            total_count = 0
            for region, rules_scoped_list in forwarding_rules:
                if rules_scoped_list.forwarding_rules:
                    total_count += len(rules_scoped_list.forwarding_rules)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'LoadBalancing',
                'resource_type': 'forwarding_rules',
                'total_count': total_count
            }]

        except Exception as e:
            logger.error(f"Error counting load balancers: {e}")
            return []

    def count_target_pools(self) -> List[Dict[str, Any]]:
        """Count target pools."""
        try:
            target_pools_client = compute_v1.TargetPoolsClient(credentials=self.credentials)
            request = compute_v1.AggregatedListTargetPoolsRequest(project=self.project_id)
            target_pools = target_pools_client.aggregated_list(request=request)

            total_count = 0
            for region, pools_scoped_list in target_pools:
                if pools_scoped_list.target_pools:
                    total_count += len(pools_scoped_list.target_pools)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'LoadBalancing',
                'resource_type': 'target_pools',
                'total_count': total_count
            }]

        except Exception as e:
            logger.error(f"Error counting target pools: {e}")
            return []

    def count_vpn_gateways(self) -> List[Dict[str, Any]]:
        """Count VPN gateways."""
        try:
            vpn_gateways_client = compute_v1.VpnGatewaysClient(credentials=self.credentials)
            request = compute_v1.AggregatedListVpnGatewaysRequest(project=self.project_id)
            vpn_gateways = vpn_gateways_client.aggregated_list(request=request)

            total_count = 0
            for region, gateways_scoped_list in vpn_gateways:
                if gateways_scoped_list.vpn_gateways:
                    total_count += len(gateways_scoped_list.vpn_gateways)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'VPC',
                'resource_type': 'vpn_gateways',
                'total_count': total_count
            }]

        except Exception as e:
            logger.error(f"Error counting VPN gateways: {e}")
            return []

    def count_cloud_routers(self) -> List[Dict[str, Any]]:
        """Count Cloud Routers."""
        try:
            routers_client = compute_v1.RoutersClient(credentials=self.credentials)
            request = compute_v1.AggregatedListRoutersRequest(project=self.project_id)
            routers = routers_client.aggregated_list(request=request)

            total_count = 0
            for region, routers_scoped_list in routers:
                if routers_scoped_list.routers:
                    total_count += len(routers_scoped_list.routers)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'VPC',
                'resource_type': 'routers',
                'total_count': total_count
            }]

        except Exception as e:
            logger.error(f"Error counting Cloud Routers: {e}")
            return []

    def count_cloud_nat(self) -> List[Dict[str, Any]]:
        """Count Cloud NAT configurations."""
        try:
            routers_client = compute_v1.RoutersClient(credentials=self.credentials)
            request = compute_v1.AggregatedListRoutersRequest(project=self.project_id)
            routers = routers_client.aggregated_list(request=request)

            total_nat_count = 0
            for region, routers_scoped_list in routers:
                if routers_scoped_list.routers:
                    for router in routers_scoped_list.routers:
                        if router.nats:
                            total_nat_count += len(router.nats)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'VPC',
                'resource_type': 'cloud_nat',
                'total_count': total_nat_count
            }]

        except Exception as e:
            logger.error(f"Error counting Cloud NAT: {e}")
            return []

    # Serverless Services
    def count_cloud_functions(self) -> List[Dict[str, Any]]:
        """Count Cloud Functions."""
        try:
            functions_client = functions_v1.CloudFunctionsServiceClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = functions_v1.ListFunctionsRequest(parent=parent)
            functions = functions_client.list_functions(request=request)

            total_count = 0
            runtime_counts = {}

            for function in functions:
                total_count += 1
                runtime = function.runtime
                runtime_counts[runtime] = runtime_counts.get(runtime, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'CloudFunctions',
                'resource_type': 'functions',
                'total_count': total_count,
                'runtime_breakdown': runtime_counts
            }]

        except Exception as e:
            logger.error(f"Error counting Cloud Functions: {e}")
            return []

    def count_cloud_run_services(self) -> List[Dict[str, Any]]:
        """Count Cloud Run services."""
        try:
            from google.cloud import run_v2

            client = run_v2.ServicesClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = run_v2.ListServicesRequest(parent=parent)
            services = client.list_services(request=request)

            service_count = sum(1 for _ in services)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'CloudRun',
                'resource_type': 'services',
                'total_count': service_count
            }]

        except Exception as e:
            logger.error(f"Error counting Cloud Run services: {e}")
            return []

    def count_app_engine_services(self) -> List[Dict[str, Any]]:
        """Count App Engine services."""
        try:
            from google.cloud import appengine_admin_v1

            client = appengine_admin_v1.ServicesClient(credentials=self.credentials)
            parent = f"apps/{self.project_id}"
            request = appengine_admin_v1.ListServicesRequest(parent=parent)
            services = client.list_services(request=request)

            service_count = sum(1 for _ in services)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'AppEngine',
                'resource_type': 'services',
                'total_count': service_count
            }]

        except Exception as e:
            logger.error(f"Error counting App Engine services: {e}")
            return []

    # Analytics & Big Data
    def count_bigquery_datasets(self) -> List[Dict[str, Any]]:
        """Count BigQuery datasets."""
        try:
            bq_client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            datasets = list(bq_client.list_datasets())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'BigQuery',
                'resource_type': 'datasets',
                'total_count': len(datasets)
            }]

        except Exception as e:
            logger.error(f"Error counting BigQuery datasets: {e}")
            return []

    def count_bigquery_tables(self) -> List[Dict[str, Any]]:
        """Count BigQuery tables across all datasets."""
        try:
            bq_client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            datasets = list(bq_client.list_datasets())

            total_tables = 0
            for dataset in datasets:
                tables = list(bq_client.list_tables(dataset.dataset_id))
                total_tables += len(tables)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'BigQuery',
                'resource_type': 'tables',
                'total_count': total_tables
            }]

        except Exception as e:
            logger.error(f"Error counting BigQuery tables: {e}")
            return []

    def count_dataflow_jobs(self) -> List[Dict[str, Any]]:
        """Count active Dataflow jobs."""
        try:
            from google.cloud import dataflow_v1beta3

            client = dataflow_v1beta3.JobsV1Beta3Client(credentials=self.credentials)
            request = dataflow_v1beta3.ListJobsRequest(
                project_id=self.project_id,
                location='us-central1'
            )
            jobs = client.list_jobs(request=request)

            job_count = sum(1 for _ in jobs)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'Dataflow',
                'resource_type': 'jobs',
                'total_count': job_count
            }]

        except Exception as e:
            logger.error(f"Error counting Dataflow jobs: {e}")
            return []

    def count_dataproc_clusters(self) -> List[Dict[str, Any]]:
        """Count Dataproc clusters."""
        try:
            from google.cloud import dataproc_v1

            client = dataproc_v1.ClusterControllerClient(credentials=self.credentials, client_options={
                'api_endpoint': 'us-central1-dataproc.googleapis.com:443'
            })
            request = dataproc_v1.ListClustersRequest(
                project_id=self.project_id,
                region='global'
            )
            clusters = client.list_clusters(request=request)

            cluster_count = sum(1 for _ in clusters)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'Dataproc',
                'resource_type': 'clusters',
                'total_count': cluster_count
            }]

        except Exception as e:
            logger.error(f"Error counting Dataproc clusters: {e}")
            return []

    def count_composer_environments(self) -> List[Dict[str, Any]]:
        """Count Cloud Composer environments."""
        try:
            from google.cloud.orchestration.airflow import service_v1

            client = service_v1.EnvironmentsClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = service_v1.ListEnvironmentsRequest(parent=parent)
            environments = client.list_environments(request=request)

            env_count = sum(1 for _ in environments)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'Composer',
                'resource_type': 'environments',
                'total_count': env_count
            }]

        except Exception as e:
            logger.error(f"Error counting Composer environments: {e}")
            return []

    # Application Integration
    def count_pubsub_topics(self) -> List[Dict[str, Any]]:
        """Count Pub/Sub topics."""
        try:
            publisher_client = pubsub_v1.PublisherClient(credentials=self.credentials)
            project_path = f"projects/{self.project_id}"
            topics = publisher_client.list_topics(request={"project": project_path})

            topic_count = sum(1 for _ in topics)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'PubSub',
                'resource_type': 'topics',
                'total_count': topic_count
            }]

        except Exception as e:
            logger.error(f"Error counting Pub/Sub topics: {e}")
            return []

    def count_pubsub_subscriptions(self) -> List[Dict[str, Any]]:
        """Count Pub/Sub subscriptions."""
        try:
            subscriber_client = pubsub_v1.SubscriberClient(credentials=self.credentials)
            project_path = f"projects/{self.project_id}"
            subscriptions = subscriber_client.list_subscriptions(request={"project": project_path})

            subscription_count = sum(1 for _ in subscriptions)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'PubSub',
                'resource_type': 'subscriptions',
                'total_count': subscription_count
            }]

        except Exception as e:
            logger.error(f"Error counting Pub/Sub subscriptions: {e}")
            return []

    # Developer Tools
    def count_cloud_build_triggers(self) -> List[Dict[str, Any]]:
        """Count Cloud Build triggers."""
        try:
            from google.cloud.devtools import cloudbuild_v1

            client = cloudbuild_v1.CloudBuildClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/global"
            request = cloudbuild_v1.ListBuildTriggersRequest(parent=parent, project_id=self.project_id)
            triggers = client.list_build_triggers(request=request)

            trigger_count = sum(1 for _ in triggers)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'CloudBuild',
                'resource_type': 'triggers',
                'total_count': trigger_count
            }]

        except Exception as e:
            logger.error(f"Error counting Cloud Build triggers: {e}")
            return []

    def count_artifact_registry_repos(self) -> List[Dict[str, Any]]:
        """Count Artifact Registry repositories."""
        try:
            from google.cloud import artifactregistry_v1

            client = artifactregistry_v1.ArtifactRegistryClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"
            request = artifactregistry_v1.ListRepositoriesRequest(parent=parent)
            repositories = client.list_repositories(request=request)

            repo_count = sum(1 for _ in repositories)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'ArtifactRegistry',
                'resource_type': 'repositories',
                'total_count': repo_count
            }]

        except Exception as e:
            logger.error(f"Error counting Artifact Registry repos: {e}")
            return []

    def count_source_repositories(self) -> List[Dict[str, Any]]:
        """Count Cloud Source Repositories."""
        try:
            from google.cloud import sourcerepo_v1

            client = sourcerepo_v1.SourceRepoClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}"
            request = sourcerepo_v1.ListReposRequest(name=parent)
            repos = client.list_repos(request=request)

            repo_count = sum(1 for _ in repos)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'SourceRepositories',
                'resource_type': 'repositories',
                'total_count': repo_count
            }]

        except Exception as e:
            logger.error(f"Error counting Source Repositories: {e}")
            return []

    # Security & Identity
    def count_service_accounts(self) -> List[Dict[str, Any]]:
        """Count service accounts."""
        try:
            from google.cloud import iam_admin_v1

            client = iam_admin_v1.IAMClient(credentials=self.credentials)
            request = iam_admin_v1.ListServiceAccountsRequest(
                name=f"projects/{self.project_id}"
            )
            service_accounts = client.list_service_accounts(request=request)

            sa_count = sum(1 for _ in service_accounts)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'IAM',
                'resource_type': 'service_accounts',
                'total_count': sa_count
            }]

        except Exception as e:
            logger.error(f"Error counting service accounts: {e}")
            return []

    def count_kms_keys(self) -> List[Dict[str, Any]]:
        """Count KMS keys."""
        try:
            kms_client = kms_v1.KeyManagementServiceClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}/locations/-"

            # This is simplified - in reality you'd iterate through locations
            total_keys = 0
            try:
                for location in ['global', 'us', 'us-central1', 'us-east1']:
                    parent_loc = f"projects/{self.project_id}/locations/{location}"
                    keyrings = kms_client.list_key_rings(parent=parent_loc)
                    for keyring in keyrings:
                        keys = kms_client.list_crypto_keys(parent=keyring.name)
                        total_keys += sum(1 for _ in keys)
            except:
                pass

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'all-regions',
                'service': 'KMS',
                'resource_type': 'keys',
                'total_count': total_keys
            }]

        except Exception as e:
            logger.error(f"Error counting KMS keys: {e}")
            return []

    def count_secrets(self) -> List[Dict[str, Any]]:
        """Count Secret Manager secrets."""
        try:
            secrets_client = secretmanager_v1.SecretManagerServiceClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}"
            request = secretmanager_v1.ListSecretsRequest(parent=parent)
            secrets = secrets_client.list_secrets(request=request)

            secret_count = sum(1 for _ in secrets)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'SecretManager',
                'resource_type': 'secrets',
                'total_count': secret_count
            }]

        except Exception as e:
            logger.error(f"Error counting secrets: {e}")
            return []

    # Management & Monitoring
    def count_logging_sinks(self) -> List[Dict[str, Any]]:
        """Count logging sinks."""
        try:
            from google.cloud import logging_v2

            client = logging_v2.ConfigServiceV2Client(credentials=self.credentials)
            parent = f"projects/{self.project_id}"
            request = logging_v2.ListSinksRequest(parent=parent)
            sinks = client.list_sinks(request=request)

            sink_count = sum(1 for _ in sinks)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'Logging',
                'resource_type': 'sinks',
                'total_count': sink_count
            }]

        except Exception as e:
            logger.error(f"Error counting logging sinks: {e}")
            return []

    def count_monitoring_alert_policies(self) -> List[Dict[str, Any]]:
        """Count monitoring alert policies."""
        try:
            from google.cloud import monitoring_v3

            client = monitoring_v3.AlertPolicyServiceClient(credentials=self.credentials)
            parent = f"projects/{self.project_id}"
            request = monitoring_v3.ListAlertPoliciesRequest(name=parent)
            policies = client.list_alert_policies(request=request)

            policy_count = sum(1 for _ in policies)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'Monitoring',
                'resource_type': 'alert_policies',
                'total_count': policy_count
            }]

        except Exception as e:
            logger.error(f"Error counting alert policies: {e}")
            return []

    # Content Delivery
    def count_dns_zones(self) -> List[Dict[str, Any]]:
        """Count Cloud DNS zones."""
        try:
            dns_client = dns.Client(project=self.project_id, credentials=self.credentials)
            zones = list(dns_client.list_zones())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'CloudDNS',
                'resource_type': 'zones',
                'total_count': len(zones)
            }]

        except Exception as e:
            logger.error(f"Error counting DNS zones: {e}")
            return []

    def count_cdn_backends(self) -> List[Dict[str, Any]]:
        """Count CDN backend services."""
        try:
            backend_services_client = compute_v1.BackendServicesClient(credentials=self.credentials)
            request = compute_v1.ListBackendServicesRequest(project=self.project_id)
            backend_services = backend_services_client.list(request=request)

            cdn_enabled_count = sum(1 for bs in backend_services if bs.enable_cdn)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'gcp',
                'account': self.project_name,
                'project_id': self.project_id,
                'region': 'global',
                'service': 'CloudCDN',
                'resource_type': 'cdn_backends',
                'total_count': cdn_enabled_count
            }]

        except Exception as e:
            logger.error(f"Error counting CDN backends: {e}")
            return []


__all__ = ['GCPInventoryCollector']
