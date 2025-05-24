"""
forecast_scoring.py

Scores each forecast after simulation based on:
- Rule activation richness
- Symbolic coherence (tag overlap)
- Variable sensitivity (volatility)
- Potential for divergence (fragility)

Author: Pulse v0.10
"""

from simulation_engine.worldstate import WorldState
from core.pulse_learning_log import log_learning_event
from datetime import datetime


def score_forecast(state: WorldState, rule_log: list[dict]) -> dict:
    """
    Assigns trust metrics to a forecast. Assumes rule_log was returned from run_rules.

    Args:
        state (WorldState): The final state of the simulation
        rule_log (list): Executed rules from rule_engine

    Returns:
        dict with 'confidence', 'fragility', and 'symbolic_driver'
    """

    if not rule_log:
        return {"confidence": 0.1, "fragility": 0.9, "symbolic_driver": "None"}

    symbolic_counts = {}
    for rule in rule_log:
        for tag in rule.get("symbolic_tags", []):
            symbolic_counts[tag] = symbolic_counts.get(tag, 0) + 1

    symbolic_driver = max(
        symbolic_counts.keys(), default="unknown", key=symbolic_counts.get
    )

    # Confidence: more diverse symbolic signals = more believable
    diversity_factor = len(symbolic_counts)
    base_conf = 0.5 + (0.05 * diversity_factor)
    confidence = min(base_conf, 0.95)

    # Fragility: based on symbolic over-weighting
    fragility = 1.0 - (0.03 * diversity_factor)
    fragility = max(0.0, min(fragility, 1.0))

    result = {
        "confidence": round(confidence, 3),
        "fragility": round(fragility, 3),
        "symbolic_driver": symbolic_driver,
    }
    log_learning_event(
        "forecast_scored",
        {
            "confidence": result["confidence"],
            "fragility": result["fragility"],
            "symbolic_driver": result["symbolic_driver"],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
    return result
