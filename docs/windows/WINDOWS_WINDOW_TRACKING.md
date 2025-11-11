# Windows Application & Window Usage Tracking

## ✅ **Implemented Feature**

The monitoring agent now tracks **application and window usage on Windows** using native Windows APIs.

## 🎯 What It Tracks

### 1. **Current Foreground Window**
- Process name (e.g., "chrome.exe", "code.exe")
- Window title (e.g., "GitHub - project/repo")
- Process ID (PID)
- Executable path

### 2. **Window Switches**
- Detects when user switches between applications
- Tracks time spent in each window/app
- Records switch events with timestamps

### 3. **Application Usage Statistics**
- Total time spent per application
- Number of sessions per application
- Window titles used per application
- Last used timestamp
- First seen timestamp

### 4. **Top Applications**
- Most used applications by time
- Application usage frequency
- Unique windows accessed

## 🔧 How It Works

### API Used
- **Windows API** via `ctypes`
- `GetForegroundWindow()` - Get current foreground window handle
- `GetWindowTextW()` - Get window title
- `psutil` - Get process information from PID

### Collection Frequency
- Checks every **5 seconds** by default
- Lightweight (uses native APIs)
- Non-intrusive

### Data Flow

```
Every 5 seconds:
  ↓
Check foreground window (Windows API)
  ↓
Detect if window/app changed?
  ↓
YES → Calculate time spent on previous window
   → Update application usage stats
   → Send to engagement scoring
   → Log window switch
  ↓
Update tracking state
```

## 📊 Data Sent to Elasticsearch

### Window Activity Summary (Every 15 min)

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "current_application": {
    "process_name": "code.exe",
    "window_title": "project.py - Visual Studio Code",
    "session_duration_seconds": 245.5
  },
  "application_usage": {
    "code.exe": {
      "total_time_seconds": 3600,
      "session_count": 8,
      "unique_windows": 12,
      "window_samples": [
        "project.py - Visual Studio Code",
        "app.py - Visual Studio Code",
        "config.json - Visual Studio Code"
      ],
      "last_used": "2024-01-15T10:30:00.000Z"
    },
    "chrome.exe": {
      "total_time_seconds": 1800,
      "session_count": 5,
      "unique_windows": 3
    }
  },
  "recent_window_changes": [
    {
      "timestamp": "2024-01-15T10:28:15.000Z",
      "previous_process": "chrome.exe",
      "previous_window": "GitHub - Issues",
      "time_spent_seconds": 120.5,
      "current_process": "code.exe",
      "current_window": "project.py - Visual Studio Code"
    }
  ],
  "total_applications_used": 5
}
```

## 🎯 Use Cases

### 1. **Productivity Analytics**
- See which applications users spend most time on
- Identify learning tools vs entertainment apps
- Measure focus time vs multitasking

### 2. **Engagement Tracking**
- Track IDE usage (code.exe, vscode, etc.)
- Monitor research time (browser activity)
- Measure documentation work

### 3. **Learning Progress**
- Development tools usage (IDEs, terminals)
- Code editor activity
- Documentation tools

### 4. **Resource Optimization**
- Identify most-used applications
- Track application switching patterns
- Measure focus vs context-switching

## 📝 What You Get

### Dashboard Can Show:

1. **Current Activity**
   - What application is user currently using
   - How long they've been in that application
   - Application name and window title

2. **Usage Patterns**
   - Top 10 applications by time
   - Application frequency charts
   - Time distribution across apps

3. **Productivity Metrics**
   - Active development time (IDE usage)
   - Research time (browser usage)
   - Focus vs context switching

4. **Engagement Insights**
   - Which learning tools are being used
   - Application diversity
   - Work patterns over time

## ⚠️ Requirements

### Windows Only
This feature only works on **Windows** systems

### Dependencies
- `psutil` - Already required
- `ctypes` - Python standard library
- `wintypes` - Windows type definitions

### No Additional Privileges Required
- Works without admin privileges (uses public APIs)
- Non-intrusive foreground window polling
- Respects user privacy (only tracks foreground window)

## 🔄 Comparison: Windows vs Linux

### Windows (New Feature):
- ✅ Foreground window tracking
- ✅ Application name + window title
- ✅ Time spent per application
- ✅ Window switch events
- ✅ Application usage summaries

### Linux (Original):
- ✅ Command execution tracking (audit logs)
- ✅ Process monitoring
- ⚠️ Window tracking limited (requires X11)

## 📈 Data Volume

### Per Day:
- **Window switches**: ~200-500 events
- **Application summaries**: 96 summaries (every 15 min)
- **Usage statistics**: Included in summaries

### Sent to ES:
- Only **significant events** and **aggregated summaries**
- Not every 5-second check
- Volume optimized with aggregation

## 🎉 Benefits

✅ **Comprehensive Activity Tracking**
- Know what applications users are using
- Track productivity vs entertainment
- Measure learning tool usage

✅ **Better Engagement Metrics**
- IDE usage = productive development
- Browser usage = research/documentation
- Multiple app types = learning diversity

✅ **Windows-Specific Insights**
- PowerShell vs cmd usage
- Visual Studio vs VS Code usage
- Windows-specific tools tracking

✅ **Dashboard Analytics**
- Application heatmaps
- Usage pattern analysis
- Productivity scoring

## 🚀 Ready to Use

The Windows window tracking is now integrated and will automatically:
1. **Detect** if running on Windows
2. **Enable** window monitoring automatically
3. **Track** window/application usage
4. **Send** summaries to Elasticsearch (aggregated)
5. **Integrate** with engagement scoring

No additional configuration needed!

