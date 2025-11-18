# Cloud Resource Inventory & Count Monitoring

## 🎯 What This System Does

Instead of monitoring **performance metrics** (CPU%, memory%), this system:

1. **Counts resources** across all cloud accounts
2. **Tracks inventory** by region/account
3. **Alerts on counts** exceeding thresholds

---

## 📊 Example: What You'll See

### Dashboard View
```
AWS Production Account - us-east-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ EC2 Instances:        52 (⚠️ Threshold: 50)
✅ RDS Databases:        18 (✓ Threshold: 20)
✅ S3 Buckets:          145 (⚠️ Threshold: 100)
✅ Lambda Functions:    425 (⚠️ Threshold: 400)
✅ VPCs:                  5 (✓ Threshold: 5)
✅ Load Balancers:       12 (✓ Threshold: 15)
✅ ECS Clusters:          8 (✓ Threshold: 10)
✅ EKS Clusters:          3 (✓ Threshold: 5)
✅ DynamoDB Tables:      35 (✓ Threshold: 50)
✅ IAM Users:           150 (✓ Threshold: 200)
✅ IAM Roles:           380 (✓ Threshold: 400)
```

### Email Alert Example
```
Subject: [WARNING] AWS Resource Count Alert

Account: production
Region: us-east-1
Service: EC2

Alert: 52 EC2 instances running (threshold: 50)

Breakdown:
- Running: 52
- Stopped: 8
- Total: 60

By Type:
- t2.micro: 30 instances
- m5.large: 15 instances
- t3.medium: 7 instances

Action: Review and terminate unused instances
```

---

## 🔵 AWS Services Coverage

### ✅ Fully Implemented (13 services)
1. **EC2** - Virtual machines count
2. **EBS** - Volume count, storage GB
3. **EC2 Snapshots** - Snapshot count
4. **AMIs** - Image count
5. **Key Pairs** - SSH key count
6. **Elastic IPs** - IP count
7. **RDS** - Database count by engine
8. **DynamoDB** - Table count
9. **S3** - Bucket count (global)
10. **Lambda** - Function count by runtime
11. **VPC** - VPC count per region
12. **ELB** - Load balancer count by type
13. **ECS** - Cluster count
14. **EKS** - Kubernetes cluster count

### 🟡 Framework Ready (55+ more services)
- Container services (ECR, Fargate)
- More databases (ElastiCache, Redshift, DocumentDB)
- Storage (EFS, FSx, Glacier)
- Networking (Subnets, Security Groups, NAT Gateways, etc.)
- Serverless (API Gateway, Step Functions, EventBridge)
- Analytics (EMR, Kinesis, Glue, Athena)
- Integration (SQS, SNS)
- Developer Tools (CodeCommit, CodeBuild, CodePipeline)
- Security (IAM, KMS, Secrets Manager, WAF)
- Management (CloudWatch, CloudFormation, Config)
- Content Delivery (CloudFront, Route 53)
- Machine Learning (SageMaker, Rekognition)

**Total: 68 AWS Services**

---

## 🟢 GCP Services (Next Priority)

Will count:
- Compute Engine instances
- Cloud SQL databases
- Cloud Storage buckets
- Cloud Functions
- GKE clusters
- Load balancers
- VPCs and subnets
- And 50+ more services

---

## 🔷 Azure Services (Next Priority)

Will count:
- Virtual Machines
- SQL Databases
- Blob Storage containers
- Azure Functions
- AKS clusters
- Load Balancers
- VNets and subnets
- And 50+ more services

---

## ⚙️ Configuration Example

### config/config.yaml
```yaml
# Resource count thresholds
thresholds:
  aws:
    # Per-region limits
    ec2:
      instances_per_region: 50
      volumes_unattached: 20
      snapshots_old_days: 90
      elastic_ips_unassigned: 5

    rds:
      instances_per_region: 20
      clusters_per_region: 10

    networking:
      vpcs_per_region: 5
      security_groups_per_vpc: 100
      load_balancers_per_region: 15

    containers:
      ecs_clusters_per_region: 10
      eks_clusters_per_region: 5
      ecr_repositories: 200

    serverless:
      lambda_functions_per_region: 400
      api_gateways_per_region: 50

    # Global (account-wide) limits
    s3_buckets_total: 100
    iam_users_total: 200
    iam_roles_total: 400
    kms_keys_total: 500
    cloudfront_distributions: 50

  gcp:
    compute:
      instances_per_zone: 50
      disks_unattached: 20

    database:
      cloudsql_instances_per_region: 20

    storage:
      buckets_total: 100

    containers:
      gke_clusters_per_region: 5

  azure:
    compute:
      vms_per_region: 50

    database:
      sql_databases_per_region: 20

    storage:
      storage_accounts: 100

    containers:
      aks_clusters_per_region: 5
```

---

## 📧 Alert Types

### 1. Threshold Exceeded
```
Alert: 52 EC2 instances in us-east-1 exceeds threshold of 50
Severity: WARNING
```

### 2. Resource Growth
```
Alert: EC2 instance count increased by 50% in last 7 days
Severity: INFO
```

### 3. Unused Resources
```
Alert: 25 EBS volumes unattached (threshold: 20)
Severity: INFO
Action: Consider deleting unused volumes
```

### 4. Regional Imbalance
```
Alert: 80% of EC2 instances in single region
Severity: INFO
Recommendation: Consider multi-region deployment
```

---

## 📈 Dashboard Features

### Resource Count Cards
```
┌─────────────────────┐
│   EC2 Instances     │
│       52            │
│  ⚠️ +2 vs threshold │
└─────────────────────┘
```

### Regional Breakdown
```
EC2 Instances by Region:
━━━━━━━━━━━━━━━━━━━━━
us-east-1:    52 ████████████░ 52%
us-west-2:    30 ███████░░░░░░ 30%
eu-west-1:    18 ████░░░░░░░░░ 18%
```

### Service Distribution
```
Resources by Service:
━━━━━━━━━━━━━━━━━━━━━
EC2:          52
RDS:          18
Lambda:      425
S3:          145
VPC:           5
```

### Trend Charts
```
EC2 Instance Count - Last 30 Days
 60 │               ╭─
 50 │           ╭───╯
 40 │       ╭───╯
 30 │   ╭───╯
 20 │───╯
    └─────────────────────
```

---

## 🎯 Benefits of This Approach

1. **Cost Optimization**
   - Identify unused resources
   - Track resource sprawl
   - Set budget-aligned limits

2. **Compliance & Governance**
   - Enforce resource limits per team/project
   - Track growth patterns
   - Audit resource distribution

3. **Capacity Planning**
   - Historical growth trends
   - Predict future needs
   - Optimize regional distribution

4. **Security**
   - Monitor IAM user/role growth
   - Track security group proliferation
   - Identify orphaned resources

5. **Multi-Account Management**
   - Compare resource counts across accounts
   - Standardize limits
   - Consolidate resources

---

## 🚀 Quick Start

1. Configure thresholds in `config.yaml`
2. Run: `python cloud_monitor.py`
3. Check dashboard: `http://localhost:3000`
4. Receive email alerts when thresholds exceeded

---

**This is INVENTORY management, not PERFORMANCE monitoring.**

You track **HOW MANY**, not **HOW BUSY**.
