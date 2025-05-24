# dev_tools/episode_memory_viewer.py

"""
Symbolic Episode Memory Viewer

CLI utility to explore symbolic memory:
- Summarizes arcs and tags
- Optional plot of arc frequency
- Optional export of summary as JSON

Author: Pulse AI Engine
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import json
from trust_system.forecast_episode_logger import summarize_episodes, plot_episode_arcs


def save_summary(summary, path):
    if not isinstance(summary, dict):
        print("❌ Summary is not a dict.")
        return
    try:
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Summary saved to {path}")
    except Exception as e:
        print(f"❌ Failed to save summary: {e}")


def main():
    parser = argparse.ArgumentParser(description="Symbolic Episode Memory Viewer")
    parser.add_argument(
        "--log",
        type=str,
        default="logs/forecast_episodes.jsonl",
        help="Path to episode log",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print arc and tag summary"
    )
    parser.add_argument(
        "--plot", action="store_true", help="Display arc frequency plot"
    )
    parser.add_argument(
        "--export", type=str, help="Optional path to export summary as JSON"
    )

    args = parser.parse_args()
    summary = summarize_episodes(args.log)

    if args.summary:
        print("\n📊 Episode Summary:")
        for k, v in summary.items():
            print(f" - {k}: {v}")

    if args.export:
        save_summary(summary, args.export)

    if args.plot:
        plot_episode_arcs(args.log)


if __name__ == "__main__":
    main()
    # Example/test usage:
    # python dev_tools/episode_memory_viewer.py --log logs/forecast_episodes.jsonl --summary
