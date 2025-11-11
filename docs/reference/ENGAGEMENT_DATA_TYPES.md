# 🎯 Engagement Scoring Data Types

This document describes the comprehensive engagement scoring system that tracks student activity and pushes data to Elasticsearch as separate data types.

## 📊 **Data Types Pushed to Elasticsearch**

### **1. 🔐 Engagement Sessions (`engagement_session`)**
Tracks complete user engagement sessions from start to completion.

**Session Start Data:**
```json
{
  "session_id": "student123_1704067200",
  "user_id": "student123",
  "start_time": "2024-01-01T12:00:00Z",
  "status": "started",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Session Completion Data:**
```json
{
  "session_id": "student123_1704067200",
  "user_id": "student123",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T14:30:00Z",
  "duration_seconds": 9000,
  "duration_minutes": 150.0,
  "commands_executed": 45,
  "apps_used": ["terminal", "code", "browser", "git"],
  "productive_time": 7200.0,
  "break_time": 1800.0,
  "engagement_score": 85.0,
  "status": "completed",
  "timestamp": "2024-01-01T14:30:00Z"
}
```

### **2. 📈 Real-time Engagement Metrics (`engagement_metrics`)**
Live engagement metrics updated during active sessions.

```json
{
  "user_id": "student123",
  "session_id": "student123_1704067200",
  "commands_executed": 45,
  "apps_used_count": 4,
  "productive_time": 7200.0,
  "break_time": 1800.0,
  "current_app": "code",
  "session_duration_minutes": 150.0,
  "timestamp": "2024-01-01T14:30:00Z"
}
```

### **3. 🧠 Learning Progress (`learning_progress`)**
Tracks skill development and learning progression across categories.

**Command-based Progress:**
```json
{
  "user_id": "student123",
  "category": "development",
  "skill_level": 15,
  "command": "git commit -m 'feature: add user authentication'",
  "timestamp": "2024-01-01T14:30:00Z"
}
```

**Application-based Progress:**
```json
{
  "user_id": "student123",
  "category": "data_analysis",
  "skill_level": 8,
  "application": "jupyter",
  "timestamp": "2024-01-01T14:30:00Z"
}
```

### **4. 📱 Application Usage Statistics (`app_usage_stats`)**
Detailed tracking of application usage patterns.

```json
{
  "app_name": "code",
  "user_id": "student123",
  "duration_seconds": 3600,
  "total_time": 7200,
  "sessions": 3,
  "last_used": "2024-01-01T14:30:00Z",
  "timestamp": "2024-01-01T14:30:00Z"
}
```

### **5. ⌨️ Command Engagement (`command_engagement`)**
Individual command execution tracking with engagement context.

```json
{
  "command": "git commit -m 'feature: add user authentication'",
  "timestamp": "2024-01-01T14:30:00Z",
  "dangerous": false,
  "duration": 2.5,
  "user_id": "student123",
  "session_id": "student123_1704067200"
}
```

### **6. 📅 Daily Activity (`daily_activity`)**
Aggregated daily engagement metrics.

```json
{
  "user_id": "student123",
  "date": "2024-01-01",
  "total_time_seconds": 9000,
  "productive_time_seconds": 7200,
  "break_time_seconds": 1800,
  "commands_executed": 45,
  "apps_used": 4,
  "timestamp": "2024-01-01T14:30:00Z"
}
```

### **7. 🌐 Cross-Server Metrics (`cross_server_metrics`)**
Comprehensive server-level engagement metrics for comparison.

```json
{
  "server_id": "lab-server-01",
  "timestamp": "2024-01-01T14:30:00Z",
  "period_hours": 24,
  "total_users": 25,
  "total_sessions": 45,
  "total_time_hours": 180.5,
  "avg_engagement_score": 78.5,
  "total_commands": 1250,
  "unique_commands": 89,
  "command_diversity": 0.071,
  "total_apps_used": 12,
  "top_apps": [["terminal", 45], ["code", 38], ["browser", 25]],
  "skill_development": {"development": 156, "system_admin": 89, "networking": 67},
  "total_skill_points": 312,
  "high_engagement_users": 18,
  "medium_engagement_users": 5,
  "low_engagement_users": 2,
  "avg_session_length": 240.7,
  "long_sessions": 28,
  "short_sessions": 8
}
```

### **8. 🏆 Cross-Server Comparison (`cross_server_comparison`)**
Relative performance comparison with peer servers.

```json
{
  "server_id": "lab-server-01",
  "timestamp": "2024-01-01T14:30:00Z",
  "peer_count": 5,
  "comparison_metrics": {
    "avg_engagement_score": {
      "local_value": 78.5,
      "peer_min": 65.2,
      "peer_max": 82.1,
      "peer_avg": 74.3,
      "relative_score": 76.8,
      "percentile": 80.0,
      "rank": 2,
      "total_peers": 5
    },
    "command_diversity": {
      "local_value": 0.071,
      "peer_min": 0.045,
      "peer_max": 0.089,
      "peer_avg": 0.062,
      "relative_score": 59.1,
      "percentile": 60.0,
      "rank": 3,
      "total_peers": 5
    }
  },
  "overall_performance": {
    "score": 67.9,
    "grade": "C+",
    "status": "Average"
  }
}
```

### **9. 🧠 Skill Progress Analytics (`skill_progress_analytics`)**
AI-powered analysis of student skill proficiency based on commands, errors, and retries.

```json
{
  "user_id": "student123",
  "analysis_period": "7 sessions",
  "total_commands": 156,
  "unique_commands": 89,
  "command_categories": {
    "beginner": {
      "count": 45,
      "percentage": 28.8,
      "commands": ["ls", "cd", "pwd", "cat", "echo"]
    },
    "intermediate": {
      "count": 67,
      "percentage": 42.9,
      "commands": ["grep", "find", "sed", "awk", "tar"]
    },
    "advanced": {
      "count": 34,
      "percentage": 21.8,
      "commands": ["git", "docker", "make", "cmake"]
    },
    "expert": {
      "count": 10,
      "percentage": 6.4,
      "commands": ["strace", "gdb", "perf"]
    }
  },
  "error_analysis": {
    "total_error_patterns": 12,
    "error_patterns": {
      "syntax_errors": 5,
      "incomplete_commands": 4,
      "dangerous_commands": 2,
      "permission_errors": 1
    },
    "error_categories": {
      "syntax": 9,
      "system_modification": 2,
      "permissions": 1
    },
    "error_rate": 7.7
  },
  "retry_patterns": {
    "total_retries": 23,
    "retry_patterns": {
      "git": 5,
      "docker": 4,
      "make": 3,
      "grep": 2
    },
    "learning_indicators": {
      "double_attempts": 8,
      "triple_attempts": 3,
      "persistent_attempts": 2
    },
    "learning_efficiency": 85.3,
    "most_retried_commands": [["git", 5], ["docker", 4], ["make", 3]]
  },
  "skill_proficiency_curve": {
    "proficiency_score": 72.5,
    "skill_level": "Advanced",
    "skill_phases": {
      "exploration": 45,
      "practice": 67,
      "mastery": 34,
      "innovation": 10
    },
    "complexity_progression": [
      {
        "timestamp": "2024-01-01T14:30:00Z",
        "command": "git commit -m 'feature: add user authentication'",
        "complexity": "advanced",
        "complexity_score": 3,
        "cumulative_score": 156
      }
    ],
    "learning_velocity": 2.3,
    "total_commands_analyzed": 156,
    "unique_commands_used": 89,
    "skill_growth_rate": 57.1
  },
  "learning_patterns": {
    "study_patterns": {
      "peak_hours": [
        {
          "hour": 14,
          "command_count": 45,
          "percentage": 100.0
        }
      ],
      "consistent_hours": [
        {
          "hour": 14,
          "command_count": 45,
          "consistency_score": 100.0
        }
      ]
    },
    "command_diversity_trend": [
      {
        "window": 1,
        "commands_analyzed": 10,
        "unique_commands": 8,
        "diversity_score": 0.8
      }
    ],
    "total_hours_active": 8,
    "most_active_hour": 14,
    "learning_consistency": 33.3
  },
  "timestamp": "2024-01-01T14:30:00Z"
}
```

### **10. 🔄 Skill Cross-Comparison (`skill_cross_comparison`)**
Comprehensive comparison of student skills against peers and benchmarks.

```json
{
  "user_id": "student123",
  "timestamp": "2024-01-01T14:30:00Z",
  "comparison_period": "current_session",
  "peer_count": 25,
  "comparison_metrics": {
    "proficiency": {
      "user_score": 72.5,
      "peer_min": 45.2,
      "peer_max": 89.7,
      "peer_avg": 68.3,
      "peer_median": 69.1,
      "rank": 8,
      "total_peers": 25,
      "percentile": 68.0,
      "performance_level": "Above Average"
    },
    "learning_efficiency": {
      "user_efficiency": 85.3,
      "peer_min": 62.1,
      "peer_max": 94.8,
      "peer_avg": 78.9,
      "rank": 5,
      "total_peers": 25,
      "percentile": 80.0,
      "efficiency_level": "Efficient"
    },
    "command_diversity": {
      "user_advanced_ratio": 28.2,
      "peer_min": 15.6,
      "peer_max": 45.3,
      "peer_avg": 26.8,
      "rank": 12,
      "total_peers": 25,
      "percentile": 52.0,
      "diversity_level": "Moderately Diverse"
    },
    "error_rate": {
      "user_error_rate": 7.7,
      "peer_min": 3.2,
      "peer_max": 18.9,
      "peer_avg": 9.1,
      "rank": 7,
      "total_peers": 25,
      "percentile": 72.0,
      "error_level": "Low"
    }
  },
  "rankings": {
    "proficiency": [
      {
        "user_id": "top_student",
        "score": 89.7,
        "rank": 1,
        "percentile": 100.0
      }
    ],
    "learning_efficiency": [
      {
        "user_id": "efficient_learner",
        "efficiency": 94.8,
        "rank": 1,
        "percentile": 100.0
      }
    ]
  },
  "percentiles": {
    "proficiency": 68.0,
    "learning_efficiency": 80.0,
    "command_diversity": 52.0,
    "error_rate": 72.0
  },
  "skill_gaps": {
    "critical_gaps": [
      {
        "metric": "command_diversity",
        "user_value": 28.2,
        "top_value": 45.3,
        "gap_percentage": 37.7,
        "recommendation": "Focus on improving command_diversity - significant gap with top performers"
      }
    ],
    "moderate_gaps": [],
    "minor_gaps": [
      {
        "metric": "proficiency",
        "user_value": 72.5,
        "top_value": 89.7,
        "gap_percentage": 19.2,
        "recommendation": "Minor improvement needed in proficiency"
      }
    ],
    "strengths": [
      {
        "metric": "learning_efficiency",
        "user_value": 85.3,
        "top_value": 78.9,
        "gap_percentage": -8.1,
        "status": "Strong performance"
      }
    ]
  },
  "improvement_opportunities": [
    {
      "priority": "High",
      "category": "command_diversity",
      "description": "Focus on improving command_diversity - significant gap with top performers",
      "action_items": [
        "Explore new command-line tools",
        "Learn different programming languages",
        "Practice with various system utilities",
        "Study different domains (networking, security, etc.)"
      ],
      "estimated_effort": "High",
      "expected_impact": "Significant"
    }
  ]
}
```

### **11. 🚨 Dropout Risk Assessment (`dropout_risk_assessment`)**
AI-powered analysis of student disengagement risk and intervention recommendations.

```json
{
  "user_id": "student123",
  "timestamp": "2024-01-01T14:30:00Z",
  "risk_score": 65.0,
  "risk_level": "High",
  "risk_factors": [
    {
      "factor": "inactivity",
      "severity": "high",
      "details": "Inactive for 45.2 minutes",
      "score_impact": 25
    },
    {
      "factor": "repeated_failures",
      "severity": "high",
      "details": "8 failed attempts in recent commands",
      "score_impact": 30
    },
    {
      "factor": "high_error_rate",
      "severity": "medium",
      "details": "Error rate: 35.2%",
      "score_impact": 20
    }
  ],
  "disengagement_indicators": [
    "extended_inactivity",
    "repeated_failures",
    "high_error_rate"
  ],
  "intervention_priority": "High",
  "recommended_actions": [
    {
      "priority": "Immediate",
      "type": "direct_contact",
      "description": "Reach out directly to student to understand challenges",
      "action": "Send personalized message or schedule 1-on-1 session",
      "expected_impact": "High"
    },
    {
      "priority": "High",
      "type": "skill_remediation",
      "description": "Provide targeted skill-building resources",
      "action": "Share tutorial videos or assign mentor for specific topics",
      "expected_impact": "High"
    }
  ]
}
```

## 🏗️ **Elasticsearch Index Structure**

### **Index Naming Convention**
Each data type gets its own index pattern:
- `{base_index}_engagement_session`
- `{base_index}_engagement_metrics`
- `{base_index}_learning_progress`
- `{base_index}_app_usage_stats`
- `{base_index}_command_engagement`
- `{base_index}_daily_activity`
- `{base_index}_cross_server_metrics`
- `{base_index}_cross_server_comparison`
- `{base_index}_skill_progress_analytics`
- `{base_index}_skill_cross_comparison`
- `{base_index}_dropout_risk_assessment`

### **Common Fields (All Documents)**
```json
{
  "timestamp": "ISO 8601 timestamp",
  "type": "data_type_name",
  "data": {
    // Actual data fields as shown above
  }
}
```

## 🎯 **Engagement Scoring Algorithm**

### **Session Engagement Score (0-100 points)**

| Category | Points | Criteria |
|----------|--------|----------|
| **Time-based** | 0-40 | Session duration scoring |
| **Command Activity** | 0-30 | Commands executed |
| **Application Diversity** | 0-20 | Different apps used |
| **Productivity** | 0-10 | Productive vs. break time ratio |

### **Scoring Breakdown**

**Time-based Scoring (0-40 points):**
- 2+ hours: 40 points
- 1+ hours: 30 points
- 30+ minutes: 20 points
- 15+ minutes: 10 points

**Command Activity (0-30 points):**
- 50+ commands: 30 points
- 25+ commands: 20 points
- 10+ commands: 15 points
- 5+ commands: 10 points

**Application Diversity (0-20 points):**
- 5+ apps: 20 points
- 3+ apps: 15 points
- 2+ apps: 10 points

**Productivity (0-10 points):**
- 70%+ productive: 10 points
- 50%+ productive: 7 points
- 30%+ productive: 4 points

## 🏫 **Learning Categories**

### **Skill Development Areas**
1. **Development**: git, python, node, npm, docker, kubectl, java, gcc, make
2. **System Admin**: systemctl, service, ps, top, htop, df, du, netstat, ss
3. **Networking**: ping, traceroute, nmap, wget, curl, ssh, scp, rsync
4. **Data Analysis**: pandas, numpy, matplotlib, jupyter, r, sql, excel
5. **Design**: gimp, inkscape, blender, figma, sketch, photoshop
6. **Documentation**: markdown, latex, asciidoc, sphinx, doxygen
7. **Collaboration**: slack, discord, teams, zoom, meet, webex
8. **Research**: browser, firefox, chrome, safari, edge, research, paper

### **Productivity Indicators**

**High Productivity:**
- git commit, git push, make, build, test, deploy, debug

**Medium Productivity:**
- edit, create, modify, analyze, research, document

**Low Productivity:**
- browse, social, entertainment, game

## 🔌 **API Endpoints**

### **Engagement Reports**
- `GET /engagement/report/<user_id>?days=7` - User engagement report
- `GET /engagement/class-summary?days=7` - Class-wide summary
- `POST /engagement/session/<user_id>` - Manage sessions

### **Cross-Server Comparison**
- `GET /engagement/cross-server-metrics` - Get server-level engagement metrics
- `POST /engagement/cross-server-comparison` - Compare with peer servers
- `GET /engagement/server-leaderboard?metric=avg_engagement_score` - Server ranking
- `GET /engagement/trends?days=7` - Engagement trends over time

### **Dropout Prediction & Intervention**
- `GET /engagement/dropout-risk/<user_id>` - Get dropout risk assessment for a user
- `GET /engagement/struggling-students?risk_threshold=Medium` - Get list of struggling students
- `GET /engagement/disengagement-alerts?hours=24` - Get recent disengagement alerts

### **Session Management**
```bash
# Start a session
curl -X POST http://localhost:5000/engagement/session/student123 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# End a session
curl -X POST http://localhost:5000/engagement/session/student123 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action": "end"}'

