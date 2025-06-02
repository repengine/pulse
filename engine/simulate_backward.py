"""simulate_backward.py

Module for backward (retrodiction) simulation in the simulation_engine package.

Contains run_retrodiction to load a historical snapshot and step backward by inverting decay.
"""

from typing import Dict, Any, List
from datetime import datetime
from intelligence.worldstate_loader import load_historical_snapshot
from engine.worldstate import WorldState

DEFAULT_DECAY_RATE: float = 0.01


def run_retrodiction(snapshot_time: datetime, steps: int) -> Dict[str, Any]:
    """
    Run retrodiction from a historical snapshot.

    Args:
        snapshot_time: datetime of the historical snapshot to load.
        steps: number of backward steps to perform.

    Returns:
        Dict with:
            - retrodicted_states: List of dicts ('step', 'overlays', 'deltas').
            - retrodiction_score: float, stubbed mean absolute error of variables.
    """
    # Load historical world state at the given snapshot time
    state: WorldState = load_historical_snapshot(snapshot_time.isoformat())

    # Initialize overlays from state (support dataclass or dict)
    if hasattr(state.overlays, "as_dict"):
        current_overlays: Dict[str, float] = state.overlays.as_dict()
    else:
        # ensure overlays is iterable and yields str→float pairs
        current_overlays = {str(k): float(v) for k, v in state.overlays.items()}

    retrodicted_states: List[Dict[str, Any]] = []

    for i in range(steps):
        previous_overlays: Dict[str, float] = {}
        deltas: Dict[str, float] = {}

        for key, value in current_overlays.items():
            # Invert decay: increase value by the decay rate
            prior_value = value * (1 + DEFAULT_DECAY_RATE)
            previous_overlays[key] = prior_value
            deltas[key] = round(prior_value - value, 4)

        retrodicted_states.append(
            {"step": i + 1, "overlays": previous_overlays.copy(), "deltas": deltas}
        )

        current_overlays = previous_overlays

    # Stub: compute retrodiction score (mean absolute error) - implement actual logic
    retrodiction_score: float = 0.0

    return {
        "retrodicted_states": retrodicted_states,
        "retrodiction_score": retrodiction_score,
    }
