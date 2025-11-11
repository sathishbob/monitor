#!/usr/bin/env python3
"""
Lab Server Monitoring AI Agent
A comprehensive monitoring solution for tracking server performance, user activity, and AI-powered analytics.

This file serves as the main entry point for the monitoring agent application. It handles:
- Configuration loading from JSON files
- Command-line argument parsing
- Application initialization and startup
- Error handling and graceful shutdown

The actual monitoring logic is implemented in separate modules within the 'agent/' package:
- agent.engagement_scoring: User engagement analysis and scoring
- agent.performance_monitor: System performance metrics collection
- agent.user_activity_monitor: User activity tracking and analysis
- agent.command_monitor: Command execution monitoring and security
- agent.ai_model: AI-powered anomaly detection and forecasting
- agent.es_manager: Elasticsearch data storage and retrieval
- agent.agent: Main monitoring agent orchestration
"""

import argparse
import json
import logging
import sys
from typing import Any

# Import all classes from agent modules
# These imports maintain backward compatibility while using the new modular structure
from agent.engagement_scoring import EngagementScoring
from agent.performance_monitor import PerformanceMonitor
from agent.user_activity_monitor import UserActivityMonitor
from agent.command_monitor import CommandMonitor
from agent.ai_model import AIModel
from agent.es_manager import ElasticsearchManager
from agent.agent import MonitorAgent

# Configure logging system
# Sets up both file and console logging with consistent formatting
logging.basicConfig(
    level=logging.INFO,  # Default log level for the application
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Timestamp, logger name, level, message
    handlers=[
        logging.FileHandler('monitor_agent.log'),  # Log to file for persistence
        logging.StreamHandler(sys.stdout)          # Log to console for real-time monitoring
    ]
)
logger = logging.getLogger(__name__)

# Reduce noise from third-party libraries
# These libraries can be very verbose, so we set them to WARNING level only
logging.getLogger('elastic_transport').setLevel(logging.WARNING)  # Elasticsearch transport layer
logging.getLogger('urllib3').setLevel(logging.WARNING)           # HTTP client library
logging.getLogger('werkzeug').setLevel(logging.WARNING)          # WSGI web server library

def load_config(config_file: str) -> dict:
    """
    Load and parse configuration from a JSON file.
    
    This function handles the configuration loading process with comprehensive error handling.
    It ensures the application fails gracefully if configuration is missing or invalid.
    
    Args:
        config_file (str): Path to the JSON configuration file
        
    Returns:
        dict: Parsed configuration dictionary
        
    Raises:
        SystemExit: If configuration file is missing, invalid, or unreadable
    """
    try:
        # Attempt to open and read the configuration file
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_file}")
        return config
        
    except FileNotFoundError:
        # Configuration file doesn't exist - critical error
        logger.error(f"Configuration file {config_file} not found")
        logger.error("Please ensure config.json exists in the application directory")
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        # Configuration file contains invalid JSON - critical error
        logger.error(f"Invalid JSON in configuration file {config_file}: {e}")
        logger.error("Please check the JSON syntax in your configuration file")
        sys.exit(1)
        
    except Exception as e:
        # Unexpected error during configuration loading - critical error
        logger.error(f"Error loading configuration: {e}")
        logger.error("Unexpected error occurred while reading configuration")
        sys.exit(1)

