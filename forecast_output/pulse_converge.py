# forecast_output/pulse_converge.py

"""
PulseConverge

Collapses a set of symbolically resonant forecasts into a single consensus narrative.
Used in Digest, memory retention, and operator briefings.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import List, Dict
from collections import Counter

logger = logging.getLogger("pulse_converge")
logging.basicConfig(level=logging.INFO)


def converge_forecast_cluster(forecasts: List[Dict], key: str = "arc_label") -> Dict:
    """
    Select the most aligned + dominant forecast from a resonant batch.

    Args:
        forecasts: list of forecast dicts
        key: symbolic field ("arc_label" or "symbolic_tag")

    Returns:
        Dict: compressed consensus forecast
    """
    counts = Counter(f.get(key, "unknown") for f in forecasts)
    dominant = counts.most_common(1)[0][0]

    cluster = [f for f in forecasts if f.get(key) == dominant]
    best = sorted(cluster, key=lambda x: x.get("alignment_score", 0), reverse=True)[0]

    consensus = json.loads(json.dumps(best))  # deep copy
    consensus["consensus_cluster_size"] = len(cluster)
    consensus["consensus_symbol"] = dominant
    consensus["source_forecast_ids"] = [f.get("trace_id") for f in cluster]

    return consensus


def summarize_consensus(consensus: Dict) -> str:
    """
    Return a one-line symbolic summary.

    Args:
        consensus: compressed forecast

    Returns:
        str: formatted summary line
    """
    return (
        f"{consensus.get('consensus_symbol')} — "
        f"alignment: {consensus.get('alignment_score', 0)}, "
        f"confidence: {consensus.get('confidence', 0)}, "
        f"based on {consensus.get('consensus_cluster_size')} forecasts"
    )


def export_converged_narrative(consensus: Dict, path: str):
    """Write compressed narrative to disk."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(consensus, ensure_ascii=False) + "\n")
        logger.info(f"✅ Compressed consensus saved to {path}")
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")


def _test_pulse_converge():
    dummy = [
        {"arc_label": "Hope Surge", "alignment_score": 0.8, "confidence": 0.7, "trace_id": "a"},
        {"arc_label": "Hope Surge", "alignment_score": 0.7, "confidence": 0.6, "trace_id": "b"},
        {"arc_label": "Collapse Risk", "alignment_score": 0.4, "confidence": 0.4, "trace_id": "c"},
    ]
    consensus = converge_forecast_cluster(dummy)
    assert consensus["consensus_symbol"] == "Hope Surge"
    logger.info("✅ Pulse converge test passed.")


if __name__ == "__main__":
    _test_pulse_converge()
