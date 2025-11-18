"""
Azure Resource Inventory Collector - Comprehensive Resource Counting

Counts all resources across ALL Azure services in multiple subscriptions.
Focuses on resource inventory, not performance metrics.
"""

import logging
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.redis import RedisManagementClient
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.servicebus import ServiceBusManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cdn import CdnManagementClient
from azure.mgmt.dns import DnsManagementClient
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class AzureInventoryCollector:
    """Collects resource counts from Azure subscriptions across all services."""

    def __init__(self, subscription_config: Dict[str, Any]):
        """Initialize Azure inventory collector."""
        self.subscription_name = subscription_config['name']
        self.subscription_id = subscription_config['subscription_id']
        self.tenant_id = subscription_config['tenant_id']
        self.client_id = subscription_config['client_id']
        self.client_secret = subscription_config['client_secret']

        # Create credential
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        logger.info(f"Initialized Azure inventory collector for: {self.subscription_name}")

    def collect_all_inventory(self) -> List[Dict[str, Any]]:
        """Collect resource counts from all Azure services."""
        all_inventory = []

        try:
            logger.info(f"Collecting inventory from {self.subscription_name}")

            # Compute services
            all_inventory.extend(self.count_virtual_machines())
            all_inventory.extend(self.count_vm_scale_sets())
            all_inventory.extend(self.count_availability_sets())
            all_inventory.extend(self.count_disks())
            all_inventory.extend(self.count_snapshots())
            all_inventory.extend(self.count_images())

            # Container services
            all_inventory.extend(self.count_aks_clusters())
            all_inventory.extend(self.count_container_instances())
            all_inventory.extend(self.count_container_registries())

            # Database services
            all_inventory.extend(self.count_sql_servers())
            all_inventory.extend(self.count_sql_databases())
            all_inventory.extend(self.count_mysql_servers())
            all_inventory.extend(self.count_postgresql_servers())
            all_inventory.extend(self.count_cosmosdb_accounts())
            all_inventory.extend(self.count_redis_caches())

            # Storage services
            all_inventory.extend(self.count_storage_accounts())
            all_inventory.extend(self.count_file_shares())
            all_inventory.extend(self.count_blob_containers())

            # Networking services
            all_inventory.extend(self.count_virtual_networks())
            all_inventory.extend(self.count_subnets())
            all_inventory.extend(self.count_network_security_groups())
            all_inventory.extend(self.count_load_balancers())
            all_inventory.extend(self.count_application_gateways())
            all_inventory.extend(self.count_public_ip_addresses())
            all_inventory.extend(self.count_network_interfaces())
            all_inventory.extend(self.count_vpn_gateways())
            all_inventory.extend(self.count_virtual_network_gateways())
            all_inventory.extend(self.count_route_tables())

            # Serverless services
            all_inventory.extend(self.count_function_apps())
            all_inventory.extend(self.count_app_service_plans())
            all_inventory.extend(self.count_web_apps())
            all_inventory.extend(self.count_logic_apps())

            # Analytics & Big Data
            all_inventory.extend(self.count_synapse_workspaces())
            all_inventory.extend(self.count_databricks_workspaces())
            all_inventory.extend(self.count_data_factories())
            all_inventory.extend(self.count_stream_analytics_jobs())

            # Application Integration
            all_inventory.extend(self.count_eventhub_namespaces())
            all_inventory.extend(self.count_servicebus_namespaces())

            # Developer Tools
            all_inventory.extend(self.count_devops_organizations())

            # Security & Identity
            all_inventory.extend(self.count_key_vaults())
            all_inventory.extend(self.count_managed_identities())

            # Management & Monitoring
            all_inventory.extend(self.count_log_analytics_workspaces())
            all_inventory.extend(self.count_action_groups())
            all_inventory.extend(self.count_alert_rules())

            # Content Delivery
            all_inventory.extend(self.count_cdn_profiles())
            all_inventory.extend(self.count_dns_zones())
            all_inventory.extend(self.count_traffic_manager_profiles())

        except Exception as e:
            logger.error(f"Error collecting Azure inventory: {e}")

        return all_inventory

    # Compute Services
    def count_virtual_machines(self) -> List[Dict[str, Any]]:
        """Count Virtual Machines."""
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            vms = list(compute_client.virtual_machines.list_all())

            status_counts = {}
            size_counts = {}

            for vm in vms:
                vm_size = vm.hardware_profile.vm_size
                size_counts[vm_size] = size_counts.get(vm_size, 0) + 1

                # Get power state
                instance_view = compute_client.virtual_machines.instance_view(
                    vm.id.split('/')[4],  # Resource group
                    vm.name
                )
                for status in instance_view.statuses:
                    if status.code.startswith('PowerState/'):
                        power_state = status.code.split('/')[-1]
                        status_counts[power_state] = status_counts.get(power_state, 0) + 1
                        break

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualMachines',
                'resource_type': 'vms',
                'total_count': len(vms),
                'running_count': status_counts.get('running', 0),
                'stopped_count': status_counts.get('deallocated', 0) + status_counts.get('stopped', 0),
                'status_breakdown': status_counts,
                'size_breakdown': size_counts
            }]

        except Exception as e:
            logger.error(f"Error counting VMs: {e}")
            return []

    def count_vm_scale_sets(self) -> List[Dict[str, Any]]:
        """Count VM Scale Sets."""
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            vmss_list = list(compute_client.virtual_machine_scale_sets.list_all())

            total_capacity = sum(vmss.sku.capacity for vmss in vmss_list if vmss.sku.capacity)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualMachines',
                'resource_type': 'vm_scale_sets',
                'total_count': len(vmss_list),
                'total_capacity': total_capacity
            }]

        except Exception as e:
            logger.error(f"Error counting VM scale sets: {e}")
            return []

    def count_availability_sets(self) -> List[Dict[str, Any]]:
        """Count Availability Sets."""
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            av_sets = list(compute_client.availability_sets.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualMachines',
                'resource_type': 'availability_sets',
                'total_count': len(av_sets)
            }]

        except Exception as e:
            logger.error(f"Error counting availability sets: {e}")
            return []

    def count_disks(self) -> List[Dict[str, Any]]:
        """Count Managed Disks."""
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            disks = list(compute_client.disks.list())

            total_size_gb = sum(disk.disk_size_gb for disk in disks if disk.disk_size_gb)
            type_counts = {}

            for disk in disks:
                disk_type = str(disk.sku.name) if disk.sku else 'unknown'
                type_counts[disk_type] = type_counts.get(disk_type, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualMachines',
                'resource_type': 'disks',
                'total_count': len(disks),
                'total_size_gb': total_size_gb,
                'type_breakdown': type_counts
            }]

        except Exception as e:
            logger.error(f"Error counting disks: {e}")
            return []

    def count_snapshots(self) -> List[Dict[str, Any]]:
        """Count Disk Snapshots."""
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            snapshots = list(compute_client.snapshots.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualMachines',
                'resource_type': 'snapshots',
                'total_count': len(snapshots)
            }]

        except Exception as e:
            logger.error(f"Error counting snapshots: {e}")
            return []

    def count_images(self) -> List[Dict[str, Any]]:
        """Count Custom Images."""
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            images = list(compute_client.images.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualMachines',
                'resource_type': 'images',
                'total_count': len(images)
            }]

        except Exception as e:
            logger.error(f"Error counting images: {e}")
            return []

    # Container Services
    def count_aks_clusters(self) -> List[Dict[str, Any]]:
        """Count AKS clusters."""
        try:
            aks_client = ContainerServiceClient(self.credential, self.subscription_id)
            clusters = list(aks_client.managed_clusters.list())

            total_nodes = 0
            for cluster in clusters:
                if cluster.agent_pool_profiles:
                    total_nodes += sum(pool.count for pool in cluster.agent_pool_profiles if pool.count)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'AKS',
                'resource_type': 'clusters',
                'total_count': len(clusters),
                'total_nodes': total_nodes
            }]

        except Exception as e:
            logger.error(f"Error counting AKS clusters: {e}")
            return []

    def count_container_instances(self) -> List[Dict[str, Any]]:
        """Count Azure Container Instances."""
        try:
            from azure.mgmt.containerinstance import ContainerInstanceManagementClient

            aci_client = ContainerInstanceManagementClient(self.credential, self.subscription_id)
            container_groups = list(aci_client.container_groups.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'ContainerInstances',
                'resource_type': 'container_groups',
                'total_count': len(container_groups)
            }]

        except Exception as e:
            logger.error(f"Error counting container instances: {e}")
            return []

    def count_container_registries(self) -> List[Dict[str, Any]]:
        """Count Azure Container Registries."""
        try:
            acr_client = ContainerRegistryManagementClient(self.credential, self.subscription_id)
            registries = list(acr_client.registries.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'ContainerRegistry',
                'resource_type': 'registries',
                'total_count': len(registries)
            }]

        except Exception as e:
            logger.error(f"Error counting container registries: {e}")
            return []

    # Database Services
    def count_sql_servers(self) -> List[Dict[str, Any]]:
        """Count SQL Servers."""
        try:
            sql_client = SqlManagementClient(self.credential, self.subscription_id)
            servers = list(sql_client.servers.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'SQLDatabase',
                'resource_type': 'servers',
                'total_count': len(servers)
            }]

        except Exception as e:
            logger.error(f"Error counting SQL servers: {e}")
            return []

    def count_sql_databases(self) -> List[Dict[str, Any]]:
        """Count SQL Databases across all servers."""
        try:
            sql_client = SqlManagementClient(self.credential, self.subscription_id)
            servers = list(sql_client.servers.list())

            total_databases = 0
            edition_counts = {}

            for server in servers:
                resource_group = server.id.split('/')[4]
                databases = list(sql_client.databases.list_by_server(resource_group, server.name))

                for db in databases:
                    if db.name.lower() != 'master':  # Exclude master database
                        total_databases += 1
                        edition = str(db.sku.tier) if db.sku else 'unknown'
                        edition_counts[edition] = edition_counts.get(edition, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'SQLDatabase',
                'resource_type': 'databases',
                'total_count': total_databases,
                'edition_breakdown': edition_counts
            }]

        except Exception as e:
            logger.error(f"Error counting SQL databases: {e}")
            return []

    def count_mysql_servers(self) -> List[Dict[str, Any]]:
        """Count Azure Database for MySQL servers."""
        try:
            from azure.mgmt.rdbms import mysql

            mysql_client = mysql.MySQLManagementClient(self.credential, self.subscription_id)
            servers = list(mysql_client.servers.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'MySQL',
                'resource_type': 'servers',
                'total_count': len(servers)
            }]

        except Exception as e:
            logger.error(f"Error counting MySQL servers: {e}")
            return []

    def count_postgresql_servers(self) -> List[Dict[str, Any]]:
        """Count Azure Database for PostgreSQL servers."""
        try:
            from azure.mgmt.rdbms import postgresql

            pg_client = postgresql.PostgreSQLManagementClient(self.credential, self.subscription_id)
            servers = list(pg_client.servers.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'PostgreSQL',
                'resource_type': 'servers',
                'total_count': len(servers)
            }]

        except Exception as e:
            logger.error(f"Error counting PostgreSQL servers: {e}")
            return []

    def count_cosmosdb_accounts(self) -> List[Dict[str, Any]]:
        """Count Cosmos DB accounts."""
        try:
            cosmos_client = CosmosDBManagementClient(self.credential, self.subscription_id)
            accounts = list(cosmos_client.database_accounts.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'CosmosDB',
                'resource_type': 'accounts',
                'total_count': len(accounts)
            }]

        except Exception as e:
            logger.error(f"Error counting Cosmos DB accounts: {e}")
            return []

    def count_redis_caches(self) -> List[Dict[str, Any]]:
        """Count Azure Cache for Redis instances."""
        try:
            redis_client = RedisManagementClient(self.credential, self.subscription_id)
            caches = list(redis_client.redis.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'RedisCache',
                'resource_type': 'caches',
                'total_count': len(caches)
            }]

        except Exception as e:
            logger.error(f"Error counting Redis caches: {e}")
            return []

    # Storage Services
    def count_storage_accounts(self) -> List[Dict[str, Any]]:
        """Count Storage Accounts."""
        try:
            storage_client = StorageManagementClient(self.credential, self.subscription_id)
            storage_accounts = list(storage_client.storage_accounts.list())

            kind_counts = {}
            for account in storage_accounts:
                kind = str(account.kind) if account.kind else 'unknown'
                kind_counts[kind] = kind_counts.get(kind, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Storage',
                'resource_type': 'storage_accounts',
                'total_count': len(storage_accounts),
                'kind_breakdown': kind_counts
            }]

        except Exception as e:
            logger.error(f"Error counting storage accounts: {e}")
            return []

    def count_file_shares(self) -> List[Dict[str, Any]]:
        """Count File Shares across all storage accounts."""
        try:
            storage_client = StorageManagementClient(self.credential, self.subscription_id)
            storage_accounts = list(storage_client.storage_accounts.list())

            total_shares = 0
            for account in storage_accounts:
                try:
                    resource_group = account.id.split('/')[4]
                    shares = list(storage_client.file_shares.list(resource_group, account.name))
                    total_shares += len(shares)
                except:
                    pass

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Storage',
                'resource_type': 'file_shares',
                'total_count': total_shares
            }]

        except Exception as e:
            logger.error(f"Error counting file shares: {e}")
            return []

    def count_blob_containers(self) -> List[Dict[str, Any]]:
        """Count Blob Containers across all storage accounts."""
        try:
            storage_client = StorageManagementClient(self.credential, self.subscription_id)
            storage_accounts = list(storage_client.storage_accounts.list())

            total_containers = 0
            for account in storage_accounts:
                try:
                    resource_group = account.id.split('/')[4]
                    containers = list(storage_client.blob_containers.list(resource_group, account.name))
                    total_containers += len(containers)
                except:
                    pass

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Storage',
                'resource_type': 'blob_containers',
                'total_count': total_containers
            }]

        except Exception as e:
            logger.error(f"Error counting blob containers: {e}")
            return []

    # Networking Services
    def count_virtual_networks(self) -> List[Dict[str, Any]]:
        """Count Virtual Networks."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            vnets = list(network_client.virtual_networks.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'vnets',
                'total_count': len(vnets)
            }]

        except Exception as e:
            logger.error(f"Error counting virtual networks: {e}")
            return []

    def count_subnets(self) -> List[Dict[str, Any]]:
        """Count Subnets across all VNets."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            vnets = list(network_client.virtual_networks.list_all())

            total_subnets = 0
            for vnet in vnets:
                if vnet.subnets:
                    total_subnets += len(vnet.subnets)

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'subnets',
                'total_count': total_subnets
            }]

        except Exception as e:
            logger.error(f"Error counting subnets: {e}")
            return []

    def count_network_security_groups(self) -> List[Dict[str, Any]]:
        """Count Network Security Groups."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            nsgs = list(network_client.network_security_groups.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'nsgs',
                'total_count': len(nsgs)
            }]

        except Exception as e:
            logger.error(f"Error counting NSGs: {e}")
            return []

    def count_load_balancers(self) -> List[Dict[str, Any]]:
        """Count Load Balancers."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            load_balancers = list(network_client.load_balancers.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'LoadBalancer',
                'resource_type': 'load_balancers',
                'total_count': len(load_balancers)
            }]

        except Exception as e:
            logger.error(f"Error counting load balancers: {e}")
            return []

    def count_application_gateways(self) -> List[Dict[str, Any]]:
        """Count Application Gateways."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            app_gateways = list(network_client.application_gateways.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'ApplicationGateway',
                'resource_type': 'app_gateways',
                'total_count': len(app_gateways)
            }]

        except Exception as e:
            logger.error(f"Error counting application gateways: {e}")
            return []

    def count_public_ip_addresses(self) -> List[Dict[str, Any]]:
        """Count Public IP Addresses."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            public_ips = list(network_client.public_ip_addresses.list_all())

            allocated = sum(1 for ip in public_ips if ip.ip_address)
            unallocated = len(public_ips) - allocated

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'public_ips',
                'total_count': len(public_ips),
                'allocated_count': allocated,
                'unallocated_count': unallocated
            }]

        except Exception as e:
            logger.error(f"Error counting public IPs: {e}")
            return []

    def count_network_interfaces(self) -> List[Dict[str, Any]]:
        """Count Network Interfaces."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            nics = list(network_client.network_interfaces.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'network_interfaces',
                'total_count': len(nics)
            }]

        except Exception as e:
            logger.error(f"Error counting network interfaces: {e}")
            return []

    def count_vpn_gateways(self) -> List[Dict[str, Any]]:
        """Count VPN Gateways."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            vpn_gateways = list(network_client.vpn_gateways.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'vpn_gateways',
                'total_count': len(vpn_gateways)
            }]

        except Exception as e:
            logger.error(f"Error counting VPN gateways: {e}")
            return []

    def count_virtual_network_gateways(self) -> List[Dict[str, Any]]:
        """Count Virtual Network Gateways."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            vnet_gateways = list(network_client.virtual_network_gateways.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'vnet_gateways',
                'total_count': len(vnet_gateways)
            }]

        except Exception as e:
            logger.error(f"Error counting virtual network gateways: {e}")
            return []

    def count_route_tables(self) -> List[Dict[str, Any]]:
        """Count Route Tables."""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            route_tables = list(network_client.route_tables.list_all())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'VirtualNetwork',
                'resource_type': 'route_tables',
                'total_count': len(route_tables)
            }]

        except Exception as e:
            logger.error(f"Error counting route tables: {e}")
            return []

    # Serverless Services
    def count_function_apps(self) -> List[Dict[str, Any]]:
        """Count Azure Function Apps."""
        try:
            web_client = WebSiteManagementClient(self.credential, self.subscription_id)
            all_apps = list(web_client.web_apps.list())

            function_apps = [app for app in all_apps if app.kind and 'functionapp' in app.kind.lower()]

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'FunctionApps',
                'resource_type': 'function_apps',
                'total_count': len(function_apps)
            }]

        except Exception as e:
            logger.error(f"Error counting function apps: {e}")
            return []

    def count_app_service_plans(self) -> List[Dict[str, Any]]:
        """Count App Service Plans."""
        try:
            web_client = WebSiteManagementClient(self.credential, self.subscription_id)
            plans = list(web_client.app_service_plans.list())

            tier_counts = {}
            for plan in plans:
                tier = str(plan.sku.tier) if plan.sku else 'unknown'
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'AppService',
                'resource_type': 'app_service_plans',
                'total_count': len(plans),
                'tier_breakdown': tier_counts
            }]

        except Exception as e:
            logger.error(f"Error counting app service plans: {e}")
            return []

    def count_web_apps(self) -> List[Dict[str, Any]]:
        """Count Web Apps."""
        try:
            web_client = WebSiteManagementClient(self.credential, self.subscription_id)
            all_apps = list(web_client.web_apps.list())

            web_apps = [app for app in all_apps if not (app.kind and 'functionapp' in app.kind.lower())]

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'AppService',
                'resource_type': 'web_apps',
                'total_count': len(web_apps)
            }]

        except Exception as e:
            logger.error(f"Error counting web apps: {e}")
            return []

    def count_logic_apps(self) -> List[Dict[str, Any]]:
        """Count Logic Apps."""
        try:
            from azure.mgmt.logic import LogicManagementClient

            logic_client = LogicManagementClient(self.credential, self.subscription_id)
            workflows = list(logic_client.workflows.list_by_subscription())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'LogicApps',
                'resource_type': 'workflows',
                'total_count': len(workflows)
            }]

        except Exception as e:
            logger.error(f"Error counting logic apps: {e}")
            return []

    # Analytics & Big Data
    def count_synapse_workspaces(self) -> List[Dict[str, Any]]:
        """Count Synapse Analytics workspaces."""
        try:
            from azure.mgmt.synapse import SynapseManagementClient

            synapse_client = SynapseManagementClient(self.credential, self.subscription_id)
            workspaces = list(synapse_client.workspaces.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Synapse',
                'resource_type': 'workspaces',
                'total_count': len(workspaces)
            }]

        except Exception as e:
            logger.error(f"Error counting Synapse workspaces: {e}")
            return []

    def count_databricks_workspaces(self) -> List[Dict[str, Any]]:
        """Count Databricks workspaces."""
        try:
            from azure.mgmt.databricks import AzureDatabricksManagementClient

            databricks_client = AzureDatabricksManagementClient(self.credential, self.subscription_id)
            workspaces = list(databricks_client.workspaces.list_by_subscription())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Databricks',
                'resource_type': 'workspaces',
                'total_count': len(workspaces)
            }]

        except Exception as e:
            logger.error(f"Error counting Databricks workspaces: {e}")
            return []

    def count_data_factories(self) -> List[Dict[str, Any]]:
        """Count Data Factories."""
        try:
            from azure.mgmt.datafactory import DataFactoryManagementClient

            adf_client = DataFactoryManagementClient(self.credential, self.subscription_id)
            factories = list(adf_client.factories.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'DataFactory',
                'resource_type': 'factories',
                'total_count': len(factories)
            }]

        except Exception as e:
            logger.error(f"Error counting data factories: {e}")
            return []

    def count_stream_analytics_jobs(self) -> List[Dict[str, Any]]:
        """Count Stream Analytics jobs."""
        try:
            from azure.mgmt.streamanalytics import StreamAnalyticsManagementClient

            asa_client = StreamAnalyticsManagementClient(self.credential, self.subscription_id)
            jobs = list(asa_client.streaming_jobs.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'StreamAnalytics',
                'resource_type': 'jobs',
                'total_count': len(jobs)
            }]

        except Exception as e:
            logger.error(f"Error counting Stream Analytics jobs: {e}")
            return []

    # Application Integration
    def count_eventhub_namespaces(self) -> List[Dict[str, Any]]:
        """Count Event Hub namespaces."""
        try:
            eventhub_client = EventHubManagementClient(self.credential, self.subscription_id)
            namespaces = list(eventhub_client.namespaces.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'EventHub',
                'resource_type': 'namespaces',
                'total_count': len(namespaces)
            }]

        except Exception as e:
            logger.error(f"Error counting Event Hub namespaces: {e}")
            return []

    def count_servicebus_namespaces(self) -> List[Dict[str, Any]]:
        """Count Service Bus namespaces."""
        try:
            servicebus_client = ServiceBusManagementClient(self.credential, self.subscription_id)
            namespaces = list(servicebus_client.namespaces.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'ServiceBus',
                'resource_type': 'namespaces',
                'total_count': len(namespaces)
            }]

        except Exception as e:
            logger.error(f"Error counting Service Bus namespaces: {e}")
            return []

    # Developer Tools
    def count_devops_organizations(self) -> List[Dict[str, Any]]:
        """Count Azure DevOps organizations (placeholder - requires special API)."""
        try:
            # Azure DevOps uses a different API and authentication
            # This is a placeholder
            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'global',
                'service': 'DevOps',
                'resource_type': 'organizations',
                'total_count': 0
            }]

        except Exception as e:
            logger.error(f"Error counting DevOps organizations: {e}")
            return []

    # Security & Identity
    def count_key_vaults(self) -> List[Dict[str, Any]]:
        """Count Key Vaults."""
        try:
            kv_client = KeyVaultManagementClient(self.credential, self.subscription_id)
            vaults = list(kv_client.vaults.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'KeyVault',
                'resource_type': 'vaults',
                'total_count': len(vaults)
            }]

        except Exception as e:
            logger.error(f"Error counting key vaults: {e}")
            return []

    def count_managed_identities(self) -> List[Dict[str, Any]]:
        """Count Managed Identities."""
        try:
            from azure.mgmt.msi import ManagedServiceIdentityClient

            msi_client = ManagedServiceIdentityClient(self.credential, self.subscription_id)
            identities = list(msi_client.user_assigned_identities.list_by_subscription())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'ManagedIdentity',
                'resource_type': 'user_assigned_identities',
                'total_count': len(identities)
            }]

        except Exception as e:
            logger.error(f"Error counting managed identities: {e}")
            return []

    # Management & Monitoring
    def count_log_analytics_workspaces(self) -> List[Dict[str, Any]]:
        """Count Log Analytics workspaces."""
        try:
            from azure.mgmt.loganalytics import LogAnalyticsManagementClient

            la_client = LogAnalyticsManagementClient(self.credential, self.subscription_id)
            workspaces = list(la_client.workspaces.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'LogAnalytics',
                'resource_type': 'workspaces',
                'total_count': len(workspaces)
            }]

        except Exception as e:
            logger.error(f"Error counting Log Analytics workspaces: {e}")
            return []

    def count_action_groups(self) -> List[Dict[str, Any]]:
        """Count Action Groups."""
        try:
            monitor_client = MonitorManagementClient(self.credential, self.subscription_id)
            action_groups = list(monitor_client.action_groups.list_by_subscription_id())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Monitor',
                'resource_type': 'action_groups',
                'total_count': len(action_groups)
            }]

        except Exception as e:
            logger.error(f"Error counting action groups: {e}")
            return []

    def count_alert_rules(self) -> List[Dict[str, Any]]:
        """Count Alert Rules."""
        try:
            monitor_client = MonitorManagementClient(self.credential, self.subscription_id)
            alert_rules = list(monitor_client.metric_alerts.list_by_subscription())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'Monitor',
                'resource_type': 'alert_rules',
                'total_count': len(alert_rules)
            }]

        except Exception as e:
            logger.error(f"Error counting alert rules: {e}")
            return []

    # Content Delivery
    def count_cdn_profiles(self) -> List[Dict[str, Any]]:
        """Count CDN profiles."""
        try:
            cdn_client = CdnManagementClient(self.credential, self.subscription_id)
            profiles = list(cdn_client.profiles.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'CDN',
                'resource_type': 'profiles',
                'total_count': len(profiles)
            }]

        except Exception as e:
            logger.error(f"Error counting CDN profiles: {e}")
            return []

    def count_dns_zones(self) -> List[Dict[str, Any]]:
        """Count DNS zones."""
        try:
            dns_client = DnsManagementClient(self.credential, self.subscription_id)
            zones = list(dns_client.zones.list())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'all-regions',
                'service': 'DNS',
                'resource_type': 'zones',
                'total_count': len(zones)
            }]

        except Exception as e:
            logger.error(f"Error counting DNS zones: {e}")
            return []

    def count_traffic_manager_profiles(self) -> List[Dict[str, Any]]:
        """Count Traffic Manager profiles."""
        try:
            from azure.mgmt.trafficmanager import TrafficManagerManagementClient

            tm_client = TrafficManagerManagementClient(self.credential, self.subscription_id)
            profiles = list(tm_client.profiles.list_by_subscription())

            return [{
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cloud_provider': 'azure',
                'account': self.subscription_name,
                'subscription_id': self.subscription_id,
                'region': 'global',
                'service': 'TrafficManager',
                'resource_type': 'profiles',
                'total_count': len(profiles)
            }]

        except Exception as e:
            logger.error(f"Error counting Traffic Manager profiles: {e}")
            return []


__all__ = ['AzureInventoryCollector']
