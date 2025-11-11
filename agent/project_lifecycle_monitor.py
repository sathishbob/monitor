"""
Project Lifecycle Tracking Module

Tracks complete project lifecycle from creation to deployment,
including builds, tests, version control, and deployment attempts.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ProjectLifecycleMonitor:
    """Monitor complete project lifecycle and development workflow."""

    def __init__(self, es_manager=None):
        self.es_manager = es_manager
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.build_events: List[Dict[str, Any]] = []
        self.deployment_events: List[Dict[str, Any]] = []
        self.version_tags: List[Dict[str, Any]] = []
        self.user_projects: Dict[str, List[str]] = defaultdict(list)

        logger.info("Project lifecycle monitor initialized")

    def track_project_creation(self, user_id: str, project_name: str,
                              project_type: str, project_path: str,
                              language: str = None, framework: str = None) -> Dict[str, Any]:
        """Track project creation."""
        timestamp = datetime.now(timezone.utc)
        project_id = f"{user_id}_{project_name}_{int(timestamp.timestamp())}"

        project_data = {
            'project_id': project_id,
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'project_name': project_name,
            'project_type': project_type,
            'project_path': project_path,
            'language': language,
            'framework': framework,
            'created_at': timestamp.isoformat(),
            'status': 'active',
            'build_count': 0,
            'successful_builds': 0,
            'deployment_count': 0,
            'version_tags': []
        }

        self.projects[project_id] = project_data
        self.user_projects[user_id].append(project_id)

        if self.es_manager:
            self.es_manager.push_data(project_data, 'project_creation')

        logger.info(f"Project created: {project_name} by {user_id}")
        return project_data

    def track_build_event(self, project_id: str, user_id: str,
                         build_tool: str, success: bool,
                         duration: float, error_message: str = None) -> Dict[str, Any]:
        """Track build/compile event."""
        timestamp = datetime.now(timezone.utc)

        build_data = {
            'timestamp': timestamp.isoformat(),
            'project_id': project_id,
            'user_id': user_id,
            'build_tool': build_tool,  # make, maven, gradle, npm, etc.
            'success': success,
            'duration_seconds': duration,
            'error_message': error_message
        }

        self.build_events.append(build_data)

        # Update project stats
        if project_id in self.projects:
            self.projects[project_id]['build_count'] += 1
            if success:
                self.projects[project_id]['successful_builds'] += 1

        if self.es_manager:
            self.es_manager.push_data(build_data, 'build_event')

        return build_data

    def track_deployment_attempt(self, project_id: str, user_id: str,
                                deployment_target: str, success: bool,
                                deployment_type: str = None,
                                error_message: str = None) -> Dict[str, Any]:
        """Track deployment attempt."""
        timestamp = datetime.now(timezone.utc)

        deployment_data = {
            'timestamp': timestamp.isoformat(),
            'project_id': project_id,
            'user_id': user_id,
            'deployment_target': deployment_target,  # production, staging, docker, cloud
            'deployment_type': deployment_type,  # manual, ci/cd, automated
            'success': success,
            'error_message': error_message
        }

        self.deployment_events.append(deployment_data)

        # Update project stats
        if project_id in self.projects:
            self.projects[project_id]['deployment_count'] += 1

        if self.es_manager:
            self.es_manager.push_data(deployment_data, 'deployment_attempt')

        return deployment_data

    def track_version_tag(self, project_id: str, user_id: str,
                         version_number: str, tag_name: str = None,
                         release_notes: str = None) -> Dict[str, Any]:
        """Track version tagging/release."""
        timestamp = datetime.now(timezone.utc)

        version_data = {
            'timestamp': timestamp.isoformat(),
            'project_id': project_id,
            'user_id': user_id,
            'version_number': version_number,
            'tag_name': tag_name,
            'release_notes': release_notes
        }

        self.version_tags.append(version_data)

        # Update project version tags
        if project_id in self.projects:
            self.projects[project_id]['version_tags'].append(version_number)

        if self.es_manager:
            self.es_manager.push_data(version_data, 'version_release')

        return version_data

    def track_feature_branch(self, project_id: str, user_id: str,
                            branch_name: str, action: str) -> Dict[str, Any]:
        """Track feature branch workflow."""
        timestamp = datetime.now(timezone.utc)

        branch_data = {
            'timestamp': timestamp.isoformat(),
            'project_id': project_id,
            'user_id': user_id,
            'branch_name': branch_name,
            'action': action  # create, merge, delete
        }

        if self.es_manager:
            self.es_manager.push_data(branch_data, 'feature_branch')

        return branch_data

    def track_milestone_completion(self, project_id: str, user_id: str,
                                  milestone_name: str,
                                  completion_percentage: float) -> Dict[str, Any]:
        """Track project milestone completion."""
        timestamp = datetime.now(timezone.utc)

        milestone_data = {
            'timestamp': timestamp.isoformat(),
            'project_id': project_id,
            'user_id': user_id,
            'milestone_name': milestone_name,
            'completion_percentage': completion_percentage,
            'completed': completion_percentage >= 100.0
        }

        if self.es_manager:
            self.es_manager.push_data(milestone_data, 'project_milestone')

        return milestone_data

    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project summary."""
        if project_id not in self.projects:
            return {'error': 'Project not found'}

        project = self.projects[project_id]

        # Get build success rate
        build_success_rate = 0
        if project['build_count'] > 0:
            build_success_rate = (project['successful_builds'] / project['build_count']) * 100

        # Get project builds
        project_builds = [b for b in self.build_events if b.get('project_id') == project_id]

        # Get deployments
        project_deployments = [d for d in self.deployment_events if d.get('project_id') == project_id]
        successful_deployments = len([d for d in project_deployments if d['success']])

        return {
            'project_id': project_id,
            'project_name': project['project_name'],
            'user_id': project['user_id'],
            'language': project.get('language'),
            'framework': project.get('framework'),
            'created_at': project['created_at'],
            'total_builds': project['build_count'],
            'successful_builds': project['successful_builds'],
            'build_success_rate': round(build_success_rate, 2),
            'total_deployments': project['deployment_count'],
            'successful_deployments': successful_deployments,
            'version_tags': project['version_tags'],
            'status': project['status'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def get_user_project_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of all projects for a user."""
        user_project_ids = self.user_projects.get(user_id, [])

        active_projects = len([pid for pid in user_project_ids
                              if self.projects.get(pid, {}).get('status') == 'active'])

        total_builds = sum(self.projects.get(pid, {}).get('build_count', 0)
                          for pid in user_project_ids)

        total_deployments = sum(self.projects.get(pid, {}).get('deployment_count', 0)
                               for pid in user_project_ids)

        return {
            'user_id': user_id,
            'total_projects': len(user_project_ids),
            'active_projects': active_projects,
            'total_builds': total_builds,
            'total_deployments': total_deployments,
            'projects': [self.get_project_summary(pid) for pid in user_project_ids],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


__all__ = ['ProjectLifecycleMonitor']
