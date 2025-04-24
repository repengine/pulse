# tools/apply_symbolic_upgrades.py

from symbolic_system.symbolic_executor import rewrite_forecast_symbolics, log_symbolic_mutation
import argparse, json
import os

def apply_symbolic_upgrades(batch_path=None, plan_path=None, out_path="revised_forecasts.jsonl"):
    """
    Apply symbolic upgrades to a batch of forecasts using an upgrade plan.
    Args:
        batch_path (str): Path to the input forecasts (.jsonl)
        plan_path (str): Path to the upgrade plan (.json)
        out_path (str): Path to write revised forecasts (.jsonl)
    Returns:
        list: The rewritten forecasts, or [] if error
    """
    if not batch_path or not plan_path:
        raise ValueError("batch_path and plan_path must be provided")
    if not os.path.isfile(batch_path):
        print(f"❌ Batch file not found: {batch_path}")
        return []
    if not os.path.isfile(plan_path):
        print(f"❌ Plan file not found: {plan_path}")
        return []
    try:
        with open(batch_path, "r") as f:
            forecasts = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load batch: {e}")
        return []
    try:
        with open(plan_path, "r") as f:
            upgrade = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load plan: {e}")
        return []
    try:
        rewritten = rewrite_forecast_symbolics(forecasts, upgrade)
    except Exception as e:
        print(f"❌ Error during symbolic rewrite: {e}")
        return []
    try:
        with open(out_path, "w") as f:
            for fc in rewritten:
                f.write(json.dumps(fc) + "\n")
                try:
                    log_symbolic_mutation(fc)
                except Exception as log_e:
                    print(f"⚠️ Logging mutation failed: {log_e}")
        print(f"✅ Wrote revised forecasts to {out_path}")
    except Exception as e:
        print(f"❌ Failed to write output: {e}")
        return []
    return rewritten

def main():
    parser = argparse.ArgumentParser(description="Apply symbolic upgrades to a batch of forecasts using an upgrade plan.")
    parser.add_argument("--batch", required=True, help="Path to input forecasts (.jsonl)")
    parser.add_argument("--plan", required=True, help="Path to upgrade plan (.json)")
    parser.add_argument("--out", default="revised_forecasts.jsonl", help="Output path for revised forecasts (.jsonl)")
    args = parser.parse_args()
    apply_symbolic_upgrades(args.batch, args.plan, args.out)

if __name__ == "__main__":
    main()
