# Lab Server Monitoring AI Agent

A comprehensive Python-based AI agent for monitoring lab server performance, user activity, and providing intelligent analytics.

## Features

- **Cross-platform Support**: Runs on both Linux and Windows systems
- **Performance Monitoring**: Tracks CPU, RAM, Disk, and Network metrics with 95% data volume reduction
- **User Activity Tracking**: Monitors active windows, keyboard input, and clipboard content
- **Command Monitoring**: Logs user-executed commands with dangerous command detection
- **Windows Application Tracking**: Monitors application usage and window activity (Windows only)
- **AI-Powered Analytics**: 
  - Anomaly detection for user activity
  - Time-series forecasting for performance metrics
  - User activity scoring and gamification support
  - Skill gap identification and dropout risk prediction
- **Inactivity Alerts**: Configurable webhook alerts when no activity is detected (command + network)
- **Data Aggregation**: Intelligent 95% volume reduction while maintaining data quality
- **Elasticsearch Integration**: Pushes aggregated data to Elasticsearch for dashboard analysis
- **Remote Command Execution**: Flask endpoint for remote command execution (optional)
- **Robust Error Handling**: Comprehensive logging and error recovery

## Requirements

### System Requirements
- Python 3.8 or higher
- Elasticsearch 7.x or higher
- Linux or Windows operating system

### Python Dependencies
Install the required packages using:
```bash
pip install -r requirements.txt
```

### Single-file Binaries
- Linux: build with `cd build && ./scripts/build.sh` (produces `build/dist/las-agent`)
- Windows: build with `cd build && powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1` (produces `build/dist/las-agent.exe`)

Run the binary directly:
```bash
./build/dist/las-agent \
  --es_host https://es.zippyops.com \
  --es_index lab_monitoring \
  --es_user <user> \
  --es_pass <pass> \
  --es_api_key <id:key-or-key> \
  --es_ca_certs /path/to/ca.crt \
  --es_insecure \
  --es_ssl_assert_hostname false \
  --es_ssl_assert_fingerprint "AA:BB:...:ZZ" \
  --es_timeout 30 \
  --es_refresh wait_for \
  --listen_port 5000 \
  --interval 30 \
  --ignore_users system root Administrator SYSTEM \
  --cmd_score_index_pattern 'lab_monitoring*'
```
On Windows:
```powershell
./build/dist/las-agent.exe `
  --es_host https://es.zippyops.com `
  --es_index lab_monitoring `
  --es_user <user> `
  --es_pass <pass> `
  --es_api_key <id:key-or-key> `
  --es_ca_certs C:\path\to\ca.crt `
  --es_insecure `
  --es_ssl_assert_hostname false `
  --es_ssl_assert_fingerprint "AA:BB:...:ZZ" `
  --es_timeout 30 `
  --es_refresh wait_for `
  --listen_port 5000 `
  --interval 30 `
  --ignore_users system root Administrator SYSTEM `
  --cmd_score_index_pattern 'lab_monitoring*'
```

## Installation

### Quick Install (Recommended)
Use pre-built packages for easy installation with automatic prerequisites and service setup.

**Debian/Ubuntu:**
```bash
# Build the package
cd packaging && ./build_debian.sh

# Install
sudo dpkg -i package/las-agent_1.0.0-1_amd64.deb
sudo apt-get install -f  # Fix dependencies if needed
sudo systemctl start las-agent
```

**RHEL/CentOS:**
```bash
# Build the package
cd packaging && ./build_rpm.sh

# Install
sudo rpm -ivh package/rpm/RPMS/x86_64/las-agent-*.rpm
sudo systemctl start las-agent
```

**Windows:**
```powershell
# Build the package
cd packaging
.\build_windows.sh  # On Linux, use build_windows.sh from WSL
# Extract the ZIP and run as Administrator:
.\install.ps1
```

See `packaging/README.md` for detailed package building and installation instructions.

### Manual Installation

1. **Clone or download the project**:
```bash
git clone <repository-url>
cd monitor
```

2. **Prepare the OS and install dependencies**:

   - Linux (Ubuntu/Debian/CentOS/RHEL/Alma/Rocky):
```bash
sudo bash setup/setup.sh
```

   - Windows (PowerShell as Administrator):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
./setup/setup_windows.ps1
```

3. **Configure Elasticsearch**:
   - Ensure Elasticsearch is running on your system
   - Default connection: `http://localhost:9200`
   - The agent will automatically create the index if it doesn't exist

4. **Configure the agent** (optional):
   - Edit `config.json` to customize settings
   - Or use command-line arguments

## Usage

### Basic Usage

