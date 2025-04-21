# tools/log_forecast_audits.py

"""
Batch Forecast Audit Logger

Runs audit trail generation across a forecast batch (.jsonl).
Appends entries to logs/forecast_audit_trail.jsonl

Author: Pulse AI Engine
"""

import argparse
import json
from trust.forecast_audit_trail import generate_forecast_audit, log_forecast_audit

def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="Pulse Forecast Audit Trail Logger")
    parser.add_argument("--batch", required=True, help="Forecast batch file (.jsonl)")
    parser.add_argument("--current-state", type=str, help="Optional worldstate for retrodiction")
    args = parser.parse_args()

    forecasts = load_jsonl(args.batch)
    current_state = None

    if args.current_state:
        try:
            with open(args.current_state, "r") as f:
                current_state = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load current state: {e}")

    for fc in forecasts:
        audit = generate_forecast_audit(fc, current_state=current_state)
        log_forecast_audit(audit)

    print(f"✅ Logged {len(forecasts)} forecasts to audit trail.")

if __name__ == "__main__":
    main()
