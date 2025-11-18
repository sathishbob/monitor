# Multi-Cloud Monitoring System

Comprehensive monitoring solution for AWS, GCP, and Azure cloud resources with automated threshold-based alerts and Elasticsearch integration.

## Features

✅ **Multi-Cloud Support**
- AWS (EC2, RDS, S3, Lambda, ELB, DynamoDB, EBS)
- Google Cloud Platform (Compute Engine, Cloud SQL, Cloud Storage, Cloud Functions)
- Microsoft Azure (VMs, SQL Database, Blob Storage, Functions)

✅ **Automated Alerting**
- Configurable threshold-based alerts
- Email notifications via SMTP
- Alert cooldown to prevent spam
- Multiple severity levels (INFO, WARNING, CRITICAL)

✅ **Data Storage**
- Elasticsearch integration for historical data
- Queryable metrics for dashboard visualization
- Retention policy configuration

✅ **Comprehensive Metrics**
- CPU, memory, disk utilization
- Network bandwidth and data transfer
- Database connections and performance
- Serverless function invocations and errors
- Storage capacity and object counts

## Installation

### Prerequisites
- Python 3.8+
- Elasticsearch 8.x (running and accessible)
- Cloud provider credentials

### Install Dependencies

```bash
cd cloud-monitor
pip install -r requirements.txt
```

## Configuration

### 1. Configure Cloud Credentials

Edit `config/config.yaml`:

**AWS:**
```yaml
aws:
  enabled: true
  accounts:
    - name: "production"
      access_key_id: "${AWS_ACCESS_KEY_ID}"
      secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
      regions:
        - "us-east-1"
        - "us-west-2"
```

**GCP:**
```yaml
gcp:
  enabled: true
  projects:
    - name: "production-project"
      project_id: "my-project-123456"
      credentials_file: "/path/to/credentials.json"
```

**Azure:**
```yaml
azure:
  enabled: true
  subscriptions:
    - name: "production"
      subscription_id: "${AZURE_SUBSCRIPTION_ID}"
      tenant_id: "${AZURE_TENANT_ID}"
      client_id: "${AZURE_CLIENT_ID}"
      client_secret: "${AZURE_CLIENT_SECRET}"
```

### 2. Configure Email Alerts

```yaml
alerting:
  enabled: true
  smtp:
    host: "smtp.gmail.com"
    port: 587
    use_tls: true
    username: "your-email@gmail.com"
    password: "your-app-password"
  recipients:
    - "admin@example.com"
    - "devops@example.com"
```

### 3. Configure Thresholds

```yaml
thresholds:
  compute:
    cpu_utilization_percent: 80
    memory_utilization_percent: 85
  
  storage:
    bucket_size_gb: 1000
    bucket_object_count: 1000000
  
  database:
    cpu_utilization_percent: 75
    connection_count: 500
  
  serverless:
    error_rate_percent: 5
    invocation_count_per_hour: 100000
```

### 4. Configure Elasticsearch

```yaml
elasticsearch:
  host: "localhost:9200"
  index: "cloud-usage-metrics"
  username: null  # Optional
  password: null  # Optional
```

## Usage

### Run Continuous Monitoring

```bash
python cloud_monitor.py
```

### Run Single Iteration (Testing)

```bash
python cloud_monitor.py --once
```

### Custom Configuration File

```bash
python cloud_monitor.py --config /path/to/custom-config.yaml
```

## Environment Variables

Set environment variables for sensitive credentials:

```bash
# AWS
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# GCP
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Azure
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

## Dashboard

Access the monitoring dashboard by opening the React application:

```bash
cd dashboard
npm install
npm start
```

Dashboard features:
- Real-time cloud resource metrics
- Historical trends and charts
- Alert history
- Resource filtering by cloud provider, account, region
- Cost tracking and projections

## Alert Examples

### CPU Alert
```
Severity: WARNING
Message: CPU utilization (85.3%) exceeds threshold (80%)

Resource Details:
- Provider: aws
- Account: production
- Region: us-east-1
- Service: EC2
- Resource ID: i-1234567890abcdef0
```

### Storage Alert
```
Severity: WARNING
Message: Storage size (1250.5 GB) exceeds threshold (1000 GB)

Resource Details:
- Provider: aws
- Account: production
- Service: S3
- Resource ID: my-large-bucket
```

## Metrics Stored in Elasticsearch

Each metric document contains:
```json
{
  "timestamp": "2025-01-18T12:00:00Z",
  "cloud_provider": "aws",
  "account": "production",
  "region": "us-east-1",
  "service": "EC2",
  "resource_type": "instance",
  "resource_id": "i-1234567890abcdef0",
  "cpu_utilization": 45.2,
  "memory_utilization": 62.5,
  "state": "running"
}
```

## Troubleshooting

### No metrics collected
- Check cloud provider credentials
- Verify IAM permissions
- Check network connectivity

### Alerts not sending
- Verify SMTP configuration
- Check email credentials
- Review spam folder

### Elasticsearch connection failed
- Confirm Elasticsearch is running
- Check host and port configuration
- Verify authentication credentials

## Architecture

```
┌─────────────────┐
│  Cloud Monitor  │
│   (Main Loop)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │         │
┌───▼──┐  ┌──▼───┐  ┌──▼────┐
│ AWS  │  │ GCP  │  │ Azure │
│Coll. │  │Coll. │  │Coll.  │
└───┬──┘  └──┬───┘  └──┬────┘
    │        │         │
    └────┬───┴─────────┘
         │
    ┌────▼─────────┐
    │   Metrics    │
    │  Processing  │
    └────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌─▼──────┐
│Alerts │  │Elastic │
│(Email)│  │ search │
└───────┘  └────────┘
```

## License

MIT License

## Support

For issues and questions, please file an issue in the repository.
