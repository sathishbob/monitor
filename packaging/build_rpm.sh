#!/bin/bash
# Build script for creating RPM package

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/package"
RPM_DIR="$PACKAGE_DIR/rpm"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Building RPM Package"
echo "========================================="
echo

# Clean previous builds
rm -rf "$RPM_DIR"

# Create tarball
echo "Creating source tarball..."
mkdir -p "$RPM_DIR/SOURCES"
tar -czf "$RPM_DIR/SOURCES/las-agent-1.0.0.tar.gz" \
    --transform "s,^,las-agent-1.0.0/," \
    agent/ \
    monitor_agent.py \
    requirements.txt \
    config.json \
    README.md \
    setup/ \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude="*.spec"

# Copy spec file
cp "$PACKAGE_DIR/rpm/las-agent.spec" "$RPM_DIR/las-agent.spec"

# Build RPM
echo "Building RPM package..."
rpmbuild -ba --define "_topdir $RPM_DIR" "$RPM_DIR/las-agent.spec"

echo
echo "========================================="
echo "Package created successfully!"
echo "========================================="
echo "Location: $RPM_DIR/RPMS/x86_64/las-agent-1.0.0-1.*.rpm"
echo
echo "To install:"
echo "  sudo rpm -ivh $RPM_DIR/RPMS/x86_64/las-agent-*.rpm"
echo
echo "Or on RHEL/CentOS:"
echo "  sudo yum install $RPM_DIR/RPMS/x86_64/las-agent-*.rpm"
echo

