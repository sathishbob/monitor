"""
EngagementScoring Module - Student Activity Tracking and Analysis

This module implements a comprehensive engagement scoring system that tracks and analyzes
student activity patterns in lab server environments. It provides real-time monitoring,
behavioral analysis, and predictive insights to identify at-risk students and optimize
learning experiences.

Key Features:
- Real-time session tracking and management
- Command execution pattern analysis
- Application usage monitoring and categorization
- Learning progress assessment and skill tracking
- Cross-server performance comparison
- AI-powered dropout prediction and risk assessment
- Engagement trend analysis and reporting

Data Types Pushed to Elasticsearch:
- engagement_session: Individual user sessions with timing and activity metrics
- engagement_metrics: Aggregated engagement scores and behavioral patterns
- learning_progress: Skill development and project work tracking
- app_usage_stats: Application usage patterns and time allocation
- command_engagement: Command execution frequency and diversity analysis
- cross_server_comparison: Performance metrics relative to peer servers
- risk_assessment: Student risk profiles and disengagement predictions

The system uses machine learning models to identify patterns, predict outcomes,
and provide actionable insights for educators and administrators.
"""

import logging
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

# Set up module-level logging
logger = logging.getLogger(__name__)

class EngagementScoring:
    """
    Comprehensive engagement scoring system for student activity tracking.
    
    This class provides a sophisticated framework for monitoring student engagement
    in lab server environments. It tracks multiple dimensions of activity including
    session management, command execution, application usage, and learning progress.
    
    The system employs AI/ML techniques to:
    - Identify engagement patterns and trends
    - Predict student dropout risk
    - Compare performance across different servers
    - Generate actionable insights for educators
    
    Core Tracking Capabilities:
    - Session duration and login patterns
    - Command execution frequency and diversity
    - Application usage and window activity
    - Learning progress indicators and skill development
    - Engagement trends over time and across sessions
    - Cross-server performance comparison
    - Risk assessment and early warning systems
    
    Data Storage:
    Pushes comprehensive data to Elasticsearch as separate, optimized data types
    for efficient querying and analysis.
    """
    
    def __init__(self, session_timeout_minutes: int = 30, inactivity_threshold_minutes: int = 15, server_id: str = None, es_manager=None):
        """
        Initialize the engagement scoring system.
        
        Args:
            session_timeout_minutes (int): Minutes of inactivity before session timeout
            inactivity_threshold_minutes (int): Minutes of inactivity before ending session
            server_id (str): Server identifier for cross-server metrics
            es_manager: Elasticsearch manager instance for data persistence
        """
        # Session management configuration
        self.session_timeout_minutes = session_timeout_minutes
        self.session_timeout_seconds = session_timeout_minutes * 60
        self.es_manager = es_manager
        
        # Session tracking and management
        # Active sessions store current user sessions with real-time data
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        # Session history maintains completed sessions for analysis
        self.session_history: List[Dict[str, Any]] = []
        
        # Command execution tracking
        # Stores command history for each user with configurable retention
        self.command_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Application usage monitoring
        # Tracks time spent, session count, and categories for each application
        self.app_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_time': 0.0,        # Total time spent in application
            'sessions': 0,             # Number of usage sessions
            'last_used': None,         # Timestamp of last usage
            'categories': set()        # Learning categories this app belongs to
        })
        
        # Engagement scoring and metrics
        # Rolling window of engagement scores for trend analysis
        self.engagement_scores: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Learning progress tracking
        # Comprehensive tracking of skill development and project work
        self.learning_progress: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'skill_levels': defaultdict(int),  # Skill proficiency levels
            'project_work': 0.0,               # Time spent on project work
            'collaboration_time': 0.0,         # Time spent collaborating
            'research_time': 0.0               # Time spent on research activities
        })
        
        # Daily activity aggregation
        # Per-user daily metrics for trend analysis and reporting
        self.daily_activity: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'total_time': 0.0,                # Total active time
            'productive_time': 0.0,            # Time spent on productive activities
            'break_time': 0.0,                 # Time spent on breaks
            'commands_executed': 0,            # Number of commands executed
            'apps_used': 0                     # Number of applications used
        })
        
        # Learning category definitions
        # Maps applications and commands to learning domains for categorization
        self.learning_categories = {
            'development': ['git', 'python', 'node', 'npm', 'docker', 'kubectl', 'java', 'gcc', 'make'],
            'system_admin': ['systemctl', 'service', 'ps', 'top', 'htop', 'df', 'du', 'netstat', 'ss'],
            'networking': ['ping', 'traceroute', 'nmap', 'wget', 'curl', 'ssh', 'scp', 'rsync'],
            'data_analysis': ['pandas', 'numpy', 'matplotlib', 'jupyter', 'r', 'sql', 'excel'],
            'design': ['gimp', 'inkscape', 'blender', 'figma', 'sketch', 'photoshop'],
            'documentation': ['markdown', 'latex', 'asciidoc', 'sphinx', 'doxygen'],
            'collaboration': ['slack', 'discord', 'teams', 'zoom', 'meet', 'webex'],
            'research': ['browser', 'firefox', 'chrome', 'safari', 'edge', 'research', 'paper']
        }
        
        # Cross-server comparison configuration
        # Enables performance comparison across multiple lab servers
        self.cross_server_enabled = True
        self.server_identifier = server_id or os.getenv('SERVER_ID', 'unknown')
        self.comparison_servers = os.getenv('COMPARISON_SERVERS', '').split(',') if os.getenv('COMPARISON_SERVERS') else []
        self.comparison_interval = int(os.getenv('COMPARISON_INTERVAL', '300'))  # 5 minutes default
        
        # Cross-server metrics storage
        # Stores comparative data and relative performance metrics
        self.cross_server_metrics: Dict[str, Dict[str, Any]] = {}
        self.relative_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.peer_benchmarks: Dict[str, Dict[str, Any]] = {}
        
        # Dropout/Struggle Prediction AI configuration
        # AI-powered risk assessment and early warning system
        self.dropout_prediction_enabled = True
        self.inactivity_threshold_minutes = inactivity_threshold_minutes
        self.failed_attempts_threshold = int(os.getenv('FAILED_ATTEMPTS_THRESHOLD', '5'))
        self.struggle_detection_window = int(os.getenv('STRUGGLE_DETECTION_WINDOW', '30'))  # minutes
        self.risk_assessment_interval = int(os.getenv('RISK_ASSESSMENT_INTERVAL', '300'))  # 5 minutes
        
        # Risk assessment and prediction storage
        # Maintains risk profiles and generates disengagement alerts
        self.student_risk_profiles: Dict[str, Dict[str, Any]] = {}
        self.disengagement_alerts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.intervention_recommendations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Productivity indicators
        self.productivity_indicators = {
            'high': ['git commit', 'git push', 'make', 'build', 'test', 'deploy', 'debug'],
            'medium': ['edit', 'create', 'modify', 'analyze', 'research', 'document'],
            'low': ['browse', 'social', 'entertainment', 'game']
        }
    
    def set_es_manager(self, es_manager):
        """Set the Elasticsearch manager for data pushing."""
        self.es_manager = es_manager
        logger.info("Elasticsearch manager set for engagement scoring")
    
    def push_to_elasticsearch(self, data: Dict[str, Any], data_type: str) -> bool:
        """Push data to Elasticsearch if manager is available."""
        if not self.es_manager:
            logger.warning(f"Cannot push {data_type} data: ES manager not available")
            return False
        
        try:
            self.es_manager.push_data(data, data_type)
            logger.debug(f"Successfully pushed {data_type} data to Elasticsearch")
            return True
        except Exception as e:
            logger.error(f"Failed to push {data_type} data to Elasticsearch: {e}")
            return False
    
    def start_session(self, user_id: str, timestamp: Optional[datetime] = None) -> str:
        """Start a new engagement session for a user."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        session_id = f"{user_id}_{int(timestamp.timestamp())}"
        
        self.active_sessions[user_id] = {
            'session_id': session_id,
            'start_time': timestamp,
            'last_activity': timestamp,
            'commands_executed': 0,
            'apps_used': set(),
            'productive_time': 0.0,
            'break_time': 0.0,
            'current_app': None,
            'current_app_start': None
        }
        
        # Push session start to Elasticsearch
        session_start_data = {
            'session_id': session_id,
            'user_id': user_id,
            'start_time': timestamp.isoformat(),
            'status': 'started',
            'timestamp': timestamp.isoformat()
        }
        self.push_to_elasticsearch(session_start_data, 'engagement_session')
        
        logger.info(f"Started engagement session {session_id} for user {user_id}")
        return session_id
    
    def end_session(self, user_id: str, timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """End an active session and return session summary."""
        if user_id not in self.active_sessions:
            return None
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        session = self.active_sessions[user_id]
        session['end_time'] = timestamp
        
        # Calculate final metrics
        duration = (timestamp - session['start_time']).total_seconds()
        session['duration_seconds'] = duration
        session['duration_minutes'] = duration / 60.0
        
        # Finalize app usage for current app
        if session['current_app'] and session['current_app_start']:
            app_duration = (timestamp - session['current_app_start']).total_seconds()
            self._update_app_usage(session['current_app'], app_duration, user_id)
        
        # Create session summary
        session_summary = {
            'session_id': session['session_id'],
            'user_id': user_id,
            'start_time': session['start_time'].isoformat(),
            'end_time': timestamp.isoformat(),
            'duration_seconds': session['duration_seconds'],
            'duration_minutes': session['duration_minutes'],
            'commands_executed': session['commands_executed'],
            'apps_used': list(session['apps_used']),
            'productive_time': session['productive_time'],
            'break_time': session['break_time'],
            'engagement_score': self._calculate_session_engagement(session),
            'status': 'completed',
            'timestamp': timestamp.isoformat()
        }
        
        # Push completed session to Elasticsearch
        self.push_to_elasticsearch(session_summary, 'engagement_session')
        
        # Store in history
        self.session_history.append(session_summary)
        
        # Update daily activity
        self._update_daily_activity(user_id, session_summary)
        
        # Remove from active sessions
        del self.active_sessions[user_id]
        
        logger.info(f"Ended engagement session {session['session_id']} for user {user_id}")
        return session_summary
    
    def update_activity(self, user_id: str, activity_type: str, data: Dict[str, Any], 
                       timestamp: Optional[datetime] = None) -> None:
        """Update engagement metrics based on user activity."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Ensure user has an active session
        if user_id not in self.active_sessions:
            self.start_session(user_id, timestamp)
        
        session = self.active_sessions[user_id]
        session['last_activity'] = timestamp
        
        if activity_type == 'command':
            self._handle_command_activity(user_id, data, timestamp)
        elif activity_type == 'window':
            self._handle_window_activity(user_id, data, timestamp)
        elif activity_type == 'clipboard':
            self._handle_clipboard_activity(user_id, data, timestamp)
        
        # Update engagement score
        self._update_engagement_score(user_id, session)
        
        # Push real-time engagement metrics
        self._push_engagement_metrics(user_id, session, timestamp)
    
    def _handle_command_activity(self, user_id: str, data: Dict[str, Any], timestamp: datetime) -> None:
        """Handle command execution activity."""
        session = self.active_sessions[user_id]
        session['commands_executed'] += 1
        
        command = data.get('command', '').lower()
        
        # Track command in history
        command_data = {
            'command': command,
            'timestamp': timestamp.isoformat(),
            'dangerous': data.get('dangerous', False),
            'duration': data.get('duration_seconds', 0),
            'user_id': user_id,
            'session_id': session['session_id']
        }
        self.command_history[user_id].append(command_data)
        
        # Push command engagement data to Elasticsearch
        self.push_to_elasticsearch(command_data, 'command_engagement')
        
        # Categorize command for learning progress
        self._categorize_command(user_id, command)
        
        # Update productivity tracking
        productivity = self._assess_command_productivity(command)
        if productivity == 'high':
            session['productive_time'] += 1.0
        elif productivity == 'low':
            session['break_time'] += 1.0
        
        logger.debug(f"User {user_id} executed command: {command} (productivity: {productivity})")
    
    def _handle_window_activity(self, user_id: str, data: Dict[str, Any], timestamp: datetime) -> None:
        """Handle window/application activity."""
        session = self.active_sessions[user_id]
        app_name = data.get('process_name', 'Unknown').lower()
        window_title = data.get('window_title', 'Unknown')
        
        # Update current app tracking
        if session['current_app'] != app_name:
            # Finalize previous app usage
            if session['current_app'] and session['current_app_start']:
                app_duration = (timestamp - session['current_app_start']).total_seconds()
                self._update_app_usage(session['current_app'], app_duration, user_id)
            
            # Start tracking new app
            session['current_app'] = app_name
            session['current_app_start'] = timestamp
            session['apps_used'].add(app_name)
        
        # Categorize application
        self._categorize_application(user_id, app_name, window_title)
        
        logger.debug(f"User {user_id} using application: {app_name}")
    
    def _handle_clipboard_activity(self, user_id: str, data: Dict[str, Any], timestamp: datetime) -> None:
        """Handle clipboard activity for engagement insights."""
        content = data.get('content', '').lower()
        
        # Analyze clipboard content for learning indicators
        if any(keyword in content for keyword in ['code', 'function', 'class', 'import', 'def']):
            self.learning_progress[user_id]['project_work'] += 0.5
        elif any(keyword in content for keyword in ['research', 'paper', 'article', 'study']):
            self.learning_progress[user_id]['research_time'] += 0.5
        
        logger.debug(f"User {user_id} clipboard activity analyzed")
    
    def _categorize_command(self, user_id: str, command: str) -> None:
        """Categorize command for learning progress tracking."""
        for category, keywords in self.learning_categories.items():
            if any(keyword in command for keyword in keywords):
                self.learning_progress[user_id]['skill_levels'][category] += 1
                
                # Push learning progress update to Elasticsearch
                progress_data = {
                    'user_id': user_id,
                    'category': category,
                    'skill_level': self.learning_progress[user_id]['skill_levels'][category],
                    'command': command,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                self.push_to_elasticsearch(progress_data, 'learning_progress')
                break
    
    def _categorize_application(self, user_id: str, app_name: str, window_title: str) -> None:
        """Categorize application usage for learning progress."""
        for category, keywords in self.learning_categories.items():
            if any(keyword in app_name for keyword in keywords):
                self.learning_progress[user_id]['skill_levels'][category] += 0.5
                
                # Push learning progress update to Elasticsearch
                progress_data = {
                    'user_id': user_id,
                    'category': category,
                    'skill_level': self.learning_progress[user_id]['skill_levels'][category],
                    'application': app_name,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                self.push_to_elasticsearch(progress_data, 'learning_progress')
                break
    
    def _assess_command_productivity(self, command: str) -> str:
        """Assess the productivity level of a command."""
        for level, indicators in self.productivity_indicators.items():
            if any(indicator in command for indicator in indicators):
                return level
        return 'medium'
    
    def _update_app_usage(self, app_name: str, duration: float, user_id: str) -> None:
        """Update application usage statistics."""
        app_data = self.app_usage[app_name]
        app_data['total_time'] += duration
        app_data['sessions'] += 1
        app_data['last_used'] = datetime.now(timezone.utc)
        
        # Add user to app usage
        if 'users' not in app_data:
            app_data['users'] = set()
        app_data['users'].add(user_id)
        
        # Push app usage stats to Elasticsearch
        app_usage_data = {
            'app_name': app_name,
            'user_id': user_id,
            'duration_seconds': duration,
            'total_time': app_data['total_time'],
            'sessions': app_data['sessions'],
            'last_used': app_data['last_used'].isoformat(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.push_to_elasticsearch(app_usage_data, 'app_usage_stats')
    
    def _update_daily_activity(self, user_id: str, session_summary: Dict[str, Any]) -> None:
        """Update daily activity tracking."""
        date_key = session_summary['start_time'][:10]  # YYYY-MM-DD
        daily = self.daily_activity[date_key]
        
        daily['total_time'] += session_summary['duration_seconds']
        daily['productive_time'] += session_summary['productive_time']
        daily['break_time'] += session_summary['break_time']
        daily['commands_executed'] += session_summary['commands_executed']
        daily['apps_used'] = max(daily['apps_used'], len(session_summary['apps_used']))
        
        # Push daily activity to Elasticsearch
        daily_data = {
            'user_id': user_id,
            'date': date_key,
            'total_time_seconds': daily['total_time'],
            'productive_time_seconds': daily['productive_time'],
            'break_time_seconds': daily['break_time'],
            'commands_executed': daily['commands_executed'],
            'apps_used': daily['apps_used'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.push_to_elasticsearch(daily_data, 'daily_activity')
    
    def _calculate_session_engagement(self, session: Dict[str, Any]) -> float:
        """Calculate engagement score for a session."""
        score = 0.0
        
        # Time-based scoring (0-40 points)
        duration_minutes = session['duration_minutes']
        if duration_minutes >= 120:  # 2+ hours
            score += 40
        elif duration_minutes >= 60:  # 1+ hours
            score += 30
        elif duration_minutes >= 30:  # 30+ minutes
            score += 20
        elif duration_minutes >= 15:  # 15+ minutes
            score += 10
        
        # Command activity scoring (0-30 points)
        commands = session['commands_executed']
        if commands >= 50:
            score += 30
        elif commands >= 25:
            score += 20
        elif commands >= 10:
            score += 15
        elif commands >= 5:
            score += 10
        
        # Application diversity scoring (0-20 points)
        apps = len(session['apps_used'])
        if apps >= 5:
            score += 20
        elif apps >= 3:
            score += 15
        elif apps >= 2:
            score += 10
        
        # Productivity scoring (0-10 points)
        productive_ratio = session['productive_time'] / max(1, session['duration_seconds'])
        if productive_ratio >= 0.7:
            score += 10
        elif productive_ratio >= 0.5:
            score += 7
        elif productive_ratio >= 0.3:
            score += 4
        
        return min(100.0, score)
    
    def _update_engagement_score(self, user_id: str, session: Dict[str, Any]) -> None:
        """Update rolling engagement score for a user."""
        current_score = self._calculate_session_engagement(session)
        self.engagement_scores[user_id].append(current_score)
    
    def _push_engagement_metrics(self, user_id: str, session: Dict[str, Any], timestamp: datetime) -> None:
        """Push real-time engagement metrics to Elasticsearch."""
        if not session:
            return
        
        metrics_data = {
            'user_id': user_id,
            'session_id': session.get('session_id'),
            'commands_executed': session.get('commands_executed', 0),
            'apps_used_count': len(session.get('apps_used', set())),
            'productive_time': session.get('productive_time', 0.0),
            'break_time': session.get('break_time', 0.0),
            'current_app': session.get('current_app'),
            'session_duration_minutes': (timestamp - session['start_time']).total_seconds() / 60.0,
            'timestamp': timestamp.isoformat()
        }
        
        self.push_to_elasticsearch(metrics_data, 'engagement_metrics')
    
    def get_engagement_report(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive engagement report for a user."""
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=days)
        
        # Filter recent sessions
        recent_sessions = [
            s for s in self.session_history 
            if s['user_id'] == user_id and 
            datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')) > cutoff_date
        ]
        
        # Calculate metrics
        total_sessions = len(recent_sessions)
        total_time = sum(s['duration_minutes'] for s in recent_sessions)
        avg_engagement = sum(s['engagement_score'] for s in recent_sessions) / max(1, total_sessions)
        
        # Command analysis
        all_commands = []
        for session in recent_sessions:
            for cmd in self.command_history[user_id]:
                if cmd['timestamp'] >= session['start_time'] and cmd['timestamp'] <= session['end_time']:
                    all_commands.append(cmd)
        
        unique_commands = len(set(cmd['command'] for cmd in all_commands))
        dangerous_commands = sum(1 for cmd in all_commands if cmd['dangerous'])
        
        # Application analysis
        app_usage = {}
        for app_name, app_data in self.app_usage.items():
            if user_id in app_data.get('users', set()):
                app_usage[app_name] = {
                    'total_time': app_data['total_time'],
                    'sessions': app_data['sessions'],
                    'last_used': app_data['last_used'].isoformat() if app_data['last_used'] else None
                }
        
        # Learning progress
        learning_data = self.learning_progress[user_id]
        skill_levels = dict(learning_data['skill_levels'])
        
        # Skill progress analytics
        skill_analytics = self._analyze_skill_progress(user_id, recent_sessions)
        
        # Engagement trends
        recent_scores = list(self.engagement_scores[user_id])[-10:]  # Last 10 scores
        score_trend = 'improving' if len(recent_scores) >= 2 and recent_scores[-1] > recent_scores[0] else 'stable'
        
        return {
            'user_id': user_id,
            'report_period_days': days,
            'generated_at': now.isoformat(),
            
            # Session metrics
            'total_sessions': total_sessions,
            'total_time_minutes': total_time,
            'total_time_hours': total_time / 60.0,
            'avg_session_length': total_time / max(1, total_sessions),
            
            # Engagement metrics
            'avg_engagement_score': avg_engagement,
            'engagement_trend': score_trend,
            'recent_scores': recent_scores,
            
            # Activity metrics
            'total_commands': len(all_commands),
            'unique_commands': unique_commands,
            'dangerous_commands': dangerous_commands,
            'command_diversity': unique_commands / max(1, len(all_commands)),
            
            # Application metrics
            'total_apps_used': len(app_usage),
            'app_usage': app_usage,
            
            # Learning progress
            'skill_levels': skill_levels,
            'project_work_time': learning_data['project_work'],
            'research_time': learning_data['research_time'],
            'collaboration_time': learning_data['collaboration_time'],
            
            # Skill progress analytics
            'skill_analytics': skill_analytics,
            
            # Recommendations
            'recommendations': self._generate_recommendations(user_id, recent_sessions, skill_levels)
        }
    
    def _generate_recommendations(self, user_id: str, recent_sessions: List[Dict], 
                                 skill_levels: Dict[str, int]) -> List[str]:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        # Analyze skill gaps
        weak_skills = [skill for skill, level in skill_levels.items() if level < 5]
        if weak_skills:
            recommendations.append(f"Focus on improving {', '.join(weak_skills[:2])} skills")
        
        # Session length recommendations
        avg_session_length = sum(s['duration_minutes'] for s in recent_sessions) / max(1, len(recent_sessions))
        if avg_session_length < 30:
            recommendations.append("Try longer study sessions (30+ minutes) for better engagement")
        elif avg_session_length > 180:
            recommendations.append("Consider taking regular breaks during long study sessions")
        
        # Command diversity recommendations
        if len(recent_sessions) > 0:
            recent_session = recent_sessions[-1]
            if recent_session['commands_executed'] < 10:
                recommendations.append("Increase command usage to improve technical skills")
        
        # Application diversity
        if len(recent_sessions) > 0:
            recent_session = recent_sessions[-1]
            if len(recent_session['apps_used']) < 3:
                recommendations.append("Try using more diverse applications to broaden your skill set")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _analyze_skill_progress(self, user_id: str, recent_sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze skill progress based on commands, errors, and retries."""
        if not recent_sessions:
            return {'error': 'No recent sessions found for skill analysis'}
        
        # Collect command data from recent sessions
        command_data = []
        for session in recent_sessions:
            for cmd in self.command_history[user_id]:
                if cmd['timestamp'] >= session['start_time'] and cmd['timestamp'] <= session['end_time']:
                    command_data.append(cmd)
        
        if not command_data:
            return {'error': 'No command data found for skill analysis'}
        
        # Analyze command patterns and errors
        skill_analysis = {
            'user_id': user_id,
            'analysis_period': f"{len(recent_sessions)} sessions",
            'total_commands': len(command_data),
            'unique_commands': len(set(cmd['command'] for cmd in command_data)),
            'command_categories': self._categorize_commands_by_skill(command_data),
            'error_analysis': self._analyze_command_errors(command_data),
            'retry_patterns': self._analyze_retry_patterns(command_data),
            'skill_proficiency_curve': self._estimate_skill_proficiency_curve(user_id, command_data),
            'learning_patterns': self._identify_learning_patterns(command_data),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Push skill analytics to Elasticsearch
        self.push_to_elasticsearch(skill_analysis, 'skill_progress_analytics')
        
        # Generate cross-comparison analytics
        cross_comparison = self._generate_skill_cross_comparison(user_id, skill_analysis)
        if cross_comparison:
            self.push_to_elasticsearch(cross_comparison, 'skill_cross_comparison')
        
        return skill_analysis
    
    def _categorize_commands_by_skill(self, command_data: List[Dict]) -> Dict[str, Any]:
        """Categorize commands by skill level and complexity."""
        skill_categories = {
            'beginner': [],
            'intermediate': [],
            'advanced': [],
            'expert': []
        }
        
        # Define command complexity levels
        beginner_commands = ['ls', 'cd', 'pwd', 'cat', 'echo', 'whoami', 'date']
        intermediate_commands = ['grep', 'find', 'sed', 'awk', 'tar', 'zip', 'unzip', 'chmod', 'chown']
        advanced_commands = ['git', 'docker', 'kubectl', 'ansible', 'terraform', 'make', 'cmake']
        expert_commands = ['strace', 'gdb', 'valgrind', 'perf', 'systemtap', 'ebpf']
        
        for cmd in command_data:
            command = cmd['command'].split()[0] if cmd['command'] else ''
            
            if command in expert_commands:
                skill_categories['expert'].append(cmd)
            elif command in advanced_commands:
                skill_categories['advanced'].append(cmd)
            elif command in intermediate_commands:
                skill_categories['intermediate'].append(cmd)
            elif command in beginner_commands:
                skill_categories['beginner'].append(cmd)
            else:
                # Analyze command complexity based on patterns
                complexity = self._assess_command_complexity(cmd['command'])
                skill_categories[complexity].append(cmd)
        
        # Calculate percentages
        total_commands = len(command_data)
        category_stats = {}
        for category, commands in skill_categories.items():
            category_stats[category] = {
                'count': len(commands),
                'percentage': round((len(commands) / total_commands) * 100, 2) if total_commands > 0 else 0,
                'commands': [cmd['command'] for cmd in commands[:10]]  # Top 10 commands
            }
        
        return category_stats
    
    def _assess_command_complexity(self, command: str) -> str:
        """Assess command complexity based on patterns and structure."""
        if not command:
            return 'beginner'
        
        complexity_score = 0
        
        # Check for pipes and redirections
        if '|' in command:
            complexity_score += 2
        if '>' in command or '<' in command or '>>' in command:
            complexity_score += 1
        if '&&' in command or '||' in command:
            complexity_score += 2
        
        # Check for complex options
        if '--' in command:
            complexity_score += 1
        if len(command.split()) > 3:
            complexity_score += 1
        
        # Check for programming constructs
        if any(pattern in command for pattern in ['for', 'while', 'if', 'case']):
            complexity_score += 3
        
        # Check for system administration
        if any(pattern in command for pattern in ['systemctl', 'service', 'iptables', 'firewall']):
            complexity_score += 2
        
        # Determine category based on score
        if complexity_score >= 5:
            return 'expert'
        elif complexity_score >= 3:
            return 'advanced'
        elif complexity_score >= 1:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _analyze_command_errors(self, command_data: List[Dict]) -> Dict[str, Any]:
        """Analyze command errors and failure patterns."""
        error_patterns = defaultdict(int)
        error_commands = defaultdict(int)
        error_categories = defaultdict(int)
        
        # Analyze commands that might indicate errors (based on duration, patterns, etc.)
        for cmd in command_data:
            command = cmd['command'].lower()
            
            # Check for common error indicators
            if any(error_indicator in command for error_indicator in ['rm -rf', 'dd if=', 'mkfs', 'fdisk']):
                error_patterns['dangerous_commands'] += 1
                error_categories['system_modification'] += 1
            
            # Check for syntax errors (commands that are likely to fail)
            if command.count('"') % 2 != 0 or command.count("'") % 2 != 0:
                error_patterns['syntax_errors'] += 1
                error_categories['syntax'] += 1
            
            # Check for incomplete commands
            if command.endswith('\\') or command.endswith('|'):
                error_patterns['incomplete_commands'] += 1
                error_categories['syntax'] += 1
            
            # Track commands that might cause errors
            if any(cmd_type in command for cmd_type in ['chmod 777', 'chown root', 'sudo rm']):
                error_patterns['permission_errors'] += 1
                error_categories['permissions'] += 1
        
        return {
            'total_error_patterns': sum(error_patterns.values()),
            'error_patterns': dict(error_patterns),
            'error_categories': dict(error_categories),
            'error_rate': round((sum(error_patterns.values()) / len(command_data)) * 100, 2) if command_data else 0
        }
    
    def _analyze_retry_patterns(self, command_data: List[Dict]) -> Dict[str, Any]:
        """Analyze command retry patterns and learning behavior."""
        command_frequency = defaultdict(int)
        retry_patterns = defaultdict(int)
        learning_indicators = defaultdict(int)
        
        # Count command frequency
        for cmd in command_data:
            command = cmd['command'].split()[0] if cmd['command'] else ''
            command_frequency[command] += 1
        
        # Identify retry patterns (commands executed multiple times)
        for command, count in command_frequency.items():
            if count > 1:
                retry_patterns[command] = count
                
                # Analyze retry behavior
                if count == 2:
                    learning_indicators['double_attempts'] += 1
                elif count == 3:
                    learning_indicators['triple_attempts'] += 1
                elif count > 3:
                    learning_indicators['persistent_attempts'] += 1
        
        # Calculate learning efficiency
        total_retries = sum(retry_patterns.values()) - len(retry_patterns)
        learning_efficiency = 0
        if total_retries > 0:
            # Lower retry count indicates better learning
            learning_efficiency = max(0, 100 - (total_retries / len(command_data)) * 100)
        
        return {
            'total_retries': total_retries,
            'retry_patterns': dict(retry_patterns),
            'learning_indicators': dict(learning_indicators),
            'learning_efficiency': round(learning_efficiency, 2),
            'most_retried_commands': sorted(retry_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _estimate_skill_proficiency_curve(self, user_id: str, command_data: List[Dict]) -> Dict[str, Any]:
        """Estimate student's skill proficiency curve using AI-like analysis."""
        if not command_data:
            return {'error': 'No command data for skill proficiency analysis'}
        
        # Calculate skill progression over time
        time_ordered_commands = sorted(command_data, key=lambda x: x['timestamp'])
        
        # Analyze skill development phases
        skill_phases = {
            'exploration': 0,      # Trying new commands
            'practice': 0,         # Repeating commands
            'mastery': 0,          # Complex command combinations
            'innovation': 0        # Creating new solutions
        }
        
        # Track command complexity progression
        complexity_progression = []
        unique_commands_seen = set()
        
        for i, cmd in enumerate(time_ordered_commands):
            command = cmd['command']
            complexity = self._assess_command_complexity(command)
            
            # Track complexity progression
            complexity_score = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}[complexity]
            complexity_progression.append({
                'timestamp': cmd['timestamp'],
                'command': command,
                'complexity': complexity,
                'complexity_score': complexity_score,
                'cumulative_score': sum(c['complexity_score'] for c in complexity_progression[:i+1])
            })
            
            # Analyze skill phases
            if command not in unique_commands_seen:
                skill_phases['exploration'] += 1
                unique_commands_seen.add(command)
            elif command in unique_commands_seen:
                skill_phases['practice'] += 1
            
            # Check for complex combinations (mastery indicator)
            if '|' in command or '&&' in command or '||' in command:
                skill_phases['mastery'] += 1
            
            # Check for innovative solutions (custom scripts, complex pipelines)
            if len(command.split()) > 5 or 'for' in command or 'while' in command:
                skill_phases['innovation'] += 1
        
        # Calculate skill proficiency score (0-100)
        total_commands = len(command_data)
        if total_commands == 0:
            proficiency_score = 0
        else:
            # Weight different factors
            exploration_weight = 0.2
            practice_weight = 0.3
            mastery_weight = 0.3
            innovation_weight = 0.2
            
            exploration_score = min(100, (skill_phases['exploration'] / total_commands) * 100)
            practice_score = min(100, (skill_phases['practice'] / total_commands) * 100)
            mastery_score = min(100, (skill_phases['mastery'] / total_commands) * 100)
            innovation_score = min(100, (skill_phases['innovation'] / total_commands) * 100)
            
            proficiency_score = (
                exploration_score * exploration_weight +
                practice_score * practice_weight +
                mastery_score * mastery_weight +
                innovation_score * innovation_weight
            )
        
        # Determine skill level
        if proficiency_score >= 80:
            skill_level = 'Expert'
        elif proficiency_score >= 60:
            skill_level = 'Advanced'
        elif proficiency_score >= 40:
            skill_level = 'Intermediate'
        elif proficiency_score >= 20:
            skill_level = 'Beginner'
        else:
            skill_level = 'Novice'
        
        # Calculate learning velocity (skill improvement rate)
        if len(complexity_progression) >= 2:
            first_score = complexity_progression[0]['cumulative_score']
            last_score = complexity_progression[-1]['cumulative_score']
            time_span = (datetime.fromisoformat(complexity_progression[-1]['timestamp'].replace('Z', '+00:00')) - 
                        datetime.fromisoformat(complexity_progression[0]['timestamp'].replace('Z', '+00:00'))).total_seconds() / 3600  # hours
            
            if time_span > 0:
                learning_velocity = (last_score - first_score) / time_span
            else:
                learning_velocity = 0
        else:
            learning_velocity = 0
        
        return {
            'proficiency_score': round(proficiency_score, 2),
            'skill_level': skill_level,
            'skill_phases': skill_phases,
            'complexity_progression': complexity_progression[-10:],  # Last 10 commands
            'learning_velocity': round(learning_velocity, 2),
            'total_commands_analyzed': total_commands,
            'unique_commands_used': len(unique_commands_seen),
            'skill_growth_rate': round((len(unique_commands_seen) / total_commands) * 100, 2) if total_commands > 0 else 0
        }
    
    def _identify_learning_patterns(self, command_data: List[Dict]) -> Dict[str, Any]:
        """Identify learning patterns and study habits."""
        if not command_data:
            return {'error': 'No command data for learning pattern analysis'}
        
        # Group commands by time periods
        time_periods = defaultdict(list)
        for cmd in command_data:
            timestamp = datetime.fromisoformat(cmd['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour
            time_periods[hour].append(cmd)
        
        # Analyze study patterns
        study_patterns = {
            'peak_hours': [],
            'consistent_hours': [],
            'irregular_patterns': []
        }
        
        # Find peak study hours
        hour_counts = {hour: len(commands) for hour, commands in time_periods.items()}
        if hour_counts:
            max_commands = max(hour_counts.values())
            peak_threshold = max_commands * 0.7
            
            for hour, count in hour_counts.items():
                if count >= peak_threshold:
                    study_patterns['peak_hours'].append({
                        'hour': hour,
                        'command_count': count,
                        'percentage': round((count / max_commands) * 100, 2)
                    })
        
        # Find consistent study hours (hours with regular activity)
        consistent_threshold = sum(hour_counts.values()) / len(hour_counts) * 0.5
        for hour, count in hour_counts.items():
            if count >= consistent_threshold:
                study_patterns['consistent_hours'].append({
                    'hour': hour,
                    'command_count': count,
                    'consistency_score': round((count / consistent_threshold) * 100, 2)
                })
        
        # Analyze command diversity over time
        command_diversity_trend = []
        window_size = min(10, len(command_data))
        
        for i in range(0, len(command_data), window_size):
            window_commands = command_data[i:i+window_size]
            unique_commands = len(set(cmd['command'] for cmd in window_commands))
            diversity_score = unique_commands / len(window_commands) if window_commands else 0
            
            command_diversity_trend.append({
                'window': i // window_size + 1,
                'commands_analyzed': len(window_commands),
                'unique_commands': unique_commands,
                'diversity_score': round(diversity_score, 3)
            })
        
        return {
            'study_patterns': study_patterns,
            'command_diversity_trend': command_diversity_trend,
            'total_hours_active': len(time_periods),
            'most_active_hour': max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None,
            'learning_consistency': round((len(study_patterns['consistent_hours']) / len(time_periods)) * 100, 2) if time_periods else 0
        }
    
    def assess_dropout_risk(self, user_id: str) -> Dict[str, Any]:
        """Assess dropout risk for a specific user using AI-powered analysis."""
        if not self.dropout_prediction_enabled:
            return {'error': 'Dropout prediction is disabled'}
        
        # Get user's recent activity and patterns
        risk_assessment = {
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'risk_score': 0.0,
            'risk_level': 'Low',
            'risk_factors': [],
            'disengagement_indicators': [],
            'intervention_priority': 'Low',
            'recommended_actions': []
        }
        
        # Check for active session
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            last_activity = session['last_activity']
            current_time = datetime.now(timezone.utc)
            inactivity_minutes = (current_time - last_activity).total_seconds() / 60
            
            # Inactivity risk
            if inactivity_minutes > self.inactivity_threshold_minutes:
                risk_assessment['risk_factors'].append({
                    'factor': 'inactivity',
                    'severity': 'high' if inactivity_minutes > 30 else 'medium',
                    'details': f'Inactive for {inactivity_minutes:.1f} minutes',
                    'score_impact': 25
                })
                risk_assessment['disengagement_indicators'].append('extended_inactivity')
        
        # Analyze command history for struggle patterns
        if user_id in self.command_history:
            recent_commands = self.command_history[user_id][-50:]  # Last 50 commands
            struggle_indicators = self._analyze_struggle_patterns(recent_commands)
            
            if struggle_indicators['total_failures'] > self.failed_attempts_threshold:
                risk_assessment['risk_factors'].append({
                    'factor': 'repeated_failures',
                    'severity': 'high',
                    'details': f'{struggle_indicators["total_failures"]} failed attempts in recent commands',
                    'score_impact': 30
                })
                risk_assessment['disengagement_indicators'].append('repeated_failures')
            
            if struggle_indicators['error_rate'] > 0.3:  # 30% error rate
                risk_assessment['risk_score'] += 20
                risk_assessment['risk_factors'].append({
                    'factor': 'high_error_rate',
                    'severity': 'medium',
                    'details': f'Error rate: {struggle_indicators["error_rate"]:.1%}',
                    'score_impact': 20
                })
                risk_assessment['disengagement_indicators'].append('high_error_rate')
        
        # Check engagement trends
        if user_id in self.engagement_scores:
            recent_scores = list(self.engagement_scores[user_id])[-5:]  # Last 5 scores
            if len(recent_scores) >= 2:
                score_trend = recent_scores[-1] - recent_scores[0]
                if score_trend < -20:  # Declining engagement
                    risk_assessment['risk_factors'].append({
                        'factor': 'declining_engagement',
                        'severity': 'medium',
                        'details': f'Engagement declined by {abs(score_trend):.1f} points',
                        'score_impact': 15
                    })
                    risk_assessment['disengagement_indicators'].append('declining_engagement')
        
        # Check session patterns
        user_sessions = [s for s in self.session_history if s['user_id'] == user_id]
        if len(user_sessions) >= 3:
            recent_sessions = user_sessions[-3:]
            avg_duration = sum(s['duration_minutes'] for s in recent_sessions) / len(recent_sessions)
            
            if avg_duration < 15:  # Short sessions
                risk_assessment['risk_factors'].append({
                    'factor': 'short_sessions',
                    'severity': 'medium',
                    'details': f'Average session duration: {avg_duration:.1f} minutes',
                    'score_impact': 10
                })
                risk_assessment['disengagement_indicators'].append('short_sessions')
        
        # Calculate overall risk score
        total_risk_score = sum(factor['score_impact'] for factor in risk_assessment['risk_factors'])
        risk_assessment['risk_score'] = min(100, total_risk_score)
        
        # Determine risk level
        if risk_assessment['risk_score'] >= 70:
            risk_assessment['risk_level'] = 'Critical'
            risk_assessment['intervention_priority'] = 'Immediate'
        elif risk_assessment['risk_score'] >= 50:
            risk_assessment['risk_level'] = 'High'
            risk_assessment['intervention_priority'] = 'High'
        elif risk_assessment['risk_score'] >= 30:
            risk_assessment['risk_level'] = 'Medium'
            risk_assessment['intervention_priority'] = 'Medium'
        elif risk_assessment['risk_score'] >= 15:
            risk_assessment['risk_level'] = 'Low'
            risk_assessment['intervention_priority'] = 'Low'
        else:
            risk_assessment['risk_level'] = 'Minimal'
            risk_assessment['intervention_priority'] = 'Monitor'
        
        # Generate intervention recommendations
        risk_assessment['recommended_actions'] = self._generate_intervention_recommendations(
            user_id, risk_assessment
        )
        
        # Store risk assessment
        self.student_risk_profiles[user_id] = risk_assessment
        
        # Push to Elasticsearch
        self.push_to_elasticsearch(risk_assessment, 'dropout_risk_assessment')
        
        return risk_assessment
    
    def _analyze_struggle_patterns(self, recent_commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze command patterns to identify struggle indicators."""
        struggle_analysis = {
            'total_failures': 0,
            'error_rate': 0.0,
            'repeated_errors': 0,
            'command_complexity_issues': 0,
            'syntax_errors': 0,
            'permission_errors': 0
        }
        
        if not recent_commands:
            return struggle_analysis
        
        # Count different types of errors
        for cmd in recent_commands:
            command = cmd.get('command', '').lower()
            
            # Check for dangerous commands that might indicate confusion
            if any(dangerous in command for dangerous in ['rm -rf', 'dd if=', 'mkfs', 'fdisk']):
                struggle_analysis['total_failures'] += 1
            
            # Check for syntax errors
            if command.count('"') % 2 != 0 or command.count("'") % 2 != 0:
                struggle_analysis['syntax_errors'] += 1
                struggle_analysis['total_failures'] += 1
            
            # Check for incomplete commands
            if command.endswith('\\') or command.endswith('|'):
                struggle_analysis['syntax_errors'] += 1
                struggle_analysis['total_failures'] += 1
            
            # Check for permission issues
            if any(perm_cmd in command for perm_cmd in ['chmod 777', 'chown root', 'sudo rm']):
                struggle_analysis['permission_errors'] += 1
                struggle_analysis['total_failures'] += 1
        
        # Calculate error rate
        struggle_analysis['error_rate'] = struggle_analysis['total_failures'] / len(recent_commands)
        
        # Check for repeated errors (same command multiple times)
        command_counts = defaultdict(int)
        for cmd in recent_commands:
            command_counts[cmd.get('command', '')] += 1
        
        repeated_commands = sum(1 for count in command_counts.values() if count > 2)
        struggle_analysis['repeated_errors'] = repeated_commands
        
        return struggle_analysis
    
    def _generate_intervention_recommendations(self, user_id: str, risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized intervention recommendations based on risk assessment."""
        recommendations = []
        
        risk_level = risk_assessment['risk_level']
        disengagement_indicators = risk_assessment['disengagement_indicators']
        
        # High priority interventions for critical/high risk
        if risk_level in ['Critical', 'High']:
            recommendations.append({
                'priority': 'Immediate',
                'type': 'direct_contact',
                'description': 'Reach out directly to student to understand challenges',
                'action': 'Send personalized message or schedule 1-on-1 session',
                'expected_impact': 'High'
            })
            
            if 'repeated_failures' in disengagement_indicators:
                recommendations.append({
                    'priority': 'High',
                    'type': 'skill_remediation',
                    'description': 'Provide targeted skill-building resources',
                    'action': 'Share tutorial videos or assign mentor for specific topics',
                    'expected_impact': 'High'
                })
        
        # Medium priority interventions
        if risk_level in ['Medium', 'High']:
            if 'extended_inactivity' in disengagement_indicators:
                recommendations.append({
                    'priority': 'Medium',
                    'type': 'engagement_boost',
                    'description': 'Increase engagement through interactive activities',
                    'action': 'Assign hands-on project or group collaboration task',
                    'expected_impact': 'Medium'
                })
            
            if 'declining_engagement' in disengagement_indicators:
                recommendations.append({
                    'priority': 'Medium',
                    'type': 'motivation_support',
                    'description': 'Provide encouragement and progress recognition',
                    'action': 'Highlight achievements and set achievable goals',
                    'expected_impact': 'Medium'
                })
        
        # General support recommendations
        if 'short_sessions' in disengagement_indicators:
            recommendations.append({
                'priority': 'Low',
                'type': 'session_optimization',
                'description': 'Optimize session length and structure',
                'action': 'Break tasks into smaller, manageable chunks',
                'expected_impact': 'Low'
            })
        
        # Add general support for all risk levels
        recommendations.append({
            'priority': 'Ongoing',
            'type': 'monitoring',
            'description': 'Continue monitoring progress and engagement',
            'action': 'Regular check-ins and progress assessments',
            'expected_impact': 'Low'
        })
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def get_struggling_students(self, risk_threshold: str = 'Medium') -> List[Dict[str, Any]]:
        """Get list of students currently struggling or at risk of disengagement."""
        struggling_students = []
        
        risk_levels = {
            'Minimal': 0,
            'Low': 1,
            'Medium': 2,
            'High': 3,
            'Critical': 4
        }
        
        threshold_level = risk_levels.get(risk_threshold, 2)
        
        for user_id, risk_profile in self.student_risk_profiles.items():
            user_risk_level = risk_profile.get('risk_level', 'Minimal')
            user_risk_value = risk_levels.get(user_risk_level, 0)
            
            if user_risk_value >= threshold_level:
                struggling_students.append({
                    'user_id': user_id,
                    'risk_level': user_risk_level,
                    'risk_score': risk_profile.get('risk_score', 0),
                    'intervention_priority': risk_profile.get('intervention_priority', 'Low'),
                    'disengagement_indicators': risk_profile.get('disengagement_indicators', []),
                    'last_assessment': risk_profile.get('timestamp', ''),
                    'recommended_actions': risk_profile.get('recommended_actions', [])
                })
        
        # Sort by risk level (highest first)
        struggling_students.sort(key=lambda x: risk_levels.get(x['risk_level'], 0), reverse=True)
        
        return struggling_students
    
    def get_disengagement_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent disengagement alerts for monitoring and intervention."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_alerts = []
        
        for user_id, alerts in self.disengagement_alerts.items():
            for alert in alerts:
                alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                if alert_time > cutoff_time:
                    recent_alerts.append(alert)
        
        # Sort by timestamp (most recent first)
        recent_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return recent_alerts
    
    def get_class_engagement_summary(self, days: int = 7) -> Dict[str, Any]:
        """Generate class-wide engagement summary."""
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=days)
        
        # Filter recent sessions
        recent_sessions = [
            s for s in self.session_history 
            if datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')) > cutoff_date
        ]
        
        if not recent_sessions:
            return {'error': 'No recent sessions found'}
        
        # Calculate class metrics
        unique_users = len(set(s['user_id'] for s in recent_sessions))
        total_time = sum(s['duration_minutes'] for s in recent_sessions)
        avg_engagement = sum(s['engagement_score'] for s in recent_sessions) / len(recent_sessions)
        
        # Top performers
        user_scores = defaultdict(list)
        for session in recent_sessions:
            user_scores[session['user_id']].append(session['engagement_score'])
        
        avg_user_scores = {user: sum(scores)/len(scores) for user, scores in user_scores.items()}
        top_performers = sorted(avg_user_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Most used applications
        app_usage = defaultdict(int)
        for session in recent_sessions:
            for app in session['apps_used']:
                app_usage[app] += 1
        
        top_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'report_period_days': days,
            'generated_at': now.isoformat(),
            'total_users': unique_users,
            'total_sessions': len(recent_sessions),
            'total_time_hours': total_time / 60.0,
            'avg_engagement_score': avg_engagement,
            'top_performers': [{'user_id': user, 'avg_score': score} for user, score in top_performers],
            'most_used_apps': [{'app': app, 'usage_count': count} for app, count in top_apps],
            'engagement_distribution': {
                'excellent': len([s for s in recent_sessions if s['engagement_score'] >= 80]),
                'good': len([s for s in recent_sessions if 60 <= s['engagement_score'] < 80]),
                'fair': len([s for s in recent_sessions if 40 <= s['engagement_score'] < 60]),
                'poor': len([s for s in recent_sessions if s['engagement_score'] < 40])
            }
        }
    
    def cleanup_old_sessions(self, days_to_keep: int = 30) -> int:
        """Clean up old session data to prevent memory bloat."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        original_count = len(self.session_history)
        self.session_history = [
            s for s in self.session_history 
            if datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')) > cutoff_date
        ]
        
        removed_count = original_count - len(self.session_history)
        logger.info(f"Cleaned up {removed_count} old sessions, keeping {len(self.session_history)} recent ones")
        
        return removed_count
    
    def generate_cross_server_metrics(self) -> Dict[str, Any]:
        """Generate comprehensive cross-server engagement metrics."""
        if not self.cross_server_enabled:
            return {'error': 'Cross-server comparison disabled'}
        
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(hours=24)  # Last 24 hours
        
        # Filter recent sessions
        recent_sessions = [
            s for s in self.session_history 
            if datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')) > cutoff_date
        ]
        
        if not recent_sessions:
            return {'error': 'No recent sessions found for comparison'}
        
        # Calculate server metrics
        total_users = len(set(s['user_id'] for s in recent_sessions))
        total_sessions = len(recent_sessions)
        total_time = sum(s['duration_minutes'] for s in recent_sessions)
        avg_engagement = sum(s['engagement_score'] for s in recent_sessions) / len(recent_sessions)
        
        # Command analysis
        all_commands = []
        for session in recent_sessions:
            for cmd in self.command_history[session['user_id']]:
                if cmd['timestamp'] >= session['start_time'] and cmd['timestamp'] <= session['end_time']:
                    all_commands.append(cmd)
        
        unique_commands = len(set(cmd['command'] for cmd in all_commands))
        dangerous_commands = sum(1 for cmd in all_commands if cmd['dangerous'])
        
        # Application analysis
        app_usage = defaultdict(int)
        for session in recent_sessions:
            for app in session['apps_used']:
                app_usage[app] += 1
        
        # Skill development analysis
        skill_development = defaultdict(int)
        for user_id, progress in self.learning_progress.items():
            for category, level in progress['skill_levels'].items():
                skill_development[category] += level
        
        # Create cross-server metrics payload
        cross_server_data = {
            'server_id': self.server_identifier,
            'timestamp': now.isoformat(),
            'period_hours': 24,
            
            # Engagement metrics
            'total_users': total_users,
            'total_sessions': total_sessions,
            'total_time_hours': total_time / 60.0,
            'avg_engagement_score': avg_engagement,
            
            # Activity metrics
            'total_commands': len(all_commands),
            'unique_commands': unique_commands,
            'dangerous_commands': dangerous_commands,
            'command_diversity': unique_commands / max(1, len(all_commands)),
            
            # Application metrics
            'total_apps_used': len(app_usage),
            'top_apps': sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:10],
            
            # Skill development
            'skill_development': dict(skill_development),
            'total_skill_points': sum(skill_development.values()),
            
            # Performance indicators
            'high_engagement_users': len([s for s in recent_sessions if s['engagement_score'] >= 80]),
            'medium_engagement_users': len([s for s in recent_sessions if 60 <= s['engagement_score'] < 80]),
            'low_engagement_users': len([s for s in recent_sessions if s['engagement_score'] < 60]),
            
            # Time distribution
            'avg_session_length': total_time / max(1, total_sessions),
            'long_sessions': len([s for s in recent_sessions if s['duration_minutes'] >= 60]),
            'short_sessions': len([s for s in recent_sessions if s['duration_minutes'] < 30])
        }
        
        # Store for local comparison
        self.cross_server_metrics[self.server_identifier] = cross_server_data
        
        # Push to Elasticsearch
        self.push_to_elasticsearch(cross_server_data, 'cross_server_metrics')
        
        return cross_server_data
    
    def generate_cross_server_comparison(self) -> Dict[str, Any]:
        """Generate cross-server comparison by aggregating data from multiple ES indices."""
        if not self.cross_server_enabled or not self.es_manager:
            return {'error': 'Cross-server comparison disabled or ES manager unavailable'}
        
        try:
            # Get cross-server metrics from all matching indices
            peer_data = self._fetch_peer_server_data()
            
            if not peer_data:
                return {'error': 'No peer server data found for comparison'}
            
            # Get local metrics
            local_metrics = self.cross_server_metrics.get(self.server_identifier)
            if not local_metrics:
                # Generate local metrics if not available
                local_metrics = self.generate_cross_server_metrics()
            
            # Perform comparative analysis
            comparison_results = self._perform_comparative_analysis(local_metrics, peer_data)
            
            # Store comparison results
            self.peer_benchmarks[self.server_identifier] = comparison_results
            
            # Push to Elasticsearch
            self.push_to_elasticsearch(comparison_results, 'cross_server_comparison')
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error generating cross-server comparison: {e}")
            return {'error': f'Failed to generate comparison: {str(e)}'}
    
    def _fetch_peer_server_data(self) -> List[Dict[str, Any]]:
        """Fetch cross-server metrics from all matching ES indices."""
        try:
            # Get index pattern from config
            index_pattern = getattr(self.es_manager, 'cross_server_index_pattern', 'lab_monitoring*')
            
            # Query for cross_server_metrics from all matching indices
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"event_type": "cross_server_metrics"}},
                            {"range": {"timestamp": {"gte": "now-24h"}}}
                        ]
                    }
                },
                "size": 100,
                "sort": [{"timestamp": {"order": "desc"}}]
            }
            
            # Search across all matching indices
            response = self.es_manager.es_client.search(
                index=index_pattern,
                body=query
            )
            
            peer_data = []
            for hit in response['hits']['hits']:
                data = hit['_source']['data']
                peer_data.append(data)
            
            logger.info(f"Fetched {len(peer_data)} peer server metrics for comparison")
            return peer_data
            
        except Exception as e:
            logger.error(f"Error fetching peer server data: {e}")
            return []
    
    def _perform_comparative_analysis(self, local_metrics: Dict[str, Any], peer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comparative analysis between local and peer server metrics."""
        try:
            # Extract metrics for comparison
            metrics_to_compare = [
                'avg_engagement_score',
                'command_diversity', 
                'total_users',
                'total_sessions',
                'total_time_hours',
                'total_skill_points',
                'high_engagement_users',
                'avg_session_length'
            ]
            
            comparison_metrics = {}
            peer_count = len(peer_data)
            
            for metric in metrics_to_compare:
                if metric not in local_metrics:
                    continue
                
                local_value = local_metrics[metric]
                peer_values = [peer[metric] for peer in peer_data if metric in peer]
                
                if not peer_values:
                    continue
                
                peer_min = min(peer_values)
                peer_max = max(peer_values)
                peer_avg = sum(peer_values) / len(peer_values)
                
                # Calculate relative score (0-100)
                if peer_max > peer_min:
                    relative_score = ((local_value - peer_min) / (peer_max - peer_min)) * 100
                else:
                    relative_score = 50.0  # Neutral if all peers have same value
                
                # Calculate percentile
                percentile = (sum(1 for v in peer_values if v <= local_value) / len(peer_values)) * 100
                
                # Calculate rank (1 = best)
                rank = sum(1 for v in peer_values if v > local_value) + 1
                
                comparison_metrics[metric] = {
                    'local_value': local_value,
                    'peer_min': peer_min,
                    'peer_max': peer_max,
                    'peer_avg': peer_avg,
                    'relative_score': round(relative_score, 1),
                    'percentile': round(percentile, 1),
                    'rank': rank,
                    'total_peers': peer_count
                }
            
            # Calculate overall performance score
            if comparison_metrics:
                avg_relative_score = sum(m['relative_score'] for m in comparison_metrics.values()) / len(comparison_metrics)
                overall_score = round(avg_relative_score, 1)
                
                # Determine grade and status
                if overall_score >= 90:
                    grade, status = "A+", "Excellent"
                elif overall_score >= 80:
                    grade, status = "A", "Very Good"
                elif overall_score >= 70:
                    grade, status = "B+", "Good"
                elif overall_score >= 60:
                    grade, status = "B", "Average"
                elif overall_score >= 50:
                    grade, status = "C+", "Below Average"
                else:
                    grade, status = "C", "Poor"
            else:
                overall_score = 0
                grade, status = "N/A", "No Data"
            
            # Generate command execution analysis
            command_analysis = self._analyze_command_executions(local_metrics, peer_data)
            
            # Generate learning progress analysis
            learning_analysis = self._analyze_learning_progress(local_metrics, peer_data)
            
            comparison_results = {
                'server_id': self.server_identifier,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'peer_count': peer_count,
                'comparison_metrics': comparison_metrics,
                'overall_performance': {
                    'score': overall_score,
                    'grade': grade,
                    'status': status
                },
                'command_execution_analysis': command_analysis,
                'learning_progress_analysis': learning_analysis
            }
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error in comparative analysis: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _analyze_command_executions(self, local_metrics: Dict[str, Any], peer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze command execution patterns compared to peers."""
        try:
            local_commands = local_metrics.get('total_commands', 0)
            local_unique = local_metrics.get('unique_commands', 0)
            local_diversity = local_metrics.get('command_diversity', 0)
            local_dangerous = local_metrics.get('dangerous_commands', 0)
            
            peer_commands = [p.get('total_commands', 0) for p in peer_data]
            peer_unique = [p.get('unique_commands', 0) for p in peer_data]
            peer_diversity = [p.get('command_diversity', 0) for p in peer_data]
            peer_dangerous = [p.get('dangerous_commands', 0) for p in peer_data]
            
            return {
                'command_volume': {
                    'local_total': local_commands,
                    'peer_avg': round(sum(peer_commands) / len(peer_commands), 1) if peer_commands else 0,
                    'volume_rank': sum(1 for v in peer_commands if v > local_commands) + 1 if peer_commands else 1
                },
                'command_diversity': {
                    'local_diversity': local_diversity,
                    'peer_avg_diversity': round(sum(peer_diversity) / len(peer_diversity), 3) if peer_diversity else 0,
                    'diversity_percentile': round((sum(1 for v in peer_diversity if v <= local_diversity) / len(peer_diversity)) * 100, 1) if peer_diversity else 50
                },
                'safety_analysis': {
                    'local_dangerous': local_dangerous,
                    'peer_avg_dangerous': round(sum(peer_dangerous) / len(peer_dangerous), 1) if peer_dangerous else 0,
                    'safety_score': max(0, 100 - (local_dangerous * 10))  # Penalty for dangerous commands
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing command executions: {e}")
            return {'error': f'Command analysis failed: {str(e)}'}
    
    def _analyze_learning_progress(self, local_metrics: Dict[str, Any], peer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze learning progress compared to peers."""
        try:
            local_skill_points = local_metrics.get('total_skill_points', 0)
            local_skill_dev = local_metrics.get('skill_development', {})
            
            peer_skill_points = [p.get('total_skill_points', 0) for p in peer_data]
            peer_skill_dev = [p.get('skill_development', {}) for p in peer_data]
            
            # Calculate skill development comparison
            skill_categories = set()
            for dev in peer_skill_dev + [local_skill_dev]:
                skill_categories.update(dev.keys())
            
            skill_comparison = {}
            for category in skill_categories:
                local_value = local_skill_dev.get(category, 0)
                peer_values = [dev.get(category, 0) for dev in peer_skill_dev]
                
                if peer_values:
                    peer_avg = sum(peer_values) / len(peer_values)
                    percentile = (sum(1 for v in peer_values if v <= local_value) / len(peer_values)) * 100
                    
                    skill_comparison[category] = {
                        'local_level': local_value,
                        'peer_avg_level': round(peer_avg, 1),
                        'percentile': round(percentile, 1),
                        'strength': percentile >= 75,
                        'weakness': percentile <= 25
                    }
            
            return {
                'overall_progress': {
                    'local_total_points': local_skill_points,
                    'peer_avg_points': round(sum(peer_skill_points) / len(peer_skill_points), 1) if peer_skill_points else 0,
                    'progress_percentile': round((sum(1 for v in peer_skill_points if v <= local_skill_points) / len(peer_skill_points)) * 100, 1) if peer_skill_points else 50
                },
                'skill_categories': skill_comparison,
                'learning_efficiency': {
                    'sessions_per_skill_point': round(local_metrics.get('total_sessions', 1) / max(1, local_skill_points), 2),
                    'time_per_skill_point': round(local_metrics.get('total_time_hours', 1) / max(1, local_skill_points), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing learning progress: {e}")
            return {'error': f'Learning analysis failed: {str(e)}'}
    


__all__ = ["EngagementScoring"]
