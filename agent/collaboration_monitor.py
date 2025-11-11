"""
Collaboration Indicators Monitor

Tracks collaboration activities including pair programming, code reviews,
screen sharing, and team communication to encourage teamwork.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class CollaborationMonitor:
    """Monitor collaboration and teamwork activities."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.collaboration_sessions: List[Dict[str, Any]] = []
        self.code_reviews: List[Dict[str, Any]] = []
        self.pair_programming_sessions: List[Dict[str, Any]] = []
        self.user_collaboration_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_sessions': 0,
            'code_reviews_given': 0,
            'code_reviews_received': 0,
            'pair_programming_time': 0,
            'help_requests': 0,
            'help_provided': 0
        })

        logger.info("Collaboration monitor initialized")

    def track_collaboration_session(self, users: List[str], session_type: str,
                                    duration: float, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track a collaboration session."""
        timestamp = datetime.now(timezone.utc)

        session_data = {
            'timestamp': timestamp.isoformat(),
            'users': users,
            'session_type': session_type,  # pair_programming, screen_share, meeting
            'duration_seconds': duration,
            'details': details or {}
        }

        self.collaboration_sessions.append(session_data)

        for user in users:
            self.user_collaboration_stats[user]['total_sessions'] += 1

        if self.es_manager:
            self.es_manager.push_data(session_data, 'collaboration_session')

        return session_data

    def track_code_review(self, reviewer: str, reviewee: str,
                         file_path: str, comments: int,
                         approval: bool = False) -> Dict[str, Any]:
        """Track a code review activity."""
        timestamp = datetime.now(timezone.utc)

        review_data = {
            'timestamp': timestamp.isoformat(),
            'reviewer': reviewer,
            'reviewee': reviewee,
            'file_path': file_path,
            'comments_count': comments,
            'approved': approval
        }

        self.code_reviews.append(review_data)

        self.user_collaboration_stats[reviewer]['code_reviews_given'] += 1
        self.user_collaboration_stats[reviewee]['code_reviews_received'] += 1

        if self.es_manager:
            self.es_manager.push_data(review_data, 'code_review')

        return review_data

    def track_help_request(self, requester: str, helper: str = None,
                          topic: str = None, resolved: bool = False) -> Dict[str, Any]:
        """Track help requests between students."""
        timestamp = datetime.now(timezone.utc)

        help_data = {
            'timestamp': timestamp.isoformat(),
            'requester': requester,
            'helper': helper,
            'topic': topic,
            'resolved': resolved
        }

        self.user_collaboration_stats[requester]['help_requests'] += 1
        if helper:
            self.user_collaboration_stats[helper]['help_provided'] += 1

        if self.es_manager:
            self.es_manager.push_data(help_data, 'help_request')

        return help_data

    def detect_pair_programming(self, user_ids: List[str], machine_id: str,
                               duration: float) -> Dict[str, Any]:
        """Detect and track pair programming."""
        timestamp = datetime.now(timezone.utc)

        pair_data = {
            'timestamp': timestamp.isoformat(),
            'users': user_ids,
            'machine_id': machine_id,
            'duration_seconds': duration,
            'detection_method': 'multi_user_activity'
        }

        self.pair_programming_sessions.append(pair_data)

        for user in user_ids:
            self.user_collaboration_stats[user]['pair_programming_time'] += duration

        if self.es_manager:
            self.es_manager.push_data(pair_data, 'pair_programming')

        return pair_data

    def get_user_collaboration_summary(self, user_id: str) -> Dict[str, Any]:
        """Get collaboration summary for user."""
        stats = self.user_collaboration_stats.get(user_id, {})

        return {
            'user_id': user_id,
            'total_collaboration_sessions': stats.get('total_sessions', 0),
            'code_reviews_given': stats.get('code_reviews_given', 0),
            'code_reviews_received': stats.get('code_reviews_received', 0),
            'pair_programming_hours': stats.get('pair_programming_time', 0) / 3600,
            'help_requests_made': stats.get('help_requests', 0),
            'help_provided_count': stats.get('help_provided', 0),
            'collaboration_score': self._calculate_collab_score(stats),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _calculate_collab_score(self, stats: Dict[str, Any]) -> float:
        """Calculate collaboration score (0-100)."""
        score = 0
        score += min(30, stats.get('total_sessions', 0) * 5)
        score += min(25, stats.get('code_reviews_given', 0) * 5)
        score += min(25, stats.get('help_provided', 0) * 5)
        score += min(20, stats.get('pair_programming_time', 0) / 3600 * 5)
        return min(100, score)


__all__ = ['CollaborationMonitor']
