#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer compiled binary if present, else venv python, else system python
BIN_PATH="$SCRIPT_DIR/../build/dist/las-agent"
PY_BIN="$SCRIPT_DIR/../venv/bin/python"
USE_BINARY=false

if [ -x "$BIN_PATH" ]; then
  USE_BINARY=true
elif [ -x "$PY_BIN" ]; then
  :
else
  PY_BIN="python3"
fi

# Required args (env with defaults)
ES_HOST="${ES_HOST:-http://localhost:9200}"
ES_INDEX="${ES_INDEX:-lab_monitoring}"
INTERVAL="${INTERVAL:-30}"
IGNORE_USERS="${IGNORE_USERS:-system root Administrator SYSTEM}"

# Security settings (env with defaults)
MONITOR_API_KEY="${MONITOR_API_KEY:-}"
MONITOR_ALLOWED_COMMANDS="${MONITOR_ALLOWED_COMMANDS:-}"
MONITOR_BIND_HOST="${MONITOR_BIND_HOST:-127.0.0.1}"
ENABLE_REMOTE_EXEC="${ENABLE_REMOTE_EXEC:-false}"
MONITOR_RATE_LIMIT="${MONITOR_RATE_LIMIT:-10}"

# Build command line in foreground (no nohup)
if $USE_BINARY; then
  CMD=("$BIN_PATH")
else
  CMD=("$PY_BIN" "$SCRIPT_DIR/../monitor_agent.py")
fi

CMD+=(--es_host "$ES_HOST" --es_index "$ES_INDEX" --interval "$INTERVAL" --ignore_users $IGNORE_USERS)

# Optional auth
if [ -n "${ES_USER:-}" ]; then CMD+=(--es_user "$ES_USER"); fi
if [ -n "${ES_PASS:-}" ]; then CMD+=(--es_pass "$ES_PASS"); fi
if [ -n "${ES_API_KEY:-}" ]; then CMD+=(--es_api_key "$ES_API_KEY"); fi

# TLS options
if [ -n "${ES_CA_CERTS:-}" ]; then CMD+=(--es_ca_certs "$ES_CA_CERTS"); fi
case "${ES_INSECURE:-}" in
  1|true|TRUE|yes|YES) CMD+=(--es_insecure) ;;
esac
if [ -n "${ES_SSL_ASSERT_HOSTNAME:-}" ]; then CMD+=(--es_ssl_assert_hostname "$ES_SSL_ASSERT_HOSTNAME"); fi
if [ -n "${ES_SSL_ASSERT_FINGERPRINT:-}" ]; then CMD+=(--es_ssl_assert_fingerprint "$ES_SSL_ASSERT_FINGERPRINT"); fi

# Timeouts / refresh
if [ -n "${ES_TIMEOUT:-}" ]; then CMD+=(--es_timeout "$ES_TIMEOUT"); fi
if [ -n "${ES_REFRESH:-}" ]; then CMD+=(--es_refresh "$ES_REFRESH"); fi

# Listen port
if [ -n "${AGENT_PORT:-}" ]; then CMD+=(--listen_port "$AGENT_PORT"); fi

# Cross-index scoring
if [ -n "${CMD_SCORE_INDEX_PATTERN:-}" ]; then CMD+=(--cmd_score_index_pattern "$CMD_SCORE_INDEX_PATTERN"); fi

# Security parameters
if [ -n "${MONITOR_API_KEY:-}" ]; then CMD+=(--api-key "$MONITOR_API_KEY"); fi
if [ -n "${MONITOR_ALLOWED_COMMANDS:-}" ]; then CMD+=(--allowed-commands $MONITOR_ALLOWED_COMMANDS); fi
if [ -n "${MONITOR_BIND_HOST:-}" ]; then CMD+=(--bind-host "$MONITOR_BIND_HOST"); fi
case "${ENABLE_REMOTE_EXEC:-}" in
  1|true|TRUE|yes|YES) CMD+=(--enable-remote-exec) ;;
esac
if [ -n "${MONITOR_RATE_LIMIT:-}" ]; then CMD+=(--rate-limit "$MONITOR_RATE_LIMIT"); fi

exec "${CMD[@]}"



