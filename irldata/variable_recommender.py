"""
variable_recommender.py

Enhanced module to analyze variable performance logs and recommend variables for PulseGrow.
Supports CSV/JSONL logs, impact/drift metrics, CLI args, and rich metadata registration.

Usage:
    python -m irldata.variable_recommender --top_n 10 --min_count 5 --output recommended_vars.json

Author: Pulse AI Engine
"""
import os
import sys
import argparse
import logging
import json
from typing import List, Dict, Optional

try:
    from memory.pulsegrow import PulseGrow
    pulse_grow = PulseGrow()
except Exception:
    pulse_grow = None

from memory.variable_performance_tracker import VariablePerformanceTracker

logger = logging.getLogger("variable_recommender")
logging.basicConfig(level=logging.INFO)

def load_variable_scores(log_path: str) -> Dict[str, Dict]:
    if not os.path.exists(log_path):
        logger.warning(f"Variable score log not found: {log_path}")
        return {}
    with open(log_path, "r", encoding="utf-8") as f:
        if log_path.endswith(".jsonl"):
            # Aggregate from JSONL
            records = [json.loads(line) for line in f if line.strip()]
        else:
            # Assume JSON summary
            return json.load(f)
    # Aggregate by variable
    scores = {}
    for rec in records:
        var = rec.get("variable")
        if not var:
            continue
        if var not in scores:
            scores[var] = {"count": 0, "confidence": 0.0, "fragility": 0.0, "certified": 0, "alignment": 0.0}
        scores[var]["count"] += 1
        scores[var]["confidence"] += rec.get("confidence", 0)
        scores[var]["fragility"] += rec.get("fragility", 0)
        scores[var]["alignment"] += rec.get("alignment_score", 0)
        if rec.get("certified"):
            scores[var]["certified"] += 1
    # Compute averages
    for var, d in scores.items():
        c = d["count"]
        if c:
            d["avg_confidence"] = round(d["confidence"] / c, 4)
            d["avg_fragility"] = round(d["fragility"] / c, 4)
            d["avg_alignment"] = round(d["alignment"] / c, 4)
            d["certified_ratio"] = round(d["certified"] / c, 4)
    return scores

def recommend_variables_by_impact(tracker: VariablePerformanceTracker, top_n: int = 10, min_count: int = 5) -> List[Dict]:
    scores = tracker.score_variable_effectiveness()
    ranked = sorted(scores.items(), key=lambda x: x[1].get("avg_confidence", 0), reverse=True)
    recommended = []
    for var, stat in ranked:
        if stat["count"] >= min_count:
            recommended.append({"variable": var, **stat})
        if len(recommended) >= top_n:
            break
    return recommended

def detect_drift_prone(tracker: VariablePerformanceTracker, threshold: float = 0.25) -> List[str]:
    return tracker.detect_variable_drift(threshold=threshold)

def register_variables_with_metadata(variables: List[Dict]):
    if not pulse_grow:
        logger.warning("PulseGrow not available.")
        return
    for var in variables:
        metadata = {
            "name": var["variable"],
            "avg_confidence": var.get("avg_confidence"),
            "avg_fragility": var.get("avg_fragility"),
            "certified_ratio": var.get("certified_ratio"),
            "avg_alignment": var.get("avg_alignment"),
            "count": var.get("count"),
        }
        pulse_grow.register_variable(var["variable"], metadata=metadata)
        logger.info(f"Registered variable: {var['variable']} with metadata: {metadata}")

def main():
    parser = argparse.ArgumentParser(description="Recommend variables for PulseGrow based on performance logs.")
    parser.add_argument("--log_path", type=str, default="logs/variable_score_log.jsonl", help="Path to variable score log (JSONL or JSON)")
    parser.add_argument("--top_n", type=int, default=10, help="Number of top variables to recommend")
    parser.add_argument("--min_count", type=int, default=5, help="Minimum count for variable inclusion")
    parser.add_argument("--output", type=str, default=None, help="Output file for recommended variables (JSON)")
    args = parser.parse_args()

    tracker = VariablePerformanceTracker()
    # Load records from log
    if os.path.exists(args.log_path):
        with open(args.log_path, "r", encoding="utf-8") as f:
            if args.log_path.endswith(".jsonl"):
                tracker.records = [json.loads(line) for line in f if line.strip()]
            else:
                # Not expected, but fallback
                tracker.records = json.load(f)
    else:
        logger.warning(f"Log file not found: {args.log_path}")
        sys.exit(1)

    recommended = recommend_variables_by_impact(tracker, top_n=args.top_n, min_count=args.min_count)
    drift_prone = detect_drift_prone(tracker)

    print("\nRecommended variables (top by avg_confidence):")
    for var in recommended:
        print(f"- {var['variable']} (count={var['count']}, avg_conf={var['avg_confidence']}, fragility={var['avg_fragility']}, certified={var['certified_ratio']})")
    print("\nDrift-prone variables:", drift_prone)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"recommended": recommended, "drift_prone": drift_prone}, f, indent=2)
        print(f"\nResults exported to {args.output}")

    register_variables_with_metadata(recommended)

if __name__ == "__main__":
    main()
