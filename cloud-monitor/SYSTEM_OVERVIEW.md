# Cloud Resource Inventory Monitoring System - Complete Overview

## System Purpose

This system monitors **resource inventory** across AWS, GCP, and Azure - counting how many resources exist rather than measuring performance metrics.

### What Changed
- **OLD Approach**: Monitor CPU%, memory%, disk usage → Alert on high utilization
- **NEW Approach**: Count resources (instances, databases, buckets) → Alert on count thresholds

### Example Alerts
```
⚠️ ALERT: 52 EC2 instances running in us-east-1 (threshold: 50)
⚠️ ALERT: 150 S3 buckets in account production (threshold: 100)
⚠️ ALERT: 25 RDS databases in us-west-2 (threshold: 20)
⚠️ ALERT: Monthly cost $32,500 exceeds budget $30,000
```

---

## Complete Service Coverage

### AWS: 51 Services Fully Implemented
**Compute (7 services)**
- EC2 instances (with state/type breakdown)
- EBS volumes
- EC2 snapshots
- AMIs
- Key pairs
- Elastic IPs
- Auto Scaling Groups

**Container (4 services)**
- ECS clusters & services
- EKS clusters
- ECR repositories
- Fargate tasks

**Database (6 services)**
- RDS instances & clusters
- DynamoDB tables
- ElastiCache clusters
- Redshift clusters
- DocumentDB
- Neptune

**Storage (5 services)**
- S3 buckets (global)
- EFS filesystems
- FSx filesystems
- Glacier vaults
- Storage Gateway

**Networking (12 services)**
- VPCs
- Subnets
- Security Groups
- Load Balancers (ALB, NLB, CLB)
- Target Groups
- NAT Gateways
- Internet Gateways
- Route Tables
- Network ACLs
- VPC Endpoints
- Transit Gateway
- Direct Connect

**Serverless (4 services)**
- Lambda functions (with runtime breakdown)
- API Gateway (REST/HTTP/WebSocket)
- Step Functions
- EventBridge rules

**Analytics (5 services)**
- EMR clusters
- Kinesis streams
- Glue jobs/crawlers
- Athena workgroups
- QuickSight dashboards

**Integration (3 services)**
- SQS queues (FIFO/Standard)
- SNS topics
- EventBridge rules

**Developer Tools (5 services)**
- CodeCommit repositories
- CodeBuild projects
- CodePipeline pipelines
- CodeDeploy applications
- Cloud9 environments

**Security (6 services)**
- IAM users/roles/policies
- KMS keys
- Secrets Manager
- Certificate Manager
- WAF ACLs
- Security Hub

**Management (6 services)**
- CloudWatch alarms
- CloudFormation stacks
- Config rules
- Systems Manager
- CloudTrail trails
- Organizations

**Content Delivery (2 services)**
- CloudFront distributions
- Route 53 hosted zones

**Machine Learning (2 services)**
- SageMaker endpoints/models
- Rekognition collections

---

### GCP: 45+ Services Fully Implemented
**Compute (6 services)**
- Compute Engine instances
- Instance templates
- Instance groups
- Persistent disks
- Snapshots
- Images

**Container (2 services)**
- GKE clusters
- GKE node pools

**Database (3 services)**
- Cloud SQL instances
- Bigtable instances
- Spanner instances

**Storage (2 services)**
- Cloud Storage buckets
- Filestore instances

**Networking (8 services)**
- VPC networks
- Subnets
- Firewall rules
- Load balancers
- Target pools
- VPN gateways
- Cloud Routers
- Cloud NAT

**Serverless (3 services)**
- Cloud Functions
- Cloud Run services
- App Engine services

**Analytics (5 services)**
- BigQuery datasets & tables
- Dataflow jobs
- Dataproc clusters
- Composer environments
- Data Fusion

**Integration (2 services)**
- Pub/Sub topics
- Pub/Sub subscriptions

**Developer Tools (3 services)**
- Cloud Build triggers
- Artifact Registry repositories
- Source Repositories

**Security (3 services)**
- Service accounts
- KMS keys
- Secret Manager secrets

**Management (2 services)**
- Logging sinks
- Monitoring alert policies

**Content Delivery (2 services)**
- Cloud DNS zones
- Cloud CDN backends

---

### Azure: 48 Services Fully Implemented
**Compute (6 services)**
- Virtual Machines
- VM Scale Sets
- Availability Sets
- Managed Disks
- Snapshots
- Images

**Container (3 services)**
- AKS clusters
- Container Instances
- Container Registries

**Database (6 services)**
- SQL Servers & Databases
- MySQL servers
- PostgreSQL servers
- Cosmos DB accounts
- Redis caches
- Synapse workspaces

