# Inactivity Alert Feature

## Overview
The monitoring agent now supports sending webhook alerts when no user activity is detected on the server for a configurable period of time.

## Configuration

Add the following section to your `config.json` file:

```json
{
  "inactivity_alert": {
    "enabled": false,
    "webhook_url": "https://your-webhook-endpoint.com/api/alert",
    "webhook_auth": "Bearer your-token-here",
    "inactivity_window_minutes": 60,
    "http_method": "POST",
    "max_retries": 3,
    "retry_delay_seconds": 5
  }
}
```

### Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | `false` | Enable/disable inactivity alerts |
| `webhook_url` | string | Conditional | `null` | URL endpoint to send alerts to |
| `webhook_auth` | string | No | `null` | Authentication token (Bearer token or API key) |
| `inactivity_window_minutes` | integer | Yes | `60` | Minutes of inactivity before triggering alert |
| `check_command_activity` | boolean | No | `true` | Check for command execution activity |
| `check_network_activity` | boolean | No | `true` | Check for network traffic activity |
| `network_traffic_bytes_threshold` | integer | No | `1024` | Minimum bytes to consider network traffic as activity |
| `http_method` | string | No | `"POST"` | HTTP method to use (currently only POST supported) |
| `max_retries` | integer | No | `3` | Number of retry attempts if webhook fails |
| `retry_delay_seconds` | integer | No | `5` | Delay between retry attempts |

## How It Works

The inactivity detection system monitors two types of activity:

### 1. Command Activity
- Monitors command execution from Linux audit logs (`/var/log/audit/audit.log`)
- Checks for commands executed within the monitoring window
- Commands executed = **Activity detected**

### 2. Network Activity  
- Monitors network traffic using system counters (via `psutil`)
- Tracks bytes sent + bytes received
- If network traffic exceeds the threshold (default 1KB) = **Activity detected**

### Activity Detection Logic
1. **Activity Detection**: Checks command execution OR network traffic
2. **Inactivity Tracking**: If neither activity type detected, count as inactive
3. **Threshold Check**: If inactive duration >= configured window (e.g., 60 min), trigger alert
4. **Webhook Notification**: A POST request is sent to the configured webhook URL
5. **Alert Suppression**: Once an alert is sent, it won't be sent again until activity resumes
6. **Auto-Reset**: When activity is detected (either type), the alert flag is reset

### Network Traffic Monitoring
The network activity check:
- Tracks cumulative bytes sent/received across all network interfaces
- Compares current total bytes to previous check
- If difference exceeds threshold (default 1KB), considers it active
- Prevents false positives from background system traffic
- Can be disabled by setting `check_network_activity: false`

## Webhook Payload

When an inactivity alert is triggered, the following JSON payload is sent:

```json
{
  "event_type": "inactivity_alert",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "server_id": "lab_server_01",
  "inactivity_duration_minutes": 65.5,
  "inactivity_threshold_minutes": 60,
  "status": "no_activity",
  "activity_check": {
    "command_activity_enabled": true,
    "command_activity_detected": false,
    "network_activity_enabled": true,
    "network_activity_detected": false,
    "network_threshold_bytes": 1024
  }
}
```

### Payload Fields

- `event_type`: Always set to `"inactivity_alert"`
- `timestamp`: ISO 8601 timestamp when the alert was triggered
- `server_id`: Unique identifier of the monitoring server
- `inactivity_duration_minutes`: Actual duration of inactivity detected
- `inactivity_threshold_minutes`: Configured threshold that triggered the alert
- `status`: Current status, set to `"no_activity"`
- `activity_check`: Detailed breakdown of activity checks
  - `command_activity_enabled`: Whether command checking is enabled
  - `command_activity_detected`: Whether commands were detected (false in alert)
  - `network_activity_enabled`: Whether network checking is enabled  
  - `network_activity_detected`: Whether network activity was detected (false in alert)
  - `network_threshold_bytes`: Configured network traffic threshold

## HTTP Headers

The webhook request includes the following headers:

```
Content-Type: application/json
User-Agent: LabServerMonitor/1.0
Authorization: Bearer <your-token>
```

If `webhook_auth` is configured, it will be automatically prefixed with "Bearer " if not already present.

## Retry Logic

If the webhook request fails, the agent will retry:
- **Up to 3 times** (configurable via `max_retries`)
- **5 seconds** delay between attempts (configurable via `retry_delay_seconds`)
- All failures are logged for troubleshooting

## Example Use Cases

### 1. Slack Notification
```json
{
  "enabled": true,
  "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "webhook_auth": null,
  "inactivity_window_minutes": 120
}
```

### 2. PagerDuty Alert
```json
{
  "enabled": true,
  "webhook_url": "https://events.pagerduty.com/v2/enqueue",
  "webhook_auth": "your-pagerduty-token",
  "inactivity_window_minutes": 30
}
```

### 3. Custom Monitoring System with Network Traffic Monitoring
```json
{
  "enabled": true,
  "webhook_url": "https://your-monitoring.com/api/alerts/server",
  "webhook_auth": "Bearer your-api-token",
  "inactivity_window_minutes": 60,
  "check_command_activity": true,
  "check_network_activity": true,
  "network_traffic_bytes_threshold": 2048
}
```

### 4. Network Traffic Only (No Command Checking)
```json
{
  "enabled": true,
  "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "webhook_auth": null,
  "inactivity_window_minutes": 30,
  "check_command_activity": false,
  "check_network_activity": true,
  "network_traffic_bytes_threshold": 5120
}
```

### 5. High Sensitivity (Strict Monitoring)
```json
{
  "enabled": true,
  "webhook_url": "https://your-endpoint.com/api/alert",
  "webhook_auth": "Bearer token",
  "inactivity_window_minutes": 15,
  "check_command_activity": true,
  "check_network_activity": true,
  "network_traffic_bytes_threshold": 512
}
```

## Security Considerations

1. **Authentication**: Always use HTTPS for webhook URLs to encrypt sensitive data
2. **Token Security**: Store webhook authentication tokens securely
3. **Network Isolation**: Consider firewall rules to restrict webhook destinations
4. **Logging**: Webhook requests and responses are logged for audit purposes

## Testing

To test the inactivity alert:

1. Configure the webhook URL to a test endpoint (e.g., https://webhook.site)
2. Set `inactivity_window_minutes` to a short duration (e.g., 5 minutes)
3. Start the monitoring agent
4. Wait for the configured duration without executing any commands
5. Check your webhook endpoint for the alert payload

## Troubleshooting

### Alerts Not Sending
- Check that `enabled` is set to `true` in config
- Verify `webhook_url` is correct and accessible
- Check logs for webhook request errors
- Ensure network connectivity to the webhook endpoint

### Too Many Alerts
- Increase `inactivity_window_minutes` to reduce alert frequency
- Review server activity patterns
- Consider implementing alert deduplication on the receiving end

### Authentication Failures
- Verify `webhook_auth` token is valid
- Check if webhook endpoint requires specific header format
- Review webhook logs for authentication error messages

## Log Messages

The agent logs the following messages related to inactivity alerts:

- **Info**: `"Inactivity webhook sent successfully"`
- **Warning**: `"Inactivity webhook attempt X failed"`
- **Error**: `"Inactivity webhook failed after X attempts"`
- **Debug**: `"Activity detected, inactivity alert reset"`

