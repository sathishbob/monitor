# Security Guide for Lab Server Monitoring AI Agent

## Overview

The monitoring agent includes several security measures to protect against unauthorized access and malicious command execution. This document outlines the security features and best practices for deployment.

## Security Features

### 1. **Authentication**
- **API Key Authentication**: All sensitive endpoints require a valid API key
- **Bearer Token**: Support for Authorization header with Bearer token
- **Query Parameter**: Fallback support for api_key query parameter
- **Environment Variable**: Set `MONITOR_API_KEY` for secure configuration

### 2. **Command Validation**
- **Whitelist Approach**: Only pre-approved commands are allowed
- **Dangerous Pattern Detection**: Blocks commands containing dangerous patterns
- **Input Sanitization**: Prevents command injection attacks
- **Safe Execution**: Commands run without shell=True to prevent injection

### 3. **Network Security**
- **Default Binding**: Flask server binds to 127.0.0.1 by default (localhost only)
- **Configurable Binding**: Can be changed via `--bind-host` parameter
- **Port Configuration**: Configurable listening port via `--listen-port`

### 4. **Rate Limiting**
- **Per-IP Limiting**: Rate limiting applied per client IP address
- **Configurable Limits**: Default 10 requests per minute, configurable
- **Automatic Reset**: Limits reset every minute

### 5. **Execution Safety**
- **Timeout Protection**: 30-second timeout on command execution
- **Working Directory Restriction**: Commands execute in `/tmp` directory
- **No Shell Execution**: Commands run as arguments, not through shell
- **Output Limiting**: Command output limited to prevent memory issues

### 6. **Audit Logging**
- **Comprehensive Logging**: All access attempts and executions logged
- **Elasticsearch Integration**: Audit events stored in Elasticsearch
- **Client IP Tracking**: Source IP addresses logged for all requests
- **Command History**: Full command execution history maintained

## Default Security Configuration

```bash
# Secure by default - remote execution disabled
./las-agent

# Enable remote execution with security
export MONITOR_API_KEY="your-secure-api-key-here"
./las-agent --enable-remote-exec --bind-host 127.0.0.1
```

## Allowed Commands (Default Whitelist)

The following commands are allowed by default:

**System Monitoring:**
- `ps`, `top`, `htop` - Process monitoring
- `df`, `du` - Disk usage
- `free`, `uptime` - System status
- `who`, `w` - User activity

**Network Monitoring:**
- `netstat`, `ss` - Network connections
- `lsof` - Open files and ports

**System Information:**
- `iostat`, `vmstat`, `sar` - Performance metrics
- `dmesg` - Kernel messages
- `journalctl` - System logs
- `systemctl`, `service`, `status` - Service management

## Dangerous Patterns Blocked

The following patterns are automatically blocked:

**System Commands:**
- `rm -rf`, `del /s /q` - File deletion
- `format`, `mkfs` - Disk formatting
- `shutdown`, `reboot`, `halt` - System shutdown
- `sudo`, `su -` - Privilege escalation

**Network Tools:**
- `netcat`, `nc`, `telnet` - Network access tools
- `ssh-keygen` - SSH key generation

**File Permissions:**
- `chmod 777`, `chmod +x` - Permission changes
- `attrib +s` - Windows attribute changes

**Registry Operations:**
- `reg add`, `reg delete`, `regedit` - Windows registry

**Process Control:**
- `taskkill`, `killall`, `pkill` - Process termination

**Shell Injection:**
- `&&`, `||`, `;`, `|`, `>`, `<` - Shell operators
- `` ` ``, `$()` - Command substitution
- `eval`, `exec`, `system` - Dynamic execution

## Security Best Practices

### 1. **API Key Management**
```bash
# Generate a strong API key
openssl rand -hex 32

# Set environment variable
export MONITOR_API_KEY="your-generated-key"

# Or use command line argument
./las-agent --api-key "your-generated-key"
```

### 2. **Network Access Control**
```bash
# Local access only (recommended)
./las-agent --bind-host 127.0.0.1

# If external access needed, use firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

### 3. **Command Whitelist Customization**
```bash
# Custom allowed commands
./las-agent --allowed-commands ps df free uptime custom_script

# Environment variable
export MONITOR_ALLOWED_COMMANDS="ps,df,free,uptime,custom_script"
```

### 4. **Rate Limiting Configuration**
```bash
# Adjust rate limits
./las-agent --rate-limit 5  # 5 requests per minute

# Environment variable
export MONITOR_RATE_LIMIT=5
```

## Security Monitoring

### 1. **Log Analysis**
Monitor the following log patterns:
```bash
# Authentication failures
grep "Authentication failed" monitor_agent.log

# Rate limit violations
grep "Rate limit exceeded" monitor_agent.log

# Command validation failures
grep "Command validation failed" monitor_agent.log

# Suspicious IP addresses
grep "client_ip" monitor_agent.log | awk '{print $NF}' | sort | uniq -c
```

### 2. **Elasticsearch Queries**
```json
// Failed authentication attempts
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "remote_command"}},
        {"term": {"authenticated": false}}
      ]
    }
  }
}

// Commands by IP address
{
  "query": {
    "term": {"type": "remote_command"}
  },
  "aggs": {
    "by_ip": {
      "terms": {"field": "client_ip"}
    }
  }
}
```

## Incident Response

### 1. **Immediate Actions**
- Disable remote execution: `--enable-remote-exec` flag
- Change API key immediately
- Review logs for unauthorized access
- Check for suspicious commands executed

### 2. **Investigation Steps**
- Analyze Elasticsearch audit logs
- Review system logs for unusual activity
- Check for unauthorized processes
- Verify file system integrity

### 3. **Recovery Steps**
- Rotate all credentials
- Update allowed command whitelist
- Review and tighten network access
- Implement additional monitoring

## Compliance Considerations

### 1. **GDPR Compliance**
- Client IP addresses logged for security
- Consider data retention policies
- Implement data anonymization if required

### 2. **SOC 2 Compliance**
- Comprehensive audit logging
- Access control and authentication
- Rate limiting and abuse prevention
- Security monitoring and alerting

### 3. **PCI DSS Compliance**
- Secure command execution
- Audit trail maintenance
- Access control implementation
- Regular security reviews

## Security Checklist

- [ ] API key is set and secure
- [ ] Remote execution is disabled by default
- [ ] Server binds to localhost only
- [ ] Command whitelist is configured
- [ ] Rate limiting is enabled
- [ ] Audit logging is active
- [ ] Firewall rules are configured
- [ ] Regular security reviews scheduled
- [ ] Incident response plan documented
- [ ] Security monitoring implemented

## Support and Reporting

For security issues or questions:
1. Review this security guide
2. Check the application logs
3. Review Elasticsearch audit data
4. Contact the development team
5. Report security vulnerabilities responsibly
