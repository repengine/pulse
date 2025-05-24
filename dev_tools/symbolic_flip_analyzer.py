# tools/symbolic_flip_analyzer.py

"""
Symbolic Flip Analyzer CLI

Analyze symbolic arc + tag transition patterns across forecast chains or episodes.

Author: Pulse AI Engine
"""

import argparse
import json
from memory.forecast_episode_tracer import build_episode_chain
from symbolic_system.symbolic_flip_classifier import (
    analyze_flip_patterns,
    detect_loops_or_cycles,
)


def load_forecasts(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def build_chains(forecasts):
    ids = [f.get("trace_id") for f in forecasts if "lineage" in f]
    return [build_episode_chain(forecasts, root_id=tid) for tid in ids]


def main():
    parser = argparse.ArgumentParser(description="Symbolic Flip Analyzer")
    parser.add_argument(
        "--batch", required=True, help="Forecast archive with symbolic data"
    )
    args = parser.parse_args()

    forecasts = load_forecasts(args.batch)
    chains = build_chains(forecasts)

    result = analyze_flip_patterns(chains)
    loops = detect_loops_or_cycles(result["all_flips"])

    print("\n🔁 Top Symbolic Flips:")
    for (a, b), count in result["top_flips"]:
        print(f" - {a} → {b}: {count}x")

    if loops:
        print("\n♻️ Symbolic Loops Detected:")
        for loop_item in loops:
            print(f" - {loop_item}")


if __name__ == "__main__":
    main()
