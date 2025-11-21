# Cloud User Activity Tracking System

## Overview
Comprehensive multi-cloud user activity tracking system that monitors what users do across AWS, GCP, and Azure accounts, generates usage metrics, and provides real-time dashboards.

## What It Tracks

### AWS (CloudTrail)
- **User Actions**: Who did what, when, and from where
- **API Calls**: All AWS API calls with parameters
- **Resources Modified**: Created, updated, deleted resources
- **Authentication**: Login attempts, MFA usage, role assumptions
- **Access Patterns**: IP addresses, user agents, locations
- **Service Usage**: Which services each user uses
- **Error Events**: Failed operations and permission denials

### GCP (Cloud Audit Logs)
- **Admin Activity**: Resource configuration changes
- **Data Access**: Read/write operations on data
- **System Events**: Automated Google Cloud actions
- **User Identity**: Who performed each action
- **Resource Changes**: All resource modifications
- **API Calls**: All GCP API invocations
- **Authentication**: Login events, service account usage

### Azure (Activity Logs)
- **Administrative Operations**: All ARM operations
- **Resource Modifications**: CRUD operations
- **User Identity**: User principal and caller information
- **Authentication Events**: Sign-ins and role assignments
- **Resource Provider Actions**: All Azure service operations
- **Subscription Activity**: Cross-subscription operations

## Features

### Activity Tracking
- **Real-time monitoring** of user activities across all clouds
- **Multi-account support** for AWS, GCP, and Azure
- **Comprehensive event capture** from native cloud audit services
- **User attribution** - track activities to specific users/service accounts
- **Geographic tracking** - source IP and location data
- **Time-series analysis** - activity patterns over time

### Usage Metrics
- **Per-user metrics**: Actions per user, services used, resources modified
- **Service usage**: Most used services by user/team
- **Action frequency**: API call volumes and patterns
- **Error rates**: Failed operations per user
- **Cost attribution**: Link activities to costs
- **Peak usage times**: When users are most active
- **Anomaly detection**: Unusual activity patterns

### Dashboards
- **User Activity Overview**: Top active users, action counts
- **Service Usage Heatmap**: Which services are used when
- **Geographic Distribution**: Where users are accessing from
- **Timeline View**: Activity over time with drill-down
- **User Profiles**: Individual user activity details
- **Anomaly Alerts**: Unusual patterns highlighted
- **Comparison Views**: Compare user/team activity

## Architecture

```
┌─────────────────────────────────────────┐
│       Cloud Audit Services              │
│  CloudTrail | Audit Logs | Activity Log │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┴─────────┐
         │  Activity Collectors│
         │  (Poll every 5 min) │
         └─────────┬───────────┘
                   │
         ┌─────────▼───────────┐
         │ Activity Processor   │
         │ - Parse events       │
         │ - Extract user info  │
         │ - Categorize actions │
         └─────────┬───────────┘
                   │
         ┌─────────▼───────────┐
         │  Metrics Generator   │
         │ - Aggregate by user  │
         │ - Calculate metrics  │
         │ - Detect anomalies   │
         └─────────┬───────────┘
                   │
         ┌─────────┴───────────┐
         │                     │
    ┌────▼─────┐      ┌────────▼────────┐
    │Elasticsearch│    │  Email Alerts   │
    │  Storage   │    │ (Anomalies)     │
    └────┬─────┘      └─────────────────┘
         │
    ┌────▼──────────┐
    │ React Dashboard│
    │ - User metrics │
    │ - Activity view│
    │ - Heatmaps     │
    └────────────────┘
```

## Installation

```bash
cd cloud-activity-monitor
pip install -r requirements.txt
```

## Configuration

Edit `config/activity-config.yaml`:

```yaml
# AWS Accounts
aws:
  enabled: true
  accounts:
    - name: "production"
      access_key_id: "${AWS_ACCESS_KEY_ID}"
      secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
      regions: ["us-east-1", "us-west-2"]
      cloudtrail_bucket: "my-cloudtrail-logs"

# GCP Projects
gcp:
  enabled: true
  projects:
    - name: "prod-project"
      project_id: "my-project-123456"
      credentials_file: "/path/to/gcp-creds.json"

# Azure Subscriptions
azure:
  enabled: true
  subscriptions:
    - name: "production"
      subscription_id: "${AZURE_SUBSCRIPTION_ID}"
      tenant_id: "${AZURE_TENANT_ID}"
      client_id: "${AZURE_CLIENT_ID}"
      client_secret: "${AZURE_CLIENT_SECRET}"
```

## Usage