**Storage (3 services)**
- Storage Accounts
- File Shares
- Blob Containers

**Networking (10 services)**
- Virtual Networks
- Subnets
- Network Security Groups
- Load Balancers
- Application Gateways
- Public IP Addresses
- Network Interfaces
- VPN Gateways
- Virtual Network Gateways
- Route Tables

**Serverless (4 services)**
- Function Apps
- App Service Plans
- Web Apps
- Logic Apps

**Analytics (4 services)**
- Synapse workspaces
- Databricks workspaces
- Data Factories
- Stream Analytics jobs

**Integration (2 services)**
- Event Hub namespaces
- Service Bus namespaces

**Security (2 services)**
- Key Vaults
- Managed Identities

**Management (3 services)**
- Log Analytics workspaces
- Action Groups
- Alert Rules

**Content Delivery (3 services)**
- CDN profiles
- DNS zones
- Traffic Manager profiles

---

## Cost Tracking

### AWS Cost Explorer
- Daily costs (last 30 days)
- Monthly costs by service
- Regional cost breakdown
- Cost anomaly detection

### GCP Cloud Billing
- Monthly cost summary
- Service-level breakdown
- Requires BigQuery billing export

### Azure Cost Management
- Monthly cost summary
- Service-level breakdown
- Resource group breakdown
- Budget alerts

---

## Alert System

### Resource Count Alerts
```yaml
Alert Severity Levels:
- INFO: 0-20% over threshold
- WARNING: 20-50% over threshold
- CRITICAL: 50%+ over threshold

Example AWS Threshold:
  ec2_instances_per_region: 50
  → Alert at 51 (INFO), 61 (WARNING), 76+ (CRITICAL)

Example GCP Threshold:
  gke_clusters_total: 5
  → Alert at 6 (INFO), 7 (WARNING), 8+ (CRITICAL)
```

### Cost Budget Alerts
```yaml
Monthly Budget Example:
  monthly_budget_usd: 30000
  → INFO at $30,001
  → WARNING at $33,000 (10% over)
  → CRITICAL at $36,000 (20% over)

Daily Budget Example:
  daily_budget_usd: 1000
  → WARNING at $1,001
```

### Email Alerts
```
Subject: [WARNING] Cloud Resource Alert - resource_count

Alert Message:
EC2 instances count (52) exceeds threshold (50) in us-east-1
[Status: {'running': 52, 'stopped': 8}, Type: {'t2.micro': 30, 'm5.large': 15}]

Resource Details:
- Provider: aws
- Account: production
- Region: us-east-1
- Service: EC2
- Resource Type: instances

Metric Information:
- Current Value: 52
- Threshold: 50

Action Required:
Review and cleanup unused EC2 instances in this region.
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────┐
│                  Cloud Accounts                      │
│  AWS (prod, dev) | GCP (projects) | Azure (subs)   │
└────────────────┬────────────────────────────────────┘
                 │
                 │ Inventory Collectors Run Every 5 Minutes
                 │
    ┌────────────┴──────────────┬────────────────────┐
    │                           │                     │
┌───▼────────────┐  ┌──────────▼──────┐  ┌──────────▼───────┐
│ AWS Inventory  │  │ GCP Inventory   │  │ Azure Inventory  │
│ Collector      │  │ Collector       │  │ Collector        │
│ (51 services)  │  │ (45+ services)  │  │ (48 services)    │
└───┬────────────┘  └──────────┬──────┘  └──────────┬───────┘
    │                          │                     │
    │          Resource Count Data (JSON)            │
    │          {                                     │
    │            service: "EC2",                     │
    │            resource_type: "instances",         │
    │            total_count: 52,                    │
    │            running_count: 52,                  │
    │            region: "us-east-1"                 │
    │          }                                     │
    │                          │                     │
    └──────────────┬───────────┴─────────────────────┘
                   │
       ┌───────────▼──────────────┐
       │   Alert Manager          │
       │   (Check Thresholds)     │
       └───────────┬──────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼──────┐      ┌──────▼───────┐
   │   Email   │      │ Elasticsearch│
   │  Alerts   │      │   Storage    │
   └───────────┘      └──────┬───────┘
                             │
                     ┌───────▼────────┐
                     │ React Dashboard│
                     │ (Resource View)│
                     └────────────────┘
```

---

## Configuration Examples

### config.yaml Thresholds
```yaml
thresholds:
  aws:
    # Per-region thresholds
    ec2_instances_per_region: 50
    rds_instances_per_region: 20
    lambda_functions_per_region: 400

    # Global thresholds
    s3_buckets_total: 100
    iam_roles_total: 400

    # Cost thresholds
    monthly_budget_usd: 30000
    daily_budget_usd: 1000

  gcp:
    computeengine_instances_total: 50
    gke_clusters_total: 5
    cloudstorage_buckets_total: 100
    monthly_budget_usd: 30000

  azure:
    virtualmachines_vms_total: 50
    aks_clusters_total: 5
    storage_storage_accounts_total: 100
    monthly_budget_usd: 30000
```

