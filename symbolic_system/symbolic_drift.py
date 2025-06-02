"""
symbolic_drift.py

Detects and logs symbolic overlay drift within the simulation.
Drift is defined as rapid, unexpected, or contradictory changes in symbolic states
that may signal narrative collapse, forecast instability, or emotional incoherence.

Author: Pulse v3.5
"""

from engine.worldstate import WorldState
from symbolic_system.symbolic_utils import get_overlay_snapshot, symbolic_tension_score
from typing import Dict


def compute_overlay_deltas(
    prev: Dict[str, float], curr: Dict[str, float]
) -> Dict[str, float]:
    """
    Computes overlay value changes between turns.
    Adds robust type handling to ensure numeric operations are safe.
    """
    deltas = {}
    for k in prev:
        prev_val = prev.get(k, 0)
        curr_val = curr.get(k, 0)
        try:
            prev_val = float(prev_val) if prev_val is not None else 0.0
            curr_val = float(curr_val) if curr_val is not None else 0.0
            deltas[k] = round(curr_val - prev_val, 3)
        except (ValueError, TypeError):
            deltas[k] = 0.0
            # Optional: add logging here for debugging unexpected types
    return deltas


def detect_symbolic_drift(
    previous_state: WorldState,
    current_state: WorldState,
    tension_threshold: float = 0.2,
    delta_threshold: float = 0.25,
) -> Dict[str, float]:
    """
    Compares two WorldStates and detects overlay drift.

    Flags overlays where change exceeds delta_threshold or
    where symbolic tension increases rapidly.

    Returns dict of overlay deltas for analysis.
    """
    prev_overlay = get_overlay_snapshot(previous_state)
    curr_overlay = get_overlay_snapshot(current_state)
    deltas = compute_overlay_deltas(prev_overlay, curr_overlay)

    # Check for rapid overlay shifts
    for overlay, change in deltas.items():
        if abs(change) > delta_threshold:
            current_state.log_event(
                f"[DRIFT] Overlay '{overlay}' shifted by {change:.3f} in one turn (THRESH = {delta_threshold})"
            )

    # Check symbolic tension spike
    prev_tension = symbolic_tension_score(prev_overlay)
    curr_tension = symbolic_tension_score(curr_overlay)
    tension_delta = curr_tension - prev_tension

    if tension_delta > tension_threshold:
        current_state.log_event(
            f"[DRIFT] Symbolic tension increased by {tension_delta:.3f} → {curr_tension:.3f}"
        )

    return deltas