# Get cross-server metrics
curl -X GET http://localhost:5000/engagement/cross-server-metrics \
  -H "Authorization: Bearer YOUR_API_KEY"

# Compare with peer servers
curl -X POST http://localhost:5000/engagement/cross-server-comparison \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_data": [
      {
        "server_id": "lab-server-02",
        "avg_engagement_score": 82.1,
        "command_diversity": 0.089,
        "total_skill_points": 298
      },
      {
        "server_id": "lab-server-03",
        "avg_engagement_score": 65.2,
        "command_diversity": 0.045,
        "total_skill_points": 156
      }
    ]
  }'

# Get server leaderboard
curl -X GET "http://localhost:5000/engagement/server-leaderboard?metric=avg_engagement_score" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get engagement trends
curl -X GET "http://localhost:5000/engagement/trends?days=7" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get dropout risk assessment for a user
curl -X GET "http://localhost:5000/engagement/dropout-risk/student123" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get list of struggling students
curl -X GET "http://localhost:5000/engagement/struggling-students?risk_threshold=High" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get recent disengagement alerts
curl -X GET "http://localhost:5000/engagement/disengagement-alerts?hours=24" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Note: Skill Progress Analytics, Cross-Comparison, and Dropout Risk Assessment are 
# automatically generated and pushed to Elasticsearch when engagement reports are generated. 
# No additional API calls are needed for data collection.

