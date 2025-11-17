"""Unit tests for Engagement Scoring Module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from agent.engagement_scoring import EngagementScoring


class TestEngagementScoringInitialization:
    """Test EngagementScoring initialization."""
    
    def test_initialization_defaults(self):
        scorer = EngagementScoring()
        
        assert scorer.session_timeout_minutes == 30
        assert scorer.active_sessions == {}
        assert scorer.dropout_prediction_enabled is True
    
    def test_initialization_custom_params(self):
        scorer = EngagementScoring(
            session_timeout_minutes=60,
            inactivity_threshold_minutes=20,
            server_id='test_server'
        )
        
        assert scorer.session_timeout_minutes == 60
        assert scorer.inactivity_threshold_minutes == 20
        assert scorer.server_identifier == 'test_server'


class TestSessionManagement:
    """Test session management."""
    
    def test_start_session(self):
        scorer = EngagementScoring()
        session_id = scorer.start_session('user1')
        
        assert session_id is not None
        assert 'user1' in scorer.active_sessions
        assert session_id.startswith('user1_')
    
    def test_start_session_with_timestamp(self):
        scorer = EngagementScoring()
        custom_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        session_id = scorer.start_session('user1', timestamp=custom_time)
        
        assert scorer.active_sessions['user1']['start_time'] == custom_time


class TestCommandTracking:
    """Test command tracking."""
    
    def test_command_history_storage(self):
        scorer = EngagementScoring()
        
        scorer.command_history['user1'].append({'command': 'ls', 'timestamp': datetime.now(timezone.utc)})
        
        assert len(scorer.command_history['user1']) == 1


class TestLearningCategories:
    """Test learning category definitions."""
    
    def test_learning_categories_defined(self):
        scorer = EngagementScoring()
        
        assert 'development' in scorer.learning_categories
        assert 'system_admin' in scorer.learning_categories
        assert 'git' in scorer.learning_categories['development']


class TestProductivityIndicators:
    """Test productivity indicators."""
    
    def test_productivity_indicators_defined(self):
        scorer = EngagementScoring()
        
        assert 'high' in scorer.productivity_indicators
        assert 'medium' in scorer.productivity_indicators
        assert 'low' in scorer.productivity_indicators


class TestElasticsearchIntegration:
    """Test Elasticsearch integration."""
    
    def test_set_es_manager(self):
        scorer = EngagementScoring()
        mock_es = Mock()
        
        scorer.set_es_manager(mock_es)
        
        assert scorer.es_manager == mock_es
    
    def test_push_to_elasticsearch_no_manager(self):
        scorer = EngagementScoring()
        
        result = scorer.push_to_elasticsearch({'test': 'data'}, 'test_type')
        
        assert result is False
    
    def test_push_to_elasticsearch_with_manager(self):
        scorer = EngagementScoring()
        mock_es = Mock()
        mock_es.push_data = Mock(return_value=True)
        scorer.set_es_manager(mock_es)
        
        result = scorer.push_to_elasticsearch({'test': 'data'}, 'test_type')
        
        mock_es.push_data.assert_called_once()


class TestCrossServerComparison:
    """Test cross-server comparison features."""
    
    def test_cross_server_enabled(self):
        scorer = EngagementScoring()
        
        assert scorer.cross_server_enabled is True
    
    def test_server_identifier_set(self):
        scorer = EngagementScoring(server_id='server_123')
        
        assert scorer.server_identifier == 'server_123'


class TestRiskAssessment:
    """Test risk assessment features."""
    
    def test_risk_profiles_initialized(self):
        scorer = EngagementScoring()
        
        assert isinstance(scorer.student_risk_profiles, dict)
        assert isinstance(scorer.disengagement_alerts, dict)
        assert isinstance(scorer.intervention_recommendations, dict)


class TestEdgeCases:
    """Test edge cases."""
    
    def test_multiple_sessions(self):
        scorer = EngagementScoring()
        
        scorer.start_session('user1')
        scorer.start_session('user2')
        scorer.start_session('user3')
        
        assert len(scorer.active_sessions) == 3
