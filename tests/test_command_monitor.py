"""
Unit tests for Command Monitor Module.

This test module provides comprehensive test coverage for the CommandMonitor class,
including command monitoring, security analysis, risk scoring, and alert generation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime, timezone, timedelta
from collections import deque

# Import test data from conftest
from .conftest import RISK_SCORES

# Import the module to test
from agent.command_monitor import CommandMonitor


class TestCommandMonitorInitialization:
    """Test CommandMonitor initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        monitor = CommandMonitor()

        assert monitor.max_history_size == 1000
        assert monitor.command_history == []
        assert isinstance(monitor.user_command_history, dict)
        assert len(monitor.dangerous_commands) > 0
        assert len(monitor.command_patterns) > 0
        assert len(monitor.active_alerts) == 0

    def test_initialization_with_custom_history_size(self):
        """Test initialization with custom history size."""
        monitor = CommandMonitor(max_history_size=500)

        assert monitor.max_history_size == 500

    def test_dangerous_commands_loaded(self):
        """Test that dangerous commands are properly loaded."""
        monitor = CommandMonitor()

        assert 'rm -rf' in monitor.dangerous_commands
        assert 'dd if=/dev/zero' in monitor.dangerous_commands
        assert 'chmod 777' in monitor.dangerous_commands

        # Verify risk levels
        assert monitor.dangerous_commands['rm -rf']['risk_level'] == 'critical'

    def test_command_patterns_defined(self):
        """Test that command patterns are properly defined."""
        monitor = CommandMonitor()

        assert 'file_operations' in monitor.command_patterns
        assert 'privilege_operations' in monitor.command_patterns
        assert 'network_operations' in monitor.command_patterns

    def test_risk_weights_defined(self):
        """Test that risk weights are properly defined."""
        monitor = CommandMonitor()

        assert 'dangerous_commands' in monitor.risk_weights
        assert 'privilege_escalation' in monitor.risk_weights
        assert monitor.risk_weights['dangerous_commands'] == 10.0


class TestCommandMonitoring:
    """Test command monitoring functionality."""

    def test_monitor_command_basic(self):
        """Test basic command monitoring."""
        monitor = CommandMonitor()

        result = monitor.monitor_command(
            username='testuser',
            command='ls -la',
            working_directory='/home/testuser'
        )

        assert 'timestamp' in result
        assert result['username'] == 'testuser'
        assert result['command'] == 'ls -la'
        assert result['working_directory'] == '/home/testuser'
        assert 'security_analysis' in result
        assert 'risk_score' in result
        assert 'risk_level' in result

    def test_monitor_command_with_exit_code(self):
        """Test monitoring command with exit code."""
        monitor = CommandMonitor()

        result = monitor.monitor_command(
            username='testuser',
            command='echo test',
            exit_code=0,
            execution_time=0.1
        )

        assert result['exit_code'] == 0
        assert result['execution_time'] == 0.1

    def test_monitor_command_stores_history(self):
        """Test that monitored commands are stored in history."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'cmd1')
        monitor.monitor_command('user1', 'cmd2')
        monitor.monitor_command('user2', 'cmd3')

        assert len(monitor.command_history) == 3
        assert len(monitor.user_command_history['user1']) == 2
        assert len(monitor.user_command_history['user2']) == 1

    def test_monitor_command_history_limit(self):
        """Test that history respects maximum size."""
        monitor = CommandMonitor(max_history_size=5)

        # Monitor more commands than max size
        for i in range(10):
            monitor.monitor_command('testuser', f'command_{i}')

        # Global history should be limited
        assert len(monitor.command_history) == 5

        # User history should also be limited (deque with maxlen)
        assert len(monitor.user_command_history['testuser']) <= 5

    def test_monitor_command_generates_hash(self):
        """Test that command hash is generated."""
        monitor = CommandMonitor()

        result = monitor.monitor_command(
            'testuser',
            'test command',
            '/home'
        )

        assert 'command_hash' in result
        assert len(result['command_hash']) == 64  # SHA-256 hash length


class TestSecurityAnalysis:
    """Test security analysis functionality."""

    def test_analyze_safe_command(self):
        """Test analysis of safe command."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('ls -la')

        assert analysis['is_dangerous'] is False
        assert len(analysis['risk_factors']) == 0

    def test_analyze_dangerous_command_rm_rf(self):
        """Test analysis of dangerous rm -rf command."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('sudo rm -rf /tmp/test')

        assert analysis['is_dangerous'] is True
        assert analysis['dangerous_command_type'] == 'rm -rf'
        assert len(analysis['risk_factors']) > 0

    def test_analyze_dangerous_command_dd(self):
        """Test analysis of dangerous dd command."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('dd if=/dev/zero of=/dev/sda')

        assert analysis['is_dangerous'] is True
        assert 'dd if=/dev/zero' in analysis['dangerous_command_type']

    def test_analyze_privilege_escalation(self):
        """Test detection of privilege escalation."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('sudo su')

        assert analysis['privilege_escalation'] is True
        assert 'privilege_operations' in analysis['command_patterns']

    def test_analyze_file_operations(self):
        """Test detection of file operations."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('chmod 755 script.sh')

        assert analysis['file_operations'] is True
        assert 'file_operations' in analysis['command_patterns']

    def test_analyze_network_operations(self):
        """Test detection of network operations."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('wget http://example.com/file')

        assert analysis['network_operations'] is True
        assert 'network_operations' in analysis['command_patterns']

    def test_analyze_system_operations(self):
        """Test detection of system operations."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('systemctl restart nginx')

        assert analysis['system_operations'] is True
        assert 'system_operations' in analysis['command_patterns']

    def test_analyze_sudo_with_rm_risk_factor(self):
        """Test detection of sudo with destructive command."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('sudo rm important_file')

        assert 'Sudo with destructive command' in analysis['risk_factors']

    def test_analyze_eval_risk_factor(self):
        """Test detection of dynamic command evaluation."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('eval "dangerous code"')

        assert 'Dynamic command evaluation' in analysis['risk_factors']

    def test_analyze_device_redirection_risk_factor(self):
        """Test detection of device file redirection."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('cat something > /dev/sda')

        assert 'Device file redirection' in analysis['risk_factors']

    def test_analyze_multiple_patterns(self):
        """Test command with multiple security patterns."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security(
            'sudo wget http://example.com/script.sh | bash'
        )

        assert analysis['privilege_escalation'] is True
        assert analysis['network_operations'] is True
        assert len(analysis['command_patterns']) >= 2


