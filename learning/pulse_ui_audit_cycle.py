# pulse/tools/pulse_ui_audit_cycle.py
"""
CLI Tool to compare recursive forecast cycles and output improvement audit.
Usage:
    python pulse/tools/pulse_ui_audit_cycle.py --prev previous.jsonl --curr current.jsonl

Features:
- Computes change in average forecast confidence and retrodiction error
- Summarizes trust label distributions and symbolic arc shifts
- Outputs readable JSON summary to CLI or optionally to file
"""

import argparse
import json
import os
from learning.recursion_audit import generate_recursion_report


def load_forecast_batch(path):
    """
    Load forecast batch from JSONL file.

    Parameters:
        path (str): path to forecast .jsonl file

    Returns:
        List[Dict]: loaded forecast objects
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ File not found: {path}")
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Pulse Recursive Audit CLI")
    parser.add_argument(
        "--prev",
        type=str,
        required=True,
        help="Path to previous forecast batch (.jsonl)",
    )
    parser.add_argument(
        "--curr",
        type=str,
        required=True,
        help="Path to current forecast batch (.jsonl)",
    )
    parser.add_argument(
        "--output", type=str, help="Optional: file path to save audit summary (.json)"
    )
    args = parser.parse_args()

    try:
        previous = load_forecast_batch(args.prev)
        current = load_forecast_batch(args.curr)
        report = generate_recursion_report(previous, current)

        print("\n🔄 Recursive Improvement Report:")
        print(json.dumps(report, indent=2))

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"📤 Report saved to {args.output}")

    except FileNotFoundError as fnf:
        print(f"❌ {fnf}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
