# forecast_output/cluster_memory_compressor.py

"""
Cluster-Based Memory Compressor

Reduces forecast batch to one top-ranked forecast per symbolic cluster.
Used for long-term retention, digest distillation, and operator view.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import os
import logging
from typing import List, Dict
from output.forecast_cluster_classifier import classify_forecast_cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def score_forecast(forecast: Dict) -> float:
    """
    Simple scoring function based on alignment + confidence.

    Args:
        forecast (Dict): Forecast dictionary.

    Returns:
        float: Score.
    """
    return forecast.get("alignment_score", 0) + forecast.get("confidence", 0)


def compress_by_cluster(
    forecasts: List[Dict],
    scoring_fn=score_forecast
) -> List[Dict]:
    """
    Select the top forecast per narrative cluster.

    Args:
        forecasts (List[Dict]): Full batch with narrative_cluster field.
        scoring_fn (Callable): Function to score forecasts.

    Returns:
        List[Dict]: Best forecast per cluster.
    """
    if not isinstance(forecasts, list):
        logger.error("Input forecasts must be a list.")
        raise ValueError("Input forecasts must be a list.")
    cluster_map: Dict[str, List[Dict]] = {}
    for fc in forecasts:
        cluster = classify_forecast_cluster(fc)
        fc["narrative_cluster"] = cluster
        cluster_map.setdefault(cluster, []).append(fc)

    compressed = []
    for cluster, fc_list in cluster_map.items():
        if not fc_list:
            logger.warning("Cluster '%s' is empty.", cluster)
            continue
        try:
            top = max(fc_list, key=scoring_fn)
            compressed.append(top)
        except Exception as e:
            logger.error("Error selecting top forecast for cluster '%s': %s", cluster, e)
    return compressed


def export_cluster_memory(forecasts: List[Dict], path: str):
    """
    Save compressed cluster memory to disk.

    Args:
        forecasts (List[Dict]): Compressed forecasts.
        path (str): Output file path.

    Raises:
        OSError: If file cannot be written.
    """
    if not isinstance(path, str) or not path.endswith(".jsonl"):
        logger.error("Invalid file path: %s", path)
        raise ValueError("Output path must be a .jsonl file")
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            for fc in forecasts:
                f.write(json.dumps(fc, ensure_ascii=False) + "\n")
        os.replace(tmp_path, path)
        logger.info("✅ Cluster memory saved to %s", path)
    except OSError as e:
        logger.error("❌ Export failed: %s", e)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    except Exception as e:
        logger.error("❌ Unexpected error: %s", e)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

# --- Simple test block ---
if __name__ == "__main__":
    # Minimal test for robustness
    test_forecasts = [
        {"id": 1, "alignment_score": 0.8, "confidence": 0.7},
        {"id": 2, "alignment_score": 0.9, "confidence": 0.6},
        {"id": 3, "alignment_score": 0.5, "confidence": 0.5},
    ]
    compressed = compress_by_cluster(test_forecasts)
    print("Compressed:", compressed)
    # export_cluster_memory(compressed, "test_cluster_memory.jsonl")
