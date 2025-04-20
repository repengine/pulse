"""
Module: pulse_lineage_scorer.py
Pulse Version: v0.100.7
Location: pulse/trust/

Purpose:
Scores symbolic coherence and divergence across a forecast lineage chain.
Detects when a symbolic arc degenerates, inverts, or contradicts its ancestry.

Features:
- Load a lineage map (trace_id → parent_id)
- Compare arc_label and symbolic_tag inheritance
- Detect reversals, decay, or contradiction from parent to child
- CLI support and summary output

Author: Pulse AI Engine
"""

import json
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger("pulse_lineage_scorer")

def build_lineage_map(forecasts: List[Dict]) -> Dict[str, str]:
    """Returns {child_trace_id: parent_trace_id} mapping."""
    lineage = {}
    for f in forecasts:
        tid = f.get("trace_id")
        pid = f.get("parent_id")
        if tid and pid:
            lineage[tid] = pid
    return lineage

def extract_forecast_by_id(forecasts: List[Dict]) -> Dict[str, Dict]:
    """Returns {trace_id: forecast} for fast lookup."""
    return {f["trace_id"]: f for f in forecasts if "trace_id" in f}

def score_arc_integrity(child: Dict, parent: Dict) -> Tuple[str, float]:
    """
    Compare child vs parent arcs:
    Returns (relation, symbolic_drift_score)
    relation: one of "same", "inverted", "rebound", "diverged", "unknown"
    symbolic_drift_score: Euclidean distance between overlays
    """
    arc1 = parent.get("arc_label", "Unknown")
    arc2 = child.get("arc_label", "Unknown")
    relation = "unknown"

    # Determine the relationship between parent and child arc labels
    if arc1 == arc2:
        relation = "same"
    elif "Hope" in arc1 and "Despair" in arc2:
        relation = "inverted"
    elif "Despair" in arc1 and "Hope" in arc2:
        relation = "rebound"
    elif arc1 != arc2:
        relation = "diverged"

    # Calculate symbolic drift score based on overlay differences
    o1 = parent.get("overlays", {})
    o2 = child.get("overlays", {})
    keys = set(o1.keys()).intersection(set(o2.keys()))
    diffs = [(o1[k] - o2[k])**2 for k in keys]
    drift_score = round(sum(diffs) ** 0.5, 4)
    return relation, drift_score

def lineage_arc_summary(forecasts: List[Dict]) -> Dict:
    """
    Summarizes symbolic arc relations across forecast ancestry.
    Returns dict with counts of divergence, inversion, etc.
    """
    lineage = build_lineage_map(forecasts)
    by_id = extract_forecast_by_id(forecasts)

    # Initialize score map to track arc relations and drift statistics
    score_map = {
        "same": 0,
        "inverted": 0,
        "rebound": 0,
        "diverged": 0,
        "unknown": 0,
        "total": 0,
        "avg_drift": 0.0
    }

    drifts = []

    # Iterate through lineage map to score each child-parent relationship
    for child_id, parent_id in lineage.items():
        child = by_id.get(child_id)
        parent = by_id.get(parent_id)
        if child and parent:
            relation, drift = score_arc_integrity(child, parent)
            score_map[relation] += 1
            drifts.append(drift)
            score_map["total"] += 1

    # Calculate average drift score if any drift values exist
    if drifts:
        score_map["avg_drift"] = round(sum(drifts) / len(drifts), 4)

    return score_map

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Lineage Scorer")
    parser.add_argument("--file", required=True, help="Path to forecast lineage .jsonl")
    args = parser.parse_args()

    with open(args.file, "r") as f:
        forecasts = []
        for line in f:
            try:
                forecasts.append(json.loads(line.strip()))
            except Exception as e:
                logger.warning(f"Failed to parse forecast: {e}")
    summary = lineage_arc_summary(forecasts)
    print(json.dumps(summary, indent=2))
