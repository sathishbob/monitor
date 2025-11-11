#!/bin/bash
# Build script for creating Debian package (.deb)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/package"
DEB_DIR="$PACKAGE_DIR/deb"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Building Debian Package"
echo "========================================="
echo

# Clean previous builds
rm -rf "$DEB_DIR"

# Create build structure
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/opt/las-agent"
mkdir -p "$DEB_DIR/var/log/las-agent"

# Copy control files
cp "$PACKAGE_DIR/debian/control" "$DEB_DIR/DEBIAN/"
cp "$PACKAGE_DIR/debian/postinst" "$DEB_DIR/DEBIAN/"
cp "$PACKAGE_DIR/debian/prerm" "$DEB_DIR/DEBIAN/"
cp "$PACKAGE_DIR/debian/postrm" "$DEB_DIR/DEBIAN/"

chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"
chmod 755 "$DEB_DIR/DEBIAN/postrm"

# Copy application files
cp -r agent "$DEB_DIR/opt/las-agent/"
cp monitor_agent.py "$DEB_DIR/opt/las-agent/"
cp requirements.txt "$DEB_DIR/opt/las-agent/"
cp config.json "$DEB_DIR/opt/las-agent/config.json.example"
cp README.md "$DEB_DIR/opt/las-agent/"

# Copy setup scripts
mkdir -p "$DEB_DIR/opt/las-agent/setup"
cp setup/run_service.sh "$DEB_DIR/opt/las-agent/setup/"
chmod +x "$DEB_DIR/opt/las-agent/setup/run_service.sh"

# Create packaging directory structure
mkdir -p "$DEB_DIR/etc/systemd/system"

# Install systemd service with new name
cp setup/las-agent.service "$DEB_DIR/etc/systemd/system/las-agent.service"

# Build .deb package
echo "Building .deb package..."
dpkg-deb --build "$DEB_DIR" "$PACKAGE_DIR/las-agent_1.0.0-1_amd64.deb"

echo
echo "========================================="
echo "Package created successfully!"
echo "========================================="
echo "Location: $PACKAGE_DIR/las-agent_1.0.0-1_amd64.deb"
echo
echo "To install:"
echo "  sudo dpkg -i $PACKAGE_DIR/las-agent_1.0.0-1_amd64.deb"
echo
echo "To install with dependencies:"
echo "  sudo apt-get install -f"
echo

