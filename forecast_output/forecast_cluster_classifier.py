# forecast_output/forecast_cluster_classifier.py

"""
Forecast Cluster Classifier

Assigns each forecast a narrative cluster label based on:
- Arc
- Tag
- Alignment
- Trust status
- Symbolic volatility

Used for: operator summaries, digest grouping, memory retention.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict
import logging

logger = logging.getLogger("forecast_cluster_classifier")
logging.basicConfig(level=logging.INFO)


def classify_forecast_cluster(forecast: Dict) -> str:
    arc = forecast.get("arc_label", "").lower()
    tag = forecast.get("symbolic_tag", "").lower()
    align = forecast.get("alignment_score", 0)
    cert = forecast.get("certified")
    attn = forecast.get("attention_score", 0)
    revision = forecast.get("symbolic_revision_needed", False)

    if arc == "hope surge" and align > 80 and cert:
        return "Resilient Hope"
    elif arc == "collapse risk" and attn > 0.7:
        return "Volatile Collapse"
    elif tag == "neutral" and align < 60:
        return "Neutral Drift"
    elif arc == "fatigue loop" and revision:
        return "Symbolic Spiral"
    elif arc == "stabilization" and cert:
        return "Reconstruction Arc"
    else:
        return "Miscellaneous Forecast"


def group_forecasts_by_cluster(forecasts: List[Dict]) -> Dict[str, List[Dict]]:
    if not isinstance(forecasts, list):
        raise ValueError("Input must be a list of dicts")
    clusters = {}
    for fc in forecasts:
        cluster = classify_forecast_cluster(fc)
        fc["narrative_cluster"] = cluster
        clusters.setdefault(cluster, []).append(fc)
    return clusters


def summarize_cluster_counts(forecasts: List[Dict]) -> Dict[str, int]:
    if not isinstance(forecasts, list):
        raise ValueError("Input must be a list of dicts")
    counts = {}
    for fc in forecasts:
        cluster = classify_forecast_cluster(fc)
        counts[cluster] = counts.get(cluster, 0) + 1
    return counts


def export_cluster_summary(counts: Dict[str, int], path: str):
    import json

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(counts, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Cluster summary saved to {path}")
    except Exception as e:
        logger.error(f"❌ Failed to write cluster summary: {e}")


def _test_forecast_cluster_classifier():
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
    clusters = group_forecasts_by_cluster(dummy)
    counts = summarize_cluster_counts(dummy)
    assert isinstance(clusters, dict)
    assert isinstance(counts, dict)
    logger.info("✅ Forecast cluster classifier test passed.")


if __name__ == "__main__":
    _test_forecast_cluster_classifier()
