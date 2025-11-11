"""
Code Quality and Testing Metrics Monitor

Tracks code quality indicators, testing practices, and code coverage
to measure coding maturity and best practices adoption.
"""

import logging
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CodeQualityMonitor:
    """Monitor code quality metrics and testing practices."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.quality_metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.test_runs: List[Dict[str, Any]] = []
        logger.info("Code quality monitor initialized")

    def analyze_code_file(self, file_path: str, user_id: str) -> Dict[str, Any]:
        """Analyze code quality for a file."""
        timestamp = datetime.now(timezone.utc)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            metrics = {
                'timestamp': timestamp.isoformat(),
                'file_path': file_path,
                'user_id': user_id,
                'total_lines': len(lines),
                'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
                'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
                'blank_lines': len([l for l in lines if not l.strip()]),
                'function_count': len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE)),
                'class_count': len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE)),
                'import_count': len(re.findall(r'^\s*(?:import|from)\s+', content, re.MULTILINE)),
                'max_line_length': max(len(l) for l in lines) if lines else 0,
                'avg_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0
            }

            # Calculate code quality score
            metrics['comment_ratio'] = metrics['comment_lines'] / max(1, metrics['code_lines'])
            metrics['quality_score'] = self._calculate_quality_score(metrics)

            self.quality_metrics[user_id].append(metrics)

            if self.es_manager:
                self.es_manager.push_data(metrics, 'code_quality')

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing code file: {e}")
            return {}

    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall code quality score (0-100)."""
        score = 50.0  # Base score

        # Comment ratio (0-20 points)
        comment_ratio = metrics['comment_ratio']
        if comment_ratio >= 0.2:
            score += 20
        elif comment_ratio >= 0.1:
            score += 15
        elif comment_ratio >= 0.05:
            score += 10

        # Function modularity (0-20 points)
        functions = metrics['function_count']
        if functions >= 5:
            score += 20
        elif functions >= 3:
            score += 15
        elif functions >= 1:
            score += 10

        # Line length (0-10 points)
        if metrics['max_line_length'] <= 88:
            score += 10
        elif metrics['max_line_length'] <= 120:
            score += 5

        return min(100, score)

    def track_test_run(self, test_framework: str, user_id: str,
                      tests_passed: int, tests_failed: int,
                      coverage: float = None, duration: float = None) -> Dict[str, Any]:
        """Track a test execution."""
        timestamp = datetime.now(timezone.utc)

        test_data = {
            'timestamp': timestamp.isoformat(),
            'test_framework': test_framework,
            'user_id': user_id,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'total_tests': tests_passed + tests_failed,
            'pass_rate': tests_passed / max(1, tests_passed + tests_failed) * 100,
            'coverage_percentage': coverage,
            'duration_seconds': duration
        }

        self.test_runs.append(test_data)

        if self.es_manager:
            self.es_manager.push_data(test_data, 'test_execution')

        return test_data

    def get_user_quality_summary(self, user_id: str) -> Dict[str, Any]:
        """Get code quality summary for user."""
        user_metrics = self.quality_metrics.get(user_id, [])

        if not user_metrics:
            return {'user_id': user_id, 'no_data': True}

        avg_quality = sum(m['quality_score'] for m in user_metrics) / len(user_metrics)
        total_functions = sum(m['function_count'] for m in user_metrics)
        avg_comment_ratio = sum(m['comment_ratio'] for m in user_metrics) / len(user_metrics)

        return {
            'user_id': user_id,
            'files_analyzed': len(user_metrics),
            'average_quality_score': round(avg_quality, 2),
            'total_functions_written': total_functions,
            'average_comment_ratio': round(avg_comment_ratio, 3),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['CodeQualityMonitor']
