"""
trust_engine.py

Computes a confidence score (0.0 to 1.0) for a given forecast object.
Scoring factors:
- Symbolic fragility (lower = more trusted)
- Capital delta significance (larger = more signal)
- Forecast novelty (vs recent memory)

Author: Pulse v0.2
"""

from symbolic_system.symbolic_utils import symbolic_fragility_index
from typing import Dict, List
from core.pulse_config import CONFIDENCE_THRESHOLD


def score_forecast(
    forecast: Dict,
    memory: List[Dict] = None,
    fragility_weight: float = 0.4,
    delta_weight: float = 0.4,
    novelty_weight: float = 0.2
) -> float:
    """
    Scores a forecast's trustworthiness using symbolic and capital features.

    Parameters:
        forecast (Dict): a single forecast object
        memory (List[Dict]): recent forecast memory for novelty comparison
        fragility_weight (float): weight of symbolic fragility in scoring
        delta_weight (float): weight of capital delta
        novelty_weight (float): weight of uniqueness

    Returns:
        float: confidence score from 0.0 (untrusted) to 1.0 (highly trusted)
    """
    fcast = forecast.get("forecast", {})
    fragility = forecast.get("fragility", 1.0)
    symbolic_penalty = min(fragility, 1.0)

    # ---- Capital Movement Signal ----
    capital_start = fcast.get("start_capital", {})
    capital_end = fcast.get("end_capital", {})

    movement_score = 0.0
    if capital_start and capital_end:
        delta_sum = 0
        for asset in ["nvda", "msft", "ibit", "spy"]:
            start = capital_start.get(asset, 0)
            end = capital_end.get(asset, 0)
            delta_sum += abs(end - start)
        movement_score = min(delta_sum / 1000.0, 1.0) if delta_sum else 0.0  # Prevent division by zero

    # ---- Novelty Filter ----
    is_duplicate = False
    if memory:
        for past in memory[-3:]:  # check last 3
            prev = past.get("forecast", {}).get("symbolic_change", {})
            curr = fcast.get("symbolic_change", {})
            if curr == prev:
                is_duplicate = True
                break
    novelty_score = 0.0 if is_duplicate else 1.0

    # ---- Combine Weights ----
    confidence = (
        (1.0 - symbolic_penalty) * fragility_weight +
        movement_score * delta_weight +
        novelty_score * novelty_weight
    )

    confidence = max(confidence, CONFIDENCE_THRESHOLD)

    return round(min(max(confidence, 0.0), 1.0), 3)
