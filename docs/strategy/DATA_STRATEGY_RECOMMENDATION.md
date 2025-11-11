# Recommended Data Strategy (Remote Dashboard)

## Revised Architecture

Since the **dashboard is remote and reads from Elasticsearch**, here's the optimized approach:

```
┌────────────────────────────────────────┐
│   Current: Everything to ES            │
│   • 6,000-10,000 docs/day              │
│   • All raw data                       │
│   • High cost                          │
└────────────────────────────────────────┘
            ↓
┌────────────────────────────────────────┐
│   Recommended: Filtered & Aggregated    │
│   • 300-400 docs/day (95% reduction)   │
│   • Aggregated summaries only          │
│   • 80% cost savings                   │
└────────────────────────────────────────┘
```

## Key Changes

### 1. **Aggregation Intervals** (Most Impact)

**Current:** Every 30 seconds → 2,880 documents/day
**Recommended:** Every 15 minutes → 96 documents/day

**Implementation:**
- Collect every 30s (unchanged for real-time monitoring)
- Buffer in memory (last 15-30 min window)
- Send **only aggregated summary** every 15 min to ES
- Calculate: avg, min, max, std_dev from window

### 2. **Command Filtering**

**Current:** ALL commands → ES
**Recommended:** Only significant commands

**Filter Logic:**
- ✅ Always send: Dangerous commands
- ✅ Always send: High-risk commands (sudo, rm -rf, etc.)
- ✅ Always send: Commands with errors
- ❌ Don't send: Routine commands (ls, cd, cat, etc.)
- ❌ Don't send: Frequently repeated commands

### 3. **User Activity Summaries**

**Current:** Every 30s → ES (2,880 docs/day)
**Recommended:** Session summaries → ES

**When to Send:**
- ✅ Session start (important event)
- ✅ Session end with summary
- ✅ Activity milestones (hourly summary)
- ❌ Don't send: Every 30s update

### 4. **Engagement Metrics**

**Current:** Real-time updates → ES
**Recommended:** Milestones only → ES

**Send Only:**
- ✅ Engagement score changes (significant)
- ✅ Risk level changes
- ✅ Milestone achievements
- ❌ Don't send: Minor incremental updates

## Implementation Plan

### Step 1: Add Aggregation Buffer (Week 1)

```python
# agent/data_aggregator.py
class DataAggregator:
    """Aggregates metrics before sending to ES."""
    
    def __init__(self, interval_minutes: int = 15):
        self.interval = interval_minutes
        self.performance_window = deque(maxlen=interval_minutes * 2)
        self.last_sent = datetime.now()
    
    def add_performance_metric(self, metric: Dict) -> None:
        """Buffer metric for aggregation."""
        self.performance_window.append(metric)
    
    def should_aggregate_and_send(self) -> bool:
        """Check if aggregation interval has elapsed."""
        if not self.performance_window:
            return False
        
        elapsed = (datetime.now() - self.last_sent).total_seconds() / 60
        return elapsed >= self.interval
    
    def aggregate_metrics(self) -> Dict[str, Any]:
        """Aggregate buffered metrics into summary."""
        if not self.performance_window:
            return None
        
        metrics_list = list(self.performance_window)
        
        # Calculate aggregations
        cpu_values = [m['cpu']['utilization_percent'] for m in metrics_list]
        memory_values = [m['memory']['ram_percent'] for m in metrics_list]
        
        aggregated = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sample_count': len(metrics_list),
            'time_window_minutes': self.interval,
            'cpu': {
                'avg': np.mean(cpu_values),
                'max': np.max(cpu_values),
                'min': np.min(cpu_values),
                'std': np.std(cpu_values)
            },
            'memory': {
                'avg': np.mean(memory_values),
                'max': np.max(memory_values),
                'min': np.min(memory_values)
            },
            # ... more aggregations
        }
        
        return aggregated
```

### Step 2: Modify Agent to Use Aggregator (Week 1)

```python
# agent/agent.py modifications

def __init__(self, ...):
    # ... existing code ...
    self.data_aggregator = DataAggregator(interval_minutes=15)

def _collect_performance_data(self) -> None:
    """Collect and buffer performance metrics."""
    try:
        # Collect metric (unchanged)
        metrics = self.performance_monitor.collect_metrics()
        
        # Buffer for aggregation
        self.data_aggregator.add_performance_metric(metrics)
        
        # Only send aggregated summary to ES (every 15 min)
        if self.data_aggregator.should_aggregate_and_send():
            aggregated = self.data_aggregator.aggregate_metrics()
            if aggregated:
                self.es_manager.index_document({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'server_id': self.server_id,
                    'event_type': 'performance_metrics_aggregated',
                    'data': aggregated
                })
                # Clear buffer
                self.data_aggregator.performance_window.clear()
                self.data_aggregator.last_sent = datetime.now()
```

