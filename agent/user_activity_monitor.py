"""
User Activity Monitor Module - User Session and Activity Tracking

This module provides comprehensive monitoring of user activity patterns in lab server
environments. It tracks user sessions, login/logout events, active processes, and
behavioral patterns to provide insights into user engagement and system usage.

Key Features:
- Real-time user session tracking and management
- Login/logout event monitoring and logging
- Active process monitoring per user
- User behavior pattern analysis
- Session timeout and cleanup management
- Cross-user activity comparison and analytics
- Integration with engagement scoring system

The module works in conjunction with the engagement scoring system to provide
comprehensive user behavior analysis and engagement metrics.
"""

import logging
import psutil
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Set up module-level logging
logger = logging.getLogger(__name__)

class UserActivityMonitor:
    """
    User activity monitoring and session management system.
    
    This class provides comprehensive tracking of user activities including session
    management, process monitoring, and behavioral pattern analysis. It integrates
    with the system's process monitoring capabilities to track user-specific
    activities and maintain session state.
    
    The monitor supports:
    - Real-time user session tracking
    - Process-level activity monitoring
    - Session timeout and cleanup
    - User behavior pattern analysis
    - Integration with engagement scoring
    - Cross-user activity comparison
    
    All user activity data is collected in real-time and can be used for
    engagement analysis, security monitoring, and resource usage optimization.
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize the user activity monitor.
        
        Args:
            session_timeout_minutes (int): Minutes of inactivity before session timeout
        """
        # Session management configuration
        self.session_timeout_minutes = session_timeout_minutes
        self.session_timeout_seconds = session_timeout_minutes * 60
        
        # User session tracking
        # Active user sessions with real-time activity data
        self.active_users: Dict[str, Dict[str, Any]] = {}
        # User session history for analysis and reporting
        self.session_history: List[Dict[str, Any]] = []
        
        # Process monitoring per user
        # Tracks active processes for each user session
        self.user_processes: Dict[str, Set[int]] = defaultdict(set)
        # Process details and metadata for each user
        self.process_details: Dict[int, Dict[str, Any]] = {}
        
        # Activity tracking and analytics
        # User activity patterns and behavioral metrics
        self.user_activity_patterns: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'login_count': 0,
            'total_session_time': 0.0,
            'average_session_time': 0.0,
            'last_activity': None,
            'favorite_applications': set(),
            'command_patterns': defaultdict(int)
        })
        
        # Performance and resource tracking
        # Resource usage per user for capacity planning
        self.user_resource_usage: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'disk_io_bytes': 0,
            'network_io_bytes': 0
        })
        
        logger.info("User activity monitor initialized with session timeout: %d minutes", session_timeout_minutes)
    
    def start_user_session(self, username: str, login_time: Optional[datetime] = None) -> bool:
        """
        Start monitoring a new user session.
        
        Args:
            username (str): Username to start monitoring
            login_time (Optional[datetime]): Login timestamp (defaults to current time)
            
        Returns:
            bool: True if session started successfully, False otherwise
        """
        try:
            # Use current time if no login time specified
            if login_time is None:
                login_time = datetime.now(timezone.utc)
            
            # Check if user already has an active session
            if username in self.active_users:
                logger.warning("User %s already has an active session", username)
                return False
            
            # Initialize new user session
            session_data = {
                'username': username,
                'login_time': login_time,
                'last_activity': login_time,
                'session_id': f"{username}_{int(login_time.timestamp())}",
                'processes': set(),
                'activity_count': 0,
                'resource_usage': {
                    'cpu_percent': 0.0,
                    'memory_mb': 0.0,
                    'disk_io_bytes': 0,
                    'network_io_bytes': 0
                }
            }
            
            # Add session to active users
            self.active_users[username] = session_data
            
            # Update user activity patterns
            self.user_activity_patterns[username]['login_count'] += 1
            self.user_activity_patterns[username]['last_activity'] = login_time
            
            # Initialize process tracking for user
            self.user_processes[username] = set()
            
            logger.info("Started monitoring session for user: %s", username)
            return True
            
        except Exception as e:
            logger.error("Error starting user session for %s: %s", username, e)
            return False
    
    def end_user_session(self, username: str, logout_time: Optional[datetime] = None) -> bool:
        """
        End monitoring for a user session.
        
        Args:
            username (str): Username to stop monitoring
            logout_time (Optional[datetime]): Logout timestamp (defaults to current time)
            
        Returns:
            bool: True if session ended successfully, False otherwise
        """
        try:
            # Check if user has an active session
            if username not in self.active_users:
                logger.warning("No active session found for user: %s", username)
                return False
            
            # Use current time if no logout time specified
            if logout_time is None:
                logout_time = datetime.now(timezone.utc)
            
            # Get session data
            session_data = self.active_users[username]
            login_time = session_data['login_time']
            
            # Calculate session duration
            session_duration = (logout_time - login_time).total_seconds() / 60.0  # minutes
            
            # Create session record for history
            session_record = {
                'username': username,
                'session_id': session_data['session_id'],
                'login_time': login_time.isoformat(),
                'logout_time': logout_time.isoformat(),
                'duration_minutes': session_duration,
                'activity_count': session_data['activity_count'],
                'final_resource_usage': session_data['resource_usage'].copy(),
                'process_count': len(session_data['processes'])
            }
            
            # Add to session history
            self.session_history.append(session_record)
            
            # Update user activity patterns
            patterns = self.user_activity_patterns[username]
            patterns['total_session_time'] += session_duration
            patterns['average_session_time'] = patterns['total_session_time'] / patterns['login_count']
            
            # Clean up user session data
            del self.active_users[username]
            
            # Clean up process tracking
            if username in self.user_processes:
                del self.user_processes[username]
            
            logger.info("Ended monitoring session for user: %s (duration: %.2f minutes)", username, session_duration)
            return True
            
        except Exception as e:
            logger.error("Error ending user session for %s: %s", username, e)
            return False
    
    def update_user_activity(self, username: str) -> bool:
        """
        Update user activity timestamp and metrics.
        
        Args:
            username (str): Username to update activity for
            
        Returns:
            bool: True if activity updated successfully, False otherwise
        """
        try:
            # Check if user has an active session
            if username not in self.active_users:
                logger.debug("No active session for user: %s", username)
                return False
            
            # Update last activity time
            current_time = datetime.now(timezone.utc)
            self.active_users[username]['last_activity'] = current_time
            self.active_users[username]['activity_count'] += 1
            
            # Update user activity patterns
            self.user_activity_patterns[username]['last_activity'] = current_time
            
            # Update resource usage metrics
            self._update_user_resource_usage(username)
            
            logger.debug("Updated activity for user: %s", username)
            return True
            
        except Exception as e:
            logger.error("Error updating activity for user %s: %s", username, e)
            return False
    
    def _update_user_resource_usage(self, username: str) -> None:
        """
        Update resource usage metrics for a specific user.
        
        Args:
            username (str): Username to update resource usage for
        """
        try:
            # Get user's active processes
            user_pids = self.user_processes.get(username, set())
            
            if not user_pids:
                return
            
            # Calculate aggregate resource usage
            total_cpu = 0.0
            total_memory = 0.0
            total_disk_io = 0
            total_network_io = 0
            
            # Sum resource usage across all user processes
            for pid in user_pids:
                try:
                    process = psutil.Process(pid)
                    
                    # CPU usage
                    cpu_percent = process.cpu_percent()
                    if cpu_percent > 0:
                        total_cpu += cpu_percent
                    
                    # Memory usage
                    memory_info = process.memory_info()
                    total_memory += memory_info.rss / (1024 * 1024)  # Convert to MB
                    
                    # Disk I/O
                    io_counters = process.io_counters()
                    if io_counters:
                        total_disk_io += io_counters.read_bytes + io_counters.write_bytes
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process may have ended or access denied
                    continue
            
            # Update user resource usage
            self.user_resource_usage[username] = {
                'cpu_percent': total_cpu,
                'memory_mb': total_memory,
                'disk_io_bytes': total_disk_io,
                'network_io_bytes': total_network_io
            }
            
            # Update session resource usage
            if username in self.active_users:
                self.active_users[username]['resource_usage'] = self.user_resource_usage[username].copy()
                
        except Exception as e:
            logger.error("Error updating resource usage for user %s: %s", username, e)
    
    def get_active_users(self) -> List[str]:
        """
        Get list of currently active users.
        
        Returns:
            List[str]: List of usernames with active sessions
        """
        return list(self.active_users.keys())
    
    def get_user_session_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information for a specific user.
        
        Args:
            username (str): Username to get session info for
            
        Returns:
            Optional[Dict[str, Any]]: Session information or None if not found
        """
        return self.active_users.get(username)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of all active and historical sessions.
        
        Returns:
            Dict[str, Any]: Session summary with statistics and metrics
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            # Calculate active session statistics
            active_sessions = len(self.active_users)
            total_active_time = 0.0
            
            for session in self.active_users.values():
                session_duration = (current_time - session['login_time']).total_seconds() / 60.0
                total_active_time += session_duration
            
            # Calculate historical session statistics
            total_sessions = len(self.session_history)
            total_session_time = sum(session['duration_minutes'] for session in self.session_history)
            average_session_time = total_session_time / total_sessions if total_sessions > 0 else 0
            
            return {
                'active_sessions': active_sessions,
                'total_active_time_minutes': total_active_time,
                'historical_sessions': total_sessions,
                'total_historical_time_minutes': total_session_time,
                'average_session_time_minutes': average_session_time,
                'active_users': list(self.active_users.keys()),
                'session_history_count': total_sessions
            }
            
        except Exception as e:
            logger.error("Error generating session summary: %s", e)
            return {}
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired user sessions based on timeout.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            current_time = datetime.now(timezone.utc)
            expired_users = []
            
            # Find expired sessions
            for username, session_data in self.active_users.items():
                last_activity = session_data['last_activity']
                time_since_activity = (current_time - last_activity).total_seconds()
                
                if time_since_activity > self.session_timeout_seconds:
                    expired_users.append(username)
            
            # End expired sessions
            for username in expired_users:
                self.end_user_session(username, current_time)
                logger.info("Cleaned up expired session for user: %s", username)
            
            return len(expired_users)
            
        except Exception as e:
            logger.error("Error cleaning up expired sessions: %s", e)
            return 0
    
    def clear_history(self) -> None:
        """Clear all session history and user activity patterns."""
        self.session_history.clear()
        self.user_activity_patterns.clear()
        logger.info("User activity monitor history cleared")
