# forecast_retrospector.py
"""
Module: forecast_retrospector.py
Purpose: Analyze the symbolic and capital alignment of past forecasts by simulating backward.
Detects where assumptions failed by comparing what the forecast implied about the past
with what Pulse now knows or reconstructs based on updated worldstate knowledge.

Future extensions may support:
- Memory correction tagging
- Scenario inversion replays
- Symbolic feedback loop analysis

Author: Pulse AI Engine
Version: v0.4.0
"""

from typing import Dict, List, Tuple
import math


def reconstruct_past_state(forecast: Dict) -> Dict:
    """
    Generate a synthetic approximation of the past state implied by a given forecast.
    Uses symbolic overlays and capital snapshot to infer the forecast's assumptions.

    Parameters:
        forecast (Dict): A single forecast entry.

    Returns:
        Dict: A reconstructed past state with symbolic scores and capital snapshot.
    """
    overlays = forecast.get("overlays", {})
    capital = forecast.get("forecast", {}).get("start_capital", {})
    return {
        "hope": overlays.get("hope", 0.5),
        "despair": overlays.get("despair", 0.5),
        "fatigue": overlays.get("fatigue", 0.5),
        "rage": overlays.get("rage", 0.5),
        "capital_snapshot": capital,
    }


def retrodict_error_score(past_state: Dict, current_state: Dict, symbolic_weight: float = 1.0, capital_weight: float = 1.0) -> float:
    """
    Compute an error score between a reconstructed past and the current believed state.
    Combines symbolic and capital deviations into a single metric.

    Parameters:
        past_state (Dict): Reconstructed past worldstate.
        current_state (Dict): Actual or inferred historical state.
        symbolic_weight (float): Multiplier for symbolic overlay differences.
        capital_weight (float): Multiplier for capital mismatch.

    Returns:
        float: Normalized root-sum-squared error score.
    """
    symbolic_keys = ["hope", "despair", "rage", "fatigue"]
    error_sum = 0.0
    for k in symbolic_keys:
        error_sum += symbolic_weight * (past_state.get(k, 0.5) - current_state.get(k, 0.5)) ** 2

    capital_keys = set(past_state.get("capital_snapshot", {}).keys()) | set(current_state.get("capital_snapshot", {}).keys())
    for k in capital_keys:
        p_val = past_state.get("capital_snapshot", {}).get(k, 0)
        c_val = current_state.get("capital_snapshot", {}).get(k, 0)
        error_sum += capital_weight * ((p_val - c_val) / 1000.0) ** 2

    return round(math.sqrt(error_sum), 4)


def retrospective_analysis_batch(forecasts: List[Dict], current_state: Dict, threshold: float = 1.5) -> List[Dict]:
    """
    Perform retrodiction error scoring across a batch of forecasts.
    Appends 'retrodiction_error' and optional trust flag if above threshold.

    Parameters:
        forecasts (List[Dict]): A batch of forecast entries.
        current_state (Dict): The latest known historical state.
        threshold (float): Error threshold above which a forecast is flagged.

    Returns:
        List[Dict]: Augmented forecasts with retrodiction error fields.
    """
    for f in forecasts:
        past_state = reconstruct_past_state(f)
        score = retrodict_error_score(past_state, current_state)
        f["retrodiction_error"] = score
        if score > threshold:
            f["retrodiction_flag"] = "⚠️ Symbolic misalignment"
    return forecasts
