# Cloud Monitor - Quick Start Guide

## Setup in 5 Minutes

### 1. Install Dependencies

```bash
cd cloud-monitor
pip install -r requirements.txt
```

### 2. Configure Credentials

Create a `.env` file:

```bash
# AWS
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# GCP
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json

# Azure
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Email (Gmail example)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Update Configuration

Edit `config/config.yaml` - set your email recipients:

```yaml
alerting:
  recipients:
    - "your-email@example.com"
```

### 4. Start Elasticsearch (if not running)

```bash
docker run -d -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.1
```

### 5. Run Monitoring

```bash
# Test single run
python cloud_monitor.py --once

# Run continuously
python cloud_monitor.py
```

### 6. Start Dashboard

```bash
cd dashboard
npm install
npm start
```

Open http://localhost:3000

## What You Get

✅ Automated monitoring of ALL cloud resources
✅ Email alerts when thresholds are exceeded
✅ Real-time dashboard with charts
✅ Historical data in Elasticsearch
✅ Multi-account/multi-project support

## Example Email Alert

```
Subject: [WARNING] Cloud Resource Alert - cpu_utilization

Cloud Resource Alert

Severity: WARNING
Timestamp: 2025-01-18 12:00:00 UTC

Alert Message:
CPU utilization (85.3%) exceeds threshold (80%)

Resource Details:
- Provider: aws
- Account: production
- Region: us-east-1
- Service: EC2
- Resource ID: i-1234567890abcdef0
```

## Troubleshooting

**Problem:** No metrics collected
**Solution:** Check credentials and IAM permissions

**Problem:** Alerts not sending
**Solution:** Verify SMTP settings and credentials

**Problem:** Dashboard shows no data
**Solution:** Ensure Elasticsearch is running and accessible

## Next Steps

1. Adjust thresholds in `config/config.yaml`
2. Add more cloud accounts
3. Customize alert recipients
4. Set up monitoring interval

For full documentation, see [README.md](README.md)