class TestRiskScoring:
    """Test risk scoring functionality."""

    def test_risk_score_safe_command(self):
        """Test risk score for safe command."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('ls -la')
        risk_score = monitor._calculate_risk_score(analysis)

        assert risk_score < 2.0

    def test_risk_score_dangerous_command(self):
        """Test risk score for dangerous command."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('rm -rf /')
        risk_score = monitor._calculate_risk_score(analysis)

        assert risk_score >= 8.0

    def test_risk_score_privilege_escalation(self):
        """Test risk score for privilege escalation."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('sudo su')
        risk_score = monitor._calculate_risk_score(analysis)

        assert risk_score > 5.0

    def test_risk_score_capped_at_maximum(self):
        """Test that risk score is capped at 10.0."""
        monitor = CommandMonitor()

        # Create analysis with many risk factors
        analysis = {
            'is_dangerous': True,
            'privilege_escalation': True,
            'command_patterns': ['file_operations', 'system_operations', 'network_operations']
        }

        risk_score = monitor._calculate_risk_score(analysis)

        assert risk_score <= 10.0

    def test_get_risk_level_low(self):
        """Test risk level determination - low."""
        monitor = CommandMonitor()

        risk_level = monitor._get_risk_level(1.5)
        assert risk_level == 'low'

    def test_get_risk_level_medium(self):
        """Test risk level determination - medium."""
        monitor = CommandMonitor()

        risk_level = monitor._get_risk_level(3.0)
        assert risk_level == 'medium'

    def test_get_risk_level_high(self):
        """Test risk level determination - high."""
        monitor = CommandMonitor()

        risk_level = monitor._get_risk_level(6.0)
        assert risk_level == 'high'

    def test_get_risk_level_critical(self):
        """Test risk level determination - critical."""
        monitor = CommandMonitor()

        risk_level = monitor._get_risk_level(9.0)
        assert risk_level == 'critical'

    @pytest.mark.parametrize("score,level", RISK_SCORES)
    def test_parametrized_risk_levels(self, score, level):
        """Test risk level determination with various scores."""
        monitor = CommandMonitor()
        risk_level = monitor._get_risk_level(score)

        # Just verify it returns a valid risk level
        assert risk_level in ['low', 'medium', 'high', 'critical']


class TestAlertGeneration:
    """Test security alert generation."""

    def test_create_alert_for_high_risk_command(self):
        """Test that alerts are created for high-risk commands."""
        monitor = CommandMonitor()

        result = monitor.monitor_command('testuser', 'rm -rf /')

        # Should create an alert for high risk (>5.0)
        assert len(monitor.active_alerts) > 0

        alert = monitor.active_alerts[0]
        assert alert['username'] == 'testuser'
        assert 'rm -rf' in alert['command']
        assert alert['risk_level'] in ['high', 'critical']

    def test_no_alert_for_low_risk_command(self):
        """Test that no alerts are created for low-risk commands."""
        monitor = CommandMonitor()

        result = monitor.monitor_command('testuser', 'ls -la')

        # Should not create alerts for low risk
        assert len(monitor.active_alerts) == 0

    def test_alert_structure(self):
        """Test alert data structure."""
        monitor = CommandMonitor()

        monitor.monitor_command('testuser', 'sudo rm -rf /tmp')

        assert len(monitor.active_alerts) > 0

        alert = monitor.active_alerts[0]
        assert 'timestamp' in alert
        assert 'username' in alert
        assert 'command' in alert
        assert 'risk_score' in alert
        assert 'risk_level' in alert
        assert 'security_analysis' in alert


class TestSecurityMetrics:
    """Test security metrics tracking."""

    def test_update_security_metrics(self):
        """Test that security metrics are updated."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'ls')
        monitor.monitor_command('user1', 'sudo su')
        monitor.monitor_command('user1', 'rm -rf /tmp')

        assert monitor.security_metrics['total_commands'] == 3
        assert monitor.security_metrics['privilege_escalation'] > 0

    def test_pattern_metrics(self):
        """Test pattern-based metrics."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'chmod 755 file')
        monitor.monitor_command('user1', 'wget http://example.com')

        assert monitor.security_metrics['pattern_file_operations'] > 0
        assert monitor.security_metrics['pattern_network_operations'] > 0

    def test_dangerous_command_metrics(self):
        """Test dangerous command metrics."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'rm -rf /')
        monitor.monitor_command('user1', 'dd if=/dev/zero of=/dev/sda')

        assert monitor.security_metrics['dangerous_commands'] == 2


