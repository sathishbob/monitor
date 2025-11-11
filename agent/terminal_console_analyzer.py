"""
Terminal/Console Patterns Analyzer

Analyzes shell history, command combinations, terminal sessions,
and command-line proficiency progression.
"""

import logging
import os
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class TerminalConsoleAnalyzer:
    """Analyze terminal and console usage patterns."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.command_sequences: List[List[str]] = []
        self.terminal_sessions: List[Dict[str, Any]] = []
        self.user_terminal_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_commands': 0,
            'command_frequency': Counter(),
            'command_combinations': Counter(),
            'shell_type': None,
            'proficiency_level': 'beginner'
        })

        logger.info("Terminal console analyzer initialized")

    def analyze_bash_history(self, user_id: str, history_file: str = None) -> Dict[str, Any]:
        """Analyze bash history file."""
        if not history_file:
            history_file = os.path.expanduser('~/.bash_history')

        if not os.path.exists(history_file):
            return {'error': 'History file not found'}

        try:
            with open(history_file, 'r', errors='ignore') as f:
                commands = [line.strip() for line in f if line.strip()]

            stats = self.user_terminal_stats[user_id]
            stats['total_commands'] = len(commands)
            stats['shell_type'] = 'bash'

            # Analyze command frequency
            stats['command_frequency'] = Counter([cmd.split()[0] for cmd in commands if cmd.split()])

            # Analyze command combinations (pipes, &&, etc.)
            for cmd in commands:
                if '|' in cmd:
                    stats['command_combinations']['pipe'] += 1
                if '&&' in cmd:
                    stats['command_combinations']['and'] += 1
                if '||' in cmd:
                    stats['command_combinations']['or'] += 1
                if '>' in cmd or '<' in cmd:
                    stats['command_combinations']['redirect'] += 1

            # Calculate proficiency
            stats['proficiency_level'] = self._calculate_proficiency(stats)

            analysis = {
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_commands': len(commands),
                'unique_commands': len(stats['command_frequency']),
                'top_commands': stats['command_frequency'].most_common(10),
                'command_combinations': dict(stats['command_combinations']),
                'proficiency_level': stats['proficiency_level']
            }

            if self.es_manager:
                self.es_manager.push_data(analysis, 'terminal_history_analysis')

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing bash history: {e}")
            return {'error': str(e)}

    def track_terminal_session(self, user_id: str, session_start: datetime,
                              session_end: datetime, commands_executed: int,
                              shell_type: str = 'bash') -> Dict[str, Any]:
        """Track a terminal session."""
        duration = (session_end - session_start).total_seconds()

        session_data = {
            'timestamp': session_start.isoformat(),
            'user_id': user_id,
            'session_start': session_start.isoformat(),
            'session_end': session_end.isoformat(),
            'duration_seconds': duration,
            'commands_executed': commands_executed,
            'shell_type': shell_type,
            'commands_per_minute': commands_executed / (duration / 60) if duration > 0 else 0
        }

        self.terminal_sessions.append(session_data)

        if self.es_manager:
            self.es_manager.push_data(session_data, 'terminal_session')

        return session_data

    def analyze_command_proficiency(self, user_id: str,
                                   commands: List[str]) -> Dict[str, Any]:
        """Analyze command-line proficiency based on command complexity."""
        basic_commands = ['ls', 'cd', 'pwd', 'cat', 'echo', 'mkdir', 'rm']
        intermediate_commands = ['grep', 'find', 'sed', 'awk', 'sort', 'uniq', 'cut']
        advanced_commands = ['xargs', 'tee', 'jq', 'awk', 'perl', 'python -c']

        proficiency = {
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'basic_usage': 0,
            'intermediate_usage': 0,
            'advanced_usage': 0,
            'pipe_usage': 0,
            'script_usage': 0
        }

        for cmd in commands:
            cmd_lower = cmd.lower()

            # Check command level
            if any(basic in cmd_lower for basic in basic_commands):
                proficiency['basic_usage'] += 1
            if any(inter in cmd_lower for inter in intermediate_commands):
                proficiency['intermediate_usage'] += 1
            if any(adv in cmd_lower for adv in advanced_commands):
                proficiency['advanced_usage'] += 1

            # Check for advanced patterns
            if '|' in cmd:
                proficiency['pipe_usage'] += 1
            if cmd.endswith('.sh') or cmd.startswith('bash') or cmd.startswith('./'):
                proficiency['script_usage'] += 1

        if self.es_manager:
            self.es_manager.push_data(proficiency, 'command_proficiency')

        return proficiency

    def _calculate_proficiency(self, stats: Dict[str, Any]) -> str:
        """Calculate terminal proficiency level."""
        combinations = sum(stats['command_combinations'].values())
        unique_commands = len(stats['command_frequency'])
        total_commands = stats['total_commands']

        # Calculate proficiency score
        score = 0
        score += min(30, unique_commands * 2)  # Max 30 points for variety
        score += min(40, combinations * 5)  # Max 40 points for combinations
        score += min(30, total_commands / 10)  # Max 30 points for experience

        if score >= 80:
            return 'expert'
        elif score >= 60:
            return 'advanced'
        elif score >= 40:
            return 'intermediate'
        else:
            return 'beginner'

    def get_user_terminal_summary(self, user_id: str) -> Dict[str, Any]:
        """Get terminal usage summary for user."""
        stats = self.user_terminal_stats.get(user_id, {})

        return {
            'user_id': user_id,
            'total_commands_executed': stats.get('total_commands', 0),
            'unique_commands_known': len(stats.get('command_frequency', {})),
            'proficiency_level': stats.get('proficiency_level', 'beginner'),
            'shell_type': stats.get('shell_type', 'unknown'),
            'top_commands': dict(stats.get('command_frequency', Counter()).most_common(5)),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['TerminalConsoleAnalyzer']
