"""
Configuration Manager for Recursive Learning

Provides functionality for managing configuration settings for recursive learning.
This allows the conversational interface to persist user preferences and settings.
"""

import os
import json
import threading
from typing import Dict, Any
from pathlib import Path

# Thread-safe lock for configuration access
_config_lock = threading.RLock()

# Default configuration path
_CONFIG_PATH = Path("recursive_training/config/recursive_learning_config.json")

# Default configuration
_DEFAULT_CONFIG = {
    "variables": [
        "spx_close",
        "us_10y_yield",
        "wb_gdp_growth_annual",
        "wb_unemployment_total",
    ],
    "batch_size_days": 30,
    "max_workers": None,  # Auto-detect based on CPU cores
    "overlap_days": 5,
    "metrics_retention_days": 30,
    "trust_threshold": 0.7,
    "enable_visualizations": True,
}

# In-memory configuration cache
_config: Dict[str, Any] = None


def _ensure_config_dir():
    """Ensure the configuration directory exists"""
    os.makedirs(_CONFIG_PATH.parent, exist_ok=True)


def _load_config() -> Dict[str, Any]:
    """
    Load configuration from file, falling back to defaults if needed.

    Returns:
        Dictionary containing configuration
    """
    global _config

    if _config is not None:
        return _config

    with _config_lock:
        if not _CONFIG_PATH.exists():
            # If no config file exists, create one with default settings
            _ensure_config_dir()
            with open(_CONFIG_PATH, "w") as f:
                json.dump(_DEFAULT_CONFIG, f, indent=2)
            _config = dict(_DEFAULT_CONFIG)
            return _config

        try:
            with open(_CONFIG_PATH, "r") as f:
                loaded_config = json.load(f)

            # Merge with defaults to ensure all keys are present
            _config = dict(_DEFAULT_CONFIG)
            _config.update(loaded_config)
            return _config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return dict(_DEFAULT_CONFIG)


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.

    Returns:
        Dictionary containing configuration
    """
    return _load_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.

    Args:
        key: Configuration key
        default: Default value if the key doesn't exist

    Returns:
        Configuration value, or default if not found
    """
    config = _load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """
    Set a specific configuration value.

    Args:
        key: Configuration key
        value: Value to set
    """
    with _config_lock:
        config = _load_config()
        config[key] = value


def save_config() -> None:
    """
    Save the current configuration to file.
    """
    with _config_lock:
        if _config is None:
            _load_config()

        _ensure_config_dir()
        with open(_CONFIG_PATH, "w") as f:
            json.dump(_config, f, indent=2)


def reset_to_defaults() -> Dict[str, Any]:
    """
    Reset configuration to default values.

    Returns:
        Dictionary containing the reset configuration
    """
    with _config_lock:
        _config = dict(_DEFAULT_CONFIG)
        save_config()
        return _config
