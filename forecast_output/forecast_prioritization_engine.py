# forecast_output/forecast_prioritization_engine.py

"""
Forecast Prioritization Engine

Ranks certified forecasts for operator view, export, or strategic use
based on alignment, confidence, arc symbolic priority, and trust.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import List, Dict

# Optional: assign strategic arc weights
ARC_PRIORITIES = {
    "Hope Surge": 3,
    "Stabilization": 2,
    "Fatigue Loop": -1,
    "Collapse Risk": -2,
    "Despair Drop": -3,
}

logger = logging.getLogger("forecast_prioritization_engine")
logging.basicConfig(level=logging.INFO)


def prioritize_by_arc_weight(forecast: Dict) -> int:
    """
    Score forecast based on arc priority value.

    Args:
        forecast: forecast dict

    Returns:
        int
    """
    arc = forecast.get("arc_label", "unknown")
    return ARC_PRIORITIES.get(arc, 0)


def rank_certified_forecasts(forecasts: List[Dict]) -> List[Dict]:
    """
    Sort certified forecasts by combined strategic value.

    Args:
        forecasts: list of forecast dicts

    Returns:
        List[Dict]
    """
    certified = [f for f in forecasts if f.get("certified")]
    return sorted(
        certified,
        key=lambda f: (
            f.get("alignment_score", 0),
            f.get("confidence", 0),
            prioritize_by_arc_weight(f),
        ),
        reverse=True,
    )


def select_top_forecasts(forecasts: List[Dict], top_n: int = 10) -> List[Dict]:
    """
    Return top-N strategic forecasts from certified list.

    Args:
        forecasts: list of forecast dicts
        top_n: number to select

    Returns:
        List[Dict]
    """
    ranked = rank_certified_forecasts(forecasts)
    return ranked[:top_n]


def export_prioritized_forecasts(forecasts: List[Dict], path: str):
    """
    Write top strategic forecasts to disk.

    Args:
        forecasts: List of certified + ranked forecasts
        path: export file path
    """
    if not isinstance(forecasts, list):
        logger.error("❌ Invalid forecasts: not a list")
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            for fc in forecasts:
                f.write(json.dumps(fc, ensure_ascii=False) + "\n")
        logger.info(f"✅ Prioritized forecasts exported to {path}")
    except Exception as e:
        logger.error(f"❌ Failed to export prioritized batch: {e}")


def _test_forecast_prioritization_engine():
    """Basic test for forecast prioritization engine."""
    dummy = [
        {
            "arc_label": "Hope Surge",
            "alignment_score": 0.9,
            "confidence": 0.8,
            "certified": True,
        },
        {
            "arc_label": "Collapse Risk",
            "alignment_score": 0.7,
            "confidence": 0.6,
            "certified": True,
        },
        {
            "arc_label": "Fatigue Loop",
            "alignment_score": 0.8,
            "confidence": 0.7,
            "certified": False,
        },
    ]
    ranked = rank_certified_forecasts(dummy)
    assert ranked and ranked[0]["arc_label"] == "Hope Surge"
    print("✅ Forecast prioritization engine test passed.")


if __name__ == "__main__":
    _test_forecast_prioritization_engine()