---

## Elasticsearch Data Structure

### Resource Count Document
```json
{
  "timestamp": "2025-01-18T12:00:00Z",
  "cloud_provider": "aws",
  "account": "production",
  "region": "us-east-1",
  "service": "EC2",
  "resource_type": "instances",
  "total_count": 52,
  "running_count": 52,
  "stopped_count": 8,
  "state_breakdown": {
    "running": 52,
    "stopped": 8,
    "terminated": 0
  },
  "type_breakdown": {
    "t2.micro": 30,
    "m5.large": 15,
    "t3.medium": 7
  }
}
```

### Cost Document
```json
{
  "timestamp": "2025-01-18T12:00:00Z",
  "cloud_provider": "aws",
  "account": "production",
  "cost_type": "monthly_by_service",
  "month": "2025-01",
  "total_cost_usd": 28450.75,
  "currency": "USD",
  "service_breakdown": {
    "EC2": 12000.50,
    "RDS": 8500.25,
    "S3": 3200.00,
    "Lambda": 1500.00,
    "Data Transfer": 3250.00
  }
}
```

---

## Running the System

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start Elasticsearch
docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0

# Configure credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

### Start Monitoring
```bash
# Run once
python cloud_monitor.py --once

# Run continuously (5-minute intervals)
python cloud_monitor.py

# Start dashboard
cd dashboard
npm install
npm start
```

---

## Dashboard Features

### Resource Inventory View
- **Total Resources**: Count across all providers
- **Cloud Providers**: Number of accounts/projects/subscriptions
- **Services Monitored**: Total unique services
- **Active Alerts**: Current threshold violations

### Resource Distribution Charts
- Pie chart: Resources by cloud provider
- Bar chart: Resources by service type
- Table: Top resources by count

### Cost Overview
- Monthly spend by provider
- Service-level cost breakdown
- Budget vs. actual comparison
- Cost trends over time

### Alert Dashboard
- Active alerts sorted by severity
- Resource count violations
- Budget overruns
- Alert history and trends

---

## Use Cases

### 1. Cost Optimization
- Identify accounts with too many resources
- Find unused/idle resources (stopped instances, unattached volumes)
- Track resource growth over time
- Correlate resource counts with costs

### 2. Compliance & Governance
- Enforce resource limits per region
- Track IAM user/role proliferation
- Monitor security group sprawl
- Audit resource creation patterns

### 3. Capacity Planning
- Predict when limits will be hit
- Plan infrastructure scaling
- Identify resource concentration risks
- Track multi-cloud distribution

### 4. Security Monitoring
- Alert on suspicious resource creation
- Track IAM role growth
- Monitor Key Vault/KMS key usage
- Detect unusual subnet/security group changes

### 5. Multi-Account Management
- Compare resource counts across accounts
- Identify accounts approaching limits
- Standardize resource allocation
- Track development vs. production resource usage

---

## Key Files

### Collectors
- `collectors/aws_inventory_collector.py` - AWS resource counting (51 services)
- `collectors/gcp_inventory_collector.py` - GCP resource counting (45+ services)
- `collectors/azure_inventory_collector.py` - Azure resource counting (48 services)
- `collectors/cost_tracker.py` - Multi-cloud cost tracking

### Core System
- `cloud_monitor.py` - Main orchestrator
- `alerting/alert_manager.py` - Threshold checking and email alerts
- `es_integration/elasticsearch_manager.py` - Data storage
- `config/config.yaml` - Configuration and thresholds

### Documentation
- `AWS_SERVICES_INVENTORY.md` - Complete AWS service list
- `COMPLETE_SERVICE_LIST.md` - Cross-cloud service comparison
- `RESOURCE_COUNT_APPROACH.md` - System architecture
- `SYSTEM_OVERVIEW.md` - This file

---

## Future Enhancements

1. **Resource Tagging Analysis** - Track resources by tags/labels
2. **Cost Anomaly Detection** - ML-based unusual spend detection
3. **Resource Lifecycle Tracking** - Monitor resource creation/deletion patterns
4. **Compliance Reporting** - Generate compliance reports
5. **Resource Recommendations** - Suggest optimizations
6. **Multi-Region Aggregation** - Cross-region resource views
7. **Custom Dashboards** - Per-team resource views
8. **Slack/Teams Integration** - Alternative alert channels

---

**Last Updated**: 2025-01-18
**System Version**: 1.0
**Total Services Covered**: 144+ services across AWS, GCP, and Azure
