# Setup Directory

This directory contains all setup, start, and run scripts for the Lab Server Monitoring Agent.

## Scripts

### Setup Scripts
- `setup.sh` - Linux/Unix setup script
- `setup_windows.ps1` - Windows PowerShell setup script

### Start Scripts
- `start_monitor.sh` - Linux/Unix startup script
- `start_monitor.bat` - Windows startup script
- `start_secure.sh` - Secure startup script with security features

### Service Scripts
- `run_service.sh` - Linux service runner script
- `run_service_windows.ps1` - Windows service runner script
- `monitor-agent.service` - Systemd service file

## Usage

### Setup
```bash
# From setup directory
./setup.sh

# Windows
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

### Starting the Agent
```bash
# From setup directory
./start_monitor.sh start

# Windows
start_monitor.bat start
```

### Service Installation

#### Linux (systemd)
```bash
# Copy service file
sudo cp setup/monitor-agent.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable --now monitor-agent
```

#### Windows (NSSM)
```powershell
# Install service using NSSM
$svcName = 'monitor-agent'
$base = 'C:\opt\monitor'
$exe = Join-Path $base 'setup\run_service_windows.ps1'
nssm install $svcName powershell.exe
nssm set $svcName AppParameters "-ExecutionPolicy Bypass -File `"$exe`" -WorkingDir `"$base`""
nssm set $svcName AppDirectory $base
nssm start $svcName
```

## Script Details

### Setup Scripts
- **`setup.sh`**: Installs OS dependencies, creates virtual environment, configures auditd
- **`setup_windows.ps1`**: Installs Python/Git via Chocolatey, creates virtual environment, enables security auditing

### Start Scripts
- **`start_monitor.sh`**: Full-featured startup script with status, stop, restart, logs commands
- **`start_monitor.bat`**: Windows equivalent of start_monitor.sh
- **`start_secure.sh`**: Secure startup with API key validation and security features

### Service Scripts
- **`run_service.sh`**: Minimal service runner for systemd
- **`run_service_windows.ps1`**: Minimal service runner for Windows services
- **`monitor-agent.service`**: Systemd service configuration

## Path Updates

All scripts use relative paths from the setup directory:
- Python script: `../monitor_agent.py`
- Virtual environment: `../venv/` or `../monitor_env/`
- Build binaries: `../build/dist/`
- Test scripts: `../test/`
- Documentation: `../docs/`

## Notes

- All scripts are now located in the setup directory
- Service scripts are optimized for minimal overhead
- Start scripts include comprehensive status and management features
- Security scripts include API key validation and rate limiting
