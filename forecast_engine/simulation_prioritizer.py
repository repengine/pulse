"""
simulation_prioritizer.py

Ranks foresight scenarios (forecasts or forks) based on strategic urgency.
Considers symbolic fragility, novelty, and capital impact.

Used to prioritize simulation effort and determine which forks are most valuable to explore.

Author: Pulse v0.3
"""

from forecast_output.forecast_age_tracker import get_forecast_age
from typing import List, Dict
from math import sqrt


def symbolic_delta_magnitude(symbolic_change: Dict[str, float]) -> float:
    """
    Computes overall symbolic novelty based on vector magnitude of overlay changes.
    """
    return round(sqrt(sum(v**2 for v in symbolic_change.values())), 4)


def capital_delta_magnitude(start: Dict[str, float], end: Dict[str, float]) -> float:
    """
    Calculates the magnitude of total capital movement (across assets).
    """
    delta_sum = sum(abs(end.get(k, 0) - start.get(k, 0)) for k in start)
    return round(min(delta_sum / 1000.0, 1.0), 3)


def rank_forecasts(forecasts: List[Dict], weights=None, debug=False) -> List[Dict]:
    """
    Scores and ranks forecasts based on:
    - Fragility
    - Symbolic novelty
    - Capital movement

    Parameters:
        forecasts: List of forecast dictionaries
        weights: Dict of scoring weights
        debug: Print score breakdowns

    Returns:
        List[Dict]: Forecasts sorted by priority_score (descending)
    """
    if weights is None:
        weights = {"fragility": 0.5, "novelty": 0.3, "capital": 0.2}

    ranked = []

    for f in forecasts:
        symbolic = f.get("forecast", {}).get("symbolic_change", {})
        capital_start = f.get("forecast", {}).get("start_capital", {})
        capital_end = f.get("forecast", {}).get("end_capital", {})

        fragility = f.get("fragility", 0.5)
        novelty = symbolic_delta_magnitude(symbolic)
        capital = capital_delta_magnitude(capital_start, capital_end)

        score = (
            fragility * weights["fragility"]
            + novelty * weights["novelty"]
            + capital * weights["capital"]
        )

        f["priority_score"] = round(score, 3)
        age = get_forecast_age(f)
        if age > 0:
            f["priority_score"] = round(max(0.05, f["priority_score"] - age * 0.01), 3)
        if debug:
            print(
                f"[PRIORITY] {
                    f.get('trace_id')} → F:{fragility} N:{novelty} C:{capital} = {
                    score:.3f}")

        ranked.append(f)

    return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)


# === Local test hook ===
def simulate_priority_test():
    from forecast_output.pfpa_logger import PFPA_ARCHIVE

    if not PFPA_ARCHIVE:
        print("⚠️ No forecasts available for prioritization.")
        return

    top = rank_forecasts(PFPA_ARCHIVE[-10:], debug=True)
    print("\n🧠 Top Prioritized Forecasts:")
    for f in top[:5]:
        print(
            f"  → {
                f.get('trace_id')} | Priority: {
                f['priority_score']} | Conf: {
                f.get('confidence')}")


if __name__ == "__main__":
    simulate_priority_test()
