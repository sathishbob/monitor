#!/bin/bash

# Lab Server Monitoring AI Agent - Secure Startup Script
# This script demonstrates how to start the agent with security features enabled

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../monitor_agent.py"
LOG_FILE="$SCRIPT_DIR/../monitor_agent.log"
PID_FILE="$SCRIPT_DIR/../monitor_agent.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    echo "🔐 Secure Monitoring Agent Startup Script"
    echo "=========================================="
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|secure-start}"
    echo ""
    echo "Commands:"
    echo "  start         Start the monitoring agent (default settings)"
    echo "  stop          Stop the monitoring agent"
    echo "  restart       Restart the monitoring agent"
    echo "  status        Show the status of the monitoring agent"
    echo "  logs          Show the latest logs"
    echo "  secure-start  Start with security features enabled"
    echo ""
    echo "Security Features:"
    echo "  🔐 API Key Authentication"
    echo "  🛡️  Command Whitelist Validation"
    echo "  🚫 Dangerous Pattern Blocking"
    echo "  ⏱️  Rate Limiting"
    echo "  📊 Comprehensive Audit Logging"
    echo "  🔒 Localhost-only Binding"
    echo ""
    echo "Environment Variables for Security:"
    echo "  MONITOR_API_KEY         API key for authentication (REQUIRED for remote exec)"
    echo "  MONITOR_ALLOWED_COMMANDS Space-separated list of allowed commands"
    echo "  MONITOR_BIND_HOST       Host to bind to (default: 127.0.0.1)"
    echo "  ENABLE_REMOTE_EXEC      Set to 'true' to enable remote execution"
    echo "  MONITOR_RATE_LIMIT      Rate limit per minute (default: 10)"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start with default security (disabled)"
    echo "  $0 secure-start             # Start with security features enabled"
    echo "  MONITOR_API_KEY=mykey $0 secure-start"
    echo ""
    echo "For full documentation, see ../docs/SECURITY.md"
}

# Function to check if agent is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to generate secure API key
generate_api_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    elif command -v python3 &> /dev/null; then
        python3 -c "import secrets; print(secrets.token_hex(32))"
    else
        print_status $YELLOW "Warning: Could not generate secure API key. Please set MONITOR_API_KEY manually."
        echo "random-key-$(date +%s)"
    fi
}

