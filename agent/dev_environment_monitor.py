"""
Development Environment Monitor - Track IDE, Tools, and Environment Setup

Monitors IDE usage, editor configurations, plugins, and development tools
to understand student tool proficiency and optimize lab environments.
"""

import logging
import platform
import psutil
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class DevEnvironmentMonitor:
    """Track development environment and tooling usage."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager

        # IDE/Editor tracking
        self.ide_tools = {
            'code': 'Visual Studio Code',
            'pycharm': 'PyCharm',
            'intellij': 'IntelliJ IDEA',
            'eclipse': 'Eclipse',
            'vim': 'Vim',
            'nvim': 'Neovim',
            'emacs': 'Emacs',
            'sublime': 'Sublime Text',
            'atom': 'Atom',
            'webstorm': 'WebStorm',
            'androidstudio': 'Android Studio',
            'xcode': 'Xcode',
            'visualstudio': 'Visual Studio',
            'jupyter': 'Jupyter',
            'spyder': 'Spyder',
            'rstudio': 'RStudio'
        }

        self.ide_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'session_count': 0,
            'total_time': 0,
            'plugins': set(),
            'languages': set()
        })

        self.user_env_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)

        logger.info("Development environment monitor initialized")

    def track_ide_usage(self, ide_name: str, user_id: str, session_duration: float,
                       plugins: List[str] = None, language: str = None) -> Dict[str, Any]:
        """Track IDE/editor usage."""
        timestamp = datetime.now(timezone.utc)

        ide_data = {
            'timestamp': timestamp.isoformat(),
            'ide_name': ide_name,
            'user_id': user_id,
            'session_duration': session_duration,
            'plugins': plugins or [],
            'language': language
        }

        # Update statistics
        self.ide_usage[ide_name]['session_count'] += 1
        self.ide_usage[ide_name]['total_time'] += session_duration
        if plugins:
            self.ide_usage[ide_name]['plugins'].update(plugins)
        if language:
            self.ide_usage[ide_name]['languages'].add(language)

        if self.es_manager:
            self.es_manager.push_data(ide_data, 'ide_usage')

        return ide_data

    def detect_running_ides(self, user_id: str) -> List[Dict[str, Any]]:
        """Detect currently running IDEs/editors."""
        running_ides = []

        for proc in psutil.process_iter(['name', 'username']):
            try:
                proc_name = proc.info['name'].lower()
                for ide_key, ide_name in self.ide_tools.items():
                    if ide_key in proc_name:
                        running_ides.append({
                            'ide_name': ide_name,
                            'process_name': proc.info['name'],
                            'pid': proc.pid,
                            'user_id': user_id,
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return running_ides

    def track_environment_setup(self, user_id: str, env_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Track environment setup (virtual envs, containers, etc.)."""
        timestamp = datetime.now(timezone.utc)

        env_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'environment_type': env_type,  # venv, conda, docker, etc.
            'details': details
        }

        self.user_env_profiles[user_id][env_type] = details

        if self.es_manager:
            self.es_manager.push_data(env_data, 'environment_setup')

        return env_data

    def get_user_tooling_profile(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive tooling profile for a user."""
        return {
            'user_id': user_id,
            'environment_setups': self.user_env_profiles.get(user_id, {}),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['DevEnvironmentMonitor']
