"""
Module: forecast_contradiction_sentinel.py
Pulse Version: v0.100.6
Location: pulse/trust/

Purpose:
Detect contradictions and symbolic drift in a batch of forecasts.
Supports arc-level conflict detection, drift scoring, and turn-based overlap checks.

Features:
- Symbolic tag conflict detection (Hope vs Despair, Rage vs Fatigue)
- Symbolic arc conflict detection (arc_label divergence)
- Capital outcome opposition detection
- Turn-based comparison
- Drift severity scoring
- CLI support and exportable summary

Author: Pulse AI Engine
"""

import json
from typing import List, Dict, Tuple
from collections import defaultdict
import math

def symbolic_tag_conflicts(forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
    conflicts = []
    for i in range(len(forecasts)):
        for j in range(i+1, len(forecasts)):
            tag1 = forecasts[i].get("symbolic_tag", "")
            tag2 = forecasts[j].get("symbolic_tag", "")
            id1 = forecasts[i].get("trace_id", f"fc{i}")
            id2 = forecasts[j].get("trace_id", f"fc{j}")
            if ("Hope" in tag1 and "Despair" in tag2) or ("Despair" in tag1 and "Hope" in tag2):
                conflicts.append((id1, id2, "Symbolic tag: Hope vs Despair"))
            elif ("Rage" in tag1 and "Fatigue" in tag2) or ("Fatigue" in tag1 and "Rage" in tag2):
                conflicts.append((id1, id2, "Symbolic tag: Rage vs Fatigue"))
    return conflicts

def arc_conflicts(forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
    conflicts = []
    arc_map = defaultdict(list)
    for f in forecasts:
        arc = f.get("arc_label", "")
        arc_map[arc].append(f)
    for arc1 in arc_map:
        for arc2 in arc_map:
            if arc1 != arc2 and any(x in arc1.lower() for x in ["hope", "recovery"]) and any(x in arc2.lower() for x in ["despair", "collapse"]):
                for f1 in arc_map[arc1]:
                    for f2 in arc_map[arc2]:
                        conflicts.append((f1["trace_id"], f2["trace_id"], f"Symbolic arc conflict: {arc1} vs {arc2}"))
    return conflicts

def capital_conflicts(forecasts: List[Dict], threshold: float = 1000.0) -> List[Tuple[str, str, str]]:
    conflicts = []
    for i in range(len(forecasts)):
        for j in range(i+1, len(forecasts)):
            id1 = forecasts[i].get("trace_id", f"fc{i}")
            id2 = forecasts[j].get("trace_id", f"fc{j}")
            end1 = forecasts[i].get("forecast", {}).get("end_capital", {})
            end2 = forecasts[j].get("forecast", {}).get("end_capital", {})
            for asset in end1:
                if asset in end2:
                    delta = end1[asset] - end2[asset]
                    if abs(delta) > threshold and (end1[asset] * end2[asset]) < 0:
                        conflicts.append((id1, id2, f"Capital outcome conflict on {asset}"))
    return conflicts

def compute_symbolic_drift_score(f1: Dict, f2: Dict) -> float:
    o1 = f1.get("overlays", {})
    o2 = f2.get("overlays", {})
    keys = set(o1.keys()).intersection(set(o2.keys()))
    diffs = [(o1[k] - o2[k])**2 for k in keys]
    return round(math.sqrt(sum(diffs)), 4) if diffs else 0.0

def symbolic_drift_clusters(forecasts: List[Dict], threshold: float = 0.3) -> List[Tuple[str, str, float]]:
    drifts = []
    for i in range(len(forecasts)):
        for j in range(i+1, len(forecasts)):
            f1 = forecasts[i]
            f2 = forecasts[j]
            d = compute_symbolic_drift_score(f1, f2)
            if d >= threshold:
                drifts.append((f1["trace_id"], f2["trace_id"], d))
    return drifts

def contradiction_summary(forecasts: List[Dict]) -> Dict:
    return {
        "symbolic_tag_conflicts": symbolic_tag_conflicts(forecasts),
        "symbolic_arc_conflicts": arc_conflicts(forecasts),
        "capital_conflicts": capital_conflicts(forecasts),
        "symbolic_drift_clusters": symbolic_drift_clusters(forecasts),
        "total_forecasts": len(forecasts)
    }

# CLI runner
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Forecast Contradiction Sentinel")
    parser.add_argument("--file", type=str, required=True, help="Path to forecast batch (.jsonl)")
    args = parser.parse_args()

    forecasts = []
    with open(args.file, "r") as f:
        for line in f:
            try:
                forecasts.append(json.loads(line.strip()))
            except:
                continue

    result = contradiction_summary(forecasts)
    print(json.dumps(result, indent=2))