# Function to start the agent securely
start_agent_secure() {
    if is_running; then
        print_status $YELLOW "Monitoring agent is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    print_status $BLUE "🔐 Starting monitoring agent with security features..."
    
    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        print_status $RED "Error: Python script not found at $PYTHON_SCRIPT"
        return 1
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_status $RED "Error: python3 is not installed or not in PATH"
        return 1
    fi
    
    # Security checks
    if [ -z "${MONITOR_API_KEY:-}" ]; then
        print_status $YELLOW "⚠️  No API key provided. Generating one for you..."
        export MONITOR_API_KEY=$(generate_api_key)
        print_status $GREEN "Generated API key: ${MONITOR_API_KEY:0:16}..."
    fi
    
    if [ "${ENABLE_REMOTE_EXEC:-}" != "true" ]; then
        print_status $YELLOW "⚠️  Remote execution not enabled. Enabling for secure startup..."
        export ENABLE_REMOTE_EXEC=true
    fi
    
    # Set secure defaults if not provided
    export MONITOR_BIND_HOST="${MONITOR_BIND_HOST:-127.0.0.1}"
    export MONITOR_RATE_LIMIT="${MONITOR_RATE_LIMIT:-10}"
    
    # Set default allowed commands if not provided
    if [ -z "${MONITOR_ALLOWED_COMMANDS:-}" ]; then
        export MONITOR_ALLOWED_COMMANDS="ps top htop df du free uptime who w netstat ss lsof iostat vmstat sar dmesg journalctl systemctl service status"
    fi
    
    print_status $GREEN "✅ Security configuration:"
    echo "   🔑 API Key: ${MONITOR_API_KEY:0:16}..."
    echo "   🛡️  Allowed Commands: ${MONITOR_ALLOWED_COMMANDS}"
    echo "   🌐 Bind Host: ${MONITOR_BIND_HOST}"
    echo "   ⏱️  Rate Limit: ${MONITOR_RATE_LIMIT}/minute"
    echo "   🔓 Remote Execution: ENABLED"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Prefer venv Python if available
    PY_BIN="python3"
    if [ -x "$SCRIPT_DIR/../venv/bin/python" ]; then
        PY_BIN="$SCRIPT_DIR/../venv/bin/python"
    elif [ -x "$SCRIPT_DIR/../monitor_env/bin/python" ]; then
        PY_BIN="$SCRIPT_DIR/../monitor_env/bin/python"
    fi

    # Use a single configuration file (config.json) and update it in-place with security settings
    CONFIG_FILE="$SCRIPT_DIR/../config.json"
    
    # Read the base config and update with security settings
    if [ -f "$CONFIG_FILE" ]; then
        # Update the config with security settings using jq if available, or sed as fallback
        if command -v jq &> /dev/null; then
            # Use jq to update config
            jq --arg api_key "$MONITOR_API_KEY" \
               --argjson allowed_commands "$(echo "$MONITOR_ALLOWED_COMMANDS" | tr ' ' '\n' | jq -R . | jq -s .)" \
               --arg bind_host "$MONITOR_BIND_HOST" \
               --argjson rate_limit "$MONITOR_RATE_LIMIT" \
               --argjson enable_remote_exec "true" \
               '.monitoring.api_key = $api_key | .monitoring.allowed_commands = $allowed_commands | .monitoring.bind_host = $bind_host | .monitoring.rate_limit_per_minute = $rate_limit | .monitoring.enable_remote_exec = $enable_remote_exec' \
               "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        else
            # Fallback to sed for basic updates
            sed -i "s/\"api_key\": null/\"api_key\": \"$MONITOR_API_KEY\"/" "$CONFIG_FILE"
            sed -i "s/\"enable_remote_exec\": false/\"enable_remote_exec\": true/" "$CONFIG_FILE"
            sed -i "s/\"bind_host\": \"127.0.0.1\"/\"bind_host\": \"$MONITOR_BIND_HOST\"/" "$CONFIG_FILE"
            sed -i "s/\"rate_limit_per_minute\": 10/\"rate_limit_per_minute\": $MONITOR_RATE_LIMIT/" "$CONFIG_FILE"
        fi
        
        print_status $GREEN "✅ Updated configuration: $CONFIG_FILE"
    else
        print_status $RED "Error: Base config.json not found"
        return 1
    fi
    
    # Build command using single config.json
    CMD=($PY_BIN "$PYTHON_SCRIPT" --config "$CONFIG_FILE")

    print_status $BLUE "🚀 Starting agent with command:"
    echo "   ${CMD[*]}"
    
    nohup "${CMD[@]}" > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        print_status $GREEN "✅ Monitoring agent started successfully (PID: $(cat $PID_FILE))"
        echo "   📝 Logs: $LOG_FILE"
        echo "   🌐 Endpoint: http://${MONITOR_BIND_HOST}:5000"
        echo "   🔑 API Key: ${MONITOR_API_KEY:0:16}..."
        echo ""
        print_status $GREEN "🔐 Security Status: ENABLED"
        echo "   - Authentication: Required"
        echo "   - Command Validation: Active"
        echo "   - Rate Limiting: ${MONITOR_RATE_LIMIT}/minute"
        echo "   - Audit Logging: Active"
        echo ""
        echo "📖 Test the security features:"
        echo "   python3 ../test/test_security.py http://${MONITOR_BIND_HOST}:5000 '$MONITOR_API_KEY'"
    else
        print_status $RED "❌ Error: Failed to start monitoring agent"
        echo "Check logs at: $LOG_FILE"
        return 1
    fi
}

