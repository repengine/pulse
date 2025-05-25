"""
Centralized configuration constants and runtime flags for Pulse.
- All simulation constants and toggles are defined here for maintainability.
- Add new config values here to avoid hardcoding in modules.
- For environment- or scenario-specific overrides, see config/simulation_config.yaml.
"""

from typing import Dict, Any
import os
import yaml
import json

# Import PATHS for dynamic path management
try:
    from core.path_registry import PATHS
except ImportError:
    PATHS = {}

# --- Trace output directory ---
TRACE_OUTPUT_DIR = PATHS.get("TRACE_OUTPUT_DIR", "logs/traces")

# Path to the main configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "default_config.json")

# --- Simulation settings ---
DEFAULT_DECAY_RATE: float = 0.1  # Default decay rate for symbolic overlays
MAX_SIMULATION_FORKS: int = 1000  # Controls fork depth for forecasts

# --- Thresholds (load from JSON if available, else fallback) ---
THRESHOLD_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "thresholds.json")


def load_thresholds():
    if os.path.exists(THRESHOLD_CONFIG_PATH):
        with open(THRESHOLD_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_thresholds(thresholds):
    with open(THRESHOLD_CONFIG_PATH, "w") as f:
        json.dump(thresholds, f, indent=2)


_thresholds = load_thresholds()
# Reduced confidence threshold to allow more forecasts through during early development
CONFIDENCE_THRESHOLD = _thresholds.get("CONFIDENCE_THRESHOLD", 0.4)  # Lowered from 0.6
DEFAULT_FRAGILITY_THRESHOLD = _thresholds.get("DEFAULT_FRAGILITY_THRESHOLD", 0.7)


def update_threshold(name, value):
    _thresholds[name] = value
    save_thresholds(_thresholds)
    globals()[name] = value


# Ensure the updated threshold is saved to the JSON file
# if (
#     "CONFIDENCE_THRESHOLD" not in _thresholds
#     or _thresholds["CONFIDENCE_THRESHOLD"] != 0.4
# ):
#     _thresholds["CONFIDENCE_THRESHOLD"] = 0.4
#     save_thresholds(_thresholds)

# --- Module toggles (global boolean flags to enable/disable key systems) ---
MODULES_ENABLED: Dict[str, bool] = {
    "symbolic_overlay": True,
    "forecast_tracker": True,
    "rule_engine": True,
    "memory_guardian": True,  # <-- Enabled for forecast memory
    "estimate_missing_variables": False,
}

# --- Feature pipelines configuration ---
FEATURE_PIPELINES: Dict[str, Any] = {
    "market_data": {
        "raw_loader": "learning.output_data_reader.load_market_data",
        "transform": "learning.transforms.data_pipeline.preprocess_pipeline",
    },
    "social_data": {
        "raw_loader": "learning.output_data_reader.load_social_data",
        "transform": "learning.transforms.basic_transforms.sentiment_score",
    },
    "ecological_data": {
        "raw_loader": "learning.output_data_reader.load_ecological_data",
        "transform": "learning.transforms.basic_transforms.lag_features",
    },
    "market_rolling_mean": {
        "raw_loader": "learning.output_data_reader.load_market_data",
        "transform": "learning.transforms.rolling_features.rolling_mean_feature",
    },
}

# --- Ensemble & AI forecasting settings ---
AI_FORECAST_ENABLED: bool = True
ENSEMBLE_WEIGHTS: Dict[str, float] = {"simulation": 0.7, "ai": 0.3}

# --- Global toggle for symbolic overlays ---
USE_SYMBOLIC_OVERLAYS = True

# --- Enhanced symbolic system configuration ---
# Master switch for the entire symbolic system
ENABLE_SYMBOLIC_SYSTEM = False

# Current system operation mode: "simulation", "retrodiction", "analysis", "forecasting"
CURRENT_SYSTEM_MODE = "simulation"

# Mode-specific symbolic processing settings
SYMBOLIC_PROCESSING_MODES = {
    "simulation": True,  # Enable in normal simulation runs
    "retrodiction": False,  # Disable in retrodiction training
    "analysis": True,  # Enable in analysis operations
    "forecasting": True,  # Enable in forecasting operations
}

# --- Trust and despair weights for capital/symbolic calculations ---
TRUST_WEIGHT: float = 1.0
DESPAIR_WEIGHT: float = 1.0

# --- Startup banner (displayed at launch) ---
STARTUP_BANNER: str = "\U0001f9e0 Starting Pulse v0.4..."

# --- Simulation run settings ---
ENABLE_TRACE_LOGGING = True


# --- ConfigLoader for YAML configs (legacy support) ---
class ConfigLoader:
    def __init__(self, config_dir="config"):
        self.config_dir = config_dir
        self.configs = {}

    def load_config(self, filename):
        path = os.path.join(self.config_dir, filename)
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
            self.configs[filename] = config
            return config
        except Exception as e:
            print(f"Error loading configuration from {path}: {e}")
            return {}

    def load_all_configs(self):
        try:
            for file in os.listdir(self.config_dir):
                if file.endswith(".yaml"):
                    self.load_config(file)
        except Exception as e:
            print(f"Error reading configuration directory {self.config_dir}: {e}")

    def get_config_value(self, filename, key, default=None):
        if filename not in self.configs:
            self.load_config(filename)
        config = self.configs.get(filename, {})
        return config.get(key, default)

    def reload_config(self, filename):
        if filename in self.configs:
            del self.configs[filename]
        return self.load_config(filename)


config_loader = ConfigLoader()


def get_config(filename, key=None, default=None):
    """
    Retrieve a config dictionary or a specific value from a YAML config file.
    If key is None, returns the whole config dict.
    """
    config = config_loader.load_config(filename)
    return config if key is None else config.get(key, default)


# --- Shadow Model Monitoring Configuration ---
SHADOW_MONITOR_CONFIG = {
    "enabled": True,
    "threshold_variance_explained": 0.35,  # Default 35%
    "window_steps": 10,  # Default window of 10 simulation steps
    "critical_variables": ["var1", "var2"],  # List of variable names to monitor
}

# --- Model registry for MLOps ---
MODEL_REGISTRY = {
    "symbolic_model": {
        "type": "symbolic",
        "path": "models/symbolic_model.pkl",
        "description": "Rule-based symbolic forecaster",
    },
    "statistical_model": {
        "type": "statistical",
        "path": "models/statistical_model.pkl",
        "description": "ARIMA/ETS statistical model",
    },
    "ml_model": {
        "type": "ml",
        "path": "models/ml_model.pt",
        "description": "LSTM/MLP neural network forecaster",
    },
}
