"""
pulse_config.py

Centralized configuration constants and runtime flags for Pulse.

- All simulation constants and toggles are defined here for maintainability.
- Add new config values here to avoid hardcoding in modules.
- For environment- or scenario-specific overrides, see config/simulation_config.yaml.
"""
from typing import Dict
from core.path_registry import PATHS
import json
import os

TRACE_OUTPUT_DIR = PATHS.get("TRACE_OUTPUT_DIR", "logs/traces")

# Simulation settings
DEFAULT_DECAY_RATE: float = 0.1  #: Default decay rate for symbolic overlays
MAX_SIMULATION_FORKS: int = 1000  #: Controls fork depth for forecasts

THRESHOLD_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "thresholds.json")

def load_thresholds():
    if os.path.exists(THRESHOLD_CONFIG_PATH):
        with open(THRESHOLD_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_thresholds(thresholds):
    with open(THRESHOLD_CONFIG_PATH, "w") as f:
        json.dump(thresholds, f, indent=2)

# Load at module import
_thresholds = load_thresholds()
CONFIDENCE_THRESHOLD = _thresholds.get("CONFIDENCE_THRESHOLD", 0.6)
DEFAULT_FRAGILITY_THRESHOLD = _thresholds.get("DEFAULT_FRAGILITY_THRESHOLD", 0.7)

def update_threshold(name, value):
    _thresholds[name] = value
    save_thresholds(_thresholds)
    globals()[name] = value

# Module toggles (global boolean flags to enable/disable key systems)
MODULES_ENABLED: Dict[str, bool] = {
    "symbolic_overlay": True,           # Enable symbolic overlay logic
    "forecast_tracker": True,           # Enable forecast tracking
    "rule_engine": True,                # Enable rule engine
    "memory_guardian": False,           # Enable memory guardian module
    "estimate_missing_variables": False,  # Estimate missing variables if True (safe by default)
}

# Global toggle for symbolic overlays
USE_SYMBOLIC_OVERLAYS = True

# Trust and despair weights for capital/symbolic calculations
TRUST_WEIGHT: float = 1.0  #: Weight for trust overlay in capital calculations
DESPAIR_WEIGHT: float = 1.0  #: Weight for despair overlay in capital calculations

# Startup banner (displayed at launch)
STARTUP_BANNER: str = "\U0001f9e0 Starting Pulse v0.4..."

# Simulation run settings
ENABLE_TRACE_LOGGING = True
#: Enable trace logging for audit trail
#: Set to False to disable trace logging for performance
# To add a new config value:
# - Add it here with a type annotation and comment
# - Import from core.pulse_config in your module
#
# For scenario/environment overrides, see config/simulation_config.yaml
