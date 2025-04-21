# pulse/tools/pulse_arc_cli.py

"""
CLI tool to track symbolic arc frequency, drift, and volatility.
Author: Pulse AI Engine
"""

import argparse
import json
import os
from pulse.symbolic_analysis.pulse_symbolic_arc_tracker import (
    track_symbolic_arcs,
    compare_arc_drift,
    compute_arc_stability,
    plot_arc_distribution,
    export_arc_summary
)


def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Pulse Arc Tracker CLI")
    parser.add_argument("--batch", type=str, help="Path to forecast batch (.jsonl)")
    parser.add_argument("--compare", nargs=2, metavar=("prev", "curr"), help="Compare arc labels across batches")
    parser.add_argument("--export", type=str, help="Path to save arc summary or drift result (JSON)")
    parser.add_argument("--plot", type=str, help="Path to save arc plot (PNG), or leave empty to display")
    args = parser.parse_args()

    if args.compare:
        prev_path, curr_path = args.compare
        prev = load_jsonl(prev_path)
        curr = load_jsonl(curr_path)
        drift = compare_arc_drift(prev, curr)
        volatility = compute_arc_stability(drift)
        print("📈 Arc Drift:")
        for arc, pct in drift.items():
            print(f" - {arc}: {pct:+.2f}%")
        print(f"\n📊 Arc Volatility Score: {volatility}")
        if args.export:
            with open(args.export, "w") as f:
                json.dump({"arc_drift": drift, "volatility": volatility}, f, indent=2)
            print(f"✅ Drift summary saved to {args.export}")
        return

    if args.batch:
        batch = load_jsonl(args.batch)
        arc_counts = track_symbolic_arcs(batch)
        print("📊 Arc Frequencies:")
        for arc, count in arc_counts.items():
            print(f" - {arc}: {count}")
        if args.export:
            export_arc_summary(arc_counts, args.export)
        if args.plot is not None:
            plot_arc_distribution(arc_counts, export_path=args.plot or None)


if __name__ == "__main__":
    main()
