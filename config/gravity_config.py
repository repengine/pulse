"""
Gravity Configuration Module

This module centralizes all constants related to the Residual-Gravity Overlay system.
It provides configuration parameters that control the behavior of the gravity-based
calculations, adaptations, and threshold values for various operational aspects.
"""

import logging

# Default logging level
DEFAULT_LOGGING_LEVEL = logging.INFO  # Default logging level for gravity components

# Core gravity parameters
DEFAULT_LAMBDA = 0.25  # Global gravity strength parameter
DEFAULT_REGULARIZATION = 1e-3  # L2 regularization coefficient
DEFAULT_LEARNING_RATE = 1e-2  # Learning rate for SGD updates
DEFAULT_MOMENTUM = 0.9  # Momentum term for smoother convergence

# Safety thresholds and limits
DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 5.0  # Threshold for limiting extreme corrections
DEFAULT_MAX_CORRECTION = 0.5  # Maximum allowed correction magnitude
DEFAULT_FRAGILITY_THRESHOLD = 3.0  # Threshold for fragility calculation
CRITICAL_MAX_WEIGHT_THRESHOLD = 100.0  # Critical threshold for maximum weight
UNHEALTHY_RMS_WEIGHT_THRESHOLD = 10.0  # Unhealthy threshold for RMS weight

# Feature flags
DEFAULT_ENABLE_ADAPTIVE_LAMBDA = True  # Flag for dynamic lambda adjustment
DEFAULT_ENABLE_WEIGHT_PRUNING = True  # Flag for weight pruning feature
DEFAULT_WEIGHT_PRUNING_THRESHOLD = 1e-4  # Threshold for pruning small weights

# Shadow Model Trigger Configuration
DEFAULT_ENABLE_SHADOW_MODEL_TRIGGER = True  # Enable shadow model trigger by default
DEFAULT_SHADOW_MODEL_VARIANCE_THRESHOLD = 0.30  # Threshold for variance explained to trigger review
DEFAULT_SHADOW_MODEL_WINDOW_SIZE = 100  # Size of the rolling window for residual tracking
DEFAULT_SHADOW_MODEL_MIN_TRIGGER_SAMPLES = 30  # Minimum samples required before variance check
DEFAULT_SHADOW_MODEL_MIN_CAUSAL_VARIANCE = 1e-6  # Minimum variance in causal residuals to avoid division by zero

# Contributor tracking
SIGNIFICANT_CONTRIBUTOR_THRESHOLD = 0.001  # For tracking significant gravity contributors

# Adaptive lambda configuration
MIN_LAMBDA_SCALE_FACTOR = 0.1  # Minimum scaling for adaptive lambda
CIRCUIT_BREAKER_LAMBDA_REDUCTION = 0.5  # Lambda reduction when circuit breaker trips

# Adaptive lambda parameters
DEFAULT_ADAPTIVE_LAMBDA_MIN = 0.01  # Minimum value for adaptive lambda
DEFAULT_ADAPTIVE_LAMBDA_MAX = 1.0  # Maximum value for adaptive lambda
DEFAULT_ADAPTIVE_LAMBDA_WINDOW_SIZE = 20  # Window size for adaptive lambda calculation
DEFAULT_ADAPTIVE_LAMBDA_RESIDUAL_THRESHOLD_HIGH = 0.5  # Upper threshold for increasing lambda
DEFAULT_ADAPTIVE_LAMBDA_RESIDUAL_THRESHOLD_LOW = 0.1  # Lower threshold for decreasing lambda
DEFAULT_ADAPTIVE_LAMBDA_INCREASE_FACTOR = 1.05  # Factor to increase lambda by
DEFAULT_ADAPTIVE_LAMBDA_DECREASE_FACTOR = 0.95  # Factor to decrease lambda by

# Fragility calculation weights
FRAGILITY_RMS_WEIGHT = 0.5  # Weight for RMS factor in fragility calculation
FRAGILITY_VOLATILITY_WEIGHT = 0.3  # Weight for volatility in fragility calculation
FRAGILITY_BREAKER_WEIGHT = 0.2  # Weight for circuit breaker in fragility calculation
MAX_CIRCUIT_BREAKER_TRIPS = 10  # Normalization factor for breaker trips

# Warning thresholds
WARNING_CIRCUIT_BREAKER_TRIPS = 5  # Warning threshold for circuit breaker trips
WARNING_FRAGILITY_THRESHOLD = 0.8  # Warning threshold for fragility

# Stagnation and efficiency check parameters
STAGNANT_WEIGHT_UPDATES = 100  # Minimum updates for stagnant weight check
STAGNANT_WEIGHT_RMS_THRESHOLD = 0.01  # RMS threshold for stagnant weights
LOW_CORRECTION_EFFICIENCY_THRESHOLD = 0.3  # Threshold for low correction efficiency
MIN_UPDATES_FOR_EFFICIENCY_CHECK = 20  # Minimum updates for correction efficiency check

# EWMA (Exponentially Weighted Moving Average) configuration
DEFAULT_EWMA_SPAN = 30.0  # Span parameter for EWMA decay of impact matrix (alpha = 2/(span+1))