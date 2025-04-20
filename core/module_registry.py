"""
module_registry.py

Tracks module states, versions, and toggle control for execution.

Each entry in MODULE_REGISTRY should have:
    - version (str): Module version string
    - enabled (bool): Whether the module is active

Provides helper functions for querying and updating module states.
"""
from typing import Dict, Any

MODULE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Core simulation engine
    "turn_engine": {"version": "v0.000", "enabled": True},
    "worldstate": {"version": "v0.001", "enabled": True},
    "decay_overlay": {"version": "v0.002", "enabled": True},
    "simulation_replayer": {"version": "v0.003", "enabled": False},
    "forecast_tracker": {"version": "v0.005", "enabled": True},
    "symbolic_memory": {"version": "v0.020", "enabled": True},
    "trust_engine": {"version": "v0.030", "enabled": False},
    # Add new modules here as needed for gating
}


def is_module_enabled(module_name: str) -> bool:
    """
    Check if a module is enabled in the registry.
    Args:
        module_name (str): The module key.
    Returns:
        bool: True if enabled, False otherwise.
    """
    return MODULE_REGISTRY.get(module_name, {}).get("enabled", False)


def set_module_enabled(module_name: str, enabled: bool) -> None:
    """
    Enable or disable a module in the registry.
    Args:
        module_name (str): The module key.
        enabled (bool): Desired enabled state.
    """
    if module_name in MODULE_REGISTRY:
        MODULE_REGISTRY[module_name]["enabled"] = enabled


def get_module_version(module_name: str) -> str:
    """
    Get the version string for a module.
    Args:
        module_name (str): The module key.
    Returns:
        str: Version string, or empty string if not found.
    """
    return MODULE_REGISTRY.get(module_name, {}).get("version", "")
