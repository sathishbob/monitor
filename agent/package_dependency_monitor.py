"""
Package and Dependency Management Monitor

Tracks package installations, dependency management, and environment setup
to understand environment proficiency and identify common blockers.
"""

import logging
import re
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PackageDependencyMonitor:
    """Monitor package management and dependency operations."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.package_operations: deque = deque(maxlen=5000)
        self.user_packages: Dict[str, Set] = defaultdict(set)
        self.dependency_conflicts: List[Dict[str, Any]] = []

        # Package managers to track
        self.package_managers = {
            'pip': 'Python',
            'npm': 'Node.js',
            'yarn': 'Node.js',
            'maven': 'Java',
            'gradle': 'Java',
            'cargo': 'Rust',
            'gem': 'Ruby',
            'composer': 'PHP',
            'conda': 'Python/Data Science',
            'apt': 'System (Debian)',
            'yum': 'System (RedHat)',
            'brew': 'System (macOS)'
        }

        logger.info("Package dependency monitor initialized")

    def track_package_operation(self, package_manager: str, operation: str,
                                package_name: str, version: str = None,
                                user_id: str = None, success: bool = True,
                                error_message: str = None) -> Dict[str, Any]:
        """Track a package management operation."""
        timestamp = datetime.now(timezone.utc)

        op_data = {
            'timestamp': timestamp.isoformat(),
            'package_manager': package_manager,
            'operation': operation,  # install, uninstall, update, etc.
            'package_name': package_name,
            'version': version,
            'user_id': user_id,
            'success': success,
            'error_message': error_message,
            'ecosystem': self.package_managers.get(package_manager, 'Unknown')
        }

        self.package_operations.append(op_data)

        if user_id and success and operation == 'install':
            self.user_packages[user_id].add(f"{package_name}:{version}" if version else package_name)

        if self.es_manager:
            self.es_manager.push_data(op_data, 'package_operation')

        return op_data

    def track_dependency_conflict(self, user_id: str, package_name: str,
                                  conflict_details: Dict[str, Any]) -> Dict[str, Any]:
        """Track dependency conflict."""
        timestamp = datetime.now(timezone.utc)

        conflict_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'package_name': package_name,
            'conflict_type': conflict_details.get('type', 'version_mismatch'),
            'details': conflict_details,
            'resolved': False
        }

        self.dependency_conflicts.append(conflict_data)

        if self.es_manager:
            self.es_manager.push_data(conflict_data, 'dependency_conflict')

        return conflict_data

    def track_virtualenv_creation(self, user_id: str, env_type: str,
                                  path: str, python_version: str = None) -> Dict[str, Any]:
        """Track virtual environment creation."""
        timestamp = datetime.now(timezone.utc)

        env_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'environment_type': env_type,  # venv, conda, virtualenv
            'path': path,
            'python_version': python_version
        }

        if self.es_manager:
            self.es_manager.push_data(env_data, 'virtualenv_creation')

        return env_data

    def get_user_package_summary(self, user_id: str) -> Dict[str, Any]:
        """Get package management summary for user."""
        user_ops = [op for op in self.package_operations if op.get('user_id') == user_id]

        if not user_ops:
            return {'user_id': user_id, 'no_data': True}

        installs = len([op for op in user_ops if op['operation'] == 'install'])
        failures = len([op for op in user_ops if not op['success']])

        return {
            'user_id': user_id,
            'total_operations': len(user_ops),
            'total_installs': installs,
            'total_failures': failures,
            'unique_packages': len(self.user_packages.get(user_id, set())),
            'success_rate': (len(user_ops) - failures) / max(1, len(user_ops)) * 100,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['PackageDependencyMonitor']
