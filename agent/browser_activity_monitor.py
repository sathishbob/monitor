"""
Browser Activity Classification Monitor - Track Educational vs Non-Educational Browsing

Classifies browser activity to measure self-directed learning, research time,
and distinguish productive vs non-productive browsing.
"""

import logging
import re
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class BrowserActivityMonitor:
    """Monitor and classify browser activity for learning analytics."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager

        # Educational site classifications
        self.educational_sites = {
            'stackoverflow.com': {'category': 'technical_help', 'value': 'high'},
            'github.com': {'category': 'code_repository', 'value': 'high'},
            'docs.python.org': {'category': 'documentation', 'value': 'high'},
            'developer.mozilla.org': {'category': 'documentation', 'value': 'high'},
            'w3schools.com': {'category': 'tutorial', 'value': 'medium'},
            'youtube.com/watch': {'category': 'video_tutorial', 'value': 'medium'},
            'coursera.org': {'category': 'online_course', 'value': 'high'},
            'udemy.com': {'category': 'online_course', 'value': 'high'},
            'khanacademy.org': {'category': 'online_course', 'value': 'high'},
            'leetcode.com': {'category': 'practice', 'value': 'high'},
            'hackerrank.com': {'category': 'practice', 'value': 'high'},
            'geeksforgeeks.org': {'category': 'tutorial', 'value': 'medium'},
            'medium.com': {'category': 'article', 'value': 'medium'},
            'wikipedia.org': {'category': 'reference', 'value': 'medium'},
            'arxiv.org': {'category': 'research_paper', 'value': 'high'},
            'scholar.google.com': {'category': 'research', 'value': 'high'}
        }

        # Non-educational sites
        self.non_educational_sites = {
            'facebook.com': 'social_media',
            'twitter.com': 'social_media',
            'instagram.com': 'social_media',
            'tiktok.com': 'social_media',
            'reddit.com': 'social_media',
            'netflix.com': 'entertainment',
            'twitch.tv': 'entertainment',
            'spotify.com': 'entertainment'
        }

        self.browsing_sessions: deque = deque(maxlen=10000)
        self.user_browsing_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'educational_time': 0,
            'non_educational_time': 0,
            'total_time': 0,
            'sites_visited': defaultdict(int),
            'categories': defaultdict(float)
        })

        logger.info("Browser activity monitor initialized")

    def track_url_visit(self, url: str, user_id: str, duration: float,
                       page_title: str = None) -> Dict[str, Any]:
        """Track a URL visit."""
        timestamp = datetime.now(timezone.utc)

        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')

        # Classify site
        classification = self._classify_url(url, domain, page_title)

        visit_data = {
            'timestamp': timestamp.isoformat(),
            'url': url[:200],  # Limit URL length
            'domain': domain,
            'page_title': page_title,
            'user_id': user_id,
            'duration_seconds': duration,
            'classification': classification['category'],
            'educational_value': classification['value'],
            'is_educational': classification['is_educational']
        }

        self.browsing_sessions.append(visit_data)

        # Update user stats
        stats = self.user_browsing_stats[user_id]
        stats['total_time'] += duration
        stats['sites_visited'][domain] += 1
        stats['categories'][classification['category']] += duration

        if classification['is_educational']:
            stats['educational_time'] += duration
        else:
            stats['non_educational_time'] += duration

        if self.es_manager:
            self.es_manager.push_data(visit_data, 'browser_activity')

        return visit_data

    def _classify_url(self, url: str, domain: str, page_title: str = None) -> Dict[str, Any]:
        """Classify URL as educational or not."""
        url_lower = url.lower()

        # Check educational sites
        for site, info in self.educational_sites.items():
            if site in domain:
                return {
                    'category': info['category'],
                    'value': info['value'],
                    'is_educational': True
                }

        # Check non-educational sites
        for site, category in self.non_educational_sites.items():
            if site in domain:
                return {
                    'category': category,
                    'value': 'none',
                    'is_educational': False
                }

        # Check for educational keywords in URL or title
        educational_keywords = ['tutorial', 'documentation', 'docs', 'learn', 'course',
                               'education', 'lecture', 'guide', 'reference', 'api']

        for keyword in educational_keywords:
            if keyword in url_lower or (page_title and keyword in page_title.lower()):
                return {
                    'category': 'educational_content',
                    'value': 'medium',
                    'is_educational': True
                }

        # Default: unknown
        return {
            'category': 'unknown',
            'value': 'low',
            'is_educational': False
        }

    def get_user_browsing_summary(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get browsing summary for a user."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_sessions = [
            s for s in self.browsing_sessions
            if s.get('user_id') == user_id and
            datetime.fromisoformat(s['timestamp'].replace('Z', '+00:00')) > cutoff
        ]

        stats = self.user_browsing_stats.get(user_id, {})

        educational_time = sum(s['duration_seconds'] for s in recent_sessions if s['is_educational'])
        total_time = sum(s['duration_seconds'] for s in recent_sessions)

        return {
            'user_id': user_id,
            'period_hours': hours,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_browsing_time': total_time,
            'educational_time': educational_time,
            'non_educational_time': total_time - educational_time,
            'educational_percentage': (educational_time / total_time * 100) if total_time > 0 else 0,
            'unique_sites': len(set(s['domain'] for s in recent_sessions)),
            'categories': dict(stats.get('categories', {})),
            'top_sites': sorted(stats.get('sites_visited', {}).items(),
                              key=lambda x: x[1], reverse=True)[:10]
        }


__all__ = ['BrowserActivityMonitor']
