"""
rule_cluster_engine.py

Clusters and scores simulation rules for mutation targeting, redundancy detection,
and trust evolution. Used in meta-learning and mutation prioritization.

Author: Pulse v0.38 – Full C Test Refined
"""

import json
import os
from typing import Dict, List, Optional
from core.path_registry import PATHS
from collections import defaultdict

RULE_REGISTRY_PATH = PATHS.get("RULE_REGISTRY", "configs/rule_registry.json")
RULE_MUTATION_LOG = PATHS.get("RULE_MUTATION_LOG", "logs/rule_mutation_log.jsonl")


def load_rules(path: Optional[str] = None) -> Dict[str, Dict]:
    """Loads the current rule registry from disk."""
    path = path or RULE_REGISTRY_PATH
    if not os.path.exists(path):
        print(f"[RuleCluster] Missing rule registry at: {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[RuleCluster] Load error: {e}")
        return {}


def cluster_rules_by_domain(rules: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Groups rule IDs by their declared domain for analysis and summarization."""
    clusters = defaultdict(list)
    for rule_id, meta in rules.items():
        domain = meta.get("domain", "unknown")
        clusters[domain].append(rule_id)
    return dict(clusters)


def score_rule_volatility(rules: Dict[str, Dict], log_path: Optional[str] = None) -> Dict[str, float]:
    """
    Uses historical mutation frequency to assess rule instability.
    Returns a normalized volatility score for each rule (0–1).
    """
    log_path = log_path or RULE_MUTATION_LOG
    volatility = defaultdict(int)
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    rule_id = entry.get("mutation", {}).get("rule")
                    if rule_id:
                        volatility[rule_id] += 1
        except Exception as e:
            print(f"[RuleVolatility] Log read failed: {e}")
    max_count = max(volatility.values(), default=1)
    return {rid: round(count / max_count, 4) for rid, count in volatility.items()}


def summarize_rule_clusters(verbose: bool = False) -> List[Dict]:
    """
    Builds a summary of rule clusters with average volatility and member count.

    Returns:
        List[Dict]: cluster summaries with structure:
            - cluster (str): domain label
            - rules (List[str])
            - volatility_score (float)
            - size (int)
    """
    rules = load_rules()
    if not rules:
        return []
    clusters = cluster_rules_by_domain(rules)
    volatility = score_rule_volatility(rules)
    summary = []
    for label, ids in clusters.items():
        v_scores = [volatility.get(r, 0.0) for r in ids]
        avg_v = round(sum(v_scores) / max(1, len(v_scores)), 4)
        summary.append({
            "cluster": label,
            "rules": ids,
            "volatility_score": avg_v,
            "size": len(ids)
        })
        if verbose:
            print(f"[Cluster] {label}: {len(ids)} rules, volatility={avg_v}")
    return sorted(summary, key=lambda x: x["volatility_score"], reverse=True)


def export_cluster_summary(path: str = "logs/rule_cluster_summary.json"):
    """Writes the current rule cluster summary to disk."""
    summary = summarize_rule_clusters()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Rule cluster summary exported to {path}")
    except Exception as e:
        print(f"❌ Failed to export summary: {e}")


if __name__ == "__main__":
    print("🧠 Rule Cluster Summary:")
    clusters = summarize_rule_clusters(verbose=True)
    for c in clusters:
        print(f"\n📦 Domain: {c['cluster']} (size: {c['size']})")
        print(f"Volatility Score: {c['volatility_score']}")
        for r in c['rules']:
            print(f" - {r}")