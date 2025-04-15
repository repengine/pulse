"""
turn_engine.py

Controls the simulation loop at the turn level. Each turn includes:
- Symbolic decay
- Causal rule execution (stubbed here)
- Capital adjustments (if any)
- Logging and state snapshotting

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import decay_overlay
from typing import Callable, Optional


def run_turn(
    state: WorldState,
    rule_fn: Optional[Callable[[WorldState], None]] = None,
    decay_rate: float = 0.01,
):
    """
    Runs a single simulation turn.

    Parameters:
        state (WorldState): the active worldstate object
        rule_fn (Callable): optional causal rule engine function
        decay_rate (float): symbolic overlay decay rate
    """
    state.increment_turn()

    # Apply decay to all symbolic overlays
    for overlay_name in ["hope", "despair", "rage", "fatigue", "trust"]:
        decay_overlay(state, overlay_name, rate=decay_rate)

    # Execute causal rules, if provided
    if rule_fn:
        rule_fn(state)

    # Optionally: insert fork tagging, forecast logging, etc.
    state.log_event(f"Turn {state.turn} completed.")
