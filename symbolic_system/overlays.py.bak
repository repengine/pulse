"""
overlays.py

Defines the symbolic overlay system for Pulse v3.5.
Overlays represent latent emotional-sentiment variables within the simulation:
Hope, Despair, Rage, Fatigue, Trust.

This module provides centralized logic to access, normalize, and modulate overlay interactions,
enabling coherent symbolic behavior across modules.

Author: Pulse v3.5
"""

from worldstate import WorldState
from state_mutation import adjust_overlay
from typing import List


OVERLAY_NAMES = ["hope", "despair", "rage", "fatigue", "trust"]


def get_overlay_value(state: WorldState, name: str) -> float:
    """
    Returns the current value of a symbolic overlay.
    """
    return getattr(state.overlays, name, 0.0)


def is_overlay_dominant(state: WorldState, name: str, threshold: float = 0.65) -> bool:
    """
    Checks if a symbolic overlay is dominant.
    """
    return get_overlay_value(state, name) >= threshold


def boost_overlay(state: WorldState, name: str, amount: float = 0.02):
    """
    Boost a symbolic overlay moderately.
    """
    adjust_overlay(state, name, amount)


def suppress_overlay(state: WorldState, name: str, amount: float = 0.02):
    """
    Suppress a symbolic overlay moderately.
    """
    adjust_overlay(state, name, -amount)


def reinforce_synergy(state: WorldState, trigger: str, affected: str, factor: float = 0.01):
    """
    Symbolic rule: when trigger overlay is high, affected overlay strengthens.
    Example: High hope reinforces trust.
    """
    if is_overlay_dominant(state, trigger):
        adjust_overlay(state, affected, factor)
        state.log_event(f"Symbolic synergy: {trigger} boosted {affected} by {factor:.3f}")


def apply_overlay_interactions(state: WorldState):
    """
    Defines basic symbolic overlay interactions.
    Called once per turn in `turn_engine.py` or via rule engine.
    """

    # Hope boosts Trust, unless countered by Rage
    reinforce_synergy(state, "hope", "trust", factor=0.01)
    if is_overlay_dominant(state, "rage"):
        suppress_overlay(state, "trust", amount=0.015)

    # Despair reinforces Fatigue
    reinforce_synergy(state, "despair", "fatigue", factor=0.015)

    # Fatigue suppresses Hope
    if is_overlay_dominant(state, "fatigue"):
        suppress_overlay(state, "hope", amount=0.02)