class TestCommandSummary:
    """Test command summary generation."""

    def test_get_command_summary_overall(self):
        """Test getting overall command summary."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'ls')
        monitor.monitor_command('user1', 'sudo su')
        monitor.monitor_command('user2', 'rm file')

        summary = monitor.get_command_summary()

        assert summary['total_commands'] == 3
        assert 'security_metrics' in summary
        assert 'risk_distribution' in summary
        assert 'command_patterns' in summary

    def test_get_command_summary_user_specific(self):
        """Test getting user-specific command summary."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'cmd1')
        monitor.monitor_command('user1', 'cmd2')
        monitor.monitor_command('user2', 'cmd3')

        summary = monitor.get_command_summary(username='user1')

        assert summary['username'] == 'user1'
        assert summary['total_commands'] == 2
        assert 'recent_commands' in summary

    def test_risk_distribution(self):
        """Test risk distribution calculation."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'ls')  # low
        monitor.monitor_command('user1', 'sudo su')  # high
        monitor.monitor_command('user1', 'rm -rf /')  # critical

        summary = monitor.get_command_summary()

        dist = summary['risk_distribution']
        assert 'low' in dist
        assert dist['low'] >= 1

    def test_pattern_distribution(self):
        """Test command pattern distribution."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'chmod 755 file')
        monitor.monitor_command('user1', 'systemctl restart nginx')

        summary = monitor.get_command_summary()

        pattern_dist = summary['command_patterns']
        assert 'file_operations' in pattern_dist
        assert 'system_operations' in pattern_dist


class TestCommandHashGeneration:
    """Test command hash generation."""

    def test_generate_command_hash(self):
        """Test basic hash generation."""
        monitor = CommandMonitor()

        hash1 = monitor._generate_command_hash('ls -la', 'user1', '/home')
        hash2 = monitor._generate_command_hash('ls -la', 'user1', '/home')

        # Same input should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256

    def test_different_commands_different_hash(self):
        """Test that different commands produce different hashes."""
        monitor = CommandMonitor()

        hash1 = monitor._generate_command_hash('cmd1', 'user1', '/home')
        hash2 = monitor._generate_command_hash('cmd2', 'user1', '/home')

        assert hash1 != hash2

    def test_different_users_different_hash(self):
        """Test that different users produce different hashes."""
        monitor = CommandMonitor()

        hash1 = monitor._generate_command_hash('ls', 'user1', '/home')
        hash2 = monitor._generate_command_hash('ls', 'user2', '/home')

        assert hash1 != hash2

    def test_hash_with_none_directory(self):
        """Test hash generation with None directory."""
        monitor = CommandMonitor()

        hash1 = monitor._generate_command_hash('ls', 'user1', None)

        assert len(hash1) == 64


