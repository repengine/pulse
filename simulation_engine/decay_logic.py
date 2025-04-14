"""
decay_logic.py

Defines symbolic and variable decay patterns used during simulation turns.
This includes simple linear decay, exponential-style decay, and
future support for conditional symbolic erosion.

Author: Pulse v3.5
"""

from worldstate import WorldState


def linear_decay(value: float, rate: float = 0.01) -> float:
    """
    Reduces a value by a fixed rate, bounded at zero.

    Parameters:
        value (float): current value
        rate (float): amount to decay

    Returns:
        float: decayed value
    """
    return max(0.0, value - rate)


def apply_overlay_decay(state: WorldState, decay_rate: float = 0.01):
    """
    Applies linear decay to all symbolic overlays.
    Use this when not running via `turn_engine.py`.
    """
    for overlay_name in ["hope", "despair", "rage", "fatigue", "trust"]:
        current_value = getattr(state.overlays, overlay_name, None)
        if current_value is not None:
            decayed = linear_decay(current_value, rate=decay_rate)
            setattr(state.overlays, overlay_name, decayed)
            state.log_event(f"[DECAY] {overlay_name}: {current_value:.3f} → {decayed:.3f}")


def decay_variable(state: WorldState, name: str, rate: float = 0.01, floor: float = 0.0):
    """
    Applies decay to a numeric variable in state.variables.

    Parameters:
        state (WorldState): simulation context
        name (str): variable key
        rate (float): decay step
        floor (float): minimum value
    """
    current = state.get_variable(name, 0.0)
    decayed = max(floor, current - rate)
    state.update_variable(name, decayed)
    state.log_event(f"[DECAY] Variable '{name}': {current:.3f} → {decayed:.3f}")
