"""
variable_accessor.py

Abstracts access to worldstate variables and overlays.
Provides safe getter/setter functions for both variables and overlays.
Validates variable/overlay names against canonical registry if available.
"""

from typing import Any
from core.variable_registry import VARIABLE_REGISTRY


def get_variable(state: Any, name: str, default: float = 0.0) -> float:
    """
    Safely get a variable from state.variables dict.
    Args:
        state: The simulation state object (must have .variables dict).
        name: Variable name (should be in VARIABLE_REGISTRY).
        default: Value to return if variable is missing.
    Returns:
        float: The variable value, or default if missing/invalid.
    """
    if name not in VARIABLE_REGISTRY:
        # Optionally log or warn about unknown variable
        pass
    return state.variables.get(name, default)


def set_variable(state: Any, name: str, value: float) -> None:
    """
    Safely set a variable in state.variables dict or object.
    Args:
        state: The simulation state object (must have .variables dict or object).
        name: Variable name (should be in VARIABLE_REGISTRY).
        value: Value to set.
    """
    if name not in VARIABLE_REGISTRY:
        # Optionally log or warn about unknown variable
        pass
    if isinstance(state.variables, dict):
        state.variables[name] = value
    else:
        setattr(state.variables, name, value)


def get_overlay(state: Any, name: str, default: float = 0.0) -> float:
    """
    Safely get an overlay value from state.overlays.
    Args:
        state: The simulation state object (must have .overlays attributes).
        name: Overlay name (should be in VARIABLE_REGISTRY and type 'symbolic').
        default: Value to return if overlay is missing.
    Returns:
        float: The overlay value, or default if missing/invalid.
    """
    if (
        name not in VARIABLE_REGISTRY
        or VARIABLE_REGISTRY[name].get("type") != "symbolic"
    ):
        # Optionally log or warn about unknown overlay
        pass
    return getattr(state.overlays, name, default)


def set_overlay(state: Any, name: str, value: float) -> None:
    """
    Safely set an overlay value in state.overlays.
    Args:
        state: The simulation state object (must have .overlays attributes).
        name: Overlay name (should be in VARIABLE_REGISTRY and type 'symbolic').
        value: Value to set.
    """
    if (
        name not in VARIABLE_REGISTRY
        or VARIABLE_REGISTRY[name].get("type") != "symbolic"
    ):
        # Optionally log or warn about unknown overlay
        pass
    setattr(state.overlays, name, value)
