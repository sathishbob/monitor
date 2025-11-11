"""
Main Monitoring Agent Module - Core Orchestration and Monitoring System

This module contains the main MonitorAgent class that orchestrates all monitoring
components and provides the primary interface for the Lab Server Monitoring Agent.
It coordinates data collection, analysis, storage, and reporting across all
specialized monitoring modules.

Key Features:
- Comprehensive system monitoring orchestration
- User activity and engagement tracking
- Performance metrics collection and analysis
- Command execution monitoring and security analysis
- AI-powered anomaly detection and forecasting
- Elasticsearch data storage and retrieval
- REST API for external integrations
- Real-time monitoring and alerting
- Cross-server performance comparison
- Risk assessment and dropout prediction

The MonitorAgent serves as the central coordinator that integrates all monitoring
capabilities into a unified, intelligent monitoring system for lab server environments.
"""

import logging
import threading
import time
import signal
import sys
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from collections import defaultdict, deque

# Import all monitoring components
from .engagement_scoring import EngagementScoring
from .performance_monitor import PerformanceMonitor
from .user_activity_monitor import UserActivityMonitor
from .command_monitor import CommandMonitor
from .ai_model import AIModel
from .es_manager import ElasticsearchManager
from .data_aggregator import DataAggregator

# Platform-specific imports
import platform
if platform.system() == "Windows":
    try:
        from .windows_window_monitor import WindowsWindowMonitor
        WINDOWS_WINDOW_MONITOR_AVAILABLE = True
    except ImportError:
        WINDOWS_WINDOW_MONITOR_AVAILABLE = False
else:
    WINDOWS_WINDOW_MONITOR_AVAILABLE = False

# Set up module-level logging
logger = logging.getLogger(__name__)

