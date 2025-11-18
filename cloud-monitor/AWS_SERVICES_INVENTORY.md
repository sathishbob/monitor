# AWS Services - Complete Inventory Coverage

## Resource Counting Approach

This system counts **how many resources exist** in each AWS account/region, NOT performance metrics.

## Example Alerts

```
⚠️ ALERT: 52 EC2 instances running in us-east-1 (threshold: 50)
⚠️ ALERT: 150 S3 buckets in account production (threshold: 100)
⚠️ ALERT: 25 RDS databases in us-west-2 (threshold: 20)
```

---

## ✅ AWS Services Covered (65+ Services)

### 1. Compute Services (7 services)

#### EC2 - Elastic Compute Cloud ✅
**Resources Counted:**
- Total instances
- Running instances
- Stopped instances
- Instance breakdown by type (t2.micro, m5.large, etc.)
- Instance breakdown by state

**Alert Example:**
```yaml
Alert: "52 EC2 instances running in us-east-1"
Threshold: max_running_instances: 50
Region: us-east-1
Breakdown:
  - running: 52
  - stopped: 8
  - terminated: 2
  Types:
  - t2.micro: 30
  - m5.large: 15
  - t3.medium: 7
```

#### EBS - Elastic Block Store ✅
**Resources Counted:**
- Total volumes
- Attached volumes
- Available volumes
- Total storage (GB)

#### EC2 Snapshots ✅
**Resources Counted:**
- Snapshots owned by account

#### AMIs - Amazon Machine Images ✅
**Resources Counted:**
- AMIs owned by account

#### Key Pairs ✅
**Resources Counted:**
- SSH key pairs

#### Elastic IPs ✅
**Resources Counted:**
- Allocated Elastic IPs
- Unassigned Elastic IPs

#### Auto Scaling Groups
**Resources Counted:**
- Auto Scaling Groups

---

### 2. Container & Orchestration (4 services)

#### ECS - Elastic Container Service ✅
**Resources Counted:**
- Clusters
- Services
- Task definitions
- Tasks running

**Alert Example:**
```yaml
Alert: "15 ECS clusters in us-east-1"
Threshold: max_ecs_clusters: 10
```

#### EKS - Elastic Kubernetes Service ✅
**Resources Counted:**
- Kubernetes clusters
- Node groups

**Alert Example:**
```yaml
Alert: "8 EKS clusters in us-west-2"
Threshold: max_eks_clusters: 5
```

#### ECR - Elastic Container Registry
**Resources Counted:**
- Container repositories
- Images

#### Fargate
**Resources Counted:**
- Fargate tasks

---

### 3. Database Services (6 services)

#### RDS - Relational Database Service ✅
**Resources Counted:**
- DB instances
- DB instances by engine (MySQL, PostgreSQL, etc.)

**Alert Example:**
```yaml
Alert: "25 RDS instances in us-east-1"
Threshold: max_rds_instances: 20
Breakdown:
  - MySQL: 15
  - PostgreSQL: 8
  - Aurora: 2
```

#### RDS Clusters
**Resources Counted:**
- Aurora clusters

#### DynamoDB ✅
**Resources Counted:**
- Tables
- Global tables

#### ElastiCache
**Resources Counted:**
- Redis clusters
- Memcached clusters

#### Redshift
**Resources Counted:**
- Data warehouse clusters

#### DocumentDB
**Resources Counted:**
- MongoDB-compatible clusters

---

### 4. Storage Services (5 services)

#### S3 - Simple Storage Service ✅
**Resources Counted:**
- Buckets (global count)

**Alert Example:**
```yaml
Alert: "150 S3 buckets in account"
Threshold: max_s3_buckets: 100
```

#### EFS - Elastic File System
**Resources Counted:**
- File systems

#### FSx
**Resources Counted:**
- FSx file systems (Windows, Lustre)

#### Glacier
**Resources Counted:**
- Vaults

#### Storage Gateway
**Resources Counted:**
- Gateways

---

### 5. Networking Services (12 services)

#### VPC - Virtual Private Cloud ✅
**Resources Counted:**
- VPCs per region

**Alert Example:**
```yaml
Alert: "8 VPCs in us-east-1"
Threshold: max_vpcs_per_region: 5
```

#### Subnets
**Resources Counted:**
- Subnets per VPC

#### Security Groups
**Resources Counted:**
- Security groups per region

#### Load Balancers ✅
**Resources Counted:**
- Application Load Balancers
- Network Load Balancers
- Classic Load Balancers

#### Target Groups
**Resources Counted:**
- Target groups

#### NAT Gateways
**Resources Counted:**
- NAT gateways

#### Internet Gateways
**Resources Counted:**
- Internet gateways

#### Route Tables
**Resources Counted:**
- Route tables

#### Network ACLs
**Resources Counted:**
- Network ACLs

#### VPC Endpoints
**Resources Counted:**
- VPC endpoints

#### Transit Gateway
**Resources Counted:**
- Transit gateways

#### Direct Connect
**Resources Counted:**
- Direct Connect connections

---

### 6. Serverless Services (4 services)

#### Lambda ✅
**Resources Counted:**
- Functions
- Functions by runtime (Python, Node.js, etc.)

**Alert Example:**
```yaml
Alert: "450 Lambda functions in us-east-1"
Threshold: max_lambda_functions: 400
Breakdown:
  - python3.9: 200
  - nodejs18.x: 150
  - python3.8: 100
```

#### API Gateway
**Resources Counted:**
- REST APIs
- HTTP APIs
- WebSocket APIs

#### Step Functions
**Resources Counted:**
- State machines

#### EventBridge
**Resources Counted:**
- Event rules

---

### 7. Analytics & Big Data (5 services)

