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
from diagnostics.recursion_audit import generate_recursion_report
from dev_tools.pulse_ui_plot import load_variable_trace, plot_variables


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


if __name__ == "__main__":
    main()
