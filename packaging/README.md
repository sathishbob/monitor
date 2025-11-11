# Package Building Guide

This directory contains packaging scripts and definitions for creating installable packages for multiple platforms.

## 📦 Supported Package Types

1. **Debian Package (.deb)** - For Debian/Ubuntu systems
2. **RPM Package (.rpm)** - For RHEL/CentOS/Fedora systems
3. **Windows Installer** - For Windows 10/11 and Windows Server

## 🏗️ Building Packages

### Build All Packages

```bash
cd packaging
./build_all.sh
```

This will create packages for all platforms.

### Build Individual Packages

#### Debian Package
```bash
./build_debian.sh
```

#### RPM Package
```bash
./build_rpm.sh
```

#### Windows Package
```bash
./build_windows.sh
```

## 📋 Requirements

### For Debian Package:
- `dpkg-deb` tool
- Administrator/root privileges

### For RPM Package:
- `rpmbuild` tool
- `tar` and `gzip` tools
- Administrator/root privileges

### For Windows Package:
- `zip` tool (usually pre-installed on Linux)
- Zip archive for distribution

## 🚀 Installation

### Debian/Ubuntu Installation

```bash
# Install the package
sudo dpkg -i package/las-agent_1.0.0-1_amd64.deb

# If dependencies are missing, fix them:
sudo apt-get install -f

# Start the service
sudo systemctl start las-agent

# Enable on boot
sudo systemctl enable las-agent

# Check status
sudo systemctl status las-agent
```

### RHEL/CentOS Installation

```bash
# Install the package
sudo rpm -ivh package/rpm/RPMS/x86_64/las-agent-1.0.0-1.*.rpm

# Or using yum/dnf
sudo yum install package/rpm/RPMS/x86_64/las-agent-*.rpm

# Start the service
sudo systemctl start las-agent

# Enable on boot
sudo systemctl enable las-agent

# Check status
sudo systemctl status las-agent
```

### Windows Installation

1. **Extract the ZIP file** to a location on the target Windows machine

2. **Run as Administrator** (Required):
   - PowerShell: Right-click `install.ps1` → "Run with PowerShell"
   - Or in PowerShell: `.\install.ps1`
   - Or use: `install.bat` (right-click → "Run as Administrator")

3. **Service Management**:
   ```powershell
   # Start service
   Start-Service -Name las-agent
   
   # Stop service
   Stop-Service -Name las-agent
   
   # Check status
   Get-Service -Name las-agent
   ```

## 🔧 Package Contents

### Debian Package
- Application files in `/opt/las-agent`
- Systemd service file
- Configuration template
- Python virtual environment setup
- Automatic user/group creation

### RPM Package
- Application files in `/opt/las-agent`
- Systemd service file
- Configuration template
- Python virtual environment setup
- Automatic user/group creation

### Windows Package
- Application files in `C:\Program Files\las-agent`
- Installation scripts (PowerShell and Batch)
- Uninstallation script
- NSSM integration for service management
- Python virtual environment setup

## ⚙️ Configuration

All packages install with a default configuration. To customize:

**Linux:**
```bash
# Edit configuration
sudo nano /opt/las-agent/config.json

# Restart service
sudo systemctl restart las-agent
```

**Windows:**
```powershell
# Edit configuration
notepad "C:\Program Files\las-agent\config.json"

# Restart service
Restart-Service -Name las-agent
```

## 🧪 Testing Installation

### Linux (systemd)
```bash
# Check service status
systemctl status las-agent

# View logs
journalctl -u las-agent -f

# Test configuration
sudo /opt/las-agent/venv/bin/python /opt/las-agent/monitor_agent.py --help
```

### Windows
```powershell
# Check service status
Get-Service -Name las-agent

# View logs
Get-Content "C:\Program Files\las-agent\logs\service.log" -Tail 50

# Test configuration
& "C:\Program Files\las-agent\venv\Scripts\python.exe" "C:\Program Files\las-agent\monitor_agent.py" --help
```

## 📝 Package Structure

```
packaging/
├── README.md                       # This file
├── build_all.sh                    # Master build script
├── build_debian.sh                 # Debian package builder
├── build_rpm.sh                    # RPM package builder
├── build_windows.sh                # Windows package builder
├── package/
│   ├── debian/                     # Debian packaging files
│   │   ├── control                 # Package metadata
│   │   ├── postinst                # Post-installation script
│   │   ├── prerm                   # Pre-removal script
│   │   └── postrm                  # Post-removal script
│   ├── rpm/                        # RPM packaging files
│   │   └── las-agent.spec          # RPM spec file
│   └── windows/                    # Windows packaging files
│       ├── install.bat             # Batch installer
│       ├── install.ps1             # PowerShell installer
│       └── uninstall.bat           # Uninstaller
└── package/                        # Output directory
    ├── deb/                        # Debian package build files
    ├── rpm/                        # RPM package build files
    └── windows_installer/          # Windows package build files
```

## 🔄 Updating Packages

### Version Update

To update the version, modify these files:
- `package/debian/control` (Version line)
- `package/rpm/las-agent.spec` (Version line)
- `build_debian.sh` (deb filename)
- `build_rpm.sh` (Source tarball name)
- `build_windows.sh` (ZIP filename)

### Rebuilding

After changes, rebuild:
```bash
./build_all.sh
```

## 🐛 Troubleshooting

### Debian Package Issues
```bash
# Check package contents
dpkg -c package/las-agent_1.0.0-1_amd64.deb

# View package information
dpkg -I package/las-agent_1.0.0-1_amd64.deb

# Remove package
sudo dpkg -r las-agent
```

### RPM Package Issues
```bash
# Check package contents
rpm -qlp package/rpm/RPMS/x86_64/las-agent-*.rpm

# View package information
rpm -qip package/rpm/RPMS/x86_64/las-agent-*.rpm

# Remove package
sudo rpm -e las-agent
```

### Windows Package Issues
- Ensure you run as Administrator
- Check that NSSM is installed or in PATH
- Verify Python 3.8+ is installed
- Check Windows Event Viewer for service errors

## 📚 Additional Resources

- [Debian Packaging Guide](https://www.debian.org/doc/manuals/packaging-tutorial/)
- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)
- [NSSM Documentation](https://nssm.cc/usage)

## ⚡ Quick Reference

```bash
# Build all packages
./build_all.sh

# Install Debian package
sudo dpkg -i package/las-agent_1.0.0-1_amd64.deb

# Install RPM package
sudo rpm -ivh package/rpm/RPMS/x86_64/las-agent-*.rpm

# Windows: Extract ZIP and run install.ps1 as Admin
```