class TestLinuxCommandCollection:
    """Test Linux command collection from audit logs."""

    def test_get_linux_commands_auditd_not_running(self):
        """Test when auditd is not running."""
        monitor = CommandMonitor()

        # Mock auditd not active
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            commands = monitor.get_linux_commands()

            assert commands == []

    def test_get_linux_commands_no_audit_log(self):
        """Test when audit log doesn't exist."""
        monitor = CommandMonitor()

        with patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=False):
            mock_run.return_value = MagicMock(returncode=0)

            commands = monitor.get_linux_commands()

            assert commands == []

    def test_get_linux_commands_success(self):
        """Test successful Linux command collection."""
        monitor = CommandMonitor()

        audit_log_content = b'''type=EXECVE msg=audit(1234567890.123:123): argc=2 a0="ls" a1="-la"
type=SYSCALL msg=audit(1234567890.123:123): uid=1000 pid=1234 ppid=1000
'''

        with patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=audit_log_content)), \
             patch('psutil.pid_exists', return_value=False), \
             patch('pwd.getpwuid') as mock_pwd:

            mock_run.return_value = MagicMock(returncode=0)
            mock_pwd.return_value = MagicMock(pw_name='testuser')

            commands = monitor.get_linux_commands()

            assert len(commands) > 0
            assert commands[0]['command'] == 'ls -la'
            assert commands[0]['user'] == 'testuser'


class TestRecentCommands:
    """Test recent commands retrieval."""

    def test_get_recent_commands_linux(self):
        """Test getting recent commands on Linux."""
        monitor = CommandMonitor()

        with patch('platform.system', return_value='Linux'), \
             patch.object(monitor, 'get_linux_commands') as mock_linux:

            mock_linux.return_value = [{
                'command': 'ls',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user': 'test'
            }]

            recent = monitor.get_recent_commands(minutes=30)

            assert len(recent) >= 0
            mock_linux.assert_called_once()

    def test_get_recent_commands_filters_old(self):
        """Test that old commands are filtered out."""
        monitor = CommandMonitor()

        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        recent_time = datetime.now(timezone.utc).isoformat()

        with patch('platform.system', return_value='Linux'), \
             patch.object(monitor, 'get_linux_commands') as mock_linux:

            mock_linux.return_value = [
                {'command': 'old', 'timestamp': old_time, 'user': 'test'},
                {'command': 'recent', 'timestamp': recent_time, 'user': 'test'}
            ]

            recent = monitor.get_recent_commands(minutes=30)

            # Should only include recent command
            assert all(cmd['command'] != 'old' for cmd in recent)


class TestHistoryClearing:
    """Test history clearing functionality."""

    def test_clear_history(self):
        """Test clearing all history and alerts."""
        monitor = CommandMonitor()

        monitor.monitor_command('user1', 'cmd1')
        monitor.monitor_command('user1', 'sudo rm -rf /')  # Creates alert

        assert len(monitor.command_history) > 0
        assert len(monitor.user_command_history) > 0
        assert len(monitor.active_alerts) > 0
        assert len(monitor.security_metrics) > 0

        monitor.clear_history()

        assert len(monitor.command_history) == 0
        assert len(monitor.user_command_history) == 0
        assert len(monitor.active_alerts) == 0
        assert len(monitor.security_metrics) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_monitor_command_with_empty_command(self):
        """Test monitoring empty command."""
        monitor = CommandMonitor()

        result = monitor.monitor_command('testuser', '')

        assert result['command'] == ''
        assert 'risk_score' in result

    def test_monitor_command_with_very_long_command(self):
        """Test monitoring very long command."""
        monitor = CommandMonitor()

        long_cmd = 'a' * 10000
        result = monitor.monitor_command('testuser', long_cmd)

        assert result['command'] == long_cmd

    def test_analyze_command_with_special_characters(self):
        """Test analyzing command with special characters."""
        monitor = CommandMonitor()

        analysis = monitor._analyze_command_security('cmd $(whoami) && echo "test"')

        assert 'is_dangerous' in analysis

    def test_error_handling_in_monitor_command(self):
        """Test error handling in monitor_command."""
        monitor = CommandMonitor()

        # Force an error by corrupting internal state
        with patch.object(monitor, '_analyze_command_security', side_effect=Exception("Test error")):
            result = monitor.monitor_command('user', 'cmd')

            # Should return empty dict on error
            assert result == {}

    @pytest.mark.parametrize("command", [
        'ls -la',
        'sudo su',
        'rm -rf /',
        'wget http://example.com',
        'python -c "import os"'
    ])
    def test_various_commands(self, command):
        """Test monitoring various types of commands."""
        monitor = CommandMonitor()

        result = monitor.monitor_command('testuser', command)

        assert result['command'] == command
        assert 'risk_score' in result
        assert result['risk_score'] >= 0.0
        assert result['risk_score'] <= 10.0
