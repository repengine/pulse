# dev_tools/pulse_ui_replay.py
"""
Module: pulse_ui_replay.py
Purpose: Replay simulation traces and visualize symbolic overlays, variables, or tag arcs.
Supports CLI-driven review of .jsonl forecast traces or simulation sequences, with export options.

Author: Pulse AI Engine
Version: v0.4.3
"""

import argparse
import json
import os
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    print("❌ matplotlib is not installed. Please install it with 'pip install matplotlib' to enable plotting.")

from typing import List, Dict, Union


def load_trace(path: str) -> List[Dict]:
    """Load a .jsonl trace file into memory."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def extract_series(trace: List[Dict], mode: str, key: str) -> List[Union[float, None]]:
    """
    Extract a sequence of values for the specified key from a trace.

    Parameters:
        trace: list of state entries
        mode: "variables" or "overlays"
        key: variable/overlay name to extract

    Returns:
def plot_series(values: List[Union[float, None]], title: str, ylabel: str, export_path: Optional{str} = None):
    """Plot a series of float values over simulation steps and optionally export to image."""
    if plt is None:
        print("❌ Plotting is unavailable because matplotlib is not installed.")
        return
    try:
        filtered = [v if isinstance(v, (int, float)) else None for v in values]
        x = list(range(len(filtered)))
        plt.figure(figsize=(8, 4))
        plt.plot(x, filtered, marker="o", linewidth=2)
        plt.title(title)
        plt.xlabel("Step")
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.tight_layout()
        if export_path:
            plt.savefig(export_path)
            print(f"📤 Plot exported to {export_path}")
        else:
            plt.show()
    except Exception as e:
        print(f"❌ Plotting failed: {e}")
            print(f"📤 Plot exported to {export_path}")
        else:
            plt.show()
    except Exception as e:
        print(f"❌ Plotting failed: {e}")


def replay_trace(path: str, mode: str, key: str, export_data: Optional{str} = None, export_plot: Optional{str} = None):
    """Load trace and display or export selected variable/overlay as a graph or JSON series."""
    try:
        trace = load_trace(path)
        values = extract_series(trace, mode=mode, key=key)
        if not any(v is not None for v in values):
            print(f"⚠️ No valid values found for {mode}:{key}")
            return
        if export_data:
            with open(export_data, "w") as f:
                json.dump({"mode": mode, "key": key, "series": values}, f, indent=2)
            print(f"✅ Data exported to {export_data}")
        title = f"{mode.capitalize()} '{key}' over Time"
        plot_series(values, title=title, ylabel=key, export_path=export_plot)
    except Exception as e:
        print(f"❌ Replay error: {e}")


def print_symbolic_tags(path: str, export_path: Optional{str} = None):
    """Print or export symbolic tag sequence from a trace."""
    try:
        trace = load_trace(path)
        lines = [f"Step {i:02d}: {step.get('symbolic_tag', 'N/A')}" for i, step in enumerate(trace)]
        if export_path:
            with open(export_path, "w") as f:
                f.write("\n".join(lines))
            print(f"✅ Symbolic tags exported to {export_path}")
        else:
            print("\n📚 Symbolic Tag Timeline:")
            for line in lines:
                print(line)
    except Exception as e:
        print(f"❌ Error reading trace: {e}")


def main():
    """CLI entrypoint for trace inspection."""
    parser = argparse.ArgumentParser(description="Pulse Trace Replay + Inspector")
    parser.add_argument("--trace", type=str, required=True, help="Path to simulation trace (.jsonl)")
    parser.add_argument("--mode", choices=["overlays", "variables"], help="Mode of inspection")
    parser.add_argument("--key", type=str, help="Variable/overlay name to extract")
    parser.add_argument("--tags", action="store_true", help="Print symbolic tag sequence")
    parser.add_argument("--export-tags", type=str, help="Optional path to save symbolic tag list")
    parser.add_argument("--export-data", type=str, help="Optional path to save extracted value series (JSON)")
    parser.add_argument("--export-plot", type=str, help="Optional path to save plot image (PNG)")
    args = parser.parse_args()

    if args.tags:
        print_symbolic_tags(args.trace, export_path=args.export_tags)
    elif args.mode and args.key:
        replay_trace(args.trace, mode=args.mode, key=args.key,
                     export_data=args.export_data, export_plot=args.export_plot)
    else:
        print("🧠 Usage Examples:")
        print("  --trace file.jsonl --tags")
        print("  --trace file.jsonl --mode overlays --key hope")
        print("  --trace file.jsonl --mode variables --key inflation_index --export-plot arc.png")
        print("  --trace file.jsonl --mode overlays --key rage --export-data rage_series.json")


if __name__ == "__main__":
    main()