# Installation Guide - Complete Package System

## 🎯 Overview

The monitoring agent can be installed via pre-built packages that automatically handle:
- ✅ All prerequisites installation
- ✅ Python virtual environment setup
- ✅ Service registration and startup
- ✅ User/account management (Linux)
- ✅ Complete configuration

## 📦 Package Types

### 1. Debian Package (.deb)
**Platforms:** Ubuntu, Debian  
**Built with:** `./build_debian.sh`  
**Install:** `sudo dpkg -i las-agent_1.0.0-1_amd64.deb`

### 2. RPM Package (.rpm)
**Platforms:** RHEL, CentOS, Fedora, Rocky Linux, AlmaLinux  
**Built with:** `./build_rpm.sh`  
**Install:** `sudo rpm -ivh las-agent-1.0.0-1.*.rpm`

### 3. Windows Installer (ZIP)
**Platforms:** Windows 10/11, Windows Server 2016+  
**Built with:** `./build_windows.sh`  
**Install:** Extract and run `install.ps1` as Administrator

## 🚀 Quick Start

### Build All Packages
```bash
cd packaging
./build_all.sh
```

### Install on Target System

**Debian/Ubuntu:**
```bash
sudo dpkg -i package/las-agent_1.0.0-1_amd64.deb
sudo systemctl start las-agent
sudo systemctl enable las-agent  # Start on boot
```

**RHEL/CentOS:**
```bash
sudo rpm -ivh package/rpm/RPMS/x86_64/las-agent-*.rpm
sudo systemctl start las-agent
sudo systemctl enable las-agent  # Start on boot
```

**Windows:**
```powershell
# Run as Administrator
.\install.ps1

# Or use batch file
.\install.bat
```

## 📋 What Gets Installed

### Linux Installation
```
/opt/las-agent/
├── agent/                    # Main application modules
├── venv/                     # Python virtual environment
├── config.json              # Configuration file
├── requirements.txt         # Python dependencies list
└── setup/
    └── run_service.sh       # Service runner script

/etc/systemd/system/
└── las-agent.service        # Systemd service file

/var/log/las-agent/      # Log directory

User: las-agent (auto-created)
Service: las-agent (auto-configured)
```

### Windows Installation
```
C:\Program Files\las-agent\
├── agent\                   # Main application modules
├── venv\                    # Python virtual environment
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies list
└── setup\
    └── run_service_windows.ps1  # Service runner script

C:\Program Files\las-agent\logs\
├── service.log             # Service output
└── service-error.log       # Error log

Service: las-agent (auto-installed)
```

## 🔧 Post-Installation Configuration

### Linux
```bash
# Edit configuration
sudo nano /opt/las-agent/config.json

# Configure Elasticsearch connection
# Update server_id for cross-server comparison
# Set up inactivity alerts

# Restart service
sudo systemctl restart las-agent
```

### Windows
```powershell
# Edit configuration
notepad "C:\Program Files\las-agent\config.json"

# Configure Elasticsearch connection
# Update server_id for cross-server comparison
# Set up inactivity alerts

# Restart service
Restart-Service -Name las-agent
```

## ✅ Verification

### Linux
```bash
# Check service status
systemctl status las-agent

# View logs
journalctl -u las-agent -f

# Check if monitoring data is being sent
tail -f /var/log/las-agent/monitor.log
```

### Windows
```powershell
# Check service status
Get-Service -Name las-agent

# View logs
Get-Content "C:\Program Files\las-agent\logs\service.log" -Tail 50

# Check if monitoring data is being sent
Get-Content "C:\Program Files\las-agent\logs\service.log" -Tail 100
```

## 🛠️ Service Management

### Linux (systemd)
```bash
# Start service
sudo systemctl start las-agent

# Stop service
sudo systemctl stop las-agent

# Restart service
sudo systemctl restart las-agent

# Check status
sudo systemctl status las-agent

# Enable on boot
sudo systemctl enable las-agent

# Disable on boot
sudo systemctl disable las-agent

# View logs
sudo journalctl -u las-agent -f
```

### Windows
```powershell
# Start service
Start-Service -Name las-agent

# Stop service
Stop-Service -Name las-agent

# Restart service
Restart-Service -Name las-agent

# Check status
Get-Service -Name las-agent

# View logs
Get-Content "C:\Program Files\las-agent\logs\service.log" -Tail 100
```

## 🗑️ Uninstallation

### Linux - Debian
```bash
sudo dpkg -r las-agent

# Optional: Remove configuration and data
sudo rm -rf /opt/las-agent
sudo rm -rf /var/log/las-agent
```

