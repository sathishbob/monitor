#!/usr/bin/env bash

set -euo pipefail

# Build a single-file Linux binary using PyInstaller.
# Produces build/dist/monitor-agent (Linux). Run this script on Linux.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="venv"
PYTHON_BIN="python3"

if [ ! -d "$VENV_DIR" ]; then
  echo "[build] Creating virtualenv..."
  $PYTHON_BIN -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "[build] Upgrading pip..."
pip install --upgrade pip >/dev/null

echo "[build] Installing requirements... (this can take a while)"
pip install -r requirements.txt >/dev/null
pip install pyinstaller >/dev/null

echo "[build] Building onefile binary..."
pyinstaller \
  --onefile \
  --name las-agent \
  --clean \
  --distpath build/dist \
  --workpath build/monitor-agent \
  --specpath build \
  monitor_agent.py

echo "[build] Done. Binary at: $PROJECT_ROOT/build/dist/las-agent"



