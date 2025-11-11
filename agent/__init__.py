"""
Agent Package Initialization

This package contains all the core monitoring and AI functionality for the Lab Server Monitoring Agent.
It provides a modular architecture where each major component is implemented in its own file.

Package Structure:
- engagement_scoring: User engagement analysis and behavioral scoring
- performance_monitor: System performance metrics collection and monitoring
- user_activity_monitor: User activity tracking and session management
- command_monitor: Command execution monitoring and security analysis
- ai_model: AI-powered anomaly detection and forecasting models
- es_manager: Elasticsearch data storage, retrieval, and management
- agent: Main monitoring agent that orchestrates all components

Usage:
    from agent import MonitorAgent, EngagementScoring, PerformanceMonitor
    from agent import UserActivityMonitor, CommandMonitor, AIModel, ElasticsearchManager

This package maintains backward compatibility by re-exporting all classes,
allowing existing code to continue working without modification.
"""

# Import all major classes from their respective modules
# This enables the package to provide a clean, unified interface
from .engagement_scoring import EngagementScoring
from .performance_monitor import PerformanceMonitor
from .user_activity_monitor import UserActivityMonitor
from .command_monitor import CommandMonitor
from .ai_model import AIModel
from .es_manager import ElasticsearchManager
from .data_aggregator import DataAggregator
from .agent import MonitorAgent

# Platform-specific imports
import platform
if platform.system() == "Windows":
    try:
        from .windows_window_monitor import WindowsWindowMonitor
    except ImportError:
        pass

# Define the public API for this package
# These are the classes that should be accessible when importing from 'agent'
__all__ = [
    'EngagementScoring',      # User engagement analysis engine
    'PerformanceMonitor',      # System performance monitoring
    'UserActivityMonitor',     # User activity tracking
    'CommandMonitor',          # Command execution monitoring
    'AIModel',                 # AI/ML model implementations
    'ElasticsearchManager',    # Elasticsearch data management
    'DataAggregator',          # Data aggregation and filtering
    'MonitorAgent',            # Main orchestration class
    'WindowsWindowMonitor'     # Windows window/app usage tracking (Windows only)
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'Lab Server Monitoring Team'
__description__ = 'Comprehensive monitoring and AI analytics for lab server environments'
