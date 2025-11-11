"""
AI Model Module - Machine Learning and Predictive Analytics

This module provides AI-powered capabilities for the Lab Server Monitoring Agent,
including anomaly detection, forecasting, and predictive analytics. It leverages
machine learning algorithms to identify patterns, predict outcomes, and provide
actionable insights from monitoring data.

Key Features:
- Anomaly detection using Isolation Forest algorithm
- Time series forecasting with ARIMA models
- Predictive analytics for user engagement
- Machine learning model training and evaluation
- Real-time prediction and scoring
- Model performance monitoring and optimization
- Integration with Elasticsearch for data storage

The module supports both supervised and unsupervised learning approaches,
enabling the system to learn from historical data and make intelligent
predictions about future events and user behavior.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta, timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

# Set up module-level logging
logger = logging.getLogger(__name__)

class AIModel:
    """
    AI-powered machine learning and predictive analytics system.
    
    This class provides comprehensive machine learning capabilities including
    anomaly detection, time series forecasting, and predictive analytics.
    It integrates with the monitoring system to provide intelligent insights
    and predictions based on historical data patterns.
    
    The AI system supports:
    - Unsupervised anomaly detection using Isolation Forest
    - Time series forecasting with ARIMA models
    - Predictive analytics for user engagement and behavior
    - Real-time scoring and prediction generation
    - Model performance monitoring and optimization
    - Integration with external data sources
    - Automated model retraining and updates
    
    All models are designed to work with time-series data and can be
    customized for specific monitoring and prediction tasks.
    """
    
    def __init__(self, contamination: float = 0.1, min_samples: int = 10):
        """
        Initialize the AI model system.
        
        Args:
            contamination (float): Expected proportion of anomalies in the data (0.0 to 1.0)
            min_samples (int): Minimum number of samples required for model training
        """
        # Configuration for machine learning models
        self.contamination = contamination
        self.min_samples = min_samples
        
        # Anomaly detection model
        # Isolation Forest for detecting outliers and anomalies in data
        self.anomaly_detector = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Time series forecasting models
        # Dictionary to store ARIMA models for different metrics
        self.forecasting_models: Dict[str, ARIMA] = {}
        # Model parameters and configuration for different time series
        self.model_configs: Dict[str, Dict[str, Any]] = {}
        
        # Data preprocessing and scaling
        # StandardScaler for normalizing numerical features
        self.scaler = StandardScaler()
        # Flag indicating if scaler has been fitted
        self.scaler_fitted = False
        
        # Model performance tracking
        # Performance metrics for anomaly detection
        self.anomaly_performance: Dict[str, float] = {}
        # Performance metrics for forecasting models
        self.forecasting_performance: Dict[str, Dict[str, float]] = {}
        # Model training history and metadata
        self.model_history: List[Dict[str, Any]] = []
        
        # Data storage and management
        # Training data for anomaly detection
        self.anomaly_training_data: List[float] = []
        # Time series data for forecasting
        self.time_series_data: Dict[str, List[Tuple[datetime, float]]] = {}
        
        logger.info("AI model system initialized with contamination: %.2f, min_samples: %d", 
                   contamination, min_samples)
    
    def train_anomaly_detector(self, data: List[float]) -> bool:
        """
        Train the anomaly detection model.
        
        Args:
            data (List[float]): Training data for anomaly detection
            
        Returns:
            bool: True if training successful, False otherwise
        """
        try:
            # Check if we have enough data for training
            if len(data) < self.min_samples:
                logger.warning("Insufficient data for training: %d samples (minimum: %d)", 
                              len(data), self.min_samples)
                return False
            
            # Convert data to numpy array and reshape for sklearn
            X = np.array(data).reshape(-1, 1)
            
            # Fit the standard scaler for data normalization
            X_scaled = self.scaler.fit_transform(X)
            self.scaler_fitted = True
            
            # Train the Isolation Forest model
            self.anomaly_detector.fit(X_scaled)
            
            # Store training data for future reference
            self.anomaly_training_data = data.copy()
            
            # Calculate and store model performance metrics
            self._evaluate_anomaly_detector(X_scaled)
            
            logger.info("Anomaly detection model trained successfully with %d samples", len(data))
            return True
            
        except Exception as e:
            logger.error("Error training anomaly detection model: %s", e)
            return False
    
    def detect_anomalies(self, data: List[float]) -> List[bool]:
        """
        Detect anomalies in the provided data.
        
        Args:
            data (List[float]): Data to analyze for anomalies
            
        Returns:
            List[bool]: List of boolean values indicating anomalies (True = anomaly)
        """
        try:
            # Check if model has been trained
            if not self.scaler_fitted:
                logger.warning("Anomaly detection model not trained yet")
                return [False] * len(data)
            
            # Convert data to numpy array and reshape
            X = np.array(data).reshape(-1, 1)
            
            # Scale the data using fitted scaler
            X_scaled = self.scaler.transform(X)
            
            # Predict anomalies (1 = normal, -1 = anomaly)
            predictions = self.anomaly_detector.predict(X_scaled)
            
            # Convert to boolean (True = anomaly, False = normal)
            anomalies = [pred == -1 for pred in predictions]
            
            logger.debug("Anomaly detection completed for %d data points", len(data))
            return anomalies
            
        except Exception as e:
            logger.error("Error detecting anomalies: %s", e)
            return [False] * len(data)
    
    def train_forecasting_model(self, metric_name: str, time_series_data: List[Tuple[datetime, float]], 
                               order: Tuple[int, int, int] = (1, 1, 1)) -> bool:
        """
        Train a time series forecasting model for a specific metric.
        
        Args:
            metric_name (str): Name of the metric to forecast
            time_series_data (List[Tuple[datetime, float]]): Time series data as (timestamp, value) pairs
            order (Tuple[int, int, int]): ARIMA model order (p, d, q)
            
        Returns:
            bool: True if training successful, False otherwise
        """
        try:
            # Check if we have enough data for training
            if len(time_series_data) < self.min_samples:
                logger.warning("Insufficient time series data for training %s: %d samples (minimum: %d)", 
                              metric_name, len(time_series_data), self.min_samples)
                return False
            
            # Sort data by timestamp
            sorted_data = sorted(time_series_data, key=lambda x: x[0])
            
            # Extract values and convert to numpy array
            values = np.array([value for _, value in sorted_data])
            
            # Check for stationarity and difference if necessary
            if not self._is_stationary(values):
                logger.info("Data for %s is not stationary, applying differencing", metric_name)
                values = np.diff(values)
                # Adjust order for differenced data
                order = (order[0], order[1] + 1, order[2])
            
            # Create and fit ARIMA model
            model = ARIMA(values, order=order)
            fitted_model = model.fit()
            
            # Store the fitted model
            self.forecasting_models[metric_name] = fitted_model
            
            # Store model configuration
            self.model_configs[metric_name] = {
                'order': order,
                'original_length': len(time_series_data),
                'differenced': not self._is_stationary(np.array([value for _, value in sorted_data])),
                'training_timestamp': datetime.now(timezone.utc)
            }
            
            # Store time series data for future reference
            self.time_series_data[metric_name] = sorted_data.copy()
            
            # Evaluate model performance
            self._evaluate_forecasting_model(metric_name, values, fitted_model)
            
            logger.info("Forecasting model trained successfully for %s with order %s", metric_name, order)
            return True
            
        except Exception as e:
            logger.error("Error training forecasting model for %s: %s", metric_name, e)
            return False
    
    def forecast(self, metric_name: str, periods: int = 5) -> List[float]:
        """
        Generate forecasts for a specific metric.
        
        Args:
            metric_name (str): Name of the metric to forecast
            periods (int): Number of periods to forecast
            
        Returns:
            List[float]: Forecasted values for the specified periods
        """
        try:
            # Check if model exists for the metric
            if metric_name not in self.forecasting_models:
                logger.warning("No forecasting model found for metric: %s", metric_name)
                return []
            
            # Get the trained model
            model = self.forecasting_models[metric_name]
            
            # Generate forecast
            forecast_result = model.forecast(steps=periods)
            
            # Convert to list and handle differenced data
            forecast_values = forecast_result.tolist()
            
            # If data was differenced, integrate back to original scale
            if self.model_configs[metric_name].get('differenced', False):
                # Get the last value from original data for integration
                original_data = [value for _, value in self.time_series_data[metric_name]]
                last_value = original_data[-1] if original_data else 0
                
                # Integrate the differenced forecast
                integrated_forecast = [last_value]
                for value in forecast_values:
                    integrated_forecast.append(integrated_forecast[-1] + value)
                
                # Remove the first value (original last value) and return forecast
                forecast_values = integrated_forecast[1:]
            
            logger.debug("Generated %d-period forecast for %s", periods, metric_name)
            return forecast_values
            
        except Exception as e:
            logger.error("Error generating forecast for %s: %s", metric_name, e)
            return []
    
    def _is_stationary(self, data: np.ndarray) -> bool:
        """
        Check if time series data is stationary using Augmented Dickey-Fuller test.
        
        Args:
            data (np.ndarray): Time series data to test
            
        Returns:
            bool: True if data is stationary, False otherwise
        """
        try:
            # Perform Augmented Dickey-Fuller test
            result = adfuller(data)
            
            # Extract p-value from test result
            p_value = result[1]
            
            # Data is stationary if p-value < 0.05
            return p_value < 0.05
            
        except Exception as e:
            logger.error("Error checking stationarity: %s", e)
            # Assume non-stationary if test fails
            return False
    
    def _evaluate_anomaly_detector(self, X_scaled: np.ndarray) -> None:
        """
        Evaluate the performance of the anomaly detection model.
        
        Args:
            X_scaled (np.ndarray): Scaled training data
        """
        try:
            # Get predictions on training data
            predictions = self.anomaly_detector.predict(X_scaled)
            
            # Calculate anomaly ratio
            anomaly_ratio = np.sum(predictions == -1) / len(predictions)
            
            # Store performance metrics
            self.anomaly_performance = {
                'anomaly_ratio': float(anomaly_ratio),
                'total_samples': len(predictions),
                'anomalies_detected': int(np.sum(predictions == -1)),
                'training_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug("Anomaly detector evaluation: anomaly ratio: %.3f", anomaly_ratio)
            
        except Exception as e:
            logger.error("Error evaluating anomaly detector: %s", e)
    
    def _evaluate_forecasting_model(self, metric_name: str, values: np.ndarray, 
                                   model: ARIMA) -> None:
        """
        Evaluate the performance of a forecasting model.
        
        Args:
            metric_name (str): Name of the metric being evaluated
            values (np.ndarray): Training data values
            model (ARIMA): Fitted ARIMA model
        """
        try:
            # Get model predictions on training data
            predictions = model.predict(start=0, end=len(values)-1)
            
            # Calculate performance metrics
            mse = mean_squared_error(values, predictions)
            mae = mean_absolute_error(values, predictions)
            rmse = np.sqrt(mse)
            
            # Store performance metrics
            self.forecasting_performance[metric_name] = {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'training_samples': len(values),
                'training_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug("Forecasting model evaluation for %s: RMSE: %.4f, MAE: %.4f", 
                        metric_name, rmse, mae)
            
        except Exception as e:
            logger.error("Error evaluating forecasting model for %s: %s", metric_name, e)
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of all AI models and their performance.
        
        Returns:
            Dict[str, Any]: Summary of AI models, performance, and configuration
        """
        try:
            return {
                'anomaly_detection': {
                    'model_type': 'IsolationForest',
                    'contamination': self.contamination,
                    'performance': self.anomaly_performance,
                    'training_samples': len(self.anomaly_training_data)
                },
                'forecasting_models': {
                    metric: {
                        'model_type': 'ARIMA',
                        'config': self.model_configs[metric],
                        'performance': self.forecasting_performance.get(metric, {}),
                        'training_samples': len(self.time_series_data.get(metric, []))
                    }
                    for metric in self.forecasting_models.keys()
                },
                'total_models': len(self.forecasting_models) + 1,  # +1 for anomaly detector
                'model_history': self.model_history[-10:] if self.model_history else []  # Last 10 entries
            }
            
        except Exception as e:
            logger.error("Error generating model summary: %s", e)
            return {}
    
    def clear_models(self) -> None:
        """Clear all trained models and training data."""
        self.forecasting_models.clear()
        self.model_configs.clear()
        self.anomaly_training_data.clear()
        self.time_series_data.clear()
        self.anomaly_performance.clear()
        self.forecasting_performance.clear()
        self.model_history.clear()
        self.scaler_fitted = False
        logger.info("All AI models and training data cleared")


__all__ = ["AIModel"]
