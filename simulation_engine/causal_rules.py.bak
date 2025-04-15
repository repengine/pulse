"""
causal_rules.py

Defines the core causal rule engine for Pulse v3.5.
Each rule mutates the worldstate based on symbolic overlays,
external variables, or simulation memory.

This version includes stub rules for symbolic/capital interactions
and placeholder logic for signal integration.

Author: Pulse v3.5
"""

from worldstate import WorldState
from state_mutation import adjust_overlay, update_numeric_variable, adjust_capital


def apply_causal_rules(state: WorldState):
    """
    Core rule engine — executes symbolic and capital-related rules.
    Designed to run once per turn via `turn_engine.py`.
    """

    # Example symbolic-interaction rule
    if state.overlays.hope > 0.7 and state.overlays.fatigue < 0.3:
        adjust_overlay(state, "trust", +0.02)
        update_numeric_variable(state, "hope_surge_count", +1, max_val=100)

    # Example feedback rule — fatigue builds if despair lingers
    if state.overlays.despair > 0.6:
        adjust_overlay(state, "fatigue", +0.015)

    # Symbolic decay risk — despair suppresses hope
    if state.overlays.despair > 0.5:
        adjust_overlay(state, "hope", -0.01)

    # Symbolic-capital interaction — if trust high, NVDA exposure increases
    if state.overlays.trust > 0.6:
        adjust_capital(state, "nvda", +500)

    # Safety check: reduce IBIT exposure if fatigue is overwhelming
    if state.overlays.fatigue > 0.75:
        adjust_capital(state, "ibit", -250)

    # Stub for future: add rules here for external signal response
    # e.g., Reddit narrative triggers, VIX spikes, etc.
