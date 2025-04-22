# memory/cluster_mutation_tracker.py

"""
Cluster Mutation Tracker

Identifies the most evolved forecast in each symbolic cluster:
- Deepest ancestry chain
- Maximum symbolic mutation depth
- Ideal long-term memory representative

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import os
import logging
from typing import List, Dict
from collections import defaultdict
from forecast_output.forecast_cluster_classifier import classify_forecast_cluster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mutation_depth(forecast: Dict) -> int:
    """
    Return length of ancestry chain if available.

    Args:
        forecast (Dict): Forecast dictionary, expects 'lineage'->'ancestors' list.

    Returns:
        int: Number of ancestors (mutation depth).
    """
    lineage = forecast.get("lineage", {})
    ancestors = lineage.get("ancestors", [])
    if not isinstance(ancestors, list):
        logger.warning("Ancestors field is not a list in forecast: %s", forecast)
        return 0
    return len(ancestors)


def track_cluster_lineage(forecasts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group forecasts by narrative cluster.

    Args:
        forecasts (List[Dict]): List of forecast dicts.

    Returns:
        Dict[str, List[Dict]]: Mapping from cluster to list of forecasts.
    """
    clusters = defaultdict(list)
    for fc in forecasts:
        cluster = classify_forecast_cluster(fc)
        fc["narrative_cluster"] = cluster
        clusters[cluster].append(fc)
    return clusters


def select_most_evolved(
    clusters: Dict[str, List[Dict]],
    mutation_depth_fn=get_mutation_depth
) -> Dict[str, Dict]:
    """
    Select the most evolved forecast in each cluster.

    Args:
        clusters (Dict[str, List[Dict]]): Clustered forecasts.
        mutation_depth_fn (Callable): Function to compute mutation depth.

    Returns:
        Dict[str, Dict]: Most evolved forecast per cluster.
    """
    leaders = {}
    for cluster, fc_list in clusters.items():
        if not fc_list:
            logger.warning("Cluster '%s' is empty.", cluster)
            continue
        try:
            deepest = max(fc_list, key=mutation_depth_fn)
            leaders[cluster] = deepest
        except Exception as e:
            logger.error("Error selecting most evolved for cluster '%s': %s", cluster, e)
    return leaders


def summarize_mutation_depths(
    clusters: Dict[str, List[Dict]],
    mutation_depth_fn=get_mutation_depth
) -> Dict[str, int]:
    """
    Return mutation depth per cluster.

    Args:
        clusters (Dict[str, List[Dict]]): Clustered forecasts.
        mutation_depth_fn (Callable): Function to compute mutation depth.

    Returns:
        Dict[str, int]: Max mutation depth per cluster.
    """
    summary = {}
    for cluster, fc_list in clusters.items():
        if not fc_list:
            summary[cluster] = 0
            continue
        try:
            summary[cluster] = max(mutation_depth_fn(fc) for fc in fc_list)
        except Exception as e:
            logger.error("Error summarizing mutation depths for cluster '%s': %s", cluster, e)
            summary[cluster] = 0
    return summary


def export_mutation_leaders(leaders: Dict[str, Dict], path: str):
    """
    Save most evolved forecast per cluster to JSONL.

    Args:
        leaders (Dict[str, Dict]): Most evolved forecast per cluster.
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
            for fc in leaders.values():
                f.write(json.dumps(fc, ensure_ascii=False) + "\n")
        os.replace(tmp_path, path)
        logger.info("✅ Exported cluster lineage leaders to %s", path)
    except OSError as e:
        logger.error("❌ Failed to write cluster leaders: %s", e)
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
        {"id": 1, "lineage": {"ancestors": [0]}, "alignment_score": 0.8, "confidence": 0.7},
        {"id": 2, "lineage": {"ancestors": [0, 1]}, "alignment_score": 0.9, "confidence": 0.6},
        {"id": 3, "lineage": {"ancestors": []}, "alignment_score": 0.5, "confidence": 0.5},
    ]
    clusters = track_cluster_lineage(test_forecasts)
    leaders = select_most_evolved(clusters)
    summary = summarize_mutation_depths(clusters)
    print("Leaders:", leaders)
    print("Summary:", summary)
    # export_mutation_leaders(leaders, "test_leaders.jsonl")