Start the monitoring agent with default settings:
```bash
python monitor_agent.py
```

### Advanced Usage

Use command-line arguments to customize behavior:
```bash
python monitor_agent.py \
    --es_host https://es.zippyops.com \
    --es_index lab_monitoring \
    --listen_port 8080 \
    --interval 60 \
    --ignore_users system root Administrator
```

### Command-Line Arguments

- `--es_host`: Elasticsearch host URL (default: http://localhost:9200)
- `--es_index`: Elasticsearch index name (default: lab_monitoring)
- `--es_user`: Elasticsearch basic auth username (env: `ES_USER`)
- `--es_pass`: Elasticsearch basic auth password (env: `ES_PASS`)
- `--es_api_key`: Elasticsearch API key (either `id:key` or just `key`) (env: `ES_API_KEY`)
- `--es_ca_certs`: Path to CA certs file (env: `ES_CA_CERTS`)
- `--es_insecure`: Disable TLS certificate verification (use with caution)
- `--es_ssl_assert_hostname`: Override asserted TLS hostname, or set to `false` to disable hostname verification (use with caution) (env: `ES_SSL_ASSERT_HOSTNAME`)
- `--es_ssl_assert_fingerprint`: Pin TLS cert by SHA256 fingerprint (env: `ES_SSL_ASSERT_FINGERPRINT`)
- `--es_timeout`: Request timeout seconds (default: 15) (env: `ES_TIMEOUT`)
- `--es_refresh`: Index refresh mode for indexing visibility (`false` | `true` | `wait_for`) (env: `ES_REFRESH`)
- `--listen_port`: Flask API listening port (default: 5000 or env `AGENT_PORT`)
- `--interval`: Data collection interval in seconds (default: 30)
- `--ignore_users`: List of users to ignore for command tracking
- `--cmd_score_index_pattern`: Index pattern (e.g., `lab_monitoring*`) to compare command volume across servers (env: `CMD_SCORE_INDEX_PATTERN`)

**Security Arguments:**
- `--api-key`: API key for Flask endpoints authentication (env: `MONITOR_API_KEY`)
- `--allowed-commands`: List of allowed commands for remote execution (env: `MONITOR_ALLOWED_COMMANDS`)
- `--bind-host`: Host to bind Flask server to (default: 127.0.0.1 for security) (env: `MONITOR_BIND_HOST`)
- `--enable-remote-exec`: Enable remote command execution (disabled by default for security)
- `--rate-limit`: Rate limit per minute for API endpoints (default: 10) (env: `MONITOR_RATE_LIMIT`)

Note: In addition to CLI args, many values can be supplied via environment variables as indicated above and are also passed through by `start_monitor.sh` when set.

### Remote Command Execution

The agent provides a Flask endpoint for remote command execution:

**⚠️ SECURITY NOTICE**: Remote command execution is **DISABLED by default** for security reasons. To enable it, you must:

1. Set an API key for authentication
2. Explicitly enable remote execution
3. Configure allowed commands whitelist

```bash
# Generate a secure API key
export MONITOR_API_KEY=$(openssl rand -hex 32)

# Enable remote execution with security
./las-agent \
  --enable-remote-exec \
  --api-key "$MONITOR_API_KEY" \
  --bind-host 127.0.0.1 \
  --allowed-commands "ps df free uptime"
```

**Security Features:**
- API key authentication required
- Command whitelist validation
- Rate limiting (10 requests/minute by default)
- Dangerous command pattern blocking
- Comprehensive audit logging
- Localhost-only binding by default

**API Usage:**
```bash
# Health check (no auth required)
curl http://localhost:5000/health

# List allowed commands
curl -H "Authorization: Bearer $MONITOR_API_KEY" \
     http://localhost:5000/commands

# Execute command
curl -X POST \
     -H "Authorization: Bearer $MONITOR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"command": "ps aux"}' \
     http://localhost:5000/execute
```

**For detailed security information, see [docs/api/SECURITY.md](docs/api/SECURITY.md)**

For comprehensive documentation, see the [docs/](docs/) directory.

```bash
# Execute a command remotely
curl -X POST http://localhost:5000/execute \
    -H "Content-Type: application/json" \
    -d '{"command": "ls -la"}'
```

**Note**: Remote command execution output is NOT pushed to Elasticsearch for security reasons.

## Data Collection

### Performance Metrics
- CPU usage percentage and frequency
- Memory usage (total, available, percentage)
- Disk usage and I/O statistics
- Network I/O statistics

### User Activity
- Active window information (title, process, user)
- Clipboard content (limited to 1000 characters)
- Idle time tracking
- User activity scoring

### Command Monitoring
- User-executed commands (via auditd on Linux, Event Logs on Windows)
- Dangerous command detection
- System process filtering

### AI Analytics
- Anomaly detection for performance metrics
- Time-series forecasting (ARIMA model)
- User activity scoring (0-100 scale)
- Skill gap identification

## Configuration

### config.json
The configuration file allows you to customize various aspects of the agent:

```json
{
    "elasticsearch": {
        "host": "http://localhost:9200",
        "index": "lab_monitoring",
        "timeout": 30
    },
    "monitoring": {
        "interval": 30,
        "max_history_size": 1000,
        "log_level": "INFO"
    },
    "users": {
        "ignore_users": ["system", "root", "Administrator", "SYSTEM"]
    }
}
```

## Elasticsearch Integration

### Index Structure
The agent creates an index with the following mapping:
```json
{
    "mappings": {
        "properties": {
            "timestamp": {"type": "date"},
            "type": {"type": "keyword"},
            "data": {"type": "object"}
        }
    }
}
```

### Data Types
- `performance`: System performance metrics
- `active_window`: Active window information
- `clipboard`: Clipboard content
- `command`: User-executed commands
- `user_analysis`: AI-generated user activity analysis
- `forecast`: Time-series forecasts

## Security Considerations

1. **Dangerous Command Detection**: The agent automatically detects and logs potentially dangerous commands
2. **User Filtering**: Configure users to ignore for command tracking
3. **System Process Filtering**: Automatically filters out system processes to reduce noise
4. **Remote Command Security**: Remote command execution is available but outputs are not logged to Elasticsearch

## Troubleshooting

### Common Issues

1. **Elasticsearch Connection Failed**:
   - Ensure Elasticsearch is running
   - Check the host URL and port
   - Verify network connectivity

2. **Permission Denied** (Linux):
   - Run with appropriate permissions for auditd access
   - Ensure user has access to `/var/log/audit/audit.log`

3. **Executed Commands Not Visible**:
   - Ensure `auditd` is installed and active (`setup.sh` enables this)
   - Verify rules loaded: `sudo ausearch -k exec_log -ts recent | tail -n 10`
   - Make sure the agent can read `/var/log/audit/audit.log` (run as root or adjust permissions)
   - In Kibana, filter by `type: command` and widen time range

3. **GUI Features Not Working**:
   - On headless Linux servers, GUI features are automatically disabled
   - Ensure X11 is available for GUI features on Linux

4. **Import Errors**:
   - Install missing dependencies: `pip install -r requirements.txt`
   - Some platform-specific packages may not be available

### Logging

The agent creates detailed logs in `monitor_agent.log`. Check this file for troubleshooting:
```bash
tail -f monitor_agent.log
```

## Service Installation

### Linux (systemd)

1) Copy files:
```bash
sudo mkdir -p /opt/las-agent
sudo cp -r . /opt/las-agent
sudo chown -R monitor:monitor /opt/las-agent || true
sudo chmod +x /opt/las-agent/run_service.sh
```

