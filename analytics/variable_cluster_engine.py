"""
variable_cluster_engine.py

Clusters simulation variables into interpretable groups based on domain,
correlation, symbolic tags, and historical trust performance.

Used for:
- Worldstate structure analysis
- Scenario summarization
- Drift detection
- Meta-learning pruning

Author: Pulse v0.38
"""

import os
import logging
from collections import defaultdict
from typing import Dict, List, Any
from engine.variable_registry import VARIABLE_REGISTRY
from analytics.variable_performance_tracker import VariablePerformanceTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cluster_by_domain() -> Dict[str, List[str]]:
    """
    Groups variables into clusters by domain (e.g. economic, symbolic).

    Returns:
        Dictionary mapping domain names to lists of variable names.
    """
    clusters: Dict[str, List[str]] = defaultdict(list)
    if not isinstance(VARIABLE_REGISTRY, dict):
        logger.error("VARIABLE_REGISTRY is not a dictionary.")
        return {}
    for var, meta in VARIABLE_REGISTRY.items():
        domain = meta.get("type", "unknown")
        clusters[domain].append(var)
    return dict(clusters)


def cluster_by_tag(tag: str) -> List[str]:
    """
    Extracts variables tagged with a given symbolic or structural label.

    Args:
        tag: The tag to filter variables by.

    Returns:
        List of variable names with the specified tag.
    """
    if not isinstance(VARIABLE_REGISTRY, dict):
        logger.error("VARIABLE_REGISTRY is not a dictionary.")
        return []
    return [v for v, meta in VARIABLE_REGISTRY.items() if tag in meta.get("tags", [])]


def score_cluster_volatility(cluster: List[str]) -> float:
    """
    Uses fragility + certified ratio to compute cluster stability.

    Args:
        cluster: List of variable names in the cluster.

    Returns:
        Volatility score (lower is more stable).
    """
    tracker = VariablePerformanceTracker()
    try:
        scores = tracker.score_variable_effectiveness()
    except Exception as e:
        logger.error(f"Error scoring variable effectiveness: {e}")
        return 0.5  # Default volatility if scoring fails

    if not isinstance(scores, dict):
        logger.warning("VariablePerformanceTracker returned non-dict scores.")
        return 0.5

    total = 0.0
    count = 0
    for var in cluster:
        if var not in scores:
            logger.warning(f"Variable '{var}' missing from performance scores.")
            continue
        frag = scores[var].get("avg_fragility", 0.5)
        cert = scores[var].get("certified_ratio", 0.5)
        volatility = (frag + (1 - cert)) / 2
        total += volatility
        count += 1
    if count == 0:
        logger.warning("No valid variables found in cluster for volatility scoring.")
        return 0.5
    return round(total / count, 4)


def summarize_clusters() -> List[Dict[str, Any]]:
    """
    Builds summary table for each cluster: members, volatility, size.

    Returns:
        List of dictionaries summarizing each cluster.
    """
    domain_clusters = cluster_by_domain()
    result: List[Dict[str, Any]] = []
    for label, vars in domain_clusters.items():
        volatility = score_cluster_volatility(vars)
        result.append(
            {
                "cluster": label,
                "variables": vars,
                "volatility_score": volatility,
                "size": len(vars),
            }
        )
    return sorted(result, key=lambda x: x["volatility_score"], reverse=True)


def test_variable_cluster_engine():
    """
    Basic test for variable cluster engine functions.
    """
    clusters = cluster_by_domain()
    assert isinstance(clusters, dict), "cluster_by_domain should return a dict"
    for domain, vars in clusters.items():
        assert isinstance(vars, list), "Each cluster should be a list"
    tag_vars = cluster_by_tag("test")
    assert isinstance(tag_vars, list), "cluster_by_tag should return a list"
    if clusters:
        first_cluster = next(iter(clusters.values()))
        score = score_cluster_volatility(first_cluster)
        assert isinstance(
            score, float
        ), "score_cluster_volatility should return a float"
    summary = summarize_clusters()
    assert isinstance(summary, list), "summarize_clusters should return a list"
    logger.info("All basic tests passed.")


if __name__ == "__main__":
    print("🧠 Variable Cluster Engine Summary:")
    try:
        clusters = summarize_clusters()
        for c in clusters:
            print(f"\n📦 Cluster: {c['cluster']}  (size: {c['size']})")
            print(f"Volatility Score: {c['volatility_score']}")
            for v in c["variables"]:
                print(f" - {v}")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

    # Optionally run tests
    if os.environ.get("PULSE_TEST", "0") == "1":
        test_variable_cluster_engine()
