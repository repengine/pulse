# tools/memory_recovery_viewer.py

"""
Blocked Memory Recovery Viewer

Explore, summarize, and export discarded forecasts from
license enforcement gates (e.g., due to drift, low alignment).

Author: Pulse AI Engine
Version: v1.0.1
"""

import argparse
import json
from typing import List, Dict


def load_blocked_forecasts(path: str) -> List[Dict]:
    """Load forecasts from blocked memory log."""
    try:
        with open(path, "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load blocked memory: {e}")
        return []


def summarize_blocked_memory(forecasts: List[Dict]) -> None:
    """Print a count summary by license status."""
    by_reason = {}
    for fc in forecasts:
        reason = fc.get("license_status", "❓ Unlabeled")
        by_reason[reason] = by_reason.get(reason, 0) + 1

    print("\n📉 Blocked Forecast Summary:")
    for reason, count in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f" - {reason}: {count}")


def export_subset(forecasts: List[Dict], reason_filter: str, out_path: str) -> None:
    """Save only forecasts matching a license status."""
    selected = [f for f in forecasts if f.get("license_status") == reason_filter]
    try:
        with open(out_path, "w") as f:
            for fc in selected:
                f.write(json.dumps(fc) + "\n")
        print(f"✅ Exported {len(selected)} forecasts to {out_path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Pulse Blocked Memory Recovery Tool")
    parser.add_argument("--log", type=str, default="logs/blocked_memory_log.jsonl", help="Path to blocked memory log")
    parser.add_argument("--summary", action="store_true", help="Show summary by license reason")
    parser.add_argument("--export", type=str, help="Path to export filtered forecasts")
    parser.add_argument("--reason", type=str, help="Filter: only export forecasts with this license status")

    args = parser.parse_args()
    forecasts = load_blocked_forecasts(args.log)

    if args.summary:
        summarize_blocked_memory(forecasts)

    if args.export and args.reason:
        export_subset(forecasts, args.reason, args.export)


if __name__ == "__main__":
    main()
