"""
decay_logic.py

Defines symbolic and variable decay patterns used during simulation turns.
This includes simple linear decay, exponential-style decay, and
future support for conditional symbolic erosion.

Author: Pulse v3.5
"""

from engine.worldstate import WorldState
# Removed hardcoded DEFAULT_DECAY_RATE import; using YAML config via config_loader instead.


from typing import Optional


def linear_decay(value: float, rate: Optional[float] = None) -> float:
    """
    Reduces a value by a fixed rate, bounded at zero.
    """
    if rate is None:
        from engine.pulse_config import config_loader

        rate = config_loader.get_config_value(
            "core_config.yaml", "default_decay_rate", 0.1
        )
    if rate is None:
        raise ValueError("Decay rate must be a float, got None.")
    return max(0.0, value - float(rate))


def apply_overlay_decay(state: WorldState, decay_rate: Optional[float] = None):
    """
    Applies linear decay to all symbolic overlays.
    Use this when not running via `turn_engine.py`.
    """
    if decay_rate is None:
        from engine.pulse_config import config_loader

        decay_rate = config_loader.get_config_value(
            "core_config.yaml", "default_decay_rate", 0.1
        )
    for overlay_name in ["hope", "despair", "rage", "fatigue", "trust"]:
        current_value = getattr(state.overlays, overlay_name, None)
        if current_value is not None:
            decayed = linear_decay(current_value, rate=decay_rate)
            setattr(state.overlays, overlay_name, decayed)
            state.log_event(
                f"[DECAY] {overlay_name}: {current_value:.3f} → {decayed:.3f}"
            )


def decay_variable(
    state: WorldState, name: str, rate: Optional[float] = None, floor: float = 0.0
):
    """
    Applies decay to a numeric variable in state.variables.

    Parameters:
        state (WorldState): simulation context
        name (str): variable key
        rate (float): decay step
        floor (float): minimum value
    """
    if rate is None:
        from engine.pulse_config import config_loader

        rate = config_loader.get_config_value(
            "core_config.yaml", "default_decay_rate", 0.1
        )
    current = state.variables.get(name, 0.0)
    decayed = max(floor, current - rate)
    state.variables[name] = decayed
    state.update_variable(name, decayed)
    state.log_event(f"[DECAY] Variable '{name}': {current:.3f} → {decayed:.3f}")