## 📊 **Query Examples**

### **Get High-Engagement Users**
```json
GET lab_monitoring_engagement_session/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "engagement_session"}},
        {"range": {"data.engagement_score": {"gte": 80}}}
      ]
    }
  }
}
```

### **Get Learning Progress by Category**
```json
GET lab_monitoring_learning_progress/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "learning_progress"}},
        {"term": {"data.category": "development"}}
      ]
    }
  },
  "sort": [{"data.timestamp": {"order": "desc"}}]
}
```

### **Get Application Usage Trends**
```json
GET lab_monitoring_app_usage_stats/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "app_usage_stats"}},
        {"term": {"data.app_name": "code"}}
      ]
    }
  },
  "aggs": {
    "daily_usage": {
      "date_histogram": {
        "field": "data.timestamp",
        "calendar_interval": "day"
      },
      "aggs": {
        "total_duration": {"sum": {"field": "data.duration_seconds"}}
      }
    }
  }
}
```

### **Get Skill Progress Analytics**
```json
GET lab_monitoring_skill_progress_analytics/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "skill_progress_analytics"}},
        {"term": {"data.user_id": "student123"}}
      ]
    }
  },
  "sort": [{"data.timestamp": {"order": "desc"}}]
}
```

### **Get Advanced Skill Level Users**
```json
GET lab_monitoring_skill_progress_analytics/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "skill_progress_analytics"}},
        {"term": {"data.skill_proficiency_curve.skill_level": "Advanced"}}
      ]
    }
  }
}
```

