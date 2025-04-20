"""
Module: pulse_lineage_tracker.py
Pulse Version: v0.100.9
Location: trust_system/

Purpose:
Traces how symbolic arcs and rule-based logic evolve across forecast ancestry.
Builds generation chains, identifies shifts, rule persistence, and arc reversals.

Features:
- Build lineage tree (trace_id → parent_id)
- Score arc consistency through lineage depth
- Track rule recurrence across generations
- CLI-ready with summary

Author: Pulse AI Engine
"""

import json
from typing import Dict, List, Tuple
from collections import defaultdict

def build_lineage_tree(forecasts: List[Dict]) -> Dict[str, List[str]]:
    """Returns parent → [child] lineage tree."""
    tree = defaultdict(list)
    for f in forecasts:
        child = f.get("trace_id")
        parent = f.get("parent_id")
        if child and parent:
            tree[parent].append(child)
    return dict(tree)

def group_by_generation(forecasts: List[Dict]) -> Dict[int, List[Dict]]:
    """Organizes forecasts by generation depth."""
    id_to_forecast = {f["trace_id"]: f for f in forecasts if "trace_id" in f}
    generation = {}
    visited = set()

    def depth(tid: str) -> int:
        if tid in visited: return 0
        visited.add(tid)
        f = id_to_forecast.get(tid, {})
        pid = f.get("parent_id")
        return 0 if not pid else 1 + depth(pid)

    for f in forecasts:
        gen = depth(f.get("trace_id", ""))
        generation.setdefault(gen, []).append(f)
    return generation

def arc_evolution_map(forecasts: List[Dict]) -> Dict[str, List[str]]:
    """Map each arc_label to its lineage progression."""
    evolution = defaultdict(list)
    for f in forecasts:
        parent = f.get("parent_id")
        if parent:
            arc = f.get("arc_label", "Unknown")
            evolution[parent].append(arc)
    return dict(evolution)

def rule_recurrence_chain(forecasts: List[Dict]) -> Dict[str, int]:
    """Count how often rules appear across forecast generations."""
    count = defaultdict(int)
    for f in forecasts:
        rule = f.get("rule_id", "")
        if rule:
            count[rule] += 1
    return dict(count)

def lineage_trace_summary(forecasts: List[Dict]) -> Dict:
    gen_map = group_by_generation(forecasts)
    arc_map = arc_evolution_map(forecasts)
    rule_freq = rule_recurrence_chain(forecasts)

    return {
        "generations": {k: len(v) for k, v in gen_map.items()},
        "rule_recurrence": rule_freq,
        "arc_map": arc_map,
        "total_forecasts": len(forecasts)
    }

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Lineage Tracker CLI")
    parser.add_argument("--file", required=True, help="Forecast batch JSONL")
    args = parser.parse_args()

    with open(args.file, "r") as f:
        forecasts = [json.loads(line.strip()) for line in f if line.strip()]
    result = lineage_trace_summary(forecasts)
    print(json.dumps(result, indent=2))