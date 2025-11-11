#!/bin/bash
# Build script for creating Windows installation package

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/package"
WIN_DIR="$PACKAGE_DIR/windows_installer"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Building Windows Installation Package"
echo "========================================="
echo

# Clean previous builds
rm -rf "$WIN_DIR"
mkdir -p "$WIN_DIR/las-agent"

# Copy application files
cp -r agent "$WIN_DIR/las-agent/"
cp monitor_agent.py "$WIN_DIR/las-agent/"
cp requirements.txt "$WIN_DIR/las-agent/"
cp config.json "$WIN_DIR/las-agent/"
cp README.md "$WIN_DIR/las-agent/"
cp setup/run_service_windows.ps1 "$WIN_DIR/las-agent/setup/"

# Copy installation scripts
cp "$PACKAGE_DIR/windows/install.bat" "$WIN_DIR/las-agent/"
cp "$PACKAGE_DIR/windows/install.ps1" "$WIN_DIR/las-agent/"
cp "$PACKAGE_DIR/windows/uninstall.bat" "$WIN_DIR/las-agent/"

# Create installation instructions
cat > "$WIN_DIR/las-agent/INSTALL.txt" << 'EOF'
Lab Server Monitoring Agent - Windows Installation
==================================================

INSTALLATION INSTRUCTIONS:
--------------------------

Option 1: PowerShell Installer (Recommended)
---------------------------------------------
1. Right-click install.ps1 and select "Run with PowerShell"
2. Or run in PowerShell: .\install.ps1


Option 2: Batch File Installer
--------------------------------
1. Right-click install.bat and select "Run as Administrator"
2. Follow the prompts


Option 3: Manual Installation
-----------------------------
1. Ensure Python 3.8+ is installed
2. Run: python -m venv venv
3. Run: venv\Scripts\activate
4. Run: pip install -r requirements.txt
5. Run: python monitor_agent.py

UNINSTALLATION:
---------------
Run uninstall.bat as Administrator

SERVICE MANAGEMENT:
-------------------
Start:   net start las-agent
Stop:    net stop las-agent
Status:  sc query las-agent

For PowerShell:
Start:   Start-Service -Name las-agent
Stop:    Stop-Service -Name las-agent
Status:  Get-Service -Name las-agent

REQUIREMENTS:
-------------
- Windows 10/11 or Windows Server 2016+
- Python 3.8 or higher
- Administrator privileges for installation
- NSSM (Non-Sucking Service Manager) for service installation

CONFIGURATION:
--------------
Edit config.json to configure:
- Elasticsearch connection
- Monitoring intervals
- API settings
- Inactivity alert settings

SUPPORT:
--------
For issues and documentation, see:
https://github.com/your-repo/monitor

EOF

# Create ZIP archive
echo "Creating ZIP archive..."
cd "$WIN_DIR"
zip -r las-agent-windows-1.0.0.zip las-agent/

echo
echo "========================================="
echo "Package created successfully!"
echo "========================================="
echo "Location: $WIN_DIR/las-agent-windows-1.0.0.zip"
echo
echo "To install, extract the ZIP and run:"
echo "  - install.ps1 (PowerShell - Recommended)"
echo "  - install.bat (Batch file)"
echo

