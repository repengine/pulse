"""
pulse_config.py

Centralized configuration constants and runtime flags for Pulse.

- All simulation constants and toggles are defined here for maintainability.
- Add new config values here to avoid hardcoding in modules.
- For environment- or scenario-specific overrides, see config/simulation_config.yaml.
"""
from typing import Dict

# Simulation settings
DEFAULT_DECAY_RATE: float = 0.1  #: Default decay rate for symbolic overlays
MAX_SIMULATION_FORKS: int = 1000  #: Controls fork depth for forecasts
CONFIDENCE_THRESHOLD: float = 0.95  #: Minimum score for trustable outputs
DEFAULT_FRAGILITY_THRESHOLD: float = 0.7  #: Default fragility threshold for symbolic overlays

# Module toggles (global boolean flags to enable/disable key systems)
MODULES_ENABLED: Dict[str, bool] = {
    "symbolic_overlay": True,           # Enable symbolic overlay logic
    "forecast_tracker": True,           # Enable forecast tracking
    "rule_engine": True,                # Enable rule engine
    "memory_guardian": False,           # Enable memory guardian module
    "estimate_missing_variables": False,  # Estimate missing variables if True (safe by default)
}

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
