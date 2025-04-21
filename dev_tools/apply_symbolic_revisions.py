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
from symbolic.symbolic_tuning_engine import (
    simulate_revised_forecast,
    compare_scores,
    log_tuning_result
)

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, help="Forecasts to revise (.jsonl)")
    parser.add_argument("--plans", required=True, help="Revision plans (.json)")
    args = parser.parse_args()

    forecasts = load_jsonl(args.batch)
    try:
        with open(args.plans, "r") as f:
            plans = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load plans: {e}")
        return

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
            log_tuning_result(fc, revised)
        except Exception as e:
            print(f"❌ Error processing {trace}: {e}")

def _test_apply_symbolic_revisions():
    print("✅ apply_symbolic_revisions.py test placeholder (CLI only)")

if __name__ == "__main__":
    main()
