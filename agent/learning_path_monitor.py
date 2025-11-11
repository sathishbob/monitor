"""
Learning Path Progress Monitor

Tracks student progress through curriculum, exercises, assignments,
and learning objectives to personalize learning paths.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class LearningPathMonitor:
    """Monitor learning path progress and curriculum completion."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.user_progress: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'completed_exercises': [],
            'completed_assignments': [],
            'milestones_achieved': [],
            'quiz_attempts': [],
            'certificates': [],
            'current_module': None,
            'progress_percentage': 0.0
        })
        self.exercises: Dict[str, Dict[str, Any]] = {}
        self.assignments: Dict[str, Dict[str, Any]] = {}

        logger.info("Learning path monitor initialized")

    def track_exercise_completion(self, user_id: str, exercise_id: str,
                                  score: float, time_taken: float,
                                  attempts: int = 1) -> Dict[str, Any]:
        """Track exercise completion."""
        timestamp = datetime.now(timezone.utc)

        exercise_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'exercise_id': exercise_id,
            'score': score,
            'time_taken_seconds': time_taken,
            'attempts': attempts,
            'completed': score >= 70.0
        }

        self.user_progress[user_id]['completed_exercises'].append(exercise_data)

        if self.es_manager:
            self.es_manager.push_data(exercise_data, 'exercise_completion')

        return exercise_data

    def track_assignment_submission(self, user_id: str, assignment_id: str,
                                   submission_time: float, grade: float = None,
                                   feedback: str = None) -> Dict[str, Any]:
        """Track assignment submission."""
        timestamp = datetime.now(timezone.utc)

        assignment_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'assignment_id': assignment_id,
            'submission_time_seconds': submission_time,
            'grade': grade,
            'feedback': feedback,
            'status': 'submitted'
        }

        self.user_progress[user_id]['completed_assignments'].append(assignment_data)

        if self.es_manager:
            self.es_manager.push_data(assignment_data, 'assignment_submission')

        return assignment_data

    def track_milestone(self, user_id: str, milestone_id: str,
                       milestone_name: str, points: int = 0) -> Dict[str, Any]:
        """Track milestone achievement."""
        timestamp = datetime.now(timezone.utc)

        milestone_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'milestone_id': milestone_id,
            'milestone_name': milestone_name,
            'points_earned': points
        }

        self.user_progress[user_id]['milestones_achieved'].append(milestone_data)

        if self.es_manager:
            self.es_manager.push_data(milestone_data, 'milestone_achievement')

        return milestone_data

    def track_quiz_attempt(self, user_id: str, quiz_id: str,
                          questions_total: int, questions_correct: int,
                          time_taken: float) -> Dict[str, Any]:
        """Track quiz/assessment attempt."""
        timestamp = datetime.now(timezone.utc)

        quiz_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'quiz_id': quiz_id,
            'total_questions': questions_total,
            'correct_answers': questions_correct,
            'score_percentage': (questions_correct / questions_total * 100) if questions_total > 0 else 0,
            'time_taken_seconds': time_taken,
            'passed': (questions_correct / questions_total) >= 0.7 if questions_total > 0 else False
        }

        self.user_progress[user_id]['quiz_attempts'].append(quiz_data)

        if self.es_manager:
            self.es_manager.push_data(quiz_data, 'quiz_attempt')

        return quiz_data

    def track_certificate(self, user_id: str, certificate_id: str,
                         certificate_name: str, completion_date: datetime = None) -> Dict[str, Any]:
        """Track certificate/badge earned."""
        timestamp = completion_date or datetime.now(timezone.utc)

        cert_data = {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'certificate_id': certificate_id,
            'certificate_name': certificate_name
        }

        self.user_progress[user_id]['certificates'].append(cert_data)

        if self.es_manager:
            self.es_manager.push_data(cert_data, 'certificate_earned')

        return cert_data

    def update_current_module(self, user_id: str, module_name: str,
                             progress_percentage: float) -> Dict[str, Any]:
        """Update user's current module progress."""
        self.user_progress[user_id]['current_module'] = module_name
        self.user_progress[user_id]['progress_percentage'] = progress_percentage

        module_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'module_name': module_name,
            'progress_percentage': progress_percentage
        }

        if self.es_manager:
            self.es_manager.push_data(module_data, 'module_progress')

        return module_data

    def get_user_learning_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning progress summary."""
        progress = self.user_progress.get(user_id, {})

        exercises = progress.get('completed_exercises', [])
        assignments = progress.get('completed_assignments', [])
        quizzes = progress.get('quiz_attempts', [])

        avg_exercise_score = sum(e['score'] for e in exercises) / len(exercises) if exercises else 0
        avg_quiz_score = sum(q['score_percentage'] for q in quizzes) / len(quizzes) if quizzes else 0

        return {
            'user_id': user_id,
            'exercises_completed': len(exercises),
            'assignments_completed': len(assignments),
            'quizzes_taken': len(quizzes),
            'milestones_achieved': len(progress.get('milestones_achieved', [])),
            'certificates_earned': len(progress.get('certificates', [])),
            'average_exercise_score': round(avg_exercise_score, 2),
            'average_quiz_score': round(avg_quiz_score, 2),
            'current_module': progress.get('current_module'),
            'overall_progress': progress.get('progress_percentage', 0),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['LearningPathMonitor']
