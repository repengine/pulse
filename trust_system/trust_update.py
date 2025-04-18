"""
trust_update.py

Adjusts historical trust memory based on retrodiction scores.
Forecasts that score well increase influence on future trust weighting.

Author: Pulse v0.3
"""

from forecast_output.pfpa_logger import PFPA_ARCHIVE
from memory.forecast_memory import ForecastMemory
from typing import Dict

pfpa_memory = ForecastMemory()

def get_pfpa_archive():
    return pfpa_memory.get_recent(100)


def update_trust_weights_from_retrodiction() -> Dict[str, float]:
    """
    Calculates adjusted memory trust weights from PFPA archive.

    Returns:
        Dict[str, float]: trace_id → weight (0.0–1.0)
    """
    weights = {}
    for forecast in PFPA_ARCHIVE:
        tid = forecast.get("trace_id", "unknown")
        base = forecast.get("confidence", 0.5)
        retro = forecast.get("retrodiction_score", None)

        if retro is None:
            weights[tid] = base
        elif retro >= 0.8:
            weights[tid] = min(1.0, base + 0.2)
        elif retro < 0.4:
            weights[tid] = max(0.0, base - 0.3)
        else:
            weights[tid] = base

    return weights


def simulate_weight_report():
    weights = update_trust_weights_from_retrodiction()
    for tid, w in weights.items():
        print(f"[MEMORY] {tid} → weight: {w:.2f}")


if __name__ == "__main__":
    simulate_weight_report()