def main():
    """
    Main function with CLI argument parsing and application initialization.
    
    This function serves as the primary entry point for the monitoring agent.
    It handles command-line arguments, loads configuration, initializes the
    monitoring agent, and starts the appropriate execution mode.
    
    Command-line arguments:
        --config: Path to configuration file (default: config.json)
        --daemon: Run the application in daemon mode (background)
        --debug: Enable debug-level logging for troubleshooting
    """
    # Set up command-line argument parser with descriptive help text
    parser = argparse.ArgumentParser(description='Lab Server Monitoring AI Agent')
    parser.add_argument('--config', default='config.json', 
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as daemon (background process)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug logging for troubleshooting')
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Configure debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Load configuration from the specified file
        logger.info("Starting Lab Server Monitoring AI Agent...")
        config = load_config(args.config)
        
        # Extract configuration sections for cleaner code organization
        # Each section contains related configuration parameters
        es_config = config.get('elasticsearch', {})           # Elasticsearch connection settings
        monitoring_config = config.get('monitoring', {})      # Core monitoring parameters
        users_config = config.get('users', {})               # User management settings
        ai_config = config.get('ai', {})                     # AI model configuration
        inactivity_alert_config = config.get('inactivity_alert', {})  # Inactivity alert settings
        
        # Initialize the monitoring agent with all configuration parameters
        # The MonitorAgent constructor accepts individual parameters for flexibility
        logger.info("Initializing monitoring agent...")
        agent = MonitorAgent(
            # Elasticsearch configuration
            es_host=es_config.get('host', 'localhost:9200'),                    # ES server address
            es_index=es_config.get('index', 'lab_monitoring'),                  # ES index name
            es_user=es_config.get('user'),                                     # ES username (optional)
            es_pass=es_config.get('pass'),                                     # ES password (optional)
            es_api_key=es_config.get('api_key'),                               # ES API key (optional)
            es_ca_certs=es_config.get('ca_certs'),                             # ES CA certificates (optional)
            es_insecure=es_config.get('insecure', False),                      # Skip SSL verification
            ssl_assert_hostname=es_config.get('ssl_assert_hostname'),       # SSL hostname assertion
            ssl_assert_fingerprint=es_config.get('ssl_assert_fingerprint'), # SSL fingerprint assertion
            cmd_score_index_pattern=es_config.get('cmd_score_index_pattern'),   # Command score index pattern
            cross_server_index_pattern=es_config.get('cross_server_index_pattern'), # Cross-server index pattern
            es_timeout=es_config.get('timeout', 15),                           # ES connection timeout
            es_max_retries=es_config.get('max_retries', 3),                    # ES retry attempts
            es_refresh=es_config.get('refresh'),                               # ES refresh policy
            
            # Core monitoring configuration
            interval=monitoring_config.get('interval', 30),                     # Data collection interval
            listen_port=monitoring_config.get('listen_port', 5000),             # API server port
            bind_host=monitoring_config.get('bind_host', '127.0.0.1'),         # API server bind address
            enable_remote_exec=monitoring_config.get('enable_remote_exec', False), # Enable remote commands
            rate_limit_per_minute=monitoring_config.get('rate_limit_per_minute', 10), # API rate limiting
            
            # User management configuration
            ignore_users=users_config.get('ignore_users', []),                  # Users to exclude from monitoring
            
            # Engagement analysis configuration
            engagement_session_timeout=monitoring_config.get('engagement_session_timeout', 30), # Session timeout
            engagement_data_retention=monitoring_config.get('engagement_data_retention', 30),   # Data retention period
            
            # Server identification and comparison
            server_id=monitoring_config.get('server_id', 'unknown'),            # Unique server identifier
            comparison_servers=monitoring_config.get('comparison_servers'),     # Servers for comparison
            comparison_interval=monitoring_config.get('comparison_interval', 300), # Comparison frequency
            
            # Risk assessment and anomaly detection
            inactivity_threshold=monitoring_config.get('inactivity_threshold', 15),           # Inactivity threshold
            failed_attempts_threshold=monitoring_config.get('failed_attempts_threshold', 5), # Failed attempts limit
            struggle_detection_window=monitoring_config.get('struggle_detection_window', 30), # Struggle detection period
            risk_assessment_interval=monitoring_config.get('risk_assessment_interval', 300),  # Risk assessment frequency
            
            # Security and access control
            api_key=monitoring_config.get('api_key'),                          # API authentication key
            allowed_commands=monitoring_config.get('allowed_commands'),         # Permitted remote commands
            
            # Inactivity alert configuration
            inactivity_alert_enabled=inactivity_alert_config.get('enabled', False),  # Enable inactivity alerts
            inactivity_webhook_url=inactivity_alert_config.get('webhook_url'),      # Webhook URL for alerts
            inactivity_webhook_auth=inactivity_alert_config.get('webhook_auth'),   # Webhook authentication
            inactivity_window_minutes=inactivity_alert_config.get('inactivity_window_minutes', 60),  # Inactivity threshold
            check_command_activity=inactivity_alert_config.get('check_command_activity', True),  # Check command activity
            check_network_activity=inactivity_alert_config.get('check_network_activity', True),  # Check network activity
            network_traffic_bytes_threshold=inactivity_alert_config.get('network_traffic_bytes_threshold', 1024)  # Network threshold
        )
        
        logger.info("Monitoring agent initialized successfully")
        
        # Start the monitoring agent in the appropriate mode
        if args.daemon:
            # Run as a background daemon process
            logger.info("Starting monitoring agent in daemon mode...")
            agent.run_as_daemon()
        else:
            # Run in foreground mode (default)
            logger.info("Starting monitoring agent in foreground mode...")
            agent.run()
            
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        logger.info("Shutting down monitoring agent...")
        logger.info("Received interrupt signal, cleaning up...")
        
    except Exception as e:
        # Handle unexpected errors during startup or execution
        logger.error(f"Fatal error: {e}")
        logger.error("Application failed to start or encountered critical error")
        sys.exit(1)

# Standard Python idiom for running the script directly
# This ensures the main() function is called when the script is executed
if __name__ == "__main__":
    main()
