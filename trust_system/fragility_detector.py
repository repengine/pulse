"""
fragility_detector.py

Calculates symbolic fragility for a given forecast using symbolic tension and overlay volatility.
Used to determine whether a forecast is emotionally unstable, even if confident.

Author: Pulse v0.2

Core Functions:
- compute_fragility(symbolic_overlay, symbolic_change)
- get_fragility_label(score)
- tag_fragility(forecasts)
- simulate_fragility_test()

Example usage:
    score = compute_fragility(overlays, deltas)
    label = get_fragility_label(score)
"""

from symbolic_system.symbolic_utils import symbolic_tension_score
from typing import Dict
import logging
from core.pulse_config import DEFAULT_FRAGILITY_THRESHOLD

logger = logging.getLogger(__name__)


def compute_fragility(
    symbolic_overlay: Dict[str, float],
    symbolic_change: Dict[str, float],
    tension_weight: float = 0.6,
    volatility_weight: float = 0.4,
    debug: bool = False,
) -> float:
    """
    Computes fragility index (0.0–1.0) from symbolic data.

    Parameters:
        symbolic_overlay (Dict): current overlay values
        symbolic_change (Dict): recent overlay deltas
        tension_weight (float): weight of symbolic conflict
        volatility_weight (float): weight of overlay shift velocity
        debug (bool): print scores during calculation

    Returns:
        float: fragility score (0.0 = stable, 1.0 = fragile)
    """
    tension = symbolic_tension_score(symbolic_overlay)
    volatility = min(sum(abs(v) for v in symbolic_change.values()) / 5.0, 1.0)
    fragility = (tension * tension_weight) + (volatility * volatility_weight)
    fragility = round(min(fragility, DEFAULT_FRAGILITY_THRESHOLD), 3)

    if debug:
        logger.info(
            f"[FRAGILITY] Tension={tension:.3f} | Volatility={volatility:.3f} → Fragility={fragility:.3f}"
        )

    return fragility


def get_fragility_label(score: float) -> str:
    """
    Maps fragility score to a symbolic label.
    """
    if score < 0.3:
        return "🟢 Stable"
    elif score < 0.6:
        return "⚠️ Moderate"
    else:
        return "🔴 Volatile"


def tag_fragility(forecasts):
    """
    Annotate each forecast with a fragility label based on its fragility score.
    Expects each forecast to have 'fragility' field or computes it if overlays/deltas are present.
    """
    for fc in forecasts:
        frag = fc.get("fragility")
        if frag is None:
            overlays = fc.get("overlays", {})
            deltas = fc.get("symbolic_change", {})
            frag = compute_fragility(overlays, deltas)
            fc["fragility"] = frag
        fc["fragility_label"] = get_fragility_label(frag)
    return forecasts


def simulate_fragility_test():
    """
    Runs a local test of fragility scoring.
    """
    overlays = {"hope": 0.8, "despair": 0.6, "rage": 0.3, "fatigue": 0.5, "trust": 0.4}
    deltas = {"hope": -0.2, "despair": +0.3, "fatigue": +0.1}
    score = compute_fragility(overlays, deltas, debug=True)
    label = get_fragility_label(score)
    print(f"[SIMULATION] Fragility Score: {score} → {label}")


if __name__ == "__main__":
    simulate_fragility_test()
