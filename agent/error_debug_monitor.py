"""
Error and Debugging Metrics Monitor - Track Compilation Errors and Debugging Activity

This module monitors error patterns, debugging sessions, and problem-solving behavior
to identify struggling students and measure learning progress.

Key Features:
- Compilation error tracking
- Runtime exception monitoring
- Debug session duration tracking
- Error resolution time measurement
- Stack trace pattern analysis
- Test failure tracking
"""

import logging
import re
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class ErrorDebugMonitor:
    """
    Error and debugging activity monitoring system.

    Tracks errors, debugging sessions, and problem-solving patterns
    to provide insights into student learning struggles and progress.
    """

    def __init__(self, es_manager=None):
        """
        Initialize the error and debug monitor.

        Args:
            es_manager: Elasticsearch manager for data persistence
        """
        self.es_manager = es_manager

        # Error tracking
        self.compilation_errors: deque = deque(maxlen=5000)
        self.runtime_errors: deque = deque(maxlen=5000)
        self.test_failures: deque = deque(maxlen=5000)

        # Debug session tracking
        self.debug_sessions: List[Dict[str, Any]] = []
        self.active_debug_sessions: Dict[str, Dict[str, Any]] = {}

        # Error patterns
        self.error_patterns = {
            'SyntaxError': {'category': 'syntax', 'severity': 'low'},
            'IndentationError': {'category': 'syntax', 'severity': 'low'},
            'NameError': {'category': 'runtime', 'severity': 'medium'},
            'TypeError': {'category': 'runtime', 'severity': 'medium'},
            'ValueError': {'category': 'runtime', 'severity': 'medium'},
            'AttributeError': {'category': 'runtime', 'severity': 'medium'},
            'KeyError': {'category': 'runtime', 'severity': 'medium'},
            'IndexError': {'category': 'runtime', 'severity': 'medium'},
            'ZeroDivisionError': {'category': 'logic', 'severity': 'low'},
            'FileNotFoundError': {'category': 'io', 'severity': 'low'},
            'PermissionError': {'category': 'io', 'severity': 'medium'},
            'ImportError': {'category': 'environment', 'severity': 'medium'},
            'ModuleNotFoundError': {'category': 'environment', 'severity': 'medium'},
            'NullPointerException': {'category': 'runtime', 'severity': 'high'},
            'SegmentationFault': {'category': 'memory', 'severity': 'high'},
            'StackOverflowError': {'category': 'recursion', 'severity': 'high'},
            'OutOfMemoryError': {'category': 'memory', 'severity': 'high'},
            'AssertionError': {'category': 'test', 'severity': 'low'},
            'CompilationError': {'category': 'compilation', 'severity': 'medium'}
        }

        # User error statistics
        self.user_error_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_errors': 0,
            'compilation_errors': 0,
            'runtime_errors': 0,
            'errors_by_type': defaultdict(int),
            'errors_by_category': defaultdict(int),
            'average_resolution_time': 0.0,
            'debug_sessions_count': 0,
            'total_debug_time': 0.0
        })

        # Error resolution tracking
        self.unresolved_errors: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        logger.info("Error and debug monitor initialized")

    def set_es_manager(self, es_manager):
        """Set Elasticsearch manager."""
        self.es_manager = es_manager

    def track_compilation_error(self, error_message: str, file_path: str,
                                line_number: int = None, user_id: str = None,
                                compiler: str = None) -> Dict[str, Any]:
        """
        Track a compilation error.

        Args:
            error_message: Error message from compiler
            file_path: File where error occurred
            line_number: Line number of error
            user_id: User who encountered the error
            compiler: Compiler/interpreter name

        Returns:
            Error data dictionary
        """
        timestamp = datetime.now(timezone.utc)

        # Classify error type
        error_type = self._classify_error(error_message)
        error_info = self.error_patterns.get(error_type, {
            'category': 'unknown',
            'severity': 'medium'
        })

        error_data = {
            'timestamp': timestamp.isoformat(),
            'error_type': 'compilation',
            'error_class': error_type,
            'error_category': error_info['category'],
            'severity': error_info['severity'],
            'message': error_message[:500],  # Limit message length
            'file_path': file_path,
            'line_number': line_number,
            'user_id': user_id,
            'compiler': compiler,
            'resolved': False,
            'resolution_time': None
        }

        # Store error
        self.compilation_errors.append(error_data)

        # Update user statistics
        if user_id:
            stats = self.user_error_stats[user_id]
            stats['total_errors'] += 1
            stats['compilation_errors'] += 1
            stats['errors_by_type'][error_type] += 1
            stats['errors_by_category'][error_info['category']] += 1

            # Add to unresolved errors
            self.unresolved_errors[user_id].append(error_data)

        # Push to Elasticsearch
        if self.es_manager:
            self.es_manager.push_data(error_data, 'compilation_error')

        logger.debug(f"Compilation error tracked: {error_type} in {file_path}")
        return error_data

    def track_runtime_error(self, error_type: str, error_message: str,
                           stack_trace: str = None, file_path: str = None,
                           line_number: int = None, user_id: str = None) -> Dict[str, Any]:
        """
        Track a runtime error/exception.

        Args:
            error_type: Type of exception (e.g., TypeError, ValueError)
            error_message: Error message
            stack_trace: Full stack trace
            file_path: File where error occurred
            line_number: Line number
            user_id: User who encountered the error

        Returns:
            Error data dictionary
        """
        timestamp = datetime.now(timezone.utc)

        error_info = self.error_patterns.get(error_type, {
            'category': 'unknown',
            'severity': 'medium'
        })

        error_data = {
            'timestamp': timestamp.isoformat(),
            'error_type': 'runtime',
            'error_class': error_type,
            'error_category': error_info['category'],
            'severity': error_info['severity'],
            'message': error_message[:500],
            'stack_trace': stack_trace[:1000] if stack_trace else None,
            'file_path': file_path,
            'line_number': line_number,
            'user_id': user_id,
            'resolved': False,
            'resolution_time': None
        }

        # Store error
        self.runtime_errors.append(error_data)

        # Update user statistics
        if user_id:
            stats = self.user_error_stats[user_id]
            stats['total_errors'] += 1
            stats['runtime_errors'] += 1
            stats['errors_by_type'][error_type] += 1
            stats['errors_by_category'][error_info['category']] += 1

            # Add to unresolved errors
            self.unresolved_errors[user_id].append(error_data)

        # Push to Elasticsearch
        if self.es_manager:
            self.es_manager.push_data(error_data, 'runtime_error')

        logger.debug(f"Runtime error tracked: {error_type} for user {user_id}")
        return error_data

    def track_test_failure(self, test_name: str, failure_message: str,
                          test_file: str = None, user_id: str = None,
                          test_framework: str = None) -> Dict[str, Any]:
        """
        Track a test failure.

        Args:
            test_name: Name of failed test
            failure_message: Failure message
            test_file: Test file path
            user_id: User running the test
            test_framework: Testing framework (pytest, junit, etc.)

        Returns:
            Test failure data
        """
        timestamp = datetime.now(timezone.utc)

        failure_data = {
            'timestamp': timestamp.isoformat(),
            'test_name': test_name,
            'failure_message': failure_message[:500],
            'test_file': test_file,
            'user_id': user_id,
            'test_framework': test_framework,
            'resolved': False
        }

        self.test_failures.append(failure_data)

        # Push to Elasticsearch
        if self.es_manager:
            self.es_manager.push_data(failure_data, 'test_failure')

        logger.debug(f"Test failure tracked: {test_name}")
        return failure_data

    def start_debug_session(self, user_id: str, file_path: str = None,
                           debugger: str = None) -> str:
        """
        Start tracking a debug session.

        Args:
            user_id: User starting debug session
            file_path: File being debugged
            debugger: Debugger tool (gdb, pdb, etc.)

        Returns:
            Debug session ID
        """
        timestamp = datetime.now(timezone.utc)
        session_id = f"{user_id}_{int(timestamp.timestamp())}"

        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'file_path': file_path,
            'debugger': debugger,
            'start_time': timestamp,
            'end_time': None,
            'duration_seconds': None,
            'breakpoints_set': 0,
            'steps_executed': 0,
            'variables_inspected': 0
        }

        self.active_debug_sessions[session_id] = session_data
        logger.info(f"Debug session started: {session_id}")
        return session_id

    def end_debug_session(self, session_id: str, breakpoints: int = 0,
                         steps: int = 0, variables: int = 0) -> Dict[str, Any]:
        """
        End a debug session.

        Args:
            session_id: Debug session ID
            breakpoints: Number of breakpoints set
            steps: Number of steps executed
            variables: Number of variables inspected

        Returns:
            Completed session data
        """
        if session_id not in self.active_debug_sessions:
            logger.warning(f"Debug session not found: {session_id}")
            return {}

        timestamp = datetime.now(timezone.utc)
        session = self.active_debug_sessions[session_id]

        session['end_time'] = timestamp
        session['duration_seconds'] = (timestamp - session['start_time']).total_seconds()
        session['breakpoints_set'] = breakpoints
        session['steps_executed'] = steps
        session['variables_inspected'] = variables

        # Update user statistics
        user_id = session['user_id']
        if user_id:
            stats = self.user_error_stats[user_id]
            stats['debug_sessions_count'] += 1
            stats['total_debug_time'] += session['duration_seconds']

        # Convert datetime to ISO format for serialization
        session_export = session.copy()
        session_export['start_time'] = session['start_time'].isoformat()
        session_export['end_time'] = session['end_time'].isoformat()

        # Store in history
        self.debug_sessions.append(session_export)

        # Remove from active sessions
        del self.active_debug_sessions[session_id]

        # Push to Elasticsearch
        if self.es_manager:
            self.es_manager.push_data(session_export, 'debug_session')

        logger.info(f"Debug session ended: {session_id} (duration: {session['duration_seconds']:.1f}s)")
        return session_export

    def mark_error_resolved(self, user_id: str, file_path: str) -> int:
        """
        Mark errors as resolved when file is successfully compiled/run.

        Args:
            user_id: User who resolved the error
            file_path: File that was fixed

        Returns:
            Number of errors marked as resolved
        """
        timestamp = datetime.now(timezone.utc)
        resolved_count = 0

        if user_id in self.unresolved_errors:
            for error in self.unresolved_errors[user_id]:
                if error['file_path'] == file_path and not error['resolved']:
                    error['resolved'] = True
                    error['resolved_timestamp'] = timestamp.isoformat()

                    # Calculate resolution time
                    error_time = datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00'))
                    resolution_time = (timestamp - error_time).total_seconds()
                    error['resolution_time'] = resolution_time

                    # Update average resolution time
                    stats = self.user_error_stats[user_id]
                    current_avg = stats['average_resolution_time']
                    total_resolved = stats.get('resolved_errors', 0)
                    stats['average_resolution_time'] = (current_avg * total_resolved + resolution_time) / (total_resolved + 1)
                    stats['resolved_errors'] = total_resolved + 1

                    resolved_count += 1

            # Remove resolved errors from unresolved list
            self.unresolved_errors[user_id] = [e for e in self.unresolved_errors[user_id] if not e['resolved']]

        logger.debug(f"Marked {resolved_count} errors as resolved for {user_id}")
        return resolved_count

    def _classify_error(self, error_message: str) -> str:
        """Classify error type from message."""
        for error_type in self.error_patterns.keys():
            if error_type.lower() in error_message.lower():
                return error_type
        return 'UnknownError'

    def get_user_error_summary(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for a user."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get recent errors
        recent_compilation = [
            e for e in self.compilation_errors
            if e.get('user_id') == user_id and
            datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) > cutoff
        ]

        recent_runtime = [
            e for e in self.runtime_errors
            if e.get('user_id') == user_id and
            datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) > cutoff
        ]

        stats = self.user_error_stats.get(user_id, {})

        return {
            'user_id': user_id,
            'period_hours': hours,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'recent_compilation_errors': len(recent_compilation),
            'recent_runtime_errors': len(recent_runtime),
            'total_recent_errors': len(recent_compilation) + len(recent_runtime),
            'unresolved_errors': len(self.unresolved_errors.get(user_id, [])),
            'errors_by_category': dict(stats.get('errors_by_category', {})),
            'average_resolution_time_seconds': stats.get('average_resolution_time', 0),
            'debug_sessions': stats.get('debug_sessions_count', 0),
            'total_debug_time_seconds': stats.get('total_debug_time', 0),
            'error_rate_per_hour': (len(recent_compilation) + len(recent_runtime)) / max(1, hours)
        }

    def get_error_patterns(self) -> Dict[str, Any]:
        """Get overall error patterns and statistics."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_compilation_errors': len(self.compilation_errors),
            'total_runtime_errors': len(self.runtime_errors),
            'total_test_failures': len(self.test_failures),
            'active_debug_sessions': len(self.active_debug_sessions),
            'completed_debug_sessions': len(self.debug_sessions),
            'users_with_errors': len(self.user_error_stats)
        }


__all__ = ['ErrorDebugMonitor']