```bash
# Run once (testing)
python activity_monitor.py --once

# Run continuously (5-minute intervals)
python activity_monitor.py

# Start dashboard
cd dashboard
npm install
npm start
# Open http://localhost:3001
```

## Data Collected

### Activity Event Structure
```json
{
  "timestamp": "2025-01-18T14:30:00Z",
  "cloud_provider": "aws",
  "account": "production",
  "region": "us-east-1",
  "user_identity": {
    "type": "IAMUser",
    "user_name": "john.doe",
    "user_id": "AIDAI...",
    "arn": "arn:aws:iam::123456789012:user/john.doe"
  },
  "event_name": "RunInstances",
  "event_source": "ec2.amazonaws.com",
  "service": "EC2",
  "action_category": "Create",
  "resources_affected": [
    {
      "type": "instance",
      "id": "i-1234567890abcdef0"
    }
  ],
  "source_ip": "203.0.113.12",
  "user_agent": "aws-cli/2.9.0",
  "success": true,
  "error_message": null
}
```

### User Metrics Structure
```json
{
  "timestamp": "2025-01-18T15:00:00Z",
  "cloud_provider": "aws",
  "account": "production",
  "user_name": "john.doe",
  "time_period": "1h",
  "metrics": {
    "total_actions": 45,
    "successful_actions": 43,
    "failed_actions": 2,
    "services_used": ["EC2", "S3", "RDS"],
    "action_types": {
      "Create": 5,
      "Read": 30,
      "Update": 8,
      "Delete": 2
    },
    "unique_resources_accessed": 12,
    "source_ips": ["203.0.113.12"],
    "peak_hour": "14:00-15:00"
  }
}
```

## Anomaly Detection

The system detects:
- **Unusual access times**: User active at odd hours
- **High error rates**: Many failed operations
- **New IP addresses**: User accessing from new location
- **Privilege escalation**: Role assumption patterns
- **Mass deletion**: Bulk delete operations
- **Service access**: User accessing new services
- **API rate spikes**: Sudden increase in API calls

## Dashboard Features

### Overview Tab
- Total users active today
- Total actions across all clouds
- Top 10 most active users
- Action success rate
- Geographic distribution map

### User Activity Tab
- Search and filter by user
- Individual user timeline
- Service usage breakdown
- Resource access patterns
- Error rate per user

### Service Usage Tab
- Heatmap: Services × Users
- Most used services
- Least used services
- Service adoption trends

### Anomalies Tab
- Real-time anomaly feed
- Anomaly severity levels
- Investigation tools
- Historical anomaly patterns

### Timeline Tab
- Interactive timeline
- Drill down by time period
- Filter by user/service/action
- Export to CSV

## Security Considerations

### Required Permissions

**AWS IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "cloudtrail:LookupEvents",
      "cloudtrail:GetTrail",
      "s3:GetObject",
      "s3:ListBucket"
    ],
    "Resource": "*"
  }]
}
```

**GCP Roles:**
- `roles/logging.viewer` - Read audit logs
- `roles/iam.securityReviewer` - User identity info

**Azure RBAC:**
- `Reader` role on subscriptions
- `Monitoring Reader` for Activity Logs

### Data Privacy
- User data stored in Elasticsearch (configure retention)
- Sensitive fields can be masked
- Access control on dashboard
- Audit trail of who viewed what

## Use Cases

1. **Security Auditing**: Track all user actions for compliance
2. **Cost Attribution**: Link user activities to cloud costs
3. **Team Productivity**: Measure team cloud usage patterns
4. **Incident Investigation**: Who did what during an incident
5. **Training Identification**: Identify users who need training
6. **Resource Optimization**: See which resources users actually use
7. **Compliance Reporting**: Generate activity reports
8. **Anomaly Response**: Alert on suspicious activities

## Performance

- Handles 100,000+ events per hour
- 5-minute data freshness
- Real-time dashboard updates
- Efficient Elasticsearch queries
- Configurable retention periods

## Files

- `activity_monitor.py` - Main orchestrator
- `collectors/aws_activity_collector.py` - AWS CloudTrail
- `collectors/gcp_activity_collector.py` - GCP Audit Logs
- `collectors/azure_activity_collector.py` - Azure Activity Logs
- `processors/activity_processor.py` - Event parsing and enrichment
- `metrics/metrics_generator.py` - Usage metrics calculation
- `anomaly/anomaly_detector.py` - Anomaly detection
- `dashboard/` - React dashboard application
- `config/activity-config.yaml` - Configuration

## Future Enhancements

- Machine learning for advanced anomaly detection
- Slack/Teams integration for alerts
- Custom report generation
- Cost correlation with activities
- Predictive analytics
- Compliance frameworks (SOC2, HIPAA, etc.)
