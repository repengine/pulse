# forecast_output/dual_narrative_compressor.py

"""
Dual Narrative Compressor

Identifies symbolic narrative forks (e.g. Hope vs Collapse)
and compresses them into operator-facing Scenario A / Scenario B summaries.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import List, Dict
from forecast_output.forecast_divergence_detector import detect_symbolic_opposition

logger = logging.getLogger("dual_narrative_compressor")
logging.basicConfig(level=logging.INFO)


def group_by_arc(forecasts: List[Dict]) -> Dict[str, List[Dict]]:
    groups = {}
    for fc in forecasts:
        arc = fc.get("arc_label", "unknown")
        groups.setdefault(arc, []).append(fc)
    return groups


def score_forecast(fc: Dict) -> float:
    return fc.get("alignment_score", 0) + fc.get("confidence", 0)


def compress_dual_pair(forecasts: List[Dict], arc_a: str, arc_b: str) -> Dict:
    """
    Return one forecast from each opposing arc.
    """
    arc_map = group_by_arc(forecasts)
    a_set = sorted(arc_map.get(arc_a, []), key=score_forecast, reverse=True)
    b_set = sorted(arc_map.get(arc_b, []), key=score_forecast, reverse=True)

    return {
        "scenario_a": {"arc": arc_a, "forecast": a_set[0] if a_set else None},
        "scenario_b": {"arc": arc_b, "forecast": b_set[0] if b_set else None},
    }


def generate_dual_scenarios(forecasts: List[Dict]) -> List[Dict]:
    """
    Return all divergent arc pairs as Scenario A/B structures.

    Returns:
        List[Dict]: each with scenario_a and scenario_b fields
    """
    pairs = detect_symbolic_opposition(forecasts)
    return [compress_dual_pair(forecasts, a, b) for a, b in pairs]


def export_dual_scenarios(scenarios: List[Dict], path: str):
    """Save dual narrative structure to disk."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Dual scenarios saved to {path}")
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")


def _test_dual_narrative_compressor():
    dummy = [
        {"arc_label": "Hope Surge", "alignment_score": 0.8},
        {"arc_label": "Collapse Risk", "alignment_score": 0.7},
        {"arc_label": "Hope Surge", "alignment_score": 0.6},
    ]
    scenarios = generate_dual_scenarios(dummy)
    assert isinstance(scenarios, list)
    logger.info("✅ Dual narrative compressor test passed.")


if __name__ == "__main__":
    _test_dual_narrative_compressor()
