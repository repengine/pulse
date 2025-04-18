"""
pulse_config.py

Centralized configuration constants and runtime flags for Pulse.
"""

# Simulation settings
DEFAULT_DECAY_RATE = 0.1
MAX_SIMULATION_FORKS = 1000
CONFIDENCE_THRESHOLD = 0.95
DEFAULT_FRAGILITY_THRESHOLD = 0.7

# Module toggles
MODULES_ENABLED = {
    "symbolic_overlay": True,
    "forecast_tracker": True,
    "rule_engine": True,
    "memory_guardian": False,
}

# Add new config constants here as needed

# Startup banner
STARTUP_BANNER = "🧠 Starting Pulse v0.4..."
