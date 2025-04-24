"""
state_mutation.py

Handles the mutation and update logic for WorldState variables, symbolic overlays, and capital exposure.
Supports safe, bounded updates from causal rules, decay logic, and external signal ingestion.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from typing import Any
from core.pulse_learning_log import log_learning_event
from datetime import datetime


def update_numeric_variable(state: WorldState, name: str, delta: float, min_val: float = 0.0, max_val: float = 1.0):
    """
    Increment or decrement a numeric variable safely within [min_val, max_val].
    Creates the variable if it doesn't exist.
    """
    current = state.get_variable(name, 0.0)
    updated = max(min(current + delta, max_val), min_val)
    state.update_variable(name, updated)
    state.log_event(f"Variable '{name}' changed by {delta:.3f} to {updated:.3f}")


def decay_overlay(state: WorldState, overlay: str, rate: float = 0.01):
    """
    Decays a symbolic overlay value slightly each turn.
    """
    current_value = getattr(state.overlays, overlay, None)
    if current_value is not None:
        new_value = max(0.0, current_value - rate)
        setattr(state.overlays, overlay, new_value)
        state.log_event(f"Overlay '{overlay}' decayed from {current_value:.3f} to {new_value:.3f}")
        log_learning_event("overlay_shift", {"overlay": overlay, "old_value": current_value, "new_value": new_value, "timestamp": datetime.utcnow().isoformat()})


def adjust_overlay(state: WorldState, overlay: str, delta: float):
    """
    Adjusts a symbolic overlay value safely between 0 and 1.
    """
    current_value = getattr(state.overlays, overlay, None)
    if current_value is not None:
        new_value = max(0.0, min(1.0, current_value + delta))
        setattr(state.overlays, overlay, new_value)
        state.log_event(f"Overlay '{overlay}' adjusted by {delta:.3f} to {new_value:.3f}")
        log_learning_event("overlay_shift", {"overlay": overlay, "old_value": current_value, "new_value": new_value, "timestamp": datetime.utcnow().isoformat()})


def adjust_capital(state: WorldState, asset: str, delta: float):
    """
    Modifies capital exposure for a given asset.
    """
    if hasattr(state.capital, asset):
        current = getattr(state.capital, asset)
        new_value = current + delta
        setattr(state.capital, asset, new_value)
        state.log_event(f"Capital exposure for '{asset}' changed by {delta:.2f} to {new_value:.2f}")
        log_learning_event("capital_shift", {"asset": asset, "old_value": current, "new_value": new_value, "timestamp": datetime.utcnow().isoformat()})