class MonitorAgent:
    """
    Main monitoring agent that orchestrates all monitoring components.
    
    This class serves as the central coordinator for the Lab Server Monitoring
    Agent, integrating all specialized monitoring modules into a unified system.
    It manages data collection, analysis, storage, and provides external APIs
    for monitoring and control.
    
    The agent coordinates:
    - System performance monitoring and metrics collection
    - User activity tracking and session management
    - Command execution monitoring and security analysis
    - Engagement scoring and behavioral analysis
    - AI-powered anomaly detection and forecasting
    - Data persistence and retrieval via Elasticsearch
    - REST API for external integrations and monitoring
    - Real-time alerting and notification systems
    
    All monitoring operations are designed to be non-intrusive and efficient,
    providing comprehensive insights while minimizing system impact.
    """
    
    def __init__(self, es_host: str = 'localhost:9200', es_index: str = 'lab_monitoring',
                 interval: int = 30, ignore_users: List[str] = None, listen_port: int = 5000,
                 es_user: Optional[str] = None, es_pass: Optional[str] = None,
                 es_api_key: Optional[str] = None, es_ca_certs: Optional[str] = None,
                 es_insecure: bool = False, ssl_assert_hostname: Optional[str] = None,
                 ssl_assert_fingerprint: Optional[str] = None, cmd_score_index_pattern: Optional[str] = None,
                 cross_server_index_pattern: Optional[str] = None, es_timeout: int = 15, es_max_retries: int = 3, es_refresh: Optional[str] = None,
                 engagement_session_timeout: int = 30, engagement_data_retention: int = 30,
                 server_id: str = 'unknown', comparison_servers: List[str] = None,
                 comparison_interval: int = 300, inactivity_threshold: int = 15,
                 failed_attempts_threshold: int = 5, struggle_detection_window: int = 30,
                 risk_assessment_interval: int = 300, api_key: Optional[str] = None,
                 allowed_commands: List[str] = None, bind_host: str = '127.0.0.1',
                 enable_remote_exec: bool = False, rate_limit_per_minute: int = 10,
                 inactivity_alert_enabled: bool = False, inactivity_webhook_url: Optional[str] = None,
                 inactivity_webhook_auth: Optional[str] = None, inactivity_window_minutes: int = 60,
                 check_command_activity: bool = True, check_network_activity: bool = True,
                 network_traffic_bytes_threshold: int = 1024):
        """
        Initialize the monitoring agent with comprehensive configuration.
        
        Args:
            es_host (str): Elasticsearch connection host and port
            es_index (str): Default Elasticsearch index name
            interval (int): Data collection interval in seconds
            ignore_users (List[str]): List of usernames to exclude from monitoring
            listen_port (int): Port for REST API server
            es_user (Optional[str]): Elasticsearch username
            es_pass (Optional[str]): Elasticsearch password
            es_api_key (Optional[str]): Elasticsearch API key
            es_ca_certs (Optional[str]): Path to CA certificates
            es_insecure (bool): Skip SSL verification
            ssl_assert_hostname (Optional[str]): SSL hostname assertion
            ssl_assert_fingerprint (Optional[str]): SSL certificate fingerprint
            cmd_score_index_pattern (Optional[str]): Command score index pattern
            es_timeout (int): Elasticsearch connection timeout
            es_max_retries (int): Maximum connection retries
            es_refresh (Optional[str]): Index refresh policy
            engagement_session_timeout (int): Session timeout in minutes
            engagement_data_retention (int): Data retention period in days
            server_id (str): Unique server identifier
            comparison_servers (List[str]): List of servers for comparison
            comparison_interval (int): Comparison interval in seconds
            inactivity_threshold (int): Inactivity threshold in minutes
            failed_attempts_threshold (int): Failed attempts threshold
            struggle_detection_window (int): Struggle detection window in minutes
            risk_assessment_interval (int): Risk assessment interval in seconds
            api_key (Optional[str]): API authentication key
            allowed_commands (List[str]): List of allowed remote commands
            bind_host (str): API server bind address
            enable_remote_exec (bool): Enable remote command execution
            rate_limit_per_minute (int): API rate limiting
        """
        # Core configuration and settings
        self.interval = interval
        self.server_id = server_id
        self.ignore_users = ignore_users or []
        self.api_key = api_key
        self.allowed_commands = allowed_commands or []
        self.enable_remote_exec = enable_remote_exec
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # API server configuration
        self.listen_port = listen_port
        self.bind_host = bind_host
        
        # Engagement and risk assessment configuration
        self.engagement_session_timeout = engagement_session_timeout
        self.engagement_data_retention = engagement_data_retention
        self.inactivity_threshold = inactivity_threshold
        self.failed_attempts_threshold = failed_attempts_threshold
        self.struggle_detection_window = struggle_detection_window
        self.risk_assessment_interval = risk_assessment_interval
        
        # Cross-server comparison configuration
        self.comparison_servers = comparison_servers or []
        self.comparison_interval = comparison_interval
        
        # Inactivity alert configuration
        self.inactivity_alert_enabled = inactivity_alert_enabled
        self.inactivity_webhook_url = inactivity_webhook_url
        self.inactivity_webhook_auth = inactivity_webhook_auth
        self.inactivity_window_minutes = inactivity_window_minutes
        self.last_activity_time = datetime.now(timezone.utc)
        self.inactivity_alert_sent = False
        # Initialize network monitoring for inactivity detection
        self.check_command_activity = check_command_activity
        self.check_network_activity = check_network_activity
        self.network_threshold_bytes = network_traffic_bytes_threshold
        self.last_network_bytes = 0
        self.initial_network_bytes = None
        
        # Initialize all monitoring components
        # Elasticsearch manager for data persistence
        self.es_manager = ElasticsearchManager(
            host=es_host,
            index=es_index,
            user=es_user,
            password=es_pass,
            api_key=es_api_key,
            ca_certs=es_ca_certs,
            insecure=es_insecure,
            ssl_assert_hostname=ssl_assert_hostname,
            ssl_assert_fingerprint=ssl_assert_fingerprint,
            timeout=es_timeout,
            max_retries=es_max_retries,
            refresh=es_refresh,
            cross_server_index_pattern=cross_server_index_pattern
        )
        
        # Performance monitoring system
        self.performance_monitor = PerformanceMonitor(max_history_size=1000)
        
        # User activity monitoring system
        self.user_activity_monitor = UserActivityMonitor(
            session_timeout_minutes=engagement_session_timeout
        )
        
        # Command execution monitoring system
        self.command_monitor = CommandMonitor(max_history_size=1000)
        
        # AI-powered analytics system
        self.ai_model = AIModel(contamination=0.1, min_samples=10)
        
        # Data aggregator for intelligent ES push management
        self.data_aggregator = DataAggregator(
            aggregation_interval_minutes=15,
            buffer_max_size=120  # Store ~60 minutes at 30s intervals
        )
        
        # Platform-specific monitoring
        self.is_windows = platform.system() == "Windows"
        if self.is_windows and WINDOWS_WINDOW_MONITOR_AVAILABLE:
            self.windows_window_monitor = WindowsWindowMonitor(check_interval_seconds=5.0)
            self.last_window_check = datetime.now(timezone.utc)
            logger.info("Windows window monitoring enabled")
        else:
            self.windows_window_monitor = None
            logger.info("Window monitoring not available (Linux or import failed)")
        
        # Engagement scoring and analysis system
        self.engagement_scoring = EngagementScoring(
            session_timeout_minutes=engagement_session_timeout,
            inactivity_threshold_minutes=inactivity_threshold,
            server_id=server_id,
            es_manager=self.es_manager
        )
        
        # System state and control
        self.running = False
        self.monitoring_thread = None
        self.api_thread = None
        
        # Data collection and storage
        self.monitoring_data: Dict[str, Any] = {}
        self.last_collection_time = None
        self.collection_count = 0
        
        # Performance and health monitoring
        self.start_time = None
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        
        # Rate limiting and security
        self.api_request_times: deque = deque(maxlen=rate_limit_per_minute)
        self.last_security_check = None
        
        # Initialize Flask application for REST API
        self.app = Flask(__name__)
        self._setup_api_routes()
        
        logger.info("Monitoring agent initialized successfully for server: %s", server_id)
    
    def _setup_api_routes(self) -> None:
        """
        Set up REST API routes and endpoints.
        
        This method configures all the API endpoints for external monitoring,
        control, and data retrieval. It includes authentication, rate limiting,
        and proper error handling for all endpoints.
        """
        # Health check endpoint
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint for monitoring system status."""
            return jsonify({
                'status': 'healthy',
                'server_id': self.server_id,
                'uptime': self._get_uptime(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # System metrics endpoint
        @self.app.route('/metrics', methods=['GET'])
        def get_metrics():
            """Get current system performance metrics."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self._check_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            try:
                metrics = self.performance_monitor.collect_metrics()
                return jsonify(metrics)
            except Exception as e:
                logger.error("Error retrieving metrics: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        # User activity endpoint
        @self.app.route('/users/activity', methods=['GET'])
        def get_user_activity():
            """Get current user activity and session information."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self._check_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            try:
                activity_summary = self.user_activity_monitor.get_session_summary()
                return jsonify(activity_summary)
            except Exception as e:
                logger.error("Error retrieving user activity: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        # Engagement scoring endpoint
        @self.app.route('/engagement/scores', methods=['GET'])
        def get_engagement_scores():
            """Get current engagement scores and analysis."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self._check_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            try:
                # This would return engagement scoring data
                # Implementation depends on specific requirements
                return jsonify({'message': 'Engagement scores endpoint'})
            except Exception as e:
                logger.error("Error retrieving engagement scores: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        # Command monitoring endpoint
        @self.app.route('/commands/summary', methods=['GET'])
        def get_command_summary():
            """Get command monitoring summary and security analysis."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self._check_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            try:
                command_summary = self.command_monitor.get_command_summary()
                return jsonify(command_summary)
            except Exception as e:
                logger.error("Error retrieving command summary: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        # AI model status endpoint
        @self.app.route('/ai/status', methods=['GET'])
        def get_ai_status():
            """Get AI model status and performance metrics."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self._check_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            try:
                ai_summary = self.ai_model.get_model_summary()
                return jsonify(ai_summary)
            except Exception as e:
                logger.error("Error retrieving AI status: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        # Remote command execution endpoint (if enabled)
        if self.enable_remote_exec:
            @self.app.route('/execute', methods=['POST'])
            def execute_command():
                """Execute remote commands (if enabled)."""
                if not self._authenticate_request():
                    return jsonify({'error': 'Unauthorized'}), 401
                
                if not self._check_rate_limit():
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                try:
                    data = request.get_json()
                    command = data.get('command', '')
                    
                    if not self._validate_command(command):
                        return jsonify({'error': 'Command not allowed'}), 403
                    
                    # Execute command and return results
                    # Implementation depends on security requirements
                    result = {'status': 'executed', 'command': command}
                    return jsonify(result)
                    
                except Exception as e:
                    logger.error("Error executing command: %s", e)
                    return jsonify({'error': 'Internal server error'}), 500
        
        # System control endpoints
        @self.app.route('/control/start', methods=['POST'])
        def start_monitoring():
            """Start the monitoring system."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                if not self.running:
                    self.start()
                    return jsonify({'status': 'started'})
                else:
                    return jsonify({'status': 'already_running'})
            except Exception as e:
                logger.error("Error starting monitoring: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/control/stop', methods=['POST'])
        def stop_monitoring():
            """Stop the monitoring system."""
            if not self._authenticate_request():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                if self.running:
                    self.stop()
                    return jsonify({'status': 'stopped'})
                else:
                    return jsonify({'status': 'not_running'})
            except Exception as e:
                logger.error("Error stopping monitoring: %s", e)
                return jsonify({'error': 'Internal server error'}), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors."""
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            return jsonify({'error': 'Internal server error'}), 500
    
    def _authenticate_request(self) -> bool:
        """
        Authenticate API request using configured API key.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Skip authentication if no API key configured
        if not self.api_key:
            return True
        
        # Get API key from request headers
        request_api_key = request.headers.get('X-API-Key')
        if not request_api_key:
            return False
        
        # Validate API key
        return request_api_key == self.api_key
    
    def _check_rate_limit(self) -> bool:
        """
        Check if request is within rate limit.
        
        Returns:
            bool: True if within rate limit, False otherwise
        """
        current_time = time.time()
        
        # Remove old requests outside the time window
        while self.api_request_times and current_time - self.api_request_times[0] > 60:
            self.api_request_times.popleft()
        
        # Check if we're at the rate limit
        if len(self.api_request_times) >= self.rate_limit_per_minute:
            return False
        
        # Add current request
        self.api_request_times.append(current_time)
        return True
    
    def _validate_command(self, command: str) -> bool:
        """
        Validate if a command is allowed for remote execution.
        
        Args:
            command (str): Command to validate
            
        Returns:
            bool: True if command is allowed, False otherwise
        """
        # Check if remote execution is enabled
        if not self.enable_remote_exec:
            return False
        
        # Check if command is in allowed list
        if command in self.allowed_commands:
            return True
        
        # Additional validation logic can be added here
        # For example, checking command patterns, user permissions, etc.
        
        return False
    
    def start(self) -> None:
        """Start the monitoring agent and all monitoring activities."""
        try:
            if self.running:
                logger.warning("Monitoring agent is already running")
                return
            
            logger.info("Starting monitoring agent...")
            self.running = True
            self.start_time = datetime.now(timezone.utc)
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            # Start API server thread
            self.api_thread = threading.Thread(target=self._run_api_server, daemon=True)
            self.api_thread.start()
            
            logger.info("Monitoring agent started successfully")
            
        except Exception as e:
            logger.error("Error starting monitoring agent: %s", e)
            self.running = False
            raise
    
    def stop(self) -> None:
        """Stop the monitoring agent and cleanup resources."""
        try:
            if not self.running:
                logger.warning("Monitoring agent is not running")
                return
            
            logger.info("Stopping monitoring agent...")
            self.running = False
            
            # Wait for threads to complete
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            if self.api_thread and self.api_thread.is_alive():
                self.api_thread.join(timeout=5)
            
            # Close Elasticsearch connection
            self.es_manager.close_connection()
            
            logger.info("Monitoring agent stopped successfully")
            
        except Exception as e:
            logger.error("Error stopping monitoring agent: %s", e)
            raise
    
    def _monitoring_loop(self) -> None:
        """
        Main monitoring loop that collects data and performs analysis.
        
        This method runs continuously while the agent is running, collecting
        system metrics, user activity data, and performing various analyses
        at regular intervals.
        """
        logger.info("Monitoring loop started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Collect system performance metrics
                self._collect_performance_data()
                
                # Collect user activity data
                self._collect_user_activity_data()
                
                # Collect command execution data
                self._collect_command_data()
                
                # Collect Windows application/window usage (Windows only)
                if self.is_windows:
                    self._collect_windows_window_activity()
                
                # Perform engagement analysis
                self._analyze_engagement()
                
                # Perform risk assessment
                self._assess_risks()
                
                # Perform cross-server comparison
                self._perform_cross_server_comparison()
                
                # Update AI models
                self._update_ai_models()
                
                # Store monitoring data
                self._store_monitoring_data()
                
                # Check for inactivity and send alert if needed
                self._check_inactivity_and_alert()
                
                # Update performance metrics
                self._update_performance_metrics(start_time)
                
                # Wait for next collection interval
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error("Error in monitoring loop: %s", e)
                self.failed_operations += 1
                time.sleep(self.interval)
        
        logger.info("Monitoring loop stopped")
    
    def _collect_performance_data(self) -> None:
        """Collect system performance metrics with intelligent aggregation."""
        try:
            # Collect current performance metrics
            metrics = self.performance_monitor.collect_metrics()
            
            # Store metrics for analysis
            self.monitoring_data['performance'] = metrics
            
            # Add to aggregation buffer
            self.data_aggregator.add_performance_metric(metrics)
            
            # Check if we should send aggregated summary to ES
            if self.data_aggregator.should_send_performance_to_es():
                aggregated_summary = self.data_aggregator.aggregate_performance_metrics()
                
                if aggregated_summary:
                    # Push aggregated summary to Elasticsearch
                    self.es_manager.index_document({
                        'timestamp': aggregated_summary['timestamp'],
                        'server_id': self.server_id,
                        'event_type': 'performance_metrics_aggregated',
                        'data': aggregated_summary
                    })
                    logger.info(f"Sent aggregated performance summary to ES (samples: {aggregated_summary['sample_count']})")
            
            logger.debug("Performance data collected and buffered")
            
        except Exception as e:
            logger.error("Error collecting performance data: %s", e)
    
    def _collect_user_activity_data(self) -> None:
        """Collect user activity and session data with aggregation."""
        try:
            # Get current user activity summary
            activity_summary = self.user_activity_monitor.get_session_summary()
            
            # Store activity data
            self.monitoring_data['user_activity'] = activity_summary
            
            # Only send activity summary at intervals (not every 30s)
            current_time = datetime.now(timezone.utc)
            elapsed = (current_time - self.data_aggregator.last_activity_sent).total_seconds()
            
            if elapsed >= self.data_aggregator.aggregation_interval_seconds:
                # Aggregate and send summary
                aggregated_activity = self.data_aggregator.aggregate_user_activity(activity_summary)
                
                self.es_manager.index_document({
                    'timestamp': aggregated_activity['timestamp'],
                    'server_id': self.server_id,
                    'event_type': 'user_activity_aggregated',
                    'data': aggregated_activity
                })
                
                self.data_aggregator.last_activity_sent = current_time
                logger.debug(f"Sent aggregated user activity summary to ES")
            
            logger.debug("User activity data collected")
            
        except Exception as e:
            logger.error("Error collecting user activity data: %s", e)
    
    def _collect_command_data(self) -> None:
        """Collect command execution and security data."""
        try:
            # First collect commands from audit logs
            self.collect_commands()
            
            # Then get command monitoring summary
            command_summary = self.command_monitor.get_command_summary()
            
            # Store command data
            self.monitoring_data['command_monitoring'] = command_summary
            
            # Push to Elasticsearch
            self.es_manager.index_document({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'server_id': self.server_id,
                'event_type': 'command_monitoring',
                'data': command_summary
            })
            
            logger.debug("Command data collected and stored")
            
        except Exception as e:
            logger.error("Error collecting command data: %s", e)
    
    def _collect_windows_window_activity(self) -> None:
        """Collect Windows application/window usage activity."""
        try:
            if not self.windows_window_monitor:
                return
            
            # Check if enough time has passed since last check (every 5 seconds)
            current_time = datetime.now(timezone.utc)
            elapsed = (current_time - self.last_window_check).total_seconds()
            
            if elapsed < self.windows_window_monitor.check_interval:
                return
            
            # Track window activity
            window_change = self.windows_window_monitor.track_window_activity()
            
            if window_change:
                # Send window change event to engagement scoring
                current_user = window_change.get('current_process', 'unknown')
                
                try:
                    self.engagement_scoring.update_activity(
                        user_id=current_user,
                        activity_type='window',
                        data={
                            'process_name': window_change.get('current_process'),
                            'window_title': window_change.get('current_window'),
                            'time_spent_seconds': window_change.get('time_spent_seconds', 0)
                        }
                    )
                except Exception as e:
                    logger.error(f"Error updating engagement for window activity: {e}")
            
            # Check if we should send aggregated summary to ES (every 15 min)
            window_summary = self.windows_window_monitor.get_application_summary()
            self.monitoring_data['windows_window_activity'] = window_summary
            
            # Send summary periodically
            if elapsed >= self.data_aggregator.aggregation_interval_seconds:
                self.es_manager.index_document({
                    'timestamp': window_summary.get('timestamp', datetime.now(timezone.utc).isoformat()),
                    'server_id': self.server_id,
                    'event_type': 'windows_window_activity',
                    'data': window_summary
                })
                logger.debug("Sent Windows window activity summary to ES")
            
            self.last_window_check = current_time
            
        except Exception as e:
            logger.error("Error collecting Windows window activity: %s", e)
    
    def collect_commands(self) -> None:
        """Collect and store command execution data from audit logs."""
        try:
            import platform
            
            # Collect commands based on platform
            if platform.system() == "Linux":
                commands = self.command_monitor.get_linux_commands()
            else:
                commands = self.command_monitor.get_windows_commands()
            
            # Filter ignored users
            commands = [c for c in commands if c.get('user') not in self.ignore_users]
            
            # Process and store individual commands
            if commands:
                for command_data in commands:
                    # Monitor each command for security analysis
                    self.command_monitor.monitor_command(
                        username=command_data.get('user', 'unknown'),
                        command=command_data.get('command', ''),
                        working_directory=command_data.get('working_directory'),
                        exit_code=command_data.get('exit_code'),
                        execution_time=command_data.get('execution_time', command_data.get('duration_seconds', 0.1))
                    )
                    
                    # Command data will be used for engagement analysis in _analyze_engagement()
                    
                    # Update engagement scoring with command activity to emit learning_progress
                    try:
                        self.engagement_scoring.update_activity(
                            user_id=command_data.get('user', 'unknown'),
                            activity_type='command',
                            data={
                                'command': command_data.get('command', ''),
                                'dangerous': False,
                                'duration_seconds': command_data.get('execution_time', command_data.get('duration_seconds', 0.0))
                            }
                        )
                    except Exception as e:
                        logger.error("Error updating engagement activity for command: %s", e)
                    
                    # Only push significant commands to Elasticsearch (filtered)
                    if self.data_aggregator.should_send_command_to_es(command_data):
                        self.es_manager.index_document({
                            'timestamp': command_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                            'server_id': self.server_id,
                            'event_type': 'command',
                            'data': command_data
                        })
                        logger.debug(f"Sent significant command to ES: {command_data.get('command', '')[:50]}")
                
                logger.debug("Collected and processed %d commands", len(commands))
            
        except Exception as e:
            logger.error("Error collecting commands: %s", e)
    
    def _analyze_engagement(self) -> None:
        """Perform engagement analysis and scoring."""
        try:
            # Get recent commands to identify active users
            recent_commands = self.command_monitor.get_recent_commands(minutes=30)
            
            # Extract unique users from recent commands
            active_users = set()
            for command in recent_commands:
                user = command.get('user', 'unknown')
                if user and user != 'unknown':
                    active_users.add(user)
            
            # Check for inactive sessions and end them
            current_time = datetime.now(timezone.utc)
            inactive_users = []
            
            for user_id in list(self.engagement_scoring.active_sessions.keys()):
                if user_id not in active_users:
                    session = self.engagement_scoring.active_sessions[user_id]
                    last_activity = session['last_activity']
                    inactivity_minutes = (current_time - last_activity).total_seconds() / 60
                    
                    # End session if inactive for more than threshold
                    if inactivity_minutes > self.engagement_scoring.inactivity_threshold_minutes:
                        inactive_users.append(user_id)
            
            # End inactive sessions
            for user_id in inactive_users:
                try:
                    self.engagement_scoring.end_session(user_id)
                    logger.info(f"Ended inactive session for user {user_id}")
                except Exception as e:
                    logger.error(f"Error ending session for user {user_id}: {e}")
            
            # Process engagement for each active user
            for user_id in active_users:
                # Start session for each user (will update if already exists)
                self.engagement_scoring.start_session(user_id)
                
                # Generate engagement report for the user
                self.engagement_scoring.get_engagement_report(user_id)
            
            # Also generate engagement metrics for the system
            self._generate_system_engagement_metrics()
            
            logger.debug("Engagement analysis completed for %d users, ended %d inactive sessions", len(active_users), len(inactive_users))
            
        except Exception as e:
            logger.error("Error analyzing engagement: %s", e)
    
    def _generate_system_engagement_metrics(self) -> None:
        """Generate system-wide engagement metrics."""
        try:
            # Get recent commands for engagement analysis
            recent_commands = self.command_monitor.get_recent_commands(minutes=30)
            
            if not recent_commands:
                return
            
            # Calculate engagement metrics
            total_commands = len(recent_commands)
            unique_users = len(set(cmd.get('user', 'unknown') for cmd in recent_commands))
            avg_execution_time = sum(cmd.get('execution_time', 0) for cmd in recent_commands) / total_commands
            
            # Categorize commands by type
            command_categories = {
                'development': 0,
                'system': 0,
                'network': 0,
                'file_ops': 0,
                'other': 0
            }
            
            for cmd in recent_commands:
                command = cmd.get('command', '').lower()
                if any(dev_cmd in command for dev_cmd in ['git', 'make', 'build', 'test', 'debug', 'compile']):
                    command_categories['development'] += 1
                elif any(sys_cmd in command for sys_cmd in ['ps', 'top', 'htop', 'systemctl', 'service']):
                    command_categories['system'] += 1
                elif any(net_cmd in command for net_cmd in ['curl', 'wget', 'ping', 'ssh', 'scp']):
                    command_categories['network'] += 1
                elif any(file_cmd in command for file_cmd in ['ls', 'cat', 'grep', 'find', 'cp', 'mv', 'rm']):
                    command_categories['file_ops'] += 1
                else:
                    command_categories['other'] += 1
            
            # Create engagement metrics data
            engagement_metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'server_id': self.server_id,
                'metrics': {
                    'total_commands': total_commands,
                    'unique_users': unique_users,
                    'avg_execution_time': avg_execution_time,
                    'command_categories': command_categories,
                    'engagement_score': min(100, (total_commands * unique_users) / 10),  # Simple scoring
                    'activity_level': 'high' if total_commands > 50 else 'medium' if total_commands > 10 else 'low'
                }
            }
            
            # Push to Elasticsearch
            self.es_manager.index_document({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'server_id': self.server_id,
                'event_type': 'engagement_metrics',
                'data': engagement_metrics
            })
            
            logger.debug("Generated system engagement metrics: %d commands, %d users", total_commands, unique_users)
            
        except Exception as e:
            logger.error("Error generating system engagement metrics: %s", e)
    
    def _assess_risks(self) -> None:
        """Perform risk assessment and generate alerts."""
        try:
            # Check if it's time for dropout risk assessment
            current_time = time.time()
            if not hasattr(self, '_last_risk_assessment'):
                self._last_risk_assessment = 0
            
            if current_time - self._last_risk_assessment >= self.risk_assessment_interval:
                # Perform dropout risk assessment for all active users
                risk_assessments = 0
                for user_id in list(self.engagement_scoring.active_sessions.keys()):
                    try:
                        risk_assessment = self.engagement_scoring.assess_dropout_risk(user_id)
                        if 'error' not in risk_assessment:
                            risk_assessments += 1
                            # Log high-risk students
                            if risk_assessment.get('risk_level') in ['High', 'Critical']:
                                logger.warning(f"High dropout risk detected for user {user_id}: {risk_assessment.get('risk_level')} risk level")
                    except Exception as e:
                        logger.error(f"Error assessing dropout risk for user {user_id}: {e}")
                
                if risk_assessments > 0:
                    logger.info(f"Completed dropout risk assessment for {risk_assessments} active users")
                
                self._last_risk_assessment = current_time
            
            logger.debug("Risk assessment completed")
            
        except Exception as e:
            logger.error("Error assessing risks: %s", e)
    
    def _perform_cross_server_comparison(self) -> None:
        """Perform cross-server performance comparison."""
        try:
            # Check if it's time for cross-server metrics generation
            current_time = time.time()
            if not hasattr(self, '_last_cross_server_metrics'):
                self._last_cross_server_metrics = 0
            
            if current_time - self._last_cross_server_metrics >= self.comparison_interval:
                # Generate cross-server metrics
                try:
                    cross_server_data = self.engagement_scoring.generate_cross_server_metrics()
                    logger.info(f"Generated cross-server metrics: {cross_server_data.get('total_users', 0)} users, {cross_server_data.get('total_sessions', 0)} sessions")
                except Exception as e:
                    logger.error(f"Error generating cross-server metrics: {e}")
                
                # Generate cross-server comparison
                try:
                    comparison_data = self.engagement_scoring.generate_cross_server_comparison()
                    if 'error' not in comparison_data:
                        logger.info(f"Generated cross-server comparison: {comparison_data.get('peer_count', 0)} peers, overall score: {comparison_data.get('overall_performance', {}).get('score', 'N/A')}")
                    else:
                        logger.debug(f"Cross-server comparison: {comparison_data.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Error generating cross-server comparison: {e}")
                
                self._last_cross_server_metrics = current_time
            
            logger.debug("Cross-server comparison completed")
            
        except Exception as e:
            logger.error("Error performing cross-server comparison: %s", e)
    
    def _update_ai_models(self) -> None:
        """Update and retrain AI models with new data."""
        try:
            # This would update AI models with new data
            # and retrain them as necessary
            
            logger.debug("AI models updated")
            
        except Exception as e:
            logger.error("Error updating AI models: %s", e)
    
    def _store_monitoring_data(self) -> None:
        """Store aggregated monitoring data."""
        try:
            # Store comprehensive monitoring data
            monitoring_summary = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'server_id': self.server_id,
                'event_type': 'monitoring_summary',
                'data': {
                    'performance': self.monitoring_data.get('performance', {}),
                    'user_activity': self.monitoring_data.get('user_activity', {}),
                    'command_monitoring': self.monitoring_data.get('command_monitoring', {}),
                    'collection_count': self.collection_count,
                    'total_operations': self.total_operations,
                    'successful_operations': self.successful_operations,
                    'failed_operations': self.failed_operations
                }
            }
            
            # Push to Elasticsearch
            self.es_manager.index_document(monitoring_summary)
            
            # Update collection count
            self.collection_count += 1
            self.last_collection_time = datetime.now(timezone.utc)
            
            logger.debug("Monitoring data stored successfully")
            
        except Exception as e:
            logger.error("Error storing monitoring data: %s", e)
    
    def _check_inactivity_and_alert(self) -> None:
        """Check for server inactivity and send webhook alert if configured."""
        try:
            # Only check if inactivity alerts are enabled
            if not self.inactivity_alert_enabled or not self.inactivity_webhook_url:
                return
            
            # Check for command activity
            has_command_activity = False
            if self.check_command_activity:
                recent_commands = self.command_monitor.get_recent_commands(minutes=self.inactivity_window_minutes)
                has_command_activity = len(recent_commands) > 0
                if has_command_activity:
                    logger.debug(f"Command activity detected: {len(recent_commands)} recent commands")
            
            # Check for network traffic activity
            has_network_activity = False
            if self.check_network_activity:
                has_network_activity = self._check_network_activity()
                if has_network_activity:
                    logger.debug("Network traffic activity detected")
            
            # Overall activity determination
            has_activity = has_command_activity or has_network_activity
            current_time = datetime.now(timezone.utc)
            
            if has_activity:
                # Activity detected - update last activity time and reset alert flag
                self.last_activity_time = current_time
                self.inactivity_alert_sent = False
                logger.debug("Activity detected (command={}, network={}), inactivity alert reset".format(
                    has_command_activity, has_network_activity))
            else:
                # No activity detected - check if we should send alert
                inactivity_duration = (current_time - self.last_activity_time).total_seconds() / 60  # minutes
                
                if inactivity_duration >= self.inactivity_window_minutes and not self.inactivity_alert_sent:
                    # Send inactivity alert
                    self._send_inactivity_webhook(inactivity_duration, has_command_activity, has_network_activity)
                    self.inactivity_alert_sent = True
                    logger.warning(f"Inactivity alert sent - no activity for {inactivity_duration:.1f} minutes")
            
        except Exception as e:
            logger.error("Error checking inactivity and sending alert: %s", e)
    
    def _check_network_activity(self) -> bool:
        """
        Check if there's significant network traffic activity.
        
        Returns:
            bool: True if network activity exceeds threshold, False otherwise
        """
        try:
            import psutil
            
            # Get current network statistics
            net_io = psutil.net_io_counters()
            if not net_io:
                return False
            
            # Calculate total bytes
            current_total_bytes = net_io.bytes_sent + net_io.bytes_recv
            
            # Initialize baseline on first check
            if self.initial_network_bytes is None:
                self.initial_network_bytes = current_total_bytes
                self.last_network_bytes = current_total_bytes
                logger.debug(f"Initialized network baseline: {current_total_bytes} bytes")
                return False
            
            # Calculate bytes transferred since last check
            bytes_transferred = current_total_bytes - self.last_network_bytes
            
            # Update last known bytes
            self.last_network_bytes = current_total_bytes
            
            # Check if activity exceeds threshold
            if bytes_transferred >= self.network_threshold_bytes:
                logger.debug(f"Network activity detected: {bytes_transferred} bytes transferred")
                return True
            
            logger.debug(f"No significant network activity: {bytes_transferred} bytes < {self.network_threshold_bytes} bytes threshold")
            return False
            
        except Exception as e:
            logger.error(f"Error checking network activity: {e}")
            return False
    
    def _send_inactivity_webhook(self, inactivity_duration_minutes: float, 
                                  has_command_activity: bool, has_network_activity: bool) -> None:
        """
        Send webhook notification for server inactivity.
        
        Args:
            inactivity_duration_minutes (float): Duration of inactivity in minutes
            has_command_activity (bool): Whether command activity was checked
            has_network_activity (bool): Whether network activity was detected
        """
        try:
            # Prepare webhook payload with detailed activity information
            payload = {
                'event_type': 'inactivity_alert',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'server_id': self.server_id,
                'inactivity_duration_minutes': round(inactivity_duration_minutes, 2),
                'inactivity_threshold_minutes': self.inactivity_window_minutes,
                'status': 'no_activity',
                'activity_check': {
                    'command_activity_enabled': self.check_command_activity,
                    'command_activity_detected': has_command_activity,
                    'network_activity_enabled': self.check_network_activity,
                    'network_activity_detected': has_network_activity,
                    'network_threshold_bytes': self.network_threshold_bytes
                }
            }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'LabServerMonitor/1.0'
            }
            
            # Add authentication if provided
            if self.inactivity_webhook_auth:
                # Support Bearer token or API key in header
                if self.inactivity_webhook_auth.startswith('Bearer '):
                    headers['Authorization'] = self.inactivity_webhook_auth
                else:
                    headers['Authorization'] = f'Bearer {self.inactivity_webhook_auth}'
            
            # Send webhook request with retries
            max_retries = 3
            retry_delay = 5
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.inactivity_webhook_url,
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    
                    logger.info(f"Inactivity webhook sent successfully (attempt {attempt + 1})")
                    return
                    
                except requests.exceptions.RequestException as e:
                    last_error = e
                    logger.warning(f"Inactivity webhook attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            
            # All retries failed
            logger.error(f"Inactivity webhook failed after {max_retries} attempts: {last_error}")
            
        except Exception as e:
            logger.error(f"Error sending inactivity webhook: {e}")
    
    def _update_performance_metrics(self, start_time: float) -> None:
        """
        Update internal performance metrics.
        
        Args:
            start_time (float): Start time of the monitoring cycle
        """
        try:
            # Calculate cycle duration
            cycle_duration = time.time() - start_time
            
            # Update operation counts
            self.total_operations += 1
            if cycle_duration < self.interval:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
            
        except Exception as e:
            logger.error("Error updating performance metrics: %s", e)
    
    def _run_api_server(self) -> None:
        """Run the Flask API server."""
        try:
            logger.info("Starting API server on %s:%d", self.bind_host, self.listen_port)
            self.app.run(
                host=self.bind_host,
                port=self.listen_port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error("Error running API server: %s", e)
    
    def _get_uptime(self) -> str:
        """
        Get system uptime as a formatted string.
        
        Returns:
            str: Formatted uptime string
        """
        if not self.start_time:
            return "0s"
        
        uptime = datetime.now(timezone.utc) - self.start_time
        total_seconds = int(uptime.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def run(self) -> None:
        """Run the monitoring agent in the main thread."""
        try:
            logger.info("Starting monitoring agent in main thread...")
            self.start()
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error("Error in main thread: %s", e)
        finally:
            self.stop()
    
    def run_as_daemon(self) -> None:
        """Run the monitoring agent as a background daemon."""
        try:
            logger.info("Starting monitoring agent as daemon...")
            self.start()
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # Keep daemon running
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error("Error in daemon mode: %s", e)
        finally:
            self.stop()
    
    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle system signals for graceful shutdown.
        
        Args:
            signum (int): Signal number
            frame: Current stack frame
        """
        logger.info("Received signal %d, shutting down gracefully...", signum)
        self.stop()
        sys.exit(0)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the monitoring agent.
        
        Returns:
            Dict[str, Any]: Complete status information
        """
        try:
            return {
                'status': 'running' if self.running else 'stopped',
                'server_id': self.server_id,
                'uptime': self._get_uptime(),
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'last_collection_time': self.last_collection_time.isoformat() if self.last_collection_time else None,
                'collection_count': self.collection_count,
                'total_operations': self.total_operations,
                'successful_operations': self.successful_operations,
                'failed_operations': self.failed_operations,
                'elasticsearch_status': self.es_manager.get_connection_status(),
                'performance_monitor_status': 'active',
                'user_activity_monitor_status': 'active',
                'command_monitor_status': 'active',
                'ai_model_status': 'active',
                'engagement_scoring_status': 'active'
            }
            
        except Exception as e:
            logger.error("Error getting status: %s", e)
            return {'status': 'error', 'error': str(e)}
