# simulation_engine/simulation_drift_detector.py

"""
Simulation Drift Detector

Compares internal simulation artifacts across two runs:
- Rule activation patterns
- Overlay decay trajectories
- Turn counts and collapse states

Identifies system instability or silent logic regressions.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
from typing import List, Dict, Tuple, Optional
from collections import Counter
import os

def load_trace(path: str) -> List[Dict]:
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        result = []
        for line in lines:
            if line.strip():
                try:
                    result.append(json.loads(line))
                except Exception as e:
                    print(f"⚠️ Skipping malformed JSON line: {e}")
        return result
    except Exception as e:
        print(f"❌ Failed to load trace: {e}")
        return []

def compare_rule_patterns(prev: List[Dict], curr: List[Dict]) -> Dict[str, int]:
    """Count how many times each rule was triggered in both runs."""
    def count_rules(trace):
        c = Counter()
        for step in trace:
            for rule_id in step.get("fired_rules", []):
                c[rule_id] += 1
        return c

    prev_counts = count_rules(prev)
    curr_counts = count_rules(curr)
    all_rules = set(prev_counts) | set(curr_counts)

    delta = {r: curr_counts.get(r, 0) - prev_counts.get(r, 0) for r in all_rules}
    return delta

def compare_overlay_trajectories(prev: List[Dict], curr: List[Dict], keys: Optional[List[str]] = None) -> Dict[str, float]:
    """Compare overlay decay paths over time."""
    def get_overlay_series(trace, key):
        return [step.get("overlays", {}).get(key, 0.5) for step in trace]

    keys = keys or ["hope", "despair", "rage", "fatigue", "trust"]
    deltas = {}

    for k in keys:
        p_series = get_overlay_series(prev, k)
        c_series = get_overlay_series(curr, k)
        min_len = min(len(p_series), len(c_series))
        if min_len == 0:
            continue
        delta_sum = sum(abs(p_series[i] - c_series[i]) for i in range(min_len))
        avg_diff = delta_sum / min_len
        deltas[k] = round(avg_diff, 4)
    return deltas

def compare_simulation_structure(prev: List[Dict], curr: List[Dict]) -> Dict:
    """Compare structure-level changes: turns, forks, collapse."""
    return {
        "turn_count_prev": len(prev),
        "turn_count_curr": len(curr),
        "turn_diff": len(curr) - len(prev),
        "collapse_trigger_prev": any("collapse" in step for step in prev),
        "collapse_trigger_curr": any("collapse" in step for step in curr)
    }

def run_simulation_drift_analysis(prev_path: str, curr_path: str, overlay_keys: Optional[List[str]] = None) -> Dict:
    """Run full simulation drift report between two trace logs."""
    prev = load_trace(prev_path)
    curr = load_trace(curr_path)
    if not prev or not curr:
        return {"error": "Unable to load one or both traces."}

    rule_delta = compare_rule_patterns(prev, curr)
    overlay_drift = compare_overlay_trajectories(prev, curr, keys=overlay_keys)
    structure_shift = compare_simulation_structure(prev, curr)

    return {
        "rule_trigger_delta": rule_delta,
        "overlay_drift": overlay_drift,
        "structure_shift": structure_shift,
        "metadata": {
            "source": "simulation_drift_detector.py",
            "prev_path": prev_path,
            "curr_path": curr_path
        }
    }

# CLI hook
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simulation Drift Detector CLI")
    parser.add_argument("--prev", type=str, required=True, help="Path to previous simulation trace (.jsonl)")
    parser.add_argument("--curr", type=str, required=True, help="Path to current simulation trace (.jsonl)")
    parser.add_argument("--export", type=str, help="Path to save JSON output")
    parser.add_argument("--overlays", type=str, help="Comma-separated overlay keys (default: hope,despair,rage,fatigue,trust)")

    args = parser.parse_args()
    overlay_keys = args.overlays.split(",") if args.overlays else None
    try:
        result = run_simulation_drift_analysis(args.prev, args.curr, overlay_keys)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error running drift analysis: {e}")
        result = {"error": str(e)}

    if args.export:
        try:
            with open(args.export, "w") as f:
                json.dump(result, f, indent=2)
            print(f"✅ Saved drift report to {args.export}")
        except Exception as e:
            print(f"❌ Failed to save: {e}")

# --- Simple test function for manual validation ---
def _test_drift_detector():
    """Basic test for drift detector."""
    # Create dummy traces
    prev = [{"fired_rules": ["A"], "overlays": {"hope": 0.5}}, {"fired_rules": ["B"], "overlays": {"hope": 0.6}}]
    curr = [{"fired_rules": ["A", "B"], "overlays": {"hope": 0.7}}, {"fired_rules": ["B"], "overlays": {"hope": 0.8}}]
    import tempfile
    prev_path = tempfile.mktemp(suffix=".jsonl")
    curr_path = tempfile.mktemp(suffix=".jsonl")
    with open(prev_path, "w") as f:
        for step in prev:
            f.write(json.dumps(step) + "\n")
    with open(curr_path, "w") as f:
        for step in curr:
            f.write(json.dumps(step) + "\n")
    print(run_simulation_drift_analysis(prev_path, curr_path))

if __name__ == "__main__":
    pass  # Remove this if you want to run _test_drift_detector()
