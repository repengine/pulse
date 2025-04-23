# pulse_ui_operator.py
"""
Pulse Operator CLI
Unified foresight console to inspect and evaluate Pulse's recursive intelligence.

Supports:
- Recursion comparison (trust + retrodiction deltas)
- Variable evolution plotting
- Trust audit report
- Operator brief generation (Markdown)

Author: Pulse AI Engine
"""

import argparse
import json
import os
from learning.recursion_audit import generate_recursion_report
from dev_tools.pulse_ui_plot import load_variable_trace, plot_variables
import core.pulse_config
from operator_interface.learning_log_viewer import load_learning_events, summarize_learning_events, render_event_digest
from core.variable_cluster_engine import summarize_clusters
from operator_interface.variable_cluster_digest_formatter import format_variable_cluster_digest_md
from operator_interface.mutation_digest_exporter import export_full_digest
from operator_interface.symbolic_contradiction_digest import format_contradiction_cluster_md

def run_cycle_comparison(prev_path: str, curr_path: str, output: str = None):
    print("🔁 Comparing recursive forecast batches...")
    with open(prev_path, "r") as f:
        previous = [json.loads(line.strip()) for line in f if line.strip()]
    with open(curr_path, "r") as f:
        current = [json.loads(line.strip()) for line in f if line.strip()]
    report = generate_recursion_report(previous, current)
    print("\n📈 Cycle-to-Cycle Audit:")
    print(json.dumps(report, indent=2))
    if output:
        with open(output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"📤 Report saved to {output}")


def run_variable_plot(trace_path: str, variables: list, export: str = None):
    traces = load_variable_trace(trace_path, variables)
    if any(steps for steps, _ in traces.values()):
        plot_variables(traces, export_path=export)
    else:
        print(f"❌ None of the variables {variables} were found in {trace_path}")


def generate_operator_brief(report_path: str, output_md: str):
    try:
        with open(report_path, "r") as f:
            data = json.load(f)

        with open(output_md, "w") as f:
            f.write("# 🧠 Pulse Operator Brief\n\n")
            f.write("## 🔄 Recursive Forecast Audit\n")
            f.write(f"- Confidence Delta: `{data.get('confidence_delta')}`\n")
            f.write(f"- Retrodiction Error Delta: `{data.get('retrodiction_error_delta')}`\n")
            f.write("\n### Trust Label Distribution\n")
            for label, count in data.get("trust_distribution_current", {}).items():
                f.write(f"- {label}: {count}\n")
            f.write("\n### Arc Shift Summary\n")
            for k, v in data.get("arc_shift_summary", {}).items():
                f.write(f"- {k.capitalize()}: {v}\n")
        print(f"✅ Markdown brief generated at {output_md}")
    except Exception as e:
        print(f"❌ Failed to generate brief: {e}")


def run_forecast_pipeline_ui(last_batch=None, log=None):
    """UI helper to run the forecast pipeline on last batch or file."""
    import tkinter
    from tkinter import filedialog, messagebox
    from output.forecast_pipeline_runner import run_forecast_pipeline

    if last_batch and isinstance(last_batch, list) and last_batch:
        forecasts = last_batch
        source = "last simulation batch"
    else:
        path = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not path:
            if log:
                log("⚠️ Pipeline cancelled.")
            return
        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            source = f"file: {path}"
        except Exception as e:
            if log:
                log(f"❌ Failed to load batch: {e}")
            return

    if log:
        log(f"🚦 Running forecast pipeline on {source}...")
    result = run_forecast_pipeline(forecasts)
    if log:
        log(f"✅ Pipeline complete. Status: {result.get('status')}, Total: {result.get('total')}, Digest: {bool(result.get('digest'))}")
    else:
        print(result)


def main():
    parser = argparse.ArgumentParser(description="Pulse Operator CLI")

    parser.add_argument("--compare", nargs=2, metavar=("PREV", "CURR"),
                        help="Compare previous vs current forecast batches (.jsonl)")
    parser.add_argument("--plot-variable", nargs="+", help="Variable(s) to plot over time")
    parser.add_argument("--history", type=str, help="Path to variable trace file")
    parser.add_argument("--export", type=str, help="Optional path to export plot or report")
    parser.add_argument("--brief", type=str, help="Generate operator markdown brief from JSON audit")

    args = parser.parse_args()

    if args.compare:
        prev_path, curr_path = args.compare
        run_cycle_comparison(prev_path, curr_path, output=args.export)

    elif args.plot_variable and args.history:
        run_variable_plot(args.history, args.plot_variable, export=args.export)

    elif args.brief:
        generate_operator_brief(args.brief, output_md=args.export or "pulse_brief.md")

    else:
        print("🧠 Pulse Operator CLI - Available Commands:")
        print("  --compare PREV.jsonl CURR.jsonl [--export audit.json]")
        print("  --plot-variable hope rage --history path/to/vars.jsonl [--export graph.png]")
        print("  --brief path/to/audit.json [--export pulse_brief.md]")
        print(f"[8] Toggle Symbolic Overlays (currently: {core.pulse_config.USE_SYMBOLIC_OVERLAYS})")
        print("[9] Run Forecast Pipeline")
        print("[L] View Learning Log")
        print("[V] View Variable Cluster Volatility")
        print("[B] View Variable Cluster Digest")
        print("[D] Export Full Mutation Digest")
        print("[Y] View Symbolic Contradiction Digest")
        choice = input("Select option: ")
        if choice == "8":
            core.pulse_config.USE_SYMBOLIC_OVERLAYS = not core.pulse_config.USE_SYMBOLIC_OVERLAYS
            print(f"Symbolic overlays now set to: {core.pulse_config.USE_SYMBOLIC_OVERLAYS}")
        elif choice == "9":
            # Try to use last_batch if available, else prompt for file
            try:
                run_forecast_pipeline_ui(
                    last_batch=globals().get("last_batch", None),
                    log=print
                )
            except Exception as e:
                print(f"❌ Pipeline error: {e}")
            return
        elif choice.lower() == "l":
            events = load_learning_events(limit=20)
            if events:
                summary = summarize_learning_events(events)
                print("\n🧾 Learning Summary:")
                for k, v in summary.items():
                    print(f" - {k}: {v} events")
                render_event_digest(events)
            else:
                print("No learning events found.")
        elif choice.lower() == "v":
            clusters = summarize_clusters()
            print("🧠 Variable Cluster Volatility Digest:")
            for c in clusters:
                print(f"\n📦 Cluster: {c['cluster']}  (size: {c['size']})")
                print(f"Volatility Score: {c['volatility_score']}")
                for v in c["variables"]:
                    print(f" - {v}")
        elif choice.lower() == "b":
            print(format_variable_cluster_digest_md())
        elif choice.lower() == "d":
            export_full_digest()
        elif choice.lower() == "y":
            from operator_interface.symbolic_contradiction_digest import load_symbolic_conflict_events
            clusters = load_symbolic_conflict_events()
            print(format_contradiction_cluster_md(clusters))


if __name__ == "__main__":
    main()