### Linux - RPM
```bash
sudo rpm -e las-agent

# Optional: Remove configuration and data
sudo rm -rf /opt/las-agent
sudo rm -rf /var/log/las-agent
```

### Windows
```powershell
# Run as Administrator
.\uninstall.bat

# Or manually remove service
Stop-Service -Name las-agent
sc delete las-agent
```

## 🔍 Troubleshooting

### Service Won't Start

**Linux:**
```bash
# Check service logs
sudo journalctl -u las-agent

# Check configuration
sudo /opt/las-agent/venv/bin/python /opt/las-agent/monitor_agent.py --help

# Test Elasticsearch connection
curl http://localhost:9200
```

**Windows:**
```powershell
# Check Event Viewer
Get-EventLog -LogName Application -Source las-agent

# Check logs
Get-Content "C:\Program Files\las-agent\logs\service-error.log"

# Test Python environment
& "C:\Program Files\las-agent\venv\Scripts\python.exe" --version
```

### Elasticsearch Connection Issues

```bash
# Test Elasticsearch connectivity
curl https://es.zippyops.com

# Check configuration
grep "es.host" /opt/las-agent/config.json

# Verify authentication
curl -u user:pass https://es.zippyops.com
```

### Permission Issues

**Linux:**
```bash
# Fix ownership
sudo chown -R las-agent:las-agent /opt/las-agent
sudo chown -R las-agent:las-agent /var/log/las-agent

# Fix permissions
sudo chmod +x /opt/las-agent/setup/run_service.sh
```

**Windows:**
```powershell
# Check service account permissions
sc qc las-agent

# Update permissions if needed
icacls "C:\Program Files\las-agent" /grant las-agent:F
```

## 📊 Data Verification

### Check Elasticsearch Data
```bash
# Query data from your server
curl "https://es.zippyops.com/lab_monitoring/_search?size=5&sort=timestamp:desc" \
  -u user:pass | jq

# Check recent performance data
curl "https://es.zippyops.com/lab_monitoring/_search?q=event_type:performance" \
  -u user:pass | jq

# Check cross-server comparison
curl "https://es.zippyops.com/lab_monitoring/_search?q=event_type:cross_server_comparison" \
  -u user:pass | jq
```

## 🔄 Updates

### Debian/Ubuntu
```bash
# Download new package
# Install
sudo dpkg -i las-agent_1.1.0-1_amd64.deb

# Configuration is preserved
sudo systemctl restart las-agent
```

### RPM
```bash
# Download new package
# Install (upgrade)
sudo rpm -Uvh las-agent-1.1.0-1.*.rpm

# Configuration is preserved
sudo systemctl restart las-agent
```

### Windows
```powershell
# Stop service
Stop-Service -Name las-agent

# Backup configuration
Copy-Item "C:\Program Files\las-agent\config.json" -Destination "$env:TEMP\config.json.bak"

# Extract new package
# Copy new files over old

# Restore configuration
Copy-Item "$env:TEMP\config.json.bak" -Destination "C:\Program Files\las-agent\config.json"

# Update service if needed
# Restart service
Start-Service -Name las-agent
```

## 📝 Configuration Reference

### Key Settings in config.json

```json
{
  "elasticsearch": {
    "host": "https://es.zippyops.com",
    "index": "lab_monitoring",
    "user": "elastic",
    "pass": "password"
  },
  "monitoring": {
    "interval": 30,
    "server_id": "lab_server_01",
    "api_key": "your-api-key"
  },
  "inactivity_alert": {
    "enabled": false,
    "webhook_url": null,
    "inactivity_window_minutes": 60,
    "check_command_activity": true,
    "check_network_activity": true,
    "network_traffic_bytes_threshold": 1024
  },
  "data_aggregation": {
    "enabled": true,
    "aggregation_interval_minutes": 15,
    "buffer_max_size": 1000
  }
}
```

## 🎓 Best Practices

1. **Configuration**: Always backup config.json before changes
2. **Elasticsearch**: Ensure elasticsearch is accessible before installing
3. **Network**: Configure firewall rules for Elasticsearch access
4. **Monitoring**: Monitor disk space for log files
5. **Security**: Use strong API keys and Elasticsearch authentication
6. **Testing**: Test configuration with `--help` flag before deploying
7. **Documentation**: Keep installation records for reference

## 📚 Additional Resources

- Main README: `/README.md`
- Packaging Guide: `packaging/README.md`
- Windows Support: `docs/windows/WINDOWS_SUPPORT_SUMMARY.md`
- Security Guide: `docs/api/SECURITY.md`
- Feature Docs: `docs/features/INACTIVITY_ALERT_FEATURE.md`

