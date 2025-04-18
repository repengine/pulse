"""
module_registry.py

Tracks module states, versions, and toggle control for execution.
"""

MODULE_REGISTRY = {
    "turn_engine": {"version": "v0.000", "enabled": True},
    "worldstate": {"version": "v0.001", "enabled": True},
    "decay_overlay": {"version": "v0.002", "enabled": True},
    "simulation_replayer": {"version": "v0.003", "enabled": False},
    "forecast_tracker": {"version": "v0.005", "enabled": True},
    "symbolic_memory": {"version": "v0.020", "enabled": True},
    "pulse_mirror_core": {"version": "v0.030", "enabled": False},
}

# Add new modules here as needed for gating
