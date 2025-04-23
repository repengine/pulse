"""
trust_update.py

Adjusts historical trust memory based on retrodiction scores.
Forecasts that score well increase influence on future trust weighting.

Author: Pulse v0.3
"""

from output.pfpa_logger import PFPA_ARCHIVE
from memory.forecast_memory import ForecastMemory
from typing import Dict, List, Callable
import logging

logger = logging.getLogger("trust_update")
logging.basicConfig(level=logging.INFO)

pfpa_memory = ForecastMemory()

TRUST_UPDATE_PLUGINS: List[Callable[[Dict[str, float]], None]] = []

def register_trust_update_plugin(plugin_fn: Callable[[Dict[str, float]], None]) -> None:
    """
    Register a plugin function for post-update actions.
    Plugin signature: plugin_fn(weights: Dict[str, float]) -> None
    """
    TRUST_UPDATE_PLUGINS.append(plugin_fn)

def run_trust_update_plugins(weights: Dict[str, float]) -> None:
    """
    Run all registered trust update plugins.
    """
    for plugin in TRUST_UPDATE_PLUGINS:
        try:
            plugin(weights)
        except Exception as e:
            logger.warning(f"[TrustUpdate] Plugin {plugin.__name__} failed: {e}")

def get_pfpa_archive() -> List[Dict]:
    """Return the most recent 100 forecasts from PFPA memory."""
    return pfpa_memory.get_recent(100)

def update_trust_weights_from_retrodiction() -> Dict[str, float]:
    """
    Calculates adjusted memory trust weights from PFPA archive.

    Returns:
        Dict[str, float]: trace_id → weight (0.0–1.0)
    """
    weights = {}
    explanations = {}
    for forecast in PFPA_ARCHIVE:
        tid = forecast.get("trace_id", "unknown")
        base = forecast.get("confidence", 0.5)
        try:
            base = float(base)
        except Exception:
            base = 0.5
        retro = forecast.get("retrodiction_score", None)
        try:
            retro = float(retro) if retro is not None else None
        except Exception:
            retro = None

        if retro is None:
            weights[tid] = base
            explanations[tid] = "No retrodiction score; base weight used."
        elif retro >= 0.8:
            weights[tid] = min(1.0, base + 0.2)
            explanations[tid] = f"High retrodiction ({retro:.2f}); weight boosted."
        elif retro < 0.4:
            weights[tid] = max(0.0, base - 0.3)
            explanations[tid] = f"Low retrodiction ({retro:.2f}); weight reduced."
        else:
            weights[tid] = base
            explanations[tid] = f"Neutral retrodiction ({retro:.2f}); base weight kept."

    logger.info(f"[TrustUpdate] Updated {len(weights)} trust weights from PFPA archive.")
    for tid, w in weights.items():
        logger.debug(f"[TrustUpdate] {tid} → weight: {w:.2f} | {explanations[tid]}")
    run_trust_update_plugins(weights)
    return weights

def simulate_weight_report() -> None:
    """
    Print a summary of trust weight adjustments.
    """
    weights = update_trust_weights_from_retrodiction()
    for tid, w in weights.items():
        print(f"[MEMORY] {tid} → weight: {w:.2f}")

# --- Unit test for trust update logic ---
def _test_update_trust_weights_from_retrodiction():
    # Simulate PFPA_ARCHIVE with edge cases
    global PFPA_ARCHIVE
    PFPA_ARCHIVE = [
        {"trace_id": "t1", "confidence": 0.7, "retrodiction_score": 0.9},
        {"trace_id": "t2", "confidence": 0.5, "retrodiction_score": 0.3},
        {"trace_id": "t3", "confidence": 0.6, "retrodiction_score": None},
        {"trace_id": "t4", "confidence": "bad", "retrodiction_score": "bad"},
    ]
    weights = update_trust_weights_from_retrodiction()
    assert abs(weights["t1"] - 0.9) < 1e-6
    assert abs(weights["t2"] - 0.2) < 1e-6
    assert abs(weights["t3"] - 0.6) < 1e-6
    assert abs(weights["t4"] - 0.5) < 1e-6
    print("✅ trust_update unit test passed.")

if __name__ == "__main__":
    simulate_weight_report()
    _test_update_trust_weights_from_retrodiction()