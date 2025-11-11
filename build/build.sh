#!/usr/bin/env bash

# Build wrapper script for Lab Server Monitoring Agent
# This script delegates to the appropriate build script in build/scripts/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SCRIPT="$SCRIPT_DIR/scripts/build.sh"

if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "Error: Build script not found at $BUILD_SCRIPT"
    exit 1
fi

echo "Building Lab Server Monitoring Agent..."
echo "Using build script: $BUILD_SCRIPT"
echo

cd "$SCRIPT_DIR"
exec "$BUILD_SCRIPT" "$@"
