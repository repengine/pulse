# dev_tools/pulse_ui_bridge.py
"""
Bridge module to unify CLI and GUI tools for the Pulse Operator Interface.
Exposes recursion audit, trust brief generation, and variable graphing for UI use.

Author: Pulse AI Engine
"""

import json
import os
from learning.recursion_audit import generate_recursion_report
from dev_tools.pulse_ui_plot import load_variable_trace, plot_variables
from tkinter import filedialog, simpledialog


def run_trust_audit_cli(prev_path: str, curr_path: str) -> dict:
    """Compare two forecast cycles and return trust audit summary."""
    try:
        with open(prev_path, "r") as f:
            previous = [json.loads(line.strip()) for line in f if line.strip()]
        with open(curr_path, "r") as f:
            current = [json.loads(line.strip()) for line in f if line.strip()]
        return generate_recursion_report(previous, current)
    except Exception as e:
        return {"error": str(e)}


def generate_markdown_brief(report_path: str, out_path: str = "pulse_brief.md") -> str:
    """Generate a markdown brief from a JSON audit report."""
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
        required_keys = ["confidence_delta", "retrodiction_error_delta", "trust_distribution_current", "arc_shift_summary"]
        if not all(k in data for k in required_keys):
            raise ValueError("Missing one or more required keys in audit report.")

        with open(out_path, "w") as f:
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
        return out_path
    except Exception as e:
        return f"❌ Failed to generate brief: {e}"


def run_variable_graph(path: str, variables: list, export_path: Optional{str} = None) -> str:
    """Plot one or more variables from a history trace."""
    try:
        if not os.path.exists(path):
            return f"❌ File not found: {path}"
        traces = load_variable_trace(path, variables)
        if any(steps for steps, _ in traces.values()):
            plot_variables(traces, export_path=export_path)
            return f"✅ Plot complete for: {', '.join(variables)}"
        return f"⚠️ No data found for variables: {variables}"
    except Exception as e:
        return f"❌ Plot error: {e}"


# Optional: hookable UI helpers

def prompt_and_run_audit(log):
    prev = filedialog.askopenfilename(title="Select previous forecast .jsonl")
    curr = filedialog.askopenfilename(title="Select current forecast .jsonl")
    if not prev or not curr:
        log("Audit cancelled.")
        return
    result = run_trust_audit_cli(prev, curr)
    log("🧠 Recursive Audit Result:")
    log(json.dumps(result, indent=2))


def prompt_and_generate_brief(log):
    report = filedialog.askopenfilename(title="Select audit report .json")
    if not report:
        return
    out = filedialog.asksaveasfilename(defaultextension=".md")
    if not out:
        return
    path = generate_markdown_brief(report, out)
    log(f"📤 Markdown brief saved to: {path}")


def prompt_and_plot_variables(log):
    file = filedialog.askopenfilename(title="Select variable history trace")
    if not file:
        return
    var = simpledialog.askstring("Variable(s)", "Enter variable(s) to plot (comma separated):")
    if not var:
        return
    export = filedialog.asksaveasfilename(defaultextension=".png", title="Export graph image (optional)")
    result = run_variable_graph(file, [v.strip() for v in var.split(",")], export_path=export or None)
    log(result)
