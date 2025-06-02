import json
import sys
from collections import Counter
import matplotlib.pyplot as plt


def load_trace(filepath):
    try:
        with open(filepath, "r") as f:
            for line in f:
                yield json.loads(line)
    except Exception as e:
        print(f"Error loading trace: {e}")
        return []


def plot_trace(events, keys=None):
    overlays = keys or ["hope", "despair", "rage", "fatigue"]
    data = {k: [e.get("overlays", {}).get(k, 0.5) for e in events] for k in overlays}
    plt.figure(figsize=(8, 4))
    for k in overlays:
        plt.plot(data[k], label=k)
    plt.title("Symbolic Overlays Over Time")
    plt.xlabel("Step")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_variable(events, var):
    vals = [e.get("variables", {}).get(var, None) for e in events]
    plt.plot(vals)
    plt.title(f"Variable '{var}' Over Time")
    plt.xlabel("Step")
    plt.ylabel(var)
    plt.tight_layout()
    plt.show()


def plot_tags(events):
    tags = [e.get("symbolic_tag", "N/A") for e in events]
    plt.plot(tags)
    plt.title("Symbolic Tags Over Time")
    plt.xlabel("Step")
    plt.ylabel("Tag")
    plt.tight_layout()
    plt.show()


def export_summary(events, out_path):
    try:
        with open(out_path, "w") as f:
            f.write(f"Total events: {len(events)}\n")
            all_keys = Counter()
            for e in events:
                all_keys.update(e.keys())
            f.write(f"Top keys: {all_keys.most_common()}\n")
            if events:
                f.write(f"First event: {events[0]}\n")
        print(f"Summary exported to {out_path}")
    except Exception as e:
        print(f"Export error: {e}")


def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print(
            "Usage: python simulation_trace_viewer.py <trace.jsonl> [--summary] [--plot] [--plot-var var] [--plot-tags] [--export-summary out.txt]"
        )
        return
    filepath = sys.argv[1]
    summary_mode = "--summary" in sys.argv
    plot_mode = "--plot" in sys.argv
    plot_var = None
    if "--plot-var" in sys.argv:
        idx = sys.argv.index("--plot-var")
        if idx + 1 < len(sys.argv):
            plot_var = sys.argv[idx + 1]
    plot_tags_mode = "--plot-tags" in sys.argv
    export_summary_path = None
    if "--export-summary" in sys.argv:
        idx = sys.argv.index("--export-summary")
        if idx + 1 < len(sys.argv):
            export_summary_path = sys.argv[idx + 1]
    events = list(load_trace(filepath))
    if summary_mode:
        print(f"Loaded {len(events)} events from {filepath}")
        if events:
            all_keys = Counter()
            for e in events:
                all_keys.update(e.keys())
            print("Top keys in events:", all_keys.most_common())
            print("First event sample:", events[0])
    elif plot_mode:
        plot_trace(events)
    elif plot_var:
        plot_variable(events, plot_var)
    elif plot_tags_mode:
        plot_tags(events)
    elif export_summary_path:
        export_summary(events, export_summary_path)
    else:
        for i, event in enumerate(events):
            print(f"Event {i}: {event}")


if __name__ == "__main__":
    main()