### Step 3: Command Filtering (Week 2)

```python
# agent/command_monitor.py modifications

def should_send_to_elasticsearch(self, command_data: Dict) -> bool:
    """Determine if command should be sent to ES."""
    command = command_data.get('command', '').lower()
    
    # Always send dangerous commands
    if command_data.get('dangerous', False):
        return True
    
    # Always send high-risk commands
    dangerous_patterns = ['sudo', 'rm -rf', 'chmod 777', 'su -', 'passwd']
    if any(pattern in command for pattern in dangerous_patterns):
        return True
    
    # Don't send routine commands
    routine_commands = ['ls', 'pwd', 'cd', 'cat', 'echo', 'date', 'whoami', 'clear']
    if any(cmd in command for cmd in routine_commands):
        return False
    
    # Send commands with significant execution time
    if command_data.get('execution_time', 0) > 5.0:  # 5+ seconds
        return True
    
    # Send commands with errors
    if command_data.get('exit_code', 0) != 0:
        return True
    
    # Skip routine commands
    return False
```

### Step 4: Session Summaries Only (Week 2)

```python
# agent/engagement_scoring.py modifications

def end_session(self, user_id: str, timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """End session and send ONLY summary to ES (not updates)."""
    # ... existing code ...
    
    # Send ONLY final summary, not intermediate updates
    session_summary = {
        'session_id': session['session_id'],
        'user_id': user_id,
        'start_time': session['start_time'].isoformat(),
        'end_time': timestamp.isoformat(),
        'duration_minutes': duration_minutes,
        'commands_executed': session['commands_executed'],
        'engagement_score': self._calculate_session_engagement(session),
        'status': 'completed',
        'timestamp': timestamp.isoformat()
    }
    
    # Send to ES
    self.push_to_elasticsearch(session_summary, 'engagement_session')
    
    return session_summary
```

## Expected Results

### Volume Reduction

| Data Type | Current | Recommended | Reduction |
|-----------|---------|-------------|-----------|
| Performance Metrics | 2,880/day | 96/day | **97%** |
| User Activity | 2,880/day | 96/day | **97%** |
| Commands | 300/day | 50/day | **83%** |
| Engagement Metrics | 750/day | 50/day | **93%** |
| Risk Assessments | 25/day | 25/day | 0% |
| **TOTAL** | **6,835/day** | **317/day** | **95%** |

### Cost Savings

**Current:**
- 6,835 docs/day × 30 days = **205,050 docs/month**
- Estimated ES cost: **$50-100/month per server**

**Recommended:**
- 317 docs/day × 30 days = **9,510 docs/month**
- Estimated ES cost: **$10-20/month per server**
- **Savings: 80-85%**

### Dashboard Experience

**What Dashboard Gets:**

1. **Recent Data (Last 6 Hours)**
   - Aggregated performance summaries every 15 min
   - Recent significant events
   - Current user activity

2. **Historical Data (Days/Weeks)**
   - Daily/Weekly summaries
   - Trends and patterns
   - Anomalies and alerts

3. **Real-Time Alerts**
   - All critical events
   - Security alerts
   - Risk assessments

## Benefits

✅ **95% volume reduction** - Massive cost savings  
✅ **Better ES performance** - Less writes = faster queries  
✅ **Faster dashboard** - Less data to query = better performance  
✅ **Same insights** - Aggregated data provides same analytics  
✅ **Simple implementation** - In-memory buffer, no new infrastructure  

## Migration Strategy

### Phase 1: Deploy Aggregator (Non-Breaking)
- Add `DataAggregator` class
- Modify `_collect_performance_data()` to buffer first
- Send aggregated summaries every 15 min
- Keep existing code as fallback

### Phase 2: Monitor & Validate (Week 2)
- Compare aggregated vs raw data
- Verify dashboard still works
- Check ES document count reduction
- Validate data quality

### Phase 3: Add Filtering (Week 3)
- Implement command filtering
- Add session summary logic
- Enable engagement milestone tracking
- Monitor volume reduction

### Phase 4: Production Cutover (Week 4)
- Remove old direct-to-ES code
- Enable full aggregation
- Monitor performance improvements
- Track cost savings

## Conclusion

**Recommendation: Implement In-Memory Aggregation**

- ✅ No local database needed (dashboard reads from ES)
- ✅ Simple implementation (buffer + aggregate)
- ✅ 95% volume reduction
- ✅ 80% cost savings
- ✅ Same dashboard functionality
- ✅ Better ES performance

This approach balances cost efficiency with data quality while keeping the dashboard experience unchanged.