### **Get High Learning Efficiency Users**
```json
GET lab_monitoring_skill_progress_analytics/_search
{
  "query": {
    "range": {
      "data.retry_patterns.learning_efficiency": {"gte": 80}
    }
  },
  "sort": [{"data.retry_patterns.learning_efficiency": {"order": "desc"}}]
}
```

### **Get Skill Cross-Comparison Data**
```json
GET lab_monitoring_skill_cross_comparison/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "skill_cross_comparison"}},
        {"term": {"data.user_id": "student123"}}
      ]
    }
  },
  "sort": [{"data.timestamp": {"order": "desc"}}]
}
```

### **Get Top Performers by Proficiency**
```json
GET lab_monitoring_skill_cross_comparison/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "skill_cross_comparison"}},
        {"range": {"data.comparison_metrics.proficiency.percentile": {"gte": 90}}}
      ]
    }
  }
}
```

### **Get Students with Critical Skill Gaps**
```json
GET lab_monitoring_skill_cross_comparison/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"type": "skill_cross_comparison"}},
        {"exists": {"field": "data.skill_gaps.critical_gaps"}}
      ]
    }
  }
}
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Engagement scoring configuration
export ENGAGEMENT_SESSION_TIMEOUT=30          # Session timeout in minutes
export ENGAGEMENT_DATA_RETENTION_DAYS=30     # Data retention period

# Cross-server comparison configuration
export SERVER_ID="lab-server-01"             # Unique server identifier
export COMPARISON_SERVERS="lab-server-02,lab-server-03"  # Comma-separated peer servers
export COMPARISON_INTERVAL=300               # Metrics generation interval (seconds)

# Dropout prediction configuration
export INACTIVITY_THRESHOLD_MINUTES=15       # Minutes of inactivity before flagging as risk
export FAILED_ATTEMPTS_THRESHOLD=5           # Number of failed attempts before flagging as risk
export STRUGGLE_DETECTION_WINDOW=30          # Minutes window for struggle pattern detection
export RISK_ASSESSMENT_INTERVAL=300          # Interval in seconds for risk assessment
```

