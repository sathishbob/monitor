"""
Windows Application & Window Usage Monitor

This module provides comprehensive tracking of Windows application usage and window activity
for engagement and productivity analytics.

Key Features:
- Real-time application window tracking
- Process foreground/background detection
- Window title and application name capture
- Time spent per application tracking
- Application usage patterns analysis
- Integration with engagement scoring

The module uses Windows APIs to track:
- Foreground window changes
- Application focus changes
- Window titles and process names
- User interaction with applications
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict, deque

# Set up module-level logging
logger = logging.getLogger(__name__)


class WindowsWindowMonitor:
    """
    Windows application and window usage monitoring system.
    
    This class tracks window and application usage on Windows systems using
    Windows APIs to detect foreground window changes and application switches.
    
    It provides:
    - Real-time window/application tracking
    - Process name and window title detection
    - Time spent per application
    - Application usage frequency
    - Integration with engagement scoring
    """
    
    def __init__(self, check_interval_seconds: float = 5.0):
        """
        Initialize Windows window monitor.
        
        Args:
            check_interval_seconds (float): Seconds between window checks (default 5)
        """
        self.check_interval = check_interval_seconds
        
        # Current tracking state
        self.current_window = None
        self.current_process_name = None
        self.current_window_title = None
        self.window_start_time = None
        
        # Historical usage tracking
        self.application_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_time_seconds': 0.0,
            'session_count': 0,
            'window_titles': set(),
            'last_used': None,
            'first_seen': None
        })
        
        # Recent window switches for reporting
        self.recent_window_changes = deque(maxlen=100)
        
        logger.info("Windows window monitor initialized")
    
    def get_current_window_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current foreground window information.
        
        Returns:
            Optional[Dict[str, Any]]: Window info or None if unavailable
        """
        try:
            import psutil
            import ctypes
            from ctypes import wintypes
            
            # Constants for Windows API
            GW_OWNER = 4
            
            # Get foreground window handle
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # Get handle of foreground window
            hwnd = user32.GetForegroundWindow()
            
            if not hwnd:
                return None
            
            # Get process ID from window handle
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid = pid.value
            
            # Get process name from PID
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                exe_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
            
            # Get window title
            length = user32.GetWindowTextLengthW(hwnd)
            window_title = None
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                window_title = buffer.value
            
            # Check if window is still valid (not a dead window)
            is_valid = user32.IsWindowVisible(hwnd)
            
            if not is_valid:
                return None
            
            return {
                'process_name': process_name,
                'exe_path': exe_path,
                'window_title': window_title or '',
                'hwnd': hwnd,
                'pid': pid
            }
            
        except ImportError:
            logger.error("Required Windows libraries not available")
            return None
        except Exception as e:
            logger.debug(f"Error getting window info: {e}")
            return None
    
    def track_window_activity(self) -> Optional[Dict[str, Any]]:
        """
        Track current window activity and return if window changed.
        
        Returns:
            Optional[Dict[str, Any]]: Window change data if window switched
        """
        try:
            current_window_info = self.get_current_window_info()
            
            if not current_window_info:
                return None
            
            process_name = current_window_info['process_name']
            window_title = current_window_info['window_title']
            pid = current_window_info['pid']
            
            current_time = datetime.now(timezone.utc)
            
            # Check if window changed
            window_changed = (
                self.current_process_name != process_name or
                self.current_window_title != window_title
            )
            
            if window_changed and self.current_process_name is not None:
                # Calculate time spent on previous window
                time_spent = 0.0
                if self.window_start_time:
                    time_spent = (current_time - self.window_start_time).total_seconds()
                
                # Update previous window usage
                if self.current_process_name:
                    self._update_application_usage(
                        self.current_process_name,
                        self.current_window_title,
                        time_spent
                    )
                
                # Log window change
                change_data = {
                    'timestamp': current_time.isoformat(),
                    'previous_process': self.current_process_name,
                    'previous_window': self.current_window_title,
                    'time_spent_seconds': time_spent,
                    'current_process': process_name,
                    'current_window': window_title
                }
                
                self.recent_window_changes.append(change_data)
                logger.debug(f"Window switched: {self.current_process_name} -> {process_name}")
                
                # Update tracking state
                self.current_process_name = process_name
                self.current_window_title = window_title
                self.current_window = current_window_info
                self.window_start_time = current_time
                
                return change_data
            
            # First time or no change
            if self.current_process_name is None:
                self.current_process_name = process_name
                self.current_window_title = window_title
                self.current_window = current_window_info
                self.window_start_time = current_time
            
            return None
            
        except Exception as e:
            logger.error(f"Error tracking window activity: {e}")
            return None
    
    def _update_application_usage(self, app_name: str, window_title: str, duration: float) -> None:
        """
        Update application usage statistics.
        
        Args:
            app_name (str): Application/process name
            window_title (str): Window title
            duration (float): Time spent in seconds
        """
        try:
            app_data = self.application_usage[app_name]
            app_data['total_time_seconds'] += duration
            app_data['session_count'] += 1
            app_data['window_titles'].add(window_title)
            app_data['last_used'] = datetime.now(timezone.utc)
            
            if app_data['first_seen'] is None:
                app_data['first_seen'] = datetime.now(timezone.utc)
                
        except Exception as e:
            logger.error(f"Error updating application usage for {app_name}: {e}")
    
    def get_application_summary(self) -> Dict[str, Any]:
        """
        Get summary of application usage.
        
        Returns:
            Dict[str, Any]: Application usage summary
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            # Calculate current session time
            current_session_time = 0.0
            if self.window_start_time:
                current_session_time = (current_time - self.window_start_time).total_seconds()
            
            summary = {
                'timestamp': current_time.isoformat(),
                'current_application': {
                    'process_name': self.current_process_name,
                    'window_title': self.current_window_title,
                    'session_duration_seconds': current_session_time
                },
                'application_usage': {
                    app: {
                        'total_time_seconds': data['total_time_seconds'],
                        'session_count': data['session_count'],
                        'unique_windows': len(data['window_titles']),
                        'window_samples': list(data['window_titles'])[:5],  # First 5 samples
                        'last_used': data['last_used'].isoformat() if data['last_used'] else None
                    }
                    for app, data in self.application_usage.items()
                },
                'recent_window_changes': list(self.recent_window_changes)[-10:],  # Last 10 changes
                'total_applications_used': len(self.application_usage)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating application summary: {e}")
            return {}
    
    def get_top_applications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top applications by usage time.
        
        Args:
            limit (int): Number of top applications to return
            
        Returns:
            List[Dict[str, Any]]: Top applications sorted by usage time
        """
        try:
            apps_list = [
                {
                    'app_name': app,
                    'total_time_minutes': data['total_time_seconds'] / 60,
                    'total_time_hours': data['total_time_seconds'] / 3600,
                    'session_count': data['session_count'],
                    'unique_windows': len(data['window_titles']),
                    'last_used': data['last_used'].isoformat() if data['last_used'] else None
                }
                for app, data in self.application_usage.items()
            ]
            
            # Sort by total time (descending)
            apps_list.sort(key=lambda x: x['total_time_seconds'], reverse=True)
            
            return apps_list[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top applications: {e}")
            return []


__all__ = ["WindowsWindowMonitor"]

