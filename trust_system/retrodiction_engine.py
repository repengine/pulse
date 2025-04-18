"""
retrodiction_engine.py

Performs retrodiction analysis: comparing past forecasts against actual outcomes.
Includes:
- Capital delta comparison (hit/miss per asset)
- Symbolic overlay trajectory match
- Summary scoring for accuracy and symbolic realism
- Batch replay and optional logging

Author: Pulse v0.3
"""

import json
import datetime
from typing import Dict, List
from memory.forecast_memory import ForecastMemory
from utils.log_utils import get_logger
from core.path_registry import PATHS

logger = get_logger(__name__)

forecast_memory = ForecastMemory(persist_dir=PATHS["FORECAST_HISTORY"])
retrodiction_memory = ForecastMemory()


def compare_outcomes(
    forecast: Dict,
    actual_exposure: Dict[str, float],
    tolerance: float = 0.03
) -> Dict[str, bool]:
    """
    Compares forecasted exposure deltas to actual observed deltas.

    Returns:
        asset → hit/miss (bool)
    """
    result = {}
    start = forecast.get("exposure_start", {})
    expected = forecast.get("exposure_end", {})

    for asset in actual_exposure:
        if asset not in start or asset not in expected:
            result[asset] = False
            continue

        expected_delta = expected[asset] - start[asset]
        actual_delta = actual_exposure[asset] - start[asset]

        if abs(expected_delta) < 1e-5:
            result[asset] = abs(actual_delta) < tolerance
        else:
            relative_error = abs((actual_delta - expected_delta) / (expected_delta or 1))
            result[asset] = relative_error <= tolerance

    return result


def match_symbolic_direction(
    forecast: Dict,
    actual_overlay: Dict[str, float],
    tolerance: float = 0.05
) -> Dict[str, bool]:
    """
    Compares symbolic drift direction: did each overlay go the predicted way?

    Returns:
        overlay → hit/miss
    """
    deltas = forecast.get("forecast", {}).get("symbolic_change", {})
    result = {}

    for key, delta in deltas.items():
        if abs(delta) < 1e-3:
            continue
        predicted_up = delta > 0
        actual_change = actual_overlay.get(key, 0) - forecast.get("symbolic_snapshot", {}).get(key, 0)
        actual_up = actual_change > 0
        result[key] = (predicted_up == actual_up) or abs(actual_change) < tolerance

    return result


def score_retrodiction_hit_ratio(hit_map: Dict[str, bool]) -> float:
    if not hit_map:
        return 0.0
    correct = sum(1 for hit in hit_map.values() if hit)
    return round(correct / len(hit_map), 3)


def retrodict_forecast(
    forecast: Dict,
    actual_exposure: Dict[str, float],
    actual_overlay: Dict[str, float] = None,
    tolerance: float = 0.03
) -> Dict[str, any]:
    """
    Runs full retrodiction on a forecast using actual exposure + symbolic overlay.

    Returns:
        Dict summary with score, hits, trust tag, and trace_id
    """
    hits = compare_outcomes(forecast, actual_exposure, tolerance)
    score = score_retrodiction_hit_ratio(hits)

    symbolic_score = None
    symbolic_hits = {}
    if actual_overlay:
        symbolic_hits = match_symbolic_direction(forecast, actual_overlay)
        symbolic_score = score_retrodiction_hit_ratio(symbolic_hits)

    return {
        "trace_id": forecast.get("trace_id", "unknown"),
        "retrodiction_score": score,
        "symbolic_score": symbolic_score,
        "asset_hits": hits,
        "symbolic_hits": symbolic_hits,
        "forecast_confidence": forecast.get("confidence", None),
        "trust_label": forecast.get("trust_label", "🟡 Unlabeled"),
        "fragility_score": forecast.get("fragility_score", None)
    }


def retrodict_all_forecasts(
    forecasts: List[Dict],
    actual_exposure: Dict[str, float],
    actual_overlay: Dict[str, float] = None
) -> List[Dict]:
    """
    Batch-mode retrodiction across all forecasts.
    """
    return [retrodict_forecast(f, actual_exposure, actual_overlay) for f in forecasts]


def save_retrodiction_results(results: Dict):
    retrodiction_memory.store(results)


def save_forecast(forecast_obj: Dict):
    forecast_memory.store(forecast_obj)


# === Local test ===
def simulate_retrodiction_test():
    from forecast_output.pfpa_logger import PFPA_ARCHIVE
    if not PFPA_ARCHIVE:
        logger.info("No forecasts in PFPA archive; skipping retrodiction.")
        return

    # Simulate truth
    actual = {"nvda": 10100, "msft": 9800, "ibit": 5300, "spy": 9600}
    overlay_truth = {"hope": 0.55, "despair": 0.3, "rage": 0.2, "fatigue": 0.5, "trust": 0.6}

    results = retrodict_all_forecasts(PFPA_ARCHIVE[-5:], actual, overlay_truth)
    for r in results:
        logger.info(f"[RETRO] {r['trace_id']} | Capital: {r['retrodiction_score']} | Symbolic: {r['symbolic_score']}")
    save_retrodiction_results(results)


if __name__ == "__main__":
    simulate_retrodiction_test()