### **Command Line Arguments**
```bash
python monitor_agent.py \
  --engagement-session-timeout 30 \
  --engagement-data-retention 30 \
  --server-id "lab-server-01" \
  --comparison-servers "lab-server-02" "lab-server-03" \
  --comparison-interval 300 \
  --inactivity-threshold 15 \
  --failed-attempts-threshold 5 \
  --struggle-detection-window 30 \
  --risk-assessment-interval 300
```

## 🔄 **Data Flow**

1. **Activity Detection**: User activity triggers engagement tracking
2. **Real-time Updates**: Metrics updated during active sessions
3. **Elasticsearch Push**: Data pushed immediately to respective indices
4. **Session Management**: Sessions started/ended based on activity
5. **Periodic Cleanup**: Old data cleaned up based on retention policy

## 📈 **Benefits**

- **Real-time Monitoring**: Live engagement tracking
- **Skill Development**: Learning progress across categories
- **Productivity Insights**: Time allocation analysis
- **Educational Analytics**: Student engagement patterns
- **Data Separation**: Clean, organized data structure
- **Scalable Architecture**: Efficient data storage and retrieval

## 🚀 **Getting Started**

1. **Enable Engagement Scoring**: Set environment variables
2. **Start Monitoring**: Run the monitoring agent
3. **Access Reports**: Use the API endpoints
4. **Analyze Data**: Query Elasticsearch indices
5. **Customize Categories**: Modify learning categories as needed

The engagement scoring system provides comprehensive insights into student learning patterns, helping educators understand engagement levels, skill development, and productivity trends in real-time.
