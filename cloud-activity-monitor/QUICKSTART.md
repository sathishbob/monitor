# Cloud Activity Monitor - Quick Start Guide

## What This System Does

This system tracks **all user activities** across AWS, GCP, and Azure accounts and provides:
- Real-time activity monitoring
- User behavior analytics
- Anomaly detection (unusual patterns, high error rates, new IPs, etc.)
- Interactive dashboards with visualizations
- Email alerts for critical anomalies

## Installation

### 1. Install Python Dependencies

```bash
cd cloud-activity-monitor
pip install -r requirements.txt
```

### 2. Setup Elasticsearch

```bash
# Using Docker (easiest)
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0
```

### 3. Configure Cloud Credentials

Edit `config/activity-config.yaml` and set your credentials:

```yaml
aws:
  enabled: true
  accounts:
    - name: "production"
      access_key_id: "YOUR_AWS_ACCESS_KEY"
      secret_access_key: "YOUR_AWS_SECRET_KEY"
      regions: ["us-east-1", "us-west-2"]

gcp:
  enabled: true
  projects:
    - name: "prod-project"
      project_id: "your-project-id"
      credentials_file: "/path/to/gcp-credentials.json"

azure:
  enabled: true
  subscriptions:
    - name: "production"
      subscription_id: "YOUR_SUBSCRIPTION_ID"
      tenant_id: "YOUR_TENANT_ID"
      client_id: "YOUR_CLIENT_ID"
      client_secret: "YOUR_CLIENT_SECRET"
```

Or use environment variables:
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AZURE_SUBSCRIPTION_ID="..."
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
```

### 4. Run the Monitor

```bash
# Test run (collect once and exit)
python activity_monitor.py --once

# Continuous monitoring (every 5 minutes)
python activity_monitor.py
```

### 5. Start the Dashboard

```bash
cd dashboard
npm install
npm start

# Dashboard will be available at http://localhost:3001
```

## Required Cloud Permissions

### AWS IAM Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "cloudtrail:LookupEvents",
      "cloudtrail:GetTrail"
    ],
    "Resource": "*"
  }]
}
```

### GCP Roles
- `roles/logging.viewer` - Read Cloud Audit Logs

### Azure RBAC
- `Reader` role on subscription
- `Monitoring Reader` for Activity Logs

## What Gets Tracked

### AWS (CloudTrail)
- Every API call made to AWS services
- User identity (IAM user, role, or assumed role)
- Source IP address and location
- Success/failure status
- Resources affected
- Timestamp and region

### GCP (Cloud Audit Logs)
- Admin activity (resource configuration changes)
- Data access (read/write operations)
- System events (automated actions)
- User identity (user or service account)
- Method called and service
- Success/failure status

### Azure (Activity Logs)
- All Azure Resource Manager operations
- Resource CRUD operations
- User identity and caller information
- Subscription and resource group
- Operation status
- Source IP and timestamp

## Dashboard Features

### Overview Tab
- Total active users
- Total actions performed
- Overall success rate
- Anomaly count
- Top 10 active users chart
- Cloud provider distribution
- Action type breakdown
- Top services used

### User Activity Tab
- Per-user metrics table
- Total actions, success/failure counts
- Error rate per user
- Services used count
- Filterable and sortable

### Services Tab
- Service usage bar chart
- Actions per service
- Most/least used services

### Anomalies Tab
- Real-time anomaly feed
- Severity levels (info, warning, critical)
- Anomaly types:
  - High error rate (>20% failures)
  - Unusual access times (late night/early morning)
  - New IP addresses
  - Mass delete operations (10+ deletes)
  - Activity spikes (3x normal)
  - New service access

### Timeline Tab
- Hourly activity line chart
- Recent activities table (last 50)
- Full activity details

## Anomaly Detection

The system automatically detects:

