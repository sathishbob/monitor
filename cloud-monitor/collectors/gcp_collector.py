"""
GCP Resource Collector - Multi-Project Cloud Monitoring

Collects usage metrics from GCP resources across multiple projects including
Compute Engine, Cloud SQL, Cloud Storage, Cloud Functions, GKE, and more.
"""

import logging
from google.cloud import compute_v1, storage, monitoring_v3, sql_v1
from google.cloud import container_v1
from google.oauth2 import service_account
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GCPCollector:
    """Collects resource usage metrics from GCP projects."""

    def __init__(self, project_config: Dict[str, Any]):
        """Initialize GCP collector for a specific project."""
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

        logger.info(f"Initialized GCP collector for project: {self.project_name}")

    def collect_all_metrics(self) -> List[Dict[str, Any]]:
        """Collect all metrics from GCP project."""
        all_metrics = []

        try:
            all_metrics.extend(self.collect_compute_metrics())
            all_metrics.extend(self.collect_storage_metrics())
            all_metrics.extend(self.collect_cloudsql_metrics())
            all_metrics.extend(self.collect_functions_metrics())
            all_metrics.extend(self.collect_gke_metrics())
            all_metrics.extend(self.collect_loadbalancer_metrics())
        except Exception as e:
            logger.error(f"Error collecting GCP metrics: {e}")

        return all_metrics

    def collect_compute_metrics(self) -> List[Dict[str, Any]]:
        """Collect Compute Engine VM metrics."""
        metrics = []

        try:
            # Initialize Compute Engine client
            instances_client = compute_v1.InstancesClient(credentials=self.credentials)
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # List all zones
            zones_client = compute_v1.ZonesClient(credentials=self.credentials)
            zones_request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = zones_client.list(request=zones_request)

            for zone in zones:
                zone_name = zone.name

                # List instances in zone
                request = compute_v1.ListInstancesRequest(
                    project=self.project_id,
                    zone=zone_name
                )

                instances = instances_client.list(request=request)

                for instance in instances:
                    # Get CPU utilization from Cloud Monitoring
                    cpu_metric = self._get_monitoring_metric(
                        monitoring_client,
                        'compute.googleapis.com/instance/cpu/utilization',
                        f'instance_id = "{instance.id}"'
                    )

                    # Get memory usage
                    memory_metric = self._get_monitoring_metric(
                        monitoring_client,
                        'compute.googleapis.com/instance/memory/percent_used',
                        f'instance_id = "{instance.id}"'
                    )

                    # Get disk usage
                    disk_metric = self._get_monitoring_metric(
                        monitoring_client,
                        'compute.googleapis.com/instance/disk/read_bytes_count',
                        f'instance_id = "{instance.id}"'
                    )

                    metric_data = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'cloud_provider': 'gcp',
                        'account': self.project_name,
                        'region': zone_name,
                        'service': 'ComputeEngine',
                        'resource_type': 'instance',
                        'resource_id': instance.name,
                        'instance_id': str(instance.id),
                        'machine_type': instance.machine_type.split('/')[-1],
                        'status': instance.status,
                        'cpu_utilization': cpu_metric * 100 if cpu_metric else None,
                        'memory_utilization': memory_metric if memory_metric else None,
                        'disk_read_bytes': disk_metric,
                        'labels': dict(instance.labels) if instance.labels else {}
                    }

                    metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} Compute Engine metrics for {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting Compute Engine metrics: {e}")

        return metrics

    def collect_storage_metrics(self) -> List[Dict[str, Any]]:
        """Collect Cloud Storage bucket metrics."""
        metrics = []

        try:
            # Initialize Storage client
            storage_client = storage.Client(
                project=self.project_id,
                credentials=self.credentials
            )
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # List all buckets
            buckets = storage_client.list_buckets()

            for bucket in buckets:
                # Get total bytes metric
                size_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'storage.googleapis.com/storage/total_bytes',
                    f'bucket_name = "{bucket.name}"'
                )

                # Get object count
                object_count_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'storage.googleapis.com/storage/object_count',
                    f'bucket_name = "{bucket.name}"'
                )

                # Count objects manually as fallback
                object_count = 0
                try:
                    blobs = bucket.list_blobs(max_results=1)
                    # Get approximate count from API
                    object_count = sum(1 for _ in blobs)
                except:
                    pass

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'gcp',
                    'account': self.project_name,
                    'region': bucket.location,
                    'service': 'CloudStorage',
                    'resource_type': 'bucket',
                    'resource_id': bucket.name,
                    'storage_class': bucket.storage_class,
                    'size_bytes': size_metric if size_metric else 0,
                    'size_gb': (size_metric / (1024**3)) if size_metric else 0,
                    'object_count': object_count_metric if object_count_metric else object_count,
                    'versioning_enabled': bucket.versioning_enabled
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} Cloud Storage metrics for {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting Cloud Storage metrics: {e}")

        return metrics

    def collect_cloudsql_metrics(self) -> List[Dict[str, Any]]:
        """Collect Cloud SQL database metrics."""
        metrics = []

        try:
            # Initialize Cloud SQL client
            sql_client = sql_v1.SqlInstancesServiceClient(credentials=self.credentials)
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # List all SQL instances
            request = sql_v1.SqlInstancesListRequest(project=self.project_id)
            instances = sql_client.list(request=request)

            for instance in instances.items:
                # Get CPU utilization
                cpu_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudsql.googleapis.com/database/cpu/utilization',
                    f'database_id = "{self.project_id}:{instance.name}"'
                )

                # Get memory utilization
                memory_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudsql.googleapis.com/database/memory/utilization',
                    f'database_id = "{self.project_id}:{instance.name}"'
                )

                # Get disk utilization
                disk_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudsql.googleapis.com/database/disk/utilization',
                    f'database_id = "{self.project_id}:{instance.name}"'
                )

                # Get connection count
                connections_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudsql.googleapis.com/database/postgresql/num_backends',
                    f'database_id = "{self.project_id}:{instance.name}"'
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'gcp',
                    'account': self.project_name,
                    'region': instance.region,
                    'service': 'CloudSQL',
                    'resource_type': 'database',
                    'resource_id': instance.name,
                    'database_version': instance.database_version,
                    'tier': instance.settings.tier if instance.settings else None,
                    'state': instance.state,
                    'cpu_utilization': cpu_metric * 100 if cpu_metric else None,
                    'memory_utilization': memory_metric * 100 if memory_metric else None,
                    'disk_utilization': disk_metric * 100 if disk_metric else None,
                    'connection_count': connections_metric,
                    'storage_gb': instance.settings.data_disk_size_gb if instance.settings else None
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} Cloud SQL metrics for {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting Cloud SQL metrics: {e}")

        return metrics

    def collect_functions_metrics(self) -> List[Dict[str, Any]]:
        """Collect Cloud Functions metrics."""
        metrics = []

        try:
            from google.cloud import functions_v1

            # Initialize Cloud Functions client
            functions_client = functions_v1.CloudFunctionsServiceClient(credentials=self.credentials)
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # List all functions
            parent = f"projects/{self.project_id}/locations/-"
            request = functions_v1.ListFunctionsRequest(parent=parent)
            functions = functions_client.list_functions(request=request)

            for function in functions:
                function_name = function.name.split('/')[-1]

                # Get invocation count
                invocations_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudfunctions.googleapis.com/function/execution_count',
                    f'function_name = "{function_name}"',
                    aggregation='sum'
                )

                # Get error count
                errors_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudfunctions.googleapis.com/function/user_error_count',
                    f'function_name = "{function_name}"',
                    aggregation='sum'
                )

                # Get execution time
                execution_time_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'cloudfunctions.googleapis.com/function/execution_times',
                    f'function_name = "{function_name}"',
                    aggregation='mean'
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'gcp',
                    'account': self.project_name,
                    'region': function.name.split('/')[3],
                    'service': 'CloudFunctions',
                    'resource_type': 'function',
                    'resource_id': function_name,
                    'runtime': function.runtime,
                    'memory_mb': function.available_memory_mb,
                    'timeout_seconds': function.timeout.seconds if function.timeout else None,
                    'status': function.status,
                    'invocations': invocations_metric or 0,
                    'errors': errors_metric or 0,
                    'error_rate': (errors_metric / invocations_metric * 100) if invocations_metric and errors_metric else 0,
                    'avg_execution_time_ms': execution_time_metric
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} Cloud Functions metrics for {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting Cloud Functions metrics: {e}")

        return metrics

    def collect_gke_metrics(self) -> List[Dict[str, Any]]:
        """Collect Google Kubernetes Engine (GKE) cluster metrics."""
        metrics = []

        try:
            # Initialize GKE client
            cluster_client = container_v1.ClusterManagerClient(credentials=self.credentials)
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # List all clusters
            parent = f"projects/{self.project_id}/locations/-"
            request = container_v1.ListClustersRequest(parent=parent)
            response = cluster_client.list_clusters(request=request)

            for cluster in response.clusters:
                # Get node pool info
                node_count = sum(pool.initial_node_count for pool in cluster.node_pools)

                # Get container CPU usage
                cpu_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'kubernetes.io/container/cpu/core_usage_time',
                    f'cluster_name = "{cluster.name}"'
                )

                # Get memory usage
                memory_metric = self._get_monitoring_metric(
                    monitoring_client,
                    'kubernetes.io/container/memory/used_bytes',
                    f'cluster_name = "{cluster.name}"'
                )

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cloud_provider': 'gcp',
                    'account': self.project_name,
                    'region': cluster.location,
                    'service': 'GKE',
                    'resource_type': 'cluster',
                    'resource_id': cluster.name,
                    'status': cluster.status,
                    'node_count': node_count,
                    'current_node_version': cluster.current_node_version,
                    'cpu_usage': cpu_metric,
                    'memory_used_bytes': memory_metric,
                    'memory_used_gb': (memory_metric / (1024**3)) if memory_metric else 0,
                    'node_pools': len(cluster.node_pools)
                }

                metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} GKE metrics for {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting GKE metrics: {e}")

        return metrics

    def collect_loadbalancer_metrics(self) -> List[Dict[str, Any]]:
        """Collect Cloud Load Balancing metrics."""
        metrics = []

        try:
            # Initialize Compute client for load balancers
            forwarding_rules_client = compute_v1.ForwardingRulesClient(credentials=self.credentials)
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # List global forwarding rules (load balancers)
            request = compute_v1.AggregatedListForwardingRulesRequest(
                project=self.project_id
            )
            forwarding_rules = forwarding_rules_client.aggregated_list(request=request)

            for region, rules_scoped_list in forwarding_rules:
                if not rules_scoped_list.forwarding_rules:
                    continue

                for rule in rules_scoped_list.forwarding_rules:
                    # Get request count
                    request_count_metric = self._get_monitoring_metric(
                        monitoring_client,
                        'loadbalancing.googleapis.com/https/request_count',
                        f'forwarding_rule_name = "{rule.name}"',
                        aggregation='sum'
                    )

                    # Get latency
                    latency_metric = self._get_monitoring_metric(
                        monitoring_client,
                        'loadbalancing.googleapis.com/https/total_latencies',
                        f'forwarding_rule_name = "{rule.name}"',
                        aggregation='mean'
                    )

                    metric_data = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'cloud_provider': 'gcp',
                        'account': self.project_name,
                        'region': region.split('/')[-1] if '/' in region else 'global',
                        'service': 'CloudLoadBalancing',
                        'resource_type': 'load_balancer',
                        'resource_id': rule.name,
                        'ip_address': rule.ip_address,
                        'port_range': rule.port_range,
                        'request_count': request_count_metric or 0,
                        'avg_latency_ms': latency_metric
                    }

                    metrics.append(metric_data)

            logger.info(f"Collected {len(metrics)} Load Balancing metrics for {self.project_name}")

        except Exception as e:
            logger.error(f"Error collecting Load Balancing metrics: {e}")

        return metrics

    def _get_monitoring_metric(self, monitoring_client, metric_type: str,
                               resource_filter: str, aggregation: str = 'mean',
                               minutes: int = 10) -> Optional[float]:
        """Get metric value from Cloud Monitoring."""
        try:
            # Define time interval
            now = datetime.now(timezone.utc)
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": int(now.timestamp())},
                "start_time": {"seconds": int((now - timedelta(minutes=minutes)).timestamp())}
            })

            # Build aggregation
            if aggregation == 'mean':
                agg = monitoring_v3.Aggregation({
                    "alignment_period": {"seconds": 60},
                    "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                })
            elif aggregation == 'sum':
                agg = monitoring_v3.Aggregation({
                    "alignment_period": {"seconds": 60},
                    "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
                })
            else:
                agg = None

            # Build request
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": f"projects/{self.project_id}",
                "filter": f'metric.type = "{metric_type}" AND {resource_filter}',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            })

            if agg:
                request.aggregation = agg

            # Execute request
            results = monitoring_client.list_time_series(request=request)

            # Get latest value
            for result in results:
                if result.points:
                    return result.points[0].value.double_value

            return None

        except Exception as e:
            logger.debug(f"Error getting monitoring metric {metric_type}: {e}")
            return None


__all__ = ['GCPCollector']