2) Install service:
```bash
sudo cp /opt/las-agent/las-agent.service /etc/systemd/system/las-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now las-agent
```

3) Optional environment overrides:
```bash
sudo systemctl edit las-agent
# Under [Service], set:
# Environment=ES_HOST=https://es.zippyops.com
# Environment=ES_INDEX=lab_monitoring
# Environment=CMD_SCORE_INDEX_PATTERN=lab_monitoring*
```

View logs:
```bash
journalctl -u las-agent -f
```

### Windows (service via NSSM)

1) Install NSSM (https://nssm.cc/).

2) Place files in `C:\opt\las-agent`, build `dist\las-agent.exe` or use Python.

3) Install the service (PowerShell as Administrator):
```powershell
$svcName = 'las-agent'
$base    = 'C:\\opt\\las-agent'
$exe     = Join-Path $base 'run_service_windows.ps1'
nssm install $svcName powershell.exe
nssm set $svcName AppParameters "-ExecutionPolicy Bypass -File `"$exe`" -WorkingDir `"$base`""
nssm set $svcName AppDirectory $base
# Optional environment
nssm set $svcName AppEnvironmentExtra "ES_HOST=https://es.zippyops.com"
nssm set $svcName AppEnvironmentExtra "ES_INDEX=lab_monitoring"
nssm set $svcName AppEnvironmentExtra "CMD_SCORE_INDEX_PATTERN=lab_monitoring*"
nssm start $svcName
```

Logs: check Windows Event Viewer (Application) or configure NSSM I/O redirection.

## Build System

This project includes a comprehensive build system in the `build/` directory:

- **[Build Scripts](build/README.md)** - Build system documentation
- **`build/build.sh`** - Linux/Unix build script
- **`build/build_windows.ps1`** - Windows build script

For detailed build documentation, see [build/README.md](build/README.md).

## Setup and Scripts

This project includes comprehensive setup and management scripts in the `setup/` directory:

- **[Setup Scripts](setup/README.md)** - Installation and configuration scripts
- **`setup/setup.sh`** - Linux/Unix setup script
- **`setup/setup_windows.ps1`** - Windows setup script
- **`setup/start_monitor.sh`** - Linux/Unix startup script
- **`setup/start_monitor.bat`** - Windows startup script

For detailed script documentation, see [setup/README.md](setup/README.md).

## Documentation

This project includes comprehensive documentation organized in the `docs/` directory:

### Quick Start
- **[Implementation Summary](docs/guides/IMPLEMENTATION_SUMMARY.md)** - What's been implemented
- **[Documentation Index](docs/guides/DOCUMENTATION_INDEX.md)** - Complete documentation guide

### Features
- **[Inactivity Alerts](docs/features/INACTIVITY_ALERT_FEATURE.md)** - Configure inactivity alerts
- **[Gamification Guide](docs/features/GAMIFICATION_GUIDE.md)** - Gamify training

### Windows Support
- **[Windows Support Summary](docs/windows/WINDOWS_SUPPORT_SUMMARY.md)** - Quick Windows guide
- **[Windows Compatibility](docs/windows/WINDOWS_COMPATIBILITY.md)** - Platform compatibility
- **[Windows Window Tracking](docs/windows/WINDOWS_WINDOW_TRACKING.md)** - Application monitoring
- **[AI Metrics on Windows](docs/windows/AI_METRICS_WINDOWS.md)** - AI capabilities

### Data Strategy
- **[Data Strategy Recommendation](docs/strategy/DATA_STRATEGY_RECOMMENDATION.md)** - Data optimization
- **[Data Strategy Analysis](docs/strategy/DATA_STRATEGY_ANALYSIS.md)** - Deep analysis
- **[Windows Verification](docs/strategy/DATA_STRATEGY_WINDOWS_VERIFICATION.md)** - Platform verification

### Reference
- **[Security Guide](docs/api/SECURITY.md)** - Comprehensive security documentation
- **[Security Summary](docs/api/SECURITY_SUMMARY.md)** - Quick security reference
- **[Data Types](docs/reference/ENGAGEMENT_DATA_TYPES.md)** - Data structures

For detailed documentation index, see [docs/README.md](docs/README.md).

## Testing

The project includes comprehensive test scripts located in the `test/` directory:

### Installation Test
```bash
python3 test/test_installation.py
```
Tests all dependencies, basic functionality, and platform-specific features.

### Security Test
```bash
python3 test/test_security.py http://localhost:5000 your-api-key
```
Tests the Flask API security features including authentication, command blocking, and rate limiting.

### Elasticsearch Connection Test
```bash
python3 test/test_es_connection.py [host] [index_name]
```
Tests Elasticsearch connectivity and index creation.

For detailed test documentation, see [test/README.md](test/README.md).

## Development

### Adding New Metrics
1. Extend the `PerformanceMonitor` class
2. Add new data collection methods
3. Update the `MonitorAgent.collect_performance_data()` method

### Adding New AI Features
1. Extend the `AIModel` class
2. Implement new analysis methods
3. Integrate with the main monitoring loop

### Platform-Specific Features
- Windows: Use `win32gui`, `win32process` for GUI features
- Linux: Use `Xlib`, `pynput` for GUI features
- Headless servers: Automatically disable GUI-dependent features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Recent Updates

### Data Aggregation (Implemented)
- **95% volume reduction** - Intelligent aggregation reduces ES documents by 95%
- **Cost savings** - 80% reduction in Elasticsearch costs
- **Smart filtering** - Only significant commands sent to ES
- **Aggregated summaries** - 15-minute intervals instead of 30 seconds

### Windows Support (Enhanced)
- **Window tracking** - Application and window usage monitoring
- **Enhanced command tracking** - Captures command-line arguments
- **Event Log integration** - Improved Windows Event Log parsing
- **Full AI features** - All analytics work on Windows

### Inactivity Alerts (New Feature)
- **Command + network monitoring** - Detects both command and network activity
- **Configurable webhooks** - Send alerts to external systems
- **Time-based windows** - Configurable inactivity thresholds
- **Retry logic** - Automatic retry on failures

See [docs/changelog/](docs/changelog/) for detailed change history.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `monitor_agent.log`
3. Open an issue on the project repository
