"""Unit tests for User Activity Monitor Module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from agent.user_activity_monitor import UserActivityMonitor


class TestUserActivityMonitorInitialization:
    """Test UserActivityMonitor initialization."""
    
    def test_initialization_defaults(self):
        monitor = UserActivityMonitor()
        assert monitor.session_timeout_minutes == 30
        assert monitor.active_users == {}
        assert monitor.session_history == []
    
    def test_initialization_custom_timeout(self):
        monitor = UserActivityMonitor(session_timeout_minutes=60)
        assert monitor.session_timeout_minutes == 60


class TestSessionManagement:
    """Test session management functionality."""
    
    def test_start_user_session(self):
        monitor = UserActivityMonitor()
        result = monitor.start_user_session('testuser')
        
        assert result is True
        assert 'testuser' in monitor.active_users
        assert monitor.user_activity_patterns['testuser']['login_count'] == 1
    
    def test_start_session_duplicate_user(self):
        monitor = UserActivityMonitor()
        monitor.start_user_session('testuser')
        result = monitor.start_user_session('testuser')
        
        assert result is False
    
    def test_end_user_session(self):
        monitor = UserActivityMonitor()
        login_time = datetime.now(timezone.utc)
        monitor.start_user_session('testuser', login_time=login_time)
        
        result = monitor.end_user_session('testuser')
        
        assert result is True
        assert 'testuser' not in monitor.active_users
        assert len(monitor.session_history) == 1
    
    def test_end_session_no_active_session(self):
        monitor = UserActivityMonitor()
        result = monitor.end_user_session('nonexistent')
        
        assert result is False
    
    def test_session_duration_calculation(self):
        monitor = UserActivityMonitor()
        login_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        monitor.start_user_session('testuser', login_time=login_time)
        
        monitor.end_user_session('testuser')
        
        session = monitor.session_history[0]
        assert session['duration_minutes'] >= 29.0


class TestActivityTracking:
    """Test activity tracking functionality."""
    
    def test_activity_patterns_initialized(self):
        monitor = UserActivityMonitor()
        patterns = monitor.user_activity_patterns['testuser']
        
        assert patterns['login_count'] == 0
        assert patterns['total_session_time'] == 0.0
    
    def test_average_session_time_calculation(self):
        monitor = UserActivityMonitor()
        
        # First session - 30 minutes
        login1 = datetime.now(timezone.utc) - timedelta(minutes=30)
        monitor.start_user_session('testuser', login_time=login1)
        monitor.end_user_session('testuser')
        
        # Second session - 60 minutes
        login2 = datetime.now(timezone.utc) - timedelta(minutes=60)
        monitor.start_user_session('testuser', login_time=login2)
        monitor.end_user_session('testuser')
        
        avg_time = monitor.user_activity_patterns['testuser']['average_session_time']
        assert avg_time > 0


class TestResourceTracking:
    """Test resource usage tracking."""
    
    def test_resource_usage_initialization(self):
        monitor = UserActivityMonitor()
        resources = monitor.user_resource_usage['testuser']
        
        assert resources['cpu_percent'] == 0.0
        assert resources['memory_mb'] == 0.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_start_session_with_custom_time(self):
        monitor = UserActivityMonitor()
        custom_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        result = monitor.start_user_session('testuser', login_time=custom_time)
        
        assert result is True
        assert monitor.active_users['testuser']['login_time'] == custom_time
    
    def test_multiple_users(self):
        monitor = UserActivityMonitor()
        
        monitor.start_user_session('user1')
        monitor.start_user_session('user2')
        monitor.start_user_session('user3')
        
        assert len(monitor.active_users) == 3
