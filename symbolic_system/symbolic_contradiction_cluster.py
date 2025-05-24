"""
symbolic_contradiction_cluster.py

Clusters forecasts into contradiction groups based on symbolic overlay divergence,
arc opposition, and narrative alignment mismatch.

Used for symbolic audit, strategic coherence checks, and contradiction memory tagging.

Author: Pulse v0.40
"""

from typing import List, Dict
from collections import defaultdict
from itertools import combinations


def cluster_symbolic_conflicts(forecasts: List[Dict]) -> List[Dict]:
    """
    Groups forecasts by origin_turn and flags symbolic contradictions between them.

    Returns:
        List[Dict]: Each dict has 'origin_turn', 'conflicts': List[Tuple[trace_id_1, trace_id_2, reason]]
    """
    turn_map = defaultdict(list)
    for f in forecasts:
        turn_map[f.get("origin_turn", -1)].append(f)

    results = []
    for turn, group in turn_map.items():
        conflicts = []
        for f1, f2 in combinations(group, 2):
            tid1 = f1.get("trace_id", "?1")
            tid2 = f2.get("trace_id", "?2")
            s1 = f1.get("forecast", {}).get("symbolic_change", {})
            s2 = f2.get("forecast", {}).get("symbolic_change", {})
            hgap = abs(s1.get("hope", 0.5) - s2.get("hope", 0.5))
            dgap = abs(s1.get("despair", 0.5) - s2.get("despair", 0.5))
            if hgap > 0.6 and dgap > 0.6:
                conflicts.append((tid1, tid2, "Hope vs Despair Paradox"))
            if f1.get("arc_label") != f2.get("arc_label"):
                conflicts.append(
                    (
                        tid1,
                        tid2,
                        f"Arc Conflict: {f1.get('arc_label')} vs {f2.get('arc_label')}",
                    )
                )
        if conflicts:
            results.append({"origin_turn": turn, "conflicts": conflicts})
    return results


def summarize_contradiction_clusters(conflict_clusters: List[Dict]) -> None:
    """
    Prints summary of contradiction clusters to CLI.
    """
    print("\n🧠 Symbolic Contradiction Cluster Summary:")
    for c in conflict_clusters:
        print(
            f"\n📦 Origin Turn: {c['origin_turn']} | Conflicts: {len(c['conflicts'])}"
        )
        for a, b, reason in c["conflicts"]:
            print(f" - {a} vs {b} → {reason}")


if __name__ == "__main__":
    # Sample forecast pair for demonstration
    f1 = {
        "trace_id": "T1",
        "origin_turn": 3,
        "arc_label": "Hope Surge",
        "forecast": {"symbolic_change": {"hope": 0.9, "despair": 0.1}},
    }
    f2 = {
        "trace_id": "T2",
        "origin_turn": 3,
        "arc_label": "Collapse Risk",
        "forecast": {"symbolic_change": {"hope": 0.2, "despair": 0.8}},
    }
    cluster = cluster_symbolic_conflicts([f1, f2])
    summarize_contradiction_clusters(cluster)