#### EMR - Elastic MapReduce
**Resources Counted:**
- EMR clusters

#### Kinesis
**Resources Counted:**
- Kinesis streams
- Kinesis Firehose delivery streams

#### Glue
**Resources Counted:**
- Glue jobs
- Crawlers
- Databases

#### Athena
**Resources Counted:**
- Workgroups

#### QuickSight
**Resources Counted:**
- Dashboards

---

### 8. Application Integration (3 services)

#### SQS - Simple Queue Service
**Resources Counted:**
- Queues (standard + FIFO)

#### SNS - Simple Notification Service
**Resources Counted:**
- Topics
- Subscriptions

#### EventBridge
**Resources Counted:**
- Event rules

---

### 9. Developer Tools (5 services)

#### CodeCommit
**Resources Counted:**
- Git repositories

#### CodeBuild
**Resources Counted:**
- Build projects

#### CodePipeline
**Resources Counted:**
- Pipelines

#### CodeDeploy
**Resources Counted:**
- Applications

#### Cloud9
**Resources Counted:**
- Development environments

---

### 10. Security & Identity (6 services)

#### IAM - Identity & Access Management
**Resources Counted:**
- Users
- Roles
- Policies (customer managed)
- Groups

**Alert Example:**
```yaml
Alert: "500 IAM roles in account"
Threshold: max_iam_roles: 400
```

#### KMS - Key Management Service
**Resources Counted:**
- Customer managed keys

#### Secrets Manager
**Resources Counted:**
- Secrets

#### Certificate Manager
**Resources Counted:**
- Certificates

#### WAF
**Resources Counted:**
- Web ACLs

#### Security Hub
**Resources Counted:**
- Enabled standards

---

### 11. Management & Governance (6 services)

#### CloudWatch
**Resources Counted:**
- Alarms
- Log groups

**Alert Example:**
```yaml
Alert: "1200 CloudWatch alarms in us-east-1"
Threshold: max_cloudwatch_alarms: 1000
```

#### CloudFormation
**Resources Counted:**
- Stacks
- Stack sets

#### Config
**Resources Counted:**
- Config rules

#### Systems Manager
**Resources Counted:**
- Parameter Store parameters
- Automation documents

#### CloudTrail
**Resources Counted:**
- Trails

#### Organizations
**Resources Counted:**
- Accounts in organization

---

### 12. Content Delivery & Edge (2 services)

#### CloudFront
**Resources Counted:**
- Distributions

#### Route 53
**Resources Counted:**
- Hosted zones
- Record sets

---

### 13. Machine Learning (3 services)

#### SageMaker
**Resources Counted:**
- Endpoints
- Models
- Notebooks

#### Rekognition
**Resources Counted:**
- Collections

#### Comprehend
**Resources Counted:**
- Document classifiers

---

## 📊 Total Service Coverage

| Category | Services | Status |
|----------|----------|--------|
| Compute | 7 | ✅ Partially Implemented |
| Containers | 4 | ✅ Partially Implemented |
| Databases | 6 | ✅ Partially Implemented |
| Storage | 5 | ✅ Partially Implemented |
| Networking | 12 | ✅ Partially Implemented |
| Serverless | 4 | ✅ Partially Implemented |
| Analytics | 5 | 🟡 Framework Ready |
| Integration | 3 | 🟡 Framework Ready |
| Developer Tools | 5 | 🟡 Framework Ready |
| Security | 6 | 🟡 Framework Ready |
| Management | 6 | 🟡 Framework Ready |
| Content Delivery | 2 | 🟡 Framework Ready |
| Machine Learning | 3 | 🟡 Framework Ready |
| **TOTAL** | **68 Services** | **13 Implemented, 55 Framework** |

---

## 🚨 Alert Configuration Examples

### config.yaml
```yaml
thresholds:
  aws:
    # Per-region thresholds
    ec2_instances_per_region: 50
    rds_instances_per_region: 20
    vpc_per_region: 5
    lambda_functions_per_region: 400
    ecs_clusters_per_region: 10
    eks_clusters_per_region: 5

    # Global (account-wide) thresholds
    s3_buckets_total: 100
    iam_users_total: 200
    iam_roles_total: 400
    cloudfront_distributions_total: 50

    # Specific resource types
    elastic_ips_unassigned: 5  # Alert if >5 unused IPs
    ebs_volumes_unattached: 20  # Alert if >20 unused volumes
    security_groups_unused: 50  # Alert if >50 unused SGs
```

### Email Alert Example
```
Subject: [WARNING] AWS Resource Count Alert - EC2 Instances

Resource Count Alert

Severity: WARNING
Cloud Provider: AWS
Account: production
Region: us-east-1

Alert Message:
EC2 instance count (52) exceeds threshold (50)

Resource Details:
- Service: EC2
- Resource Type: instances
- Current Count: 52
- Threshold: 50
- Running: 52
- Stopped: 8

Breakdown by Instance Type:
- t2.micro: 30 instances
- m5.large: 15 instances
- t3.medium: 7 instances

Action Required:
Review and cleanup unused EC2 instances in this region.
```

---

## 💾 Elasticsearch Data Structure

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
    "stopped": 8
  },
  "type_breakdown": {
    "t2.micro": 30,
    "m5.large": 15,
    "t3.medium": 7
  }
}
```

---

## 🎯 Use Cases

1. **Cost Optimization:** Identify unused resources
2. **Compliance:** Track resource limits
3. **Security:** Monitor IAM user/role growth
4. **Capacity Planning:** Track resource growth trends
5. **Multi-Account Management:** Compare resource counts across accounts
6. **Region Analysis:** Identify regions with most resources

---

**Last Updated:** 2025-01-18
