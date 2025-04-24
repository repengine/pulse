# tools/apply_symbolic_revisions.py

"""
Apply Symbolic Revisions CLI

Takes a batch of revision_candidate forecasts and revision plans,
simulates revised forecasts, scores them, and logs before/after.

Author: Pulse AI Engine
"""

import argparse
import json
from typing import List, Dict, Any
import os
from symbolic_system.symbolic_tuning_engine import (
    simulate_revised_forecast,
    compare_scores,
    log_tuning_result
)

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        print(f"❌ File not found: {path}")
        return []
    try:
        with open(path, "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return []

def apply_symbolic_revisions(batch_path=None, plans_path=None):
    """
    Apply symbolic revisions to a batch of forecasts using revision plans.
    Args:
        batch_path (str): Path to the input forecasts (.jsonl)
        plans_path (str): Path to the revision plans (.json)
    Returns:
        list: The revised forecasts, or [] if error
    """
    if not batch_path or not plans_path:
        raise ValueError("batch_path and plans_path must be provided")
    forecasts = load_jsonl(batch_path)
    if not forecasts:
        print("❌ No forecasts loaded.")
        return []
    if not os.path.isfile(plans_path):
        print(f"❌ Plans file not found: {plans_path}")
        return []
    try:
        with open(plans_path, "r") as f:
            plans = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load plans: {e}")
        return []
    revised_forecasts = []
    for fc in forecasts:
        trace = fc.get("trace_id")
        plan = next((p["plan"] for p in plans if p.get("trace_id") == trace), None)
        if not plan:
            print(f"⚠️ No plan found for {trace}")
            continue
        try:
            revised = simulate_revised_forecast(fc, plan)
            delta = compare_scores(fc, revised)
            print(f"🔁 {trace} → {delta}")
            revised["revision_plan"] = plan
            try:
                log_tuning_result(fc, revised)
            except Exception as log_e:
                print(f"⚠️ Logging tuning result failed for {trace}: {log_e}")
            revised_forecasts.append(revised)
        except Exception as e:
            print(f"❌ Error processing {trace}: {e}")
    print(f"✅ Revised {len(revised_forecasts)} forecasts out of {len(forecasts)}")
    return revised_forecasts

def main():
    parser = argparse.ArgumentParser(description="Apply symbolic revisions to a batch of forecasts using revision plans.")
    parser.add_argument("--batch", required=True, help="Forecasts to revise (.jsonl)")
    parser.add_argument("--plans", required=True, help="Revision plans (.json)")
    args = parser.parse_args()
    apply_symbolic_revisions(args.batch, args.plans)

if __name__ == "__main__":
    main()
