"""
symbolic_utils.py

Utility functions for working with symbolic overlays in Pulse.
Supports normalization, overlay state summaries, symbolic tension scoring,
and fragility estimation.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from typing import Dict
import math


def get_overlay_snapshot(state: WorldState) -> Dict[str, float]:
    """
    Returns a dict of all symbolic overlay values.
    """
    return state.overlays.as_dict()


def normalize_overlay_vector(overlays: Dict[str, float]) -> Dict[str, float]:
    """
    Normalizes overlay values into a unit vector for comparison/scoring.
    """
    total = sum(overlays.values())
    if total == 0:
        return {k: 0.0 for k in overlays}
    return {k: v / total for k, v in overlays.items()}


def symbolic_tension_score(overlays: Dict[str, float]) -> float:
    """
    Calculates a tension score based on internal contradictions.
    High Hope + High Despair, or High Trust + High Rage, increases tension.
    """
    h, d, r, f, t = (
        overlays.get("hope", 0),
        overlays.get("despair", 0),
        overlays.get("rage", 0),
        overlays.get("fatigue", 0),
        overlays.get("trust", 0),
    )
    # Contradictory pairs (hope vs despair, rage vs trust)
    tension = (
        (h * d) +               # Hope-Despair conflict
        (r * t) +               # Rage-Trust conflict
        (f * h * 0.5)           # Fatigue suppressing Hope
    )
    return round(tension, 3)


def symbolic_fragility_index(state: WorldState) -> float:
    """
    Returns a symbolic fragility index for the current state.
    Based on tension + low Trust or spiking Rage/Despair.

    Range: 0.0 (stable) → 1.0+ (fragile)
    """
    overlays = get_overlay_snapshot(state)
    tension = symbolic_tension_score(overlays)
    fragility = tension

    # Amplify fragility if Trust is low while Despair or Rage are high
    if overlays.get("trust", 0.5) < 0.3:
        fragility += overlays.get("despair", 0) * 0.5
        fragility += overlays.get("rage", 0) * 0.4

    return round(min(fragility, 1.0), 3)


def compute_symbolic_drift_penalty(forecast: dict) -> float:
    """
    Returns a penalty (0–1) for symbolic fragmentation or arc volatility.
    """
    if forecast.get("symbolic_fragmented"):
        return 0.2  # Default penalty for fragmented forecast
    if forecast.get("arc_volatility_score", 0) > 0.7:
        return 0.1  # Penalty for unstable symbolic arcs
    return 0.0
