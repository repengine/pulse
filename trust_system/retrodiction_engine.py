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

from typing import Dict, List, Optional, Union, Any
from memory.forecast_memory import ForecastMemory
from utils.log_utils import get_logger
from core.path_registry import PATHS
from pathlib import Path

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

logger = get_logger(__name__)

# Fix Path type for persist_dir
forecast_memory = ForecastMemory(persist_dir=str(PATHS["FORECAST_HISTORY"]))
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
        result[asset] = abs(actual_delta) < tolerance if abs(expected_delta) < 1e-5 else abs((actual_delta - expected_delta) / (expected_delta or 1)) <= tolerance
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
    correct = sum(hit_map.values())
    return round(correct / len(hit_map), 3)


def retrodict_forecast(
    forecast: Dict,
    actual_exposure: Dict[str, float],
    actual_overlay: Optional[Dict[str, float]] = None,
    tolerance: float = 0.03
) -> Dict[str, Any]:
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
        "forecast_confidence": forecast.get("confidence"),
        "trust_label": forecast.get("trust_label", "🟡 Unlabeled"),
        "fragility_score": forecast.get("fragility_score")
    }


def retrodict_all_forecasts(
    forecasts: List[Dict],
    actual_exposure: Dict[str, float],
    actual_overlay: Optional[Dict[str, float]] = None
) -> List[Dict]:
    """
    Batch-mode retrodiction across all forecasts.
    """
    if actual_exposure is None:
        actual_exposure = {}
    else:
        actual_exposure = {k: float(v) for k, v in actual_exposure.items()}
    if actual_overlay is None:
        actual_overlay = {}
    else:
        actual_overlay = {k: float(v) for k, v in actual_overlay.items()}
    return [retrodict_forecast(f, actual_exposure, actual_overlay) for f in forecasts]


def save_retrodiction_results(results):
    # PATCH: Ensure overlays are serializable before storing
    def overlay_to_dict(overlay):
        if hasattr(overlay, "as_dict"):
            return overlay.as_dict()
        return dict(overlay)
    if isinstance(results, dict):
        if "overlays" in results:
            results["overlays"] = overlay_to_dict(results["overlays"])
        if "forks" in results:
            for fork in results["forks"]:
                if "overlays" in fork:
                    fork["overlays"] = overlay_to_dict(fork["overlays"])
    elif isinstance(results, list):
        for res in results:
            if "overlays" in res:
                res["overlays"] = overlay_to_dict(res["overlays"])
            if "forks" in res:
                for fork in res["forks"]:
                    if "overlays" in fork:
                        fork["overlays"] = overlay_to_dict(fork["overlays"])
    if isinstance(results, list):
        for res in results:
            retrodiction_memory.store(res)
    else:
        retrodiction_memory.store(results)


def save_forecast(forecast_obj: Dict):
    # PATCH: Ensure overlays are serializable before storing
    def overlay_to_dict(overlay):
        if hasattr(overlay, "as_dict"):
            return overlay.as_dict()
        return dict(overlay)
    if "overlays" in forecast_obj:
        forecast_obj["overlays"] = overlay_to_dict(forecast_obj["overlays"])
    if "forks" in forecast_obj:
        for fork in forecast_obj["forks"]:
            if "overlays" in fork:
                fork["overlays"] = overlay_to_dict(fork["overlays"])
    forecast_memory.store(forecast_obj)


# === Local test ===
def simulate_retrodiction_test():
    from forecast_output.pfpa_logger import PFPA_ARCHIVE
    if not PFPA_ARCHIVE:
        logger.info("No forecasts in PFPA archive; skipping retrodiction.")
        return

    # Simulate truth
    actual = {"nvda": 10100, "msft": 9800, "ibit": 5300, "spy": 9600}
    # Convert int values to float to satisfy type checker
    actual_float = {k: float(v) for k, v in actual.items()}
    overlay_truth = {"hope": 0.55, "despair": 0.3, "rage": 0.2, "fatigue": 0.5, "trust": 0.6}

    results = retrodict_all_forecasts(PFPA_ARCHIVE[-5:], actual_float, overlay_truth)
    for r in results:
        logger.info(f"[RETRO] {r['trace_id']} | Capital: {r['retrodiction_score']} | Symbolic: {r['symbolic_score']}")
    save_retrodiction_results(results)


if __name__ == "__main__":
    simulate_retrodiction_test()
