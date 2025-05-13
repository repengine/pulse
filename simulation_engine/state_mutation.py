"""
state_mutation.py

Handles the mutation and update logic for WorldState variables, symbolic overlays, and capital exposure.
Supports safe, bounded updates from causal rules, decay logic, and external signal ingestion.

This module is a core component of the Pulse simulation engine, responsible for
making controlled changes to the WorldState object during simulation turns. All
changes are validated, bounded, and logged for traceability.

Functions:
    update_numeric_variable: Update a variable with bounds checking
    decay_overlay: Apply gradual decay to symbolic overlays
    adjust_overlay: Modify symbolic overlays with bounds checking
    adjust_capital: Update capital exposure values

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from typing import Any, Union, Optional
from core.pulse_learning_log import log_learning_event
from datetime import datetime, timezone
from symbolic_system.context import is_symbolic_enabled


def update_numeric_variable(
    state: WorldState, 
    name: str, 
    delta: float, 
    min_val: float = 0.0, 
    max_val: float = 1.0
) -> float:
    """
    Increment or decrement a numeric variable safely within bounds [min_val, max_val].
    Creates the variable if it doesn't exist.
    
    Args:
        state: The WorldState object to modify
        name: Name of the variable to update
        delta: Amount to change the variable (positive or negative)
        min_val: Minimum allowed value (default: 0.0)
        max_val: Maximum allowed value (default: 1.0)
        
    Returns:
        float: The new value of the variable after update
        
    Example:
        >>> new_value = update_numeric_variable(state, "inflation_index", +0.03, min_val=0.0, max_val=2.0)
        >>> print(f"Inflation index is now {new_value}")
    """
    current = getattr(state.variables, name, 0.0)
    updated = max(min(current + delta, max_val), min_val)
    setattr(state.variables, name, updated)
    state.log_event(f"Variable '{name}' changed by {delta:.3f} to {updated:.3f}")
    return updated


def decay_overlay(state: WorldState, overlay: str, rate: float = 0.01) -> Optional[float]:
    """
    Decays a symbolic overlay value slightly each turn.
    This represents the natural return to baseline for emotional states
    when no external forces are acting on them.
    
    Args:
        state: The WorldState object to modify
        overlay: Name of the overlay to decay (e.g., "hope", "trust", "despair")
        rate: Decay rate per turn (default: 0.01)
        
    Returns:
        float: The new overlay value after decay, or None if the overlay doesn't exist
        
    Example:
        >>> new_value = decay_overlay(state, "hope", rate=0.02)
        >>> print(f"Hope decayed to {new_value}")
    """
    current_value = getattr(state.overlays, overlay, None)
    if current_value is not None:
        new_value = max(0.0, current_value - rate)
        setattr(state.overlays, overlay, new_value)
        state.log_event(f"Overlay '{overlay}' decayed from {current_value:.3f} to {new_value:.3f}")
        log_learning_event("overlay_shift", {
            "overlay": overlay, 
            "old_value": current_value, 
            "new_value": new_value,
            "shift_type": "decay",
            "rate": rate,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return new_value
    return None


def adjust_overlay(state: WorldState, overlay: str, delta: float) -> Optional[float]:
    """
    Adjusts a symbolic overlay value safely between 0 and 1.
    This is used for rule-based or event-triggered emotional state changes.
    If symbolic processing is disabled, this is a no-op.
    
    Args:
        state: The WorldState object to modify
        overlay: Name of the overlay to adjust (e.g., "hope", "trust", "despair")
        delta: Amount to change the overlay (positive or negative)
        
    Returns:
        float: The new overlay value after adjustment, or None if the overlay doesn't exist
        
    Example:
        >>> new_value = adjust_overlay(state, "trust", +0.1)
        >>> print(f"Trust increased to {new_value}")
    """
    # Import directly inside function to get the freshest values
    # Do not use is_symbolic_enabled() to ensure we get the actual current value
    from core.pulse_config import ENABLE_SYMBOLIC_SYSTEM, CURRENT_SYSTEM_MODE, SYMBOLIC_PROCESSING_MODES
    
    # Skip all processing if symbolic system is disabled globally - highest priority check
    if not ENABLE_SYMBOLIC_SYSTEM:
        return getattr(state.overlays, overlay, None)
    
    # Skip if disabled for current mode
    if CURRENT_SYSTEM_MODE in SYMBOLIC_PROCESSING_MODES and not SYMBOLIC_PROCESSING_MODES.get(CURRENT_SYSTEM_MODE, True):
        return getattr(state.overlays, overlay, None)
    
    # Only proceed with overlay adjustment if symbolic processing is enabled
    current_value = getattr(state.overlays, overlay, None)
    if current_value is not None:
        new_value = max(0.0, min(1.0, current_value + delta))
        
        # Only update the value if symbolic processing is enabled
        setattr(state.overlays, overlay, new_value)
        
        # Determine if we're in minimal processing mode
        minimal_processing = CURRENT_SYSTEM_MODE == "retrodiction" and SYMBOLIC_PROCESSING_MODES.get("retrodiction", False)
        
        # Only log events if we're not in minimal processing mode
        if not minimal_processing:
            state.log_event(f"Overlay '{overlay}' adjusted by {delta:.3f} to {new_value:.3f}")
            log_learning_event("overlay_shift", {
                "overlay": overlay,
                "old_value": current_value,
                "new_value": new_value,
                "shift_type": "adjustment",
                "delta": delta,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return new_value
    return None


def adjust_capital(state: WorldState, asset: str, delta: float) -> Optional[float]:
    """
    Modifies capital exposure for a given asset.
    Unlike overlays, capital values are not bounded and can be negative
    (representing short positions or debt).
    
    Args:
        state: The WorldState object to modify
        asset: Name of the capital asset to adjust (e.g., "nvda", "msft", "cash")
        delta: Amount to change the capital (positive or negative)
        
    Returns:
        float: The new capital value after adjustment, or None if the asset doesn't exist
        
    Example:
        >>> new_value = adjust_capital(state, "nvda", +500.0)
        >>> print(f"NVDA position increased to ${new_value:.2f}")
    """
    if hasattr(state.capital, asset):
        current = getattr(state.capital, asset)
        new_value = current + delta
        setattr(state.capital, asset, new_value)
        state.log_event(f"Capital exposure for '{asset}' changed by {delta:.2f} to {new_value:.2f}")
        log_learning_event("capital_shift", {
            "asset": asset, 
            "old_value": current, 
            "new_value": new_value,
            "delta": delta,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return new_value
    return None
