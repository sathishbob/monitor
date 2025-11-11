#!/bin/bash
# Master build script - Builds packages for all platforms

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Building All Package Types"
echo "========================================="
echo

# Build Debian package
echo "Building Debian package..."
./build_debian.sh
echo

# Build RPM package
echo "Building RPM package..."
./build_rpm.sh
echo

# Build Windows package
echo "Building Windows package..."
./build_windows.sh
echo

echo "========================================="
echo "All Packages Built Successfully!"
echo "========================================="
echo
echo "Generated packages:"
echo "  - package/las-agent_1.0.0-1_amd64.deb"
echo "  - package/rpm/RPMS/x86_64/las-agent-1.0.0-1.*.rpm"
echo "  - package/windows_installer/las-agent-windows-1.0.0.zip"
echo
echo "Installation commands:"
echo "  Debian/Ubuntu: sudo dpkg -i package/las-agent_1.0.0-1_amd64.deb"
echo "  RHEL/CentOS:   sudo rpm -ivh package/rpm/RPMS/x86_64/las-agent-*.rpm"
echo "  Windows:       Extract ZIP and run install.ps1"
echo

