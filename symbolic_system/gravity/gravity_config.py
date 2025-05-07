"""
gravity_config.py

Configuration parameters for the Symbolic Gravity Fabric system.

This module provides configuration management for the residual gravity engine,
symbolic pillar system, and overall fabric behavior.

Author: Pulse v3.5
"""

from typing import Dict, Any, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)


class ResidualGravityConfig:
    """
    Configuration for the Residual Gravity Engine and associated components.
    
    Attributes
    ----------
    lambda_ : float
        Global gravity strength parameter (0 ≤ λ ≤ 1)
    regularization : float
        L2 regularization coefficient to prevent weight blow-up
    learning_rate : float
        Learning rate for SGD updates
    momentum : float
        Momentum term for smoother convergence
    enable_momentum : bool
        Whether to use momentum in weight updates
    circuit_breaker_threshold : float
        Maximum allowed gravity correction before circuit breaker trips
    max_correction : float
        Maximum allowed correction magnitude
    enable_adaptive_lambda : bool
        Whether to dynamically adjust lambda based on system state
    enable_weight_pruning : bool
        Whether to prune small weights to prevent overfitting
    weight_pruning_threshold : float
        Minimum weight magnitude to keep during pruning
    fragility_threshold : float
        RMS weight threshold for considering the system fragile
    """
    
    def __init__(self, **kwargs):
        """
        Initialize configuration with default values or provided kwargs.
        
        Parameters
        ----------
        **kwargs : dict
            Configuration parameters to override defaults
        """
        # Default configuration
        self.lambda_ = 0.25
        self.regularization = 1e-3
        self.learning_rate = 1e-2
        self.momentum = 0.9
        self.enable_momentum = True
        self.circuit_breaker_threshold = 5.0
        self.max_correction = 0.5
        self.enable_adaptive_lambda = True
        self.enable_weight_pruning = True
        self.weight_pruning_threshold = 1e-4
        self.fragility_threshold = 3.0
        self.symbolic_decay_rate = 0.01
        
        # Additional configuration for symbolic pillars
        self.decay_rate = 0.01
        self.interaction_strength = 0.1
        self.log_level = "INFO"
        
        # Pillar specific configurations
        self.pillar_config = {
            "default_max_capacity": 1.0,
            "default_growth_rate": 0.05,
            "enable_interactions": True,
            "auto_register_pillars": True
        }
        
        # Feature flags
        self.features = {
            "enable_visualization": True,
            "enable_history_tracking": True,
            "enable_circuit_breaker_alerts": True,
            "enable_metric_logging": True
        }
        
        # Override defaults with provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation of configuration
        """
        result = {}
        
        # Add all attributes that don't start with _
        for key in dir(self):
            if not key.startswith('_') and not callable(getattr(self, key)):
                result[key] = getattr(self, key)
                
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ResidualGravityConfig':
        """
        Create configuration from dictionary.
        
        Parameters
        ----------
        config_dict : Dict[str, Any]
            Dictionary with configuration parameters
            
        Returns
        -------
        ResidualGravityConfig
            Configuration instance
        """
        return cls(**config_dict)
    
    def save(self, path: str) -> None:
        """
        Save configuration to file.
        
        Parameters
        ----------
        path : str
            Path to save file
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load(cls, path: str) -> 'ResidualGravityConfig':
        """
        Load configuration from file.
        
        Parameters
        ----------
        path : str
            Path to load file from
            
        Returns
        -------
        ResidualGravityConfig
            Configuration instance
        """
        with open(path, 'r') as f:
            config_dict = json.load(f)
            
        return cls.from_dict(config_dict)


# Default configuration instance
default_config = ResidualGravityConfig()


def get_config() -> ResidualGravityConfig:
    """
    Get the current configuration, possibly from environment settings.
    
    Returns
    -------
    ResidualGravityConfig
        Configuration instance
    """
    # Check if config should be loaded from file
    config_path = os.environ.get('PULSE_GRAVITY_CONFIG')
    if config_path and os.path.exists(config_path):
        try:
            return ResidualGravityConfig.load(config_path)
        except Exception as e:
            logger.warning(f"Error loading gravity config from {config_path}: {e}")
            
    # Return default configuration
    return default_config