"""
Time Distribution Analysis Module

Analyzes how students distribute their time across activities,
identifies optimal productivity periods, and tracks context switching.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class TimeDistributionAnalyzer:
    """Analyze time distribution and productivity patterns."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.time_blocks: List[Dict[str, Any]] = []
        self.context_switches: List[Dict[str, Any]] = []
        self.user_time_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'active_coding_time': 0,
            'passive_reading_time': 0,
            'problem_solving_time': 0,
            'break_time': 0,
            'context_switches': 0,
            'productivity_by_hour': defaultdict(float)
        })

        logger.info("Time distribution analyzer initialized")

    def track_time_block(self, user_id: str, activity_type: str,
                        start_time: datetime, end_time: datetime,
                        productivity_score: float = None) -> Dict[str, Any]:
        """Track a block of time spent on an activity."""
        duration = (end_time - start_time).total_seconds()

        time_block = {
            'timestamp': start_time.isoformat(),
            'user_id': user_id,
            'activity_type': activity_type,  # coding, reading, debugging, break
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'hour_of_day': start_time.hour,
            'day_of_week': start_time.weekday(),
            'productivity_score': productivity_score
        }

        self.time_blocks.append(time_block)

        # Update user statistics
        stats = self.user_time_stats[user_id]
        if activity_type == 'coding':
            stats['active_coding_time'] += duration
        elif activity_type == 'reading':
            stats['passive_reading_time'] += duration
        elif activity_type == 'debugging':
            stats['problem_solving_time'] += duration
        elif activity_type == 'break':
            stats['break_time'] += duration

        stats['productivity_by_hour'][start_time.hour] += duration

        if self.es_manager:
            self.es_manager.push_data(time_block, 'time_block')

        return time_block

    def track_context_switch(self, user_id: str, from_activity: str,
                            to_activity: str, reason: str = None) -> Dict[str, Any]:
        """Track context switching between activities."""
        timestamp = datetime.now(timezone.utc)

        switch_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'from_activity': from_activity,
            'to_activity': to_activity,
            'reason': reason
        }

        self.context_switches.append(switch_data)
        self.user_time_stats[user_id]['context_switches'] += 1

        if self.es_manager:
            self.es_manager.push_data(switch_data, 'context_switch')

        return switch_data

    def analyze_productivity_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze productivity patterns for a user."""
        stats = self.user_time_stats.get(user_id, {})

        # Find peak productivity hours
        productivity_by_hour = stats.get('productivity_by_hour', {})
        if productivity_by_hour:
            peak_hour = max(productivity_by_hour.items(), key=lambda x: x[1])[0]
        else:
            peak_hour = None

        total_active_time = (stats.get('active_coding_time', 0) +
                            stats.get('passive_reading_time', 0) +
                            stats.get('problem_solving_time', 0))

        return {
            'user_id': user_id,
            'active_coding_percentage': (stats.get('active_coding_time', 0) / total_active_time * 100) if total_active_time > 0 else 0,
            'passive_reading_percentage': (stats.get('passive_reading_time', 0) / total_active_time * 100) if total_active_time > 0 else 0,
            'problem_solving_percentage': (stats.get('problem_solving_time', 0) / total_active_time * 100) if total_active_time > 0 else 0,
            'break_time_hours': stats.get('break_time', 0) / 3600,
            'context_switches_count': stats.get('context_switches', 0),
            'peak_productivity_hour': peak_hour,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def get_optimal_study_times(self, user_id: str) -> List[int]:
        """Get optimal study hours for a user based on historical productivity."""
        stats = self.user_time_stats.get(user_id, {})
        productivity_by_hour = stats.get('productivity_by_hour', {})

        if not productivity_by_hour:
            return []

        # Sort hours by productivity
        sorted_hours = sorted(productivity_by_hour.items(), key=lambda x: x[1], reverse=True)

        # Return top 3 most productive hours
        return [hour for hour, _ in sorted_hours[:3]]


__all__ = ['TimeDistributionAnalyzer']
