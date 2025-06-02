"""
Pulse Forecast Episode Tracer (CLI)

Usage:
    python tools/trace_forecast_episode.py --batch path.jsonl --root TRACE_ID
"""

import argparse
import json
from analytics.forecast_episode_tracer import (
    build_episode_chain,
    summarize_lineage_drift,
)


def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Forecast Lineage Tracer")
    parser.add_argument("--batch", required=True, help="Forecast archive (.jsonl)")
    parser.add_argument("--root", required=True, help="Trace ID to start from")
    args = parser.parse_args()

    forecasts = load_jsonl(args.batch)
    chain = build_episode_chain(forecasts, args.root)
    summary = summarize_lineage_drift(chain)

    print(f"📜 Episode Chain ({len(chain)} versions):")
    for i, fc in enumerate(chain):
        print(
            f" [{i}] {fc.get('trace_id')} — {fc.get('arc_label')} / {fc.get('symbolic_tag')}"
        )

    print("\n🧠 Symbolic Drift Summary:")
    for k, v in summary.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
