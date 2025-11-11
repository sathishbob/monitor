"""
File System Activity Monitor Module - Track File Operations and Code Changes

This module provides comprehensive monitoring of file system activities including
file creation, modification, deletion, and project structure analysis.

Key Features:
- Real-time file system event monitoring
- Code file tracking by extension
- Project directory structure analysis
- Git activity monitoring
- File line count tracking
- Code change patterns analysis
"""

import logging
import os
import platform
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)

class FileSystemMonitor:
    """
    File system activity monitoring and code change tracking.

    Monitors file operations to understand student coding activity,
    project development, and learning progress through code artifacts.
    """

    def __init__(self, watch_directories: List[str] = None, es_manager=None):
        """
        Initialize the file system monitor.

        Args:
            watch_directories: List of directories to monitor
            es_manager: Elasticsearch manager for data persistence
        """
        self.es_manager = es_manager
        self.watch_directories = watch_directories or []

        # File activity tracking
        self.file_events: deque = deque(maxlen=10000)
        self.file_stats: Dict[str, Dict[str, Any]] = {}

        # Code file extensions to track
        self.code_extensions = {
            '.py': 'Python',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'Header',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bat': 'Batch',
            '.ps1': 'PowerShell',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.r': 'R',
            '.m': 'MATLAB'
        }

        # Project-related files
        self.project_files = {
            'package.json': 'Node.js Project',
            'requirements.txt': 'Python Project',
            'pom.xml': 'Maven Project',
            'build.gradle': 'Gradle Project',
            'Cargo.toml': 'Rust Project',
            'go.mod': 'Go Project',
            'Gemfile': 'Ruby Project',
            'composer.json': 'PHP Project',
            'Dockerfile': 'Docker Project',
            'docker-compose.yml': 'Docker Compose',
            '.gitignore': 'Git Repository',
            'README.md': 'Documentation',
            'Makefile': 'Make Build',
            'CMakeLists.txt': 'CMake Build'
        }

        # Git activity tracking
        self.git_operations: List[Dict[str, Any]] = []

        # File statistics
        self.file_type_stats: Dict[str, int] = defaultdict(int)
        self.lines_of_code: Dict[str, int] = defaultdict(int)

        # User activity mapping
        self.user_file_activity: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        logger.info("File system monitor initialized")

    def set_es_manager(self, es_manager):
        """Set Elasticsearch manager."""
        self.es_manager = es_manager

    def track_file_event(self, event_type: str, file_path: str, user_id: str = None,
                        timestamp: datetime = None) -> Dict[str, Any]:
        """
        Track a file system event.

        Args:
            event_type: Type of event (create, modify, delete, rename)
            file_path: Path to the file
            user_id: User who performed the action
            timestamp: Event timestamp

        Returns:
            Event data dictionary
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        try:
            file_path_obj = Path(file_path)
            file_ext = file_path_obj.suffix.lower()
            file_name = file_path_obj.name

            # Classify file type
            file_type = self.code_extensions.get(file_ext, 'Other')
            is_code_file = file_ext in self.code_extensions
            is_project_file = file_name in self.project_files

            # Get file size and line count
            file_size = 0
            line_count = 0
            if os.path.exists(file_path) and event_type != 'delete':
                try:
                    file_size = os.path.getsize(file_path)
                    if is_code_file:
                        line_count = self._count_lines(file_path)
                except (OSError, PermissionError):
                    pass

            # Create event record
            event_data = {
                'timestamp': timestamp.isoformat(),
                'event_type': event_type,
                'file_path': file_path,
                'file_name': file_name,
                'file_extension': file_ext,
                'file_type': file_type,
                'is_code_file': is_code_file,
                'is_project_file': is_project_file,
                'file_size_bytes': file_size,
                'line_count': line_count,
                'user_id': user_id,
                'directory': str(file_path_obj.parent)
            }

            # Store event
            self.file_events.append(event_data)

            # Update user activity
            if user_id:
                self.user_file_activity[user_id].append(event_data)

            # Update statistics
            if event_type == 'create' or event_type == 'modify':
                self.file_type_stats[file_type] += 1
                if is_code_file:
                    self.lines_of_code[file_type] += line_count

            # Push to Elasticsearch
            if self.es_manager:
                self.es_manager.push_data(event_data, 'filesystem_activity')

            logger.debug(f"Tracked {event_type} event for {file_name} ({file_type})")
            return event_data

        except Exception as e:
            logger.error(f"Error tracking file event: {e}")
            return {}

    def _count_lines(self, file_path: str) -> int:
        """Count lines in a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.debug(f"Could not count lines in {file_path}: {e}")
            return 0

    def track_git_operation(self, operation: str, user_id: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Track Git operations.

        Args:
            operation: Git operation (commit, push, pull, branch, merge)
            user_id: User performing the operation
            details: Additional operation details

        Returns:
            Git operation data
        """
        timestamp = datetime.now(timezone.utc)

        git_data = {
            'timestamp': timestamp.isoformat(),
            'operation': operation,
            'user_id': user_id,
            'details': details or {}
        }

        self.git_operations.append(git_data)

        # Push to Elasticsearch
        if self.es_manager:
            self.es_manager.push_data(git_data, 'git_activity')

        logger.info(f"Git operation tracked: {operation} by {user_id}")
        return git_data

    def scan_directory_changes(self, directory: str, user_id: str = None) -> Dict[str, Any]:
        """
        Scan a directory for recent changes.

        Args:
            directory: Directory to scan
            user_id: User associated with the scan

        Returns:
            Directory analysis data
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {'error': 'Directory does not exist'}

            analysis = {
                'directory': directory,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id,
                'total_files': 0,
                'total_directories': 0,
                'code_files_by_type': defaultdict(int),
                'total_lines_of_code': 0,
                'project_files_found': [],
                'recent_modifications': []
            }

            # Walk directory
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories and common excludes
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'build', 'dist']]

                analysis['total_directories'] += len(dirs)

                for file_name in files:
                    if file_name.startswith('.'):
                        continue

                    file_path = os.path.join(root, file_name)
                    analysis['total_files'] += 1

                    # Check if it's a code file
                    file_ext = Path(file_name).suffix.lower()
                    if file_ext in self.code_extensions:
                        file_type = self.code_extensions[file_ext]
                        analysis['code_files_by_type'][file_type] += 1

                        # Count lines
                        lines = self._count_lines(file_path)
                        analysis['total_lines_of_code'] += lines

                    # Check if it's a project file
                    if file_name in self.project_files:
                        analysis['project_files_found'].append({
                            'file': file_name,
                            'type': self.project_files[file_name],
                            'path': file_path
                        })

                    # Check modification time
                    try:
                        mtime = os.path.getmtime(file_path)
                        if time.time() - mtime < 3600:  # Modified in last hour
                            analysis['recent_modifications'].append({
                                'file': file_name,
                                'path': file_path,
                                'modified_ago_seconds': int(time.time() - mtime)
                            })
                    except OSError:
                        pass

            # Convert defaultdict to regular dict for JSON serialization
            analysis['code_files_by_type'] = dict(analysis['code_files_by_type'])

            # Push to Elasticsearch
            if self.es_manager:
                self.es_manager.push_data(analysis, 'directory_scan')

            logger.info(f"Directory scan completed: {directory}")
            return analysis

        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            return {'error': str(e)}

    def get_user_file_activity(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get file activity summary for a user."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        activities = self.user_file_activity.get(user_id, [])
        recent_activities = [
            a for a in activities
            if datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) > cutoff
        ]

        summary = {
            'user_id': user_id,
            'period_hours': hours,
            'total_events': len(recent_activities),
            'files_created': len([a for a in recent_activities if a['event_type'] == 'create']),
            'files_modified': len([a for a in recent_activities if a['event_type'] == 'modify']),
            'files_deleted': len([a for a in recent_activities if a['event_type'] == 'delete']),
            'code_files_touched': len([a for a in recent_activities if a['is_code_file']]),
            'total_lines_changed': sum(a.get('line_count', 0) for a in recent_activities),
            'file_types_worked': list(set(a['file_type'] for a in recent_activities)),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        return summary

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get overall project statistics."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_events': len(self.file_events),
            'file_type_distribution': dict(self.file_type_stats),
            'lines_of_code_by_type': dict(self.lines_of_code),
            'total_git_operations': len(self.git_operations),
            'monitored_directories': self.watch_directories
        }


__all__ = ['FileSystemMonitor']
