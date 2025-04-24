"""
Consolidated simulation module: core simulation functions, state mutation, IO, and replay.
"""

from simulation_engine.worldstate import WorldState
# Consolidated core and utils simulation modules
from src.simulation_core import (
    simulate_turn, simulate_forward, simulate_backward,
    simulate_counterfactual, reset_state, inverse_decay,
    get_overlays_dict
)
from src.simulation_utils import (
    update_numeric_variable, decay_overlay, adjust_overlay,
    adjust_capital, save_worldstate_to_file,
    load_worldstate_from_file, ReplayerConfig, SimulationReplayer
)

__all__ = [
    "WorldState",
    "simulate_turn",
    "simulate_forward",
    "simulate_backward",
    "simulate_counterfactual",
    "reset_state",
    "inverse_decay",
    "get_overlays_dict",
    "update_numeric_variable",
    "decay_overlay",
    "adjust_overlay",
    "adjust_capital",
    "save_worldstate_to_file",
    "load_worldstate_from_file",
    "ReplayerConfig",
    "SimulationReplayer",
]