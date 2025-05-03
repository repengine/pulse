"""
overlays.py

Defines the symbolic overlay system for Pulse v3.5.
Overlays represent latent emotional-sentiment variables within the simulation:
Hope, Despair, Rage, Fatigue, Trust.

This module provides centralized logic to access, normalize, and modulate overlay interactions,
enabling coherent symbolic behavior across modules.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_overlay
from typing import List, Dict, Optional
from core.pulse_config import MODULES_ENABLED

# Import optimization utilities
from symbolic_system.optimization import (
    lazy_symbolic,
    cached_symbolic,
    training_optimized,
    get_operation_level
)

OVERLAY_NAMES = getattr(__import__('core.pulse_config'), 'OVERLAY_NAMES', ["hope", "despair", "rage", "fatigue", "trust"])


@lazy_symbolic
def get_overlay_value(state: WorldState, name: str) -> float:
    """
    Returns the current value of a symbolic overlay.
    """
    return getattr(state.overlays, name, 0.0)


@lazy_symbolic
def is_overlay_dominant(state: WorldState, name: str, threshold: float = 0.65) -> bool:
    """
    Checks if a symbolic overlay is dominant.
    """
    return get_overlay_value(state, name) >= threshold


@lazy_symbolic
def boost_overlay(state: WorldState, name: str, amount: float = 0.02):
    """
    Boost a symbolic overlay moderately.
    """
    adjust_overlay(state, name, amount)


@lazy_symbolic
def suppress_overlay(state: WorldState, name: str, amount: float = 0.02):
    """
    Suppress a symbolic overlay moderately.
    """
    adjust_overlay(state, name, -amount)


@lazy_symbolic
def reinforce_synergy(state: WorldState, trigger: str, affected: str, factor: float = 0.01):
    """
    Symbolic rule: when trigger overlay is high, affected overlay strengthens.
    Example: High hope reinforces trust.
    """
    if is_overlay_dominant(state, trigger):
        adjust_overlay(state, affected, factor)
        state.log_event(f"Symbolic synergy: {trigger} boosted {affected} by {factor:.3f}")


@training_optimized(default_value=None)
def apply_overlay_interactions(state: WorldState):
    """
    Defines basic symbolic overlay interactions.
    Called once per turn in `turn_engine.py` or via rule engine.
    
    This function has optimized behavior in different modes:
    - In 'full' mode: All interactions are applied
    - In 'minimal' mode: Only essential interactions are applied
    - In 'none' mode: No interactions are applied (returns None)
    """
    # Determine operation level based on current mode
    operation_level = get_operation_level()
    
    # Skip processing entirely if in 'none' operation level
    if operation_level == "none":
        return None
    
    # Use simplified processing in 'minimal' mode (for training/retrodiction)
    if operation_level == "minimal":
        # Apply only the most critical interactions with minimal logging
        if get_overlay_value(state, "hope") >= 0.7:
            adjust_overlay(state, "trust", 0.01)
        if get_overlay_value(state, "despair") >= 0.7:
            adjust_overlay(state, "fatigue", 0.01)
        return

    # Full processing for normal simulation mode
    # Hope boosts Trust, unless countered by Rage
    reinforce_synergy(state, "hope", "trust", factor=0.01)
    if is_overlay_dominant(state, "rage"):
        suppress_overlay(state, "trust", amount=0.015)

    # Despair reinforces Fatigue
    reinforce_synergy(state, "despair", "fatigue", factor=0.015)

    # Fatigue suppresses Hope
    if is_overlay_dominant(state, "fatigue"):
        suppress_overlay(state, "hope", amount=0.02)


@cached_symbolic(ttl_seconds=300)
def get_overlay_summary(state: WorldState) -> Dict[str, Dict[str, float]]:
    """
    Generate a summary of the current overlay state with 
    categorization of dominant emotions.
    
    This is a potentially expensive operation that benefits from caching.
    
    Returns:
        Dict with overlay summary information
    """
    summary = {
        "dominant": {},
        "moderate": {},
        "suppressed": {}
    }
    
    for name in OVERLAY_NAMES:
        value = get_overlay_value(state, name)
        if value >= 0.65:
            summary["dominant"][name] = value
        elif value >= 0.35:
            summary["moderate"][name] = value
        else:
            summary["suppressed"][name] = value
            
    return summary
