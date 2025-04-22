"""
rule_cluster_viewer.py

Displays rule clusters by domain and volatility for operator review.
Used in trust diagnostics, mutation targeting, and symbolic system overview.

Author: Pulse v0.38
"""

from simulation_engine.rule_cluster_engine import summarize_rule_clusters

def render_cluster_digest(limit: int = 10, volatility_threshold: float = 0.0):
    clusters = summarize_rule_clusters()
    print("\n📊 Rule Cluster Digest:")
    count = 0
    for c in clusters:
        if c["volatility_score"] < volatility_threshold:
            continue
        count += 1
        print(f"\n📦 Cluster: {c['cluster']}  (size: {c['size']})")
        print(f"Volatility Score: {c['volatility_score']:.3f}")
        for r in c["rules"]:
            print(f" - {r}")
        if count >= limit:
            break

if __name__ == "__main__":
    render_cluster_digest(limit=10, volatility_threshold=0.1)