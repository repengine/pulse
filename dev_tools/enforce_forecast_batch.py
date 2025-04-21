# tools/enforce_forecast_batch.py

"""
Forecast Batch License Enforcer

Applies license rules to forecast batch:
- Annotates license status
- Exports only approved forecasts
- Optionally saves rejected ones and summary stats

Author: Pulse AI Engine
"""

import argparse
import json
from trust_system.license_enforcer import (
    annotate_forecasts,
    filter_licensed,
    summarize_license_distribution,
    export_rejected_forecasts
)

def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def save_jsonl(batch, path):
    with open(path, "w") as f:
        for fc in batch:
            f.write(json.dumps(fc) + "\n")
    print(f"✅ Saved {len(batch)} licensed forecasts to {path}")

def main():
    parser = argparse.ArgumentParser(description="Pulse License Enforcer CLI")
    parser.add_argument("--batch", required=True, help="Forecast batch (.jsonl)")
    parser.add_argument("--output", required=True, help="Path to save approved forecasts")
    parser.add_argument("--rejected", type=str, help="Optional: save unlicensed forecasts here")
    parser.add_argument("--summary", action="store_true", help="Print license breakdown")

    args = parser.parse_args()

    forecasts = load_jsonl(args.batch)
    forecasts = annotate_forecasts(forecasts)

    licensed = filter_licensed(forecasts)
    save_jsonl(licensed, args.output)

    if args.rejected:
        export_rejected_forecasts(forecasts, args.rejected)

    if args.summary:
        breakdown = summarize_license_distribution(forecasts)
        print("\n📊 License Summary:")
        for k, v in breakdown.items():
            print(f" - {k}: {v}")

if __name__ == "__main__":
    main()
