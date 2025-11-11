# Windows Support - Implementation Summary

## ✅ What Works on Windows

### 1. **Performance & System Monitoring** ✅
- **CPU Usage** - Tracked via `psutil`
- **Memory Usage** - Tracked via `psutil`
- **Disk I/O** - Tracked via `psutil`
- **Network Traffic** - Tracked via `psutil`
- **Process Monitoring** - Works via `psutil`

### 2. **Enhanced Command Tracking** ✅ (Just Implemented)

The Windows implementation now captures:

```json
{
  "command": "C:\\Users\\jsmith\\App.exe --arg1 value1",
  "process_name": "App.exe",
  "user": "DOMAIN\\jsmith",
  "pid": 12345,
  "timestamp": "2024-01-15T10:30:00.000+00:00",
  "dangerous": false,
  "execution_time": 5.2
}
```

**Captured Data:**
- ✅ Full command line with arguments
- ✅ Process name
- ✅ Domain username
- ✅ Process ID (PID)
- ✅ Accurate timestamp from Event Log
- ✅ Dangerous command detection
- ✅ Execution time estimation

**How It Works:**
- Queries Windows Event Log (ID 4688 - Process Creation)
- Uses PowerShell to extract detailed event data
- Parses XML event data for command line, user, process info
- Estimates execution time based on command patterns
- Filters dangerous commands for security alerts

### 3. **All Core Features** ✅
- **Data Aggregation** - Works cross-platform
- **Engagement Scoring** - Works with captured data
- **Risk Assessment** - Works with available metrics
- **Dashboard Integration** - Reads from Elasticsearch
- **Inactivity Alerts** - Works (uses both command + network activity)
- **Network Traffic Monitoring** - Works for inactivity detection

## 📋 Windows Requirements

### Prerequisites:
1. **Admin Privileges** - Required to read Security Event Log
2. **Event ID 4688 Enabled** - Process creation logging must be enabled
3. **PowerShell Access** - Must be able to execute PowerShell

### Enable Event ID 4688 (If Needed):

```powershell
# Run as Administrator
auditpol /set /category:"Detailed Tracking" /success:enable /failure:enable
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
```

Or via Group Policy:
- Computer Configuration → Policies → Windows Settings → Security Settings → Advanced Audit Policy
- Enable "Audit Detailed Tracking" → "Audit Process Creation"

## 🎯 Quick Start on Windows

### 1. Install Requirements:
```powershell
pip install psutil requests flask elasticsearch
```

### 2. Configure for Windows:
Edit `config.json`:
```json
{
  "monitoring": {
    "server_id": "windows_server_01",
    "interval": 30
  },
  "elasticsearch": {
    "host": "https://es.zippyops.com",
    "index": "lab_monitoring"
  }
}
```

### 3. Run with Admin Privileges:
```powershell
# Run as Administrator
python monitor_agent.py --config config.json
```

## 🔍 What You'll Get

### Dashboard Data from Windows:

1. **Performance Metrics** (Every 15 min aggregate)
   - CPU utilization averages
   - Memory usage statistics
   - Disk I/O summaries
   - Network throughput

2. **Command Events** (Filtered)
   - All dangerous commands
   - Commands with errors
   - Long-running commands (>5 sec)
   - NOT: Routine commands (ls, cd, etc.)

3. **User Activity**
   - Active users
   - Session summaries
   - Process counts

4. **Security Alerts**
   - Dangerous command detection
   - Risk assessments
   - Anomaly detection

## ⚠️ Limitations

### What's Different on Windows:

| Feature | Linux | Windows |
|---------|-------|---------|
| Command Arguments | ✅ Full | ✅ Full (just added) |
| Execution Time | ✅ Actual | ⚠️ Estimated |
| Process Trees | ✅ Full | ⚠️ Limited |
| Audit Trail | ✅ Detailed | ⚠️ Event Log |
| Real-time Tracking | ✅ Yes | ⚠️ Delayed (Event Log) |

### Execution Time on Windows:
- **Linux**: Uses actual process creation/exit times
- **Windows**: Estimates based on command patterns:
  - Quick commands: 0.1 seconds
  - Build/compile/backup: 5 seconds
  - Default: 0.5 seconds

## 🧪 Testing on Windows

### Test Command Tracking:
```python
from agent.command_monitor import CommandMonitor

monitor = CommandMonitor()
commands = monitor.get_windows_commands()

for cmd in commands:
    print(f"User: {cmd['user']}")
    print(f"Command: {cmd['command']}")
    print(f"Time: {cmd['timestamp']}")
    print("---")
```

### Check If Event Log Access Works:
```powershell
# Run as Administrator
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4688} -MaxEvents 5
```

If you see output, Windows command tracking will work.

## 📊 Expected Data Volume on Windows

### Per Day:
- **Performance**: 96 aggregated summaries (vs 2,880 raw on Linux)
- **Commands**: ~100-200 filtered events (vs all commands on Linux)
- **Activity**: 96 summaries
- **Total**: ~300-400 documents/day

### Volume Reduction: **~95%** (same as Linux implementation)

## ✅ Conclusion

**Windows Support Status:**
- ✅ **Performance Monitoring**: Full support
- ✅ **Command Tracking**: Enhanced support (just implemented)
- ✅ **Data Aggregation**: Works perfectly
- ✅ **Dashboard**: Will receive all necessary data
- ✅ **Volume Reduction**: 95% reduction works on Windows too

**Bottom Line:**
The monitoring agent **WORKS ON WINDOWS** and will:
- Track system performance
- Capture command execution (with arguments!)
- Monitor user activity
- Send aggregated data to Elasticsearch
- Support dashboard analytics
- Provide 95% volume reduction

Just needs:
- Admin privileges
- Event Log access configured
- Python + dependencies installed