# Function to start the agent (default)
start_agent() {
    if is_running; then
        print_status $YELLOW "Monitoring agent is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    print_status $BLUE "🚀 Starting monitoring agent with default settings..."

    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        print_status $RED "Error: Python script not found at $PYTHON_SCRIPT"
        return 1
    fi

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_status $RED "Error: python3 is not installed or not in PATH"
        return 1
    fi

    # Prefer venv Python if available
    PY_BIN="python3"
    if [ -x "$SCRIPT_DIR/../venv/bin/python" ]; then
        PY_BIN="$SCRIPT_DIR/../venv/bin/python"
    elif [ -x "$SCRIPT_DIR/../monitor_env/bin/python" ]; then
        PY_BIN="$SCRIPT_DIR/../monitor_env/bin/python"
    fi

    # Use single configuration file (config.json) as-is
    CONFIG_FILE="$SCRIPT_DIR/../config.json"
    if [ ! -f "$CONFIG_FILE" ]; then
        print_status $RED "Error: Base config.json not found at $CONFIG_FILE"
        return 1
    fi

    # Build command and start
    CMD=($PY_BIN "$PYTHON_SCRIPT" --config "$CONFIG_FILE")

    print_status $BLUE "🚀 Starting agent with command:"
    echo "   ${CMD[*]}"

    nohup "${CMD[@]}" > "$LOG_FILE" 2>&1 &

    # Save PID
    echo $! > "$PID_FILE"

    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        print_status $GREEN "✅ Monitoring agent started successfully (PID: $(cat $PID_FILE))"
        echo "   📝 Logs: $LOG_FILE"
        echo "   🌐 Endpoint: http://127.0.0.1:5000"
    else
        print_status $RED "❌ Error: Failed to start monitoring agent"
        echo "Check logs at: $LOG_FILE"
        return 1
    fi
}

# Function to stop the agent
stop_agent() {
    if ! is_running; then
        print_status $YELLOW "Monitoring agent is not running"
        return 0
    fi
    
    print_status $BLUE "🛑 Stopping monitoring agent..."
    pid=$(cat "$PID_FILE")
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            print_status $GREEN "✅ Monitoring agent stopped successfully"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    print_status $YELLOW "⚠️  Force killing monitoring agent..."
    kill -9 "$pid" 2>/dev/null
    rm -f "$PID_FILE"
    print_status $GREEN "✅ Monitoring agent force stopped"
}

# Function to show status
show_status() {
    if is_running; then
        pid=$(cat "$PID_FILE")
        print_status $GREEN "✅ Monitoring agent is running (PID: $pid)"
        echo "   📝 Log file: $LOG_FILE"
        
        # Show security status
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "🔐 Security Status:"
            if grep -q "Remote command execution: ENABLED" "$LOG_FILE" 2>/dev/null; then
                print_status $GREEN "   🔓 Remote execution: ENABLED"
                if grep -q "WARNING: No API key set" "$LOG_FILE" 2>/dev/null; then
                    print_status $YELLOW "   ⚠️  Authentication: WARNING - No API key"
                else
                    print_status $GREEN "   🔑 Authentication: Active"
                fi
            else
                print_status $BLUE "   🔒 Remote execution: DISABLED (secure by default)"
            fi
            
            echo ""
            echo "📊 Recent activity:"
            tail -n 5 "$LOG_FILE" | grep -E "(INFO|WARNING|ERROR)" | tail -n 3
        fi
    else
        print_status $YELLOW "❌ Monitoring agent is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Latest logs from $LOG_FILE ==="
        tail -n 50 "$LOG_FILE"
    else
        print_status $YELLOW "No log file found at $LOG_FILE"
    fi
}

# Main script logic
case "${1:-}" in
    start)
        start_agent
        ;;
    stop)
        stop_agent
        ;;
    restart)
        stop_agent
        sleep 2
        start_agent
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    secure-start)
        start_agent_secure
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit $?