1. **High Error Rate**: User has >20% failed operations
2. **Unusual Access Time**: Activity during 10 PM - 6 AM
3. **New IP Address**: User accessing from previously unseen IP
4. **Mass Delete**: 10+ delete operations in one period
5. **Activity Spike**: Activity >3x higher than user's baseline
6. **New Service**: User accessing a service for the first time

Configure thresholds in `config/activity-config.yaml`:
```yaml
anomaly_detection:
  enabled: true
  error_rate_threshold: 0.20  # 20%
  action_spike_multiplier: 3.0  # 3x
  unusual_hour_start: 22  # 10 PM
  unusual_hour_end: 6  # 6 AM
  mass_delete_threshold: 10
```

## Email Alerts

Critical anomalies trigger email alerts. Configure in `config/activity-config.yaml`:

```yaml
alerting:
  enabled: true
  smtp:
    host: "smtp.gmail.com"
    port: 587
    use_tls: true
    username: "your-email@gmail.com"
    password: "your-app-password"  # For Gmail, use App Password
  recipients:
    - "security@example.com"
    - "admin@example.com"
```

## Data Storage

All data is stored in Elasticsearch indices:
- **Type: user_activity** - Individual activity events
- **Type: user_summary** - Aggregated user metrics (per 5-min period)
- **Type: anomaly** - Detected anomalies

Default index: `cloud-user-activities`

Data retention: 90 days (configurable in `activity-config.yaml`)

## Monitoring Frequency

By default, the system polls every **5 minutes** and looks back **5 minutes** for new activities.

Adjust in `config/activity-config.yaml`:
```yaml
monitoring:
  interval_minutes: 5  # How often to collect
  lookback_minutes: 5  # How far back to look
```

## Example Queries

### Elasticsearch Queries

```bash
# Get all activities from last hour
curl -X POST "localhost:9200/cloud-user-activities/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"range": {"timestamp": {"gte": "now-1h"}}},
        {"term": {"type": "user_activity"}}
      ]
    }
  }
}'

# Get all anomalies
curl -X POST "localhost:9200/cloud-user-activities/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"term": {"type": "anomaly"}},
  "sort": [{"timestamp": "desc"}]
}'

# Get specific user's activities
curl -X POST "localhost:9200/cloud-user-activities/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "user_activity"}},
        {"term": {"user_identity.user_name": "john.doe"}}
      ]
    }
  }
}'
```

## Troubleshooting

### No activities being collected

1. Check CloudTrail is enabled in AWS
2. Verify IAM permissions
3. Check `activity-monitor.log` for errors
4. Run with `--once` flag to test

### Dashboard shows no data

1. Verify Elasticsearch is running: `curl localhost:9200`
2. Check index exists: `curl localhost:9200/_cat/indices`
3. Check CORS if accessing from different host
4. Look at browser console for errors

### High memory usage

Adjust data retention or reduce monitoring frequency

### Permissions errors

Review required permissions for each cloud provider above

## Production Deployment

### Run as a Service (Linux)

Create `/etc/systemd/system/cloud-activity-monitor.service`:

```ini
[Unit]
Description=Cloud Activity Monitor
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/cloud-activity-monitor
ExecStart=/usr/bin/python3 /opt/cloud-activity-monitor/activity_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cloud-activity-monitor
sudo systemctl start cloud-activity-monitor
sudo journalctl -u cloud-activity-monitor -f
```

### Run with Docker

```bash
# Build image
docker build -t cloud-activity-monitor .

# Run container
docker run -d \
  --name activity-monitor \
  -v $(pwd)/config:/app/config \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  cloud-activity-monitor
```

## Support

For issues and questions:
1. Check logs in `activity-monitor.log`
2. Review configuration in `config/activity-config.yaml`
3. Test with `--once` flag for debugging
4. Check Elasticsearch connectivity

## Architecture

```
CloudTrail/AuditLogs/ActivityLogs
           ↓
    Activity Collectors
           ↓
    Anomaly Detector
           ↓
    Elasticsearch
           ↓
    React Dashboard
```

All components run independently and are horizontally scalable.
