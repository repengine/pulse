# dev_tools/pulse_ui_plot.py
"""
Pulse Variable Grapher CLI
Usage:
    python pulse/tools/pulse_ui_plot.py --var hope --file history_logs/vars_run017.jsonl

Features:
- Plot one or more variables over time from Pulse simulation history logs
- Optionally export to PNG image
- Handles missing data, malformed lines, or absent variables gracefully
"""

import argparse
import json
import os
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional


def load_variable_trace(
    file_path: str, var_names: List[str]
) -> Dict[str, Tuple[List[int], List[float]]]:
    """
    Loads variable values across steps from JSONL file.

    Parameters:
        file_path (str): Path to history_logs file
        var_names (List[str]): List of variable names to extract

    Returns:
        Dict[str, Tuple[List[int], List[float]]]: {var_name: ([steps], [values])}
    """
    traces = {var: ([], []) for var in var_names}

    if not os.path.exists(file_path):
        print(f"❌ File '{file_path}' does not exist.")
        return traces

    with open(file_path, "r") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                step = record.get("step")
                variables = record.get("variables", {})
                for var in var_names:
                    val = variables.get(var)
                    if val is not None:
                        traces[var][0].append(step)
                        traces[var][1].append(val)
            except json.JSONDecodeError:
                print("⚠️ Skipping malformed line in JSONL file.")
                continue

    return traces


def plot_variables(
    traces: Dict[str, Tuple[List[int], List[float]]], export_path: Optional[str] = None
):
    """
    Plots one or more variables on a shared timeline.

    Parameters:
        traces (dict): {var_name: (steps, values)}
        export_path (str): Optional path to save image
    """
    plt.figure(figsize=(10, 5))
    for var_name, (steps, values) in traces.items():
        if steps:
            plt.plot(steps, values, label=var_name, marker="o", linewidth=2)

    plt.title("Pulse Variable Timeline")
    plt.xlabel("Simulation Step")
    plt.ylabel("Value")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if export_path:
        try:
            plt.savefig(export_path)
            print(f"📤 Plot exported to {export_path}")
        except Exception as e:
            print(f"❌ Failed to export plot: {e}")
    else:
        plt.show()


def plot_alignment_scores(path: str, path_out: Optional[str] = None, **kwargs):
    """
    Plots alignment scores from JSON or JSONL file.
    Parameters:
        path (str): Path to JSON or JSONL file containing alignment scores
        path_out (str): Optional path to save alignment plot image
        **kwargs: Accepts save_path for backward compatibility
    """
    save_path = kwargs.get("save_path") or path_out
    with open(path, "r") as f:
        if path.endswith(".jsonl"):
            data = [json.loads(line) for line in f if line.strip()]
        else:
            data = json.load(f)

    scores = [d["alignment_score"] for d in data if "alignment_score" in d]
    ids = [d.get("forecast_id", f"fc{i}") for i, d in enumerate(data)]

    plt.figure(figsize=(10, 4))
    plt.bar(ids, scores, color="mediumpurple", edgecolor="black")
    plt.title("Forecast Alignment Index Scores")
    plt.xlabel("Forecast ID")
    plt.ylabel("Alignment Score (0–100)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    if save_path:
        try:
            plt.savefig(save_path)
            print(f"📤 Alignment plot exported to {save_path}")
        except Exception as e:
            print(f"❌ Failed to export alignment plot: {e}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Pulse Variable Grapher")
    parser.add_argument("--file", type=str, help="Path to variable trace file (.jsonl)")
    parser.add_argument(
        "--var", type=str, nargs="+", help="Variable(s) to plot (e.g. hope rage)"
    )
    parser.add_argument(
        "--export", type=str, help="Optional: path to save plot image (e.g. graph.png)"
    )
    parser.add_argument(
        "--alignment", type=str, help="Path to JSON or JSONL with alignment scores"
    )
    parser.add_argument(
        "--save", type=str, help="Optional: path to save alignment plot image"
    )
    args = parser.parse_args()

    if args.alignment:
        plot_alignment_scores(args.alignment, path_out=args.save)
        return

    if args.file and args.var:
        traces = load_variable_trace(args.file, args.var)
        any_found = any(steps for steps, values in traces.values())
        if any_found:
            plot_variables(traces, export_path=args.export)
        else:
            print(f"❌ None of the specified variables were found in {args.file}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
