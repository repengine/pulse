"""
PATCHED: forecast_compressor.py
Pulse Version: v0.21.2
Patch: Auto-calls forecast_summary_synthesizer after compressing clusters
"""

import json
import os
from typing import List, Dict, Optional

from forecast_output.forecast_summary_synthesizer import summarize_forecasts
from utils.log_utils import get_logger
from core.path_registry import PATHS
from trust_system.trust_engine import compute_symbolic_attention_score

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

COMPRESSED_OUTPUT = PATHS["FORECAST_COMPRESSED"]

logger = get_logger(__name__)

def compress_forecasts(
    forecasts: List[Dict],
    cluster_key: str = "symbolic_tag",
    top_n: int = None,
    summarize: bool = True,
    arc_drift: Optional[Dict[str, int]] = None
) -> List[Dict]:
    """
    Compresses forecasts by clustering and summarizing.

    Args:
        forecasts: List of forecast dicts.
        cluster_key: Key to cluster by ("symbolic_tag", "narrative_theme", etc).
        top_n: Only keep top N clusters (by count).
        summarize: If True, call forecast_summary_synthesizer.
        arc_drift: Optional dict of arc drift deltas for attention scoring.

    Returns:
        List of compressed cluster dicts.
    """
    from collections import defaultdict, Counter

    if not isinstance(forecasts, list):
        logger.warning("Input 'forecasts' is not a list.")
        return []
    clusters = defaultdict(list)
    for f in forecasts:
        label = f.get(cluster_key, "unknown")
        clusters[label].append(f)

    if top_n:
        clusters = dict(sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:top_n])

    compressed = []
    for label, group in clusters.items():
        confs = [f.get("confidence", 0.0) or 0.0 for f in group]
        avg_conf = round(sum(confs) / len(confs), 3) if confs else 0.0
        drivers = []
        for f in group:
            ds = f.get("drivers") or f.get("driver") or []
            if isinstance(ds, str):
                ds = [ds]
            drivers.extend(ds)
        top_drivers = [d for d, _ in Counter(drivers).most_common(3)]
        # Compute attention score for the cluster (use first example's arc_label)
        attention = 0.0
        if arc_drift and group:
            arc_label = group[0].get("arc_label", "unknown")
            try:
                attention = compute_symbolic_attention_score({"arc_label": arc_label}, arc_drift)
            except Exception as e:
                logger.warning(f"Attention score error for arc_label {arc_label}: {e}")
                attention = None
        compressed.append({
            "tag": label,
            "count": len(group),
            "avg_confidence": avg_conf,
            "top_drivers": top_drivers,
            "examples": group[:2],
            "attention_score": attention
        })

    try:
        with open(COMPRESSED_OUTPUT, "w") as f:
            json.dump(compressed, f, indent=2)
        logger.info(f"Compressed forecasts written to {COMPRESSED_OUTPUT}")
    except Exception as e:
        logger.warning(f"Failed to write compressed output: {e}")

    if summarize:
        try:
            summarize_forecasts(compressed)
        except Exception as e:
            logger.warning(f"Summary synthesizer failed: {e}")

    return compressed

if __name__ == "__main__":
    # Example usage/test
    sample = [
        {"symbolic_tag": "hope", "confidence": 0.62, "drivers": ["NVDA earnings", "AI sentiment"]},
        {"symbolic_tag": "hope", "confidence": 0.68, "drivers": ["FED stance"]},
        {"symbolic_tag": "fatigue", "confidence": 0.43, "drivers": ["news overload"]}
    ]
    result = compress_forecasts(sample)
    print(json.dumps(result, indent=2))
