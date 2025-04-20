"""
PATCHED: ui_test.py
Adds:
- Button: "Check Contradictions"
- Loads forecast batch and runs contradiction checks using forecast_contradiction_sentinel.py
"""

import tkinter as tk
from tkinter import ttk, filedialog
import json

from trust.forecast_contradiction_sentinel import scan_forecast_batch

def check_contradictions_from_ui(app):
    file_path = filedialog.askopenfilename(filetypes=[("JSONL files", "*.jsonl")])
    if not file_path:
        app.log("No file selected.")
        return
    try:
        with open(file_path, "r") as f:
            forecasts = [json.loads(line.strip()) for line in f if line.strip()]
        result = scan_forecast_batch(forecasts)
        app.log("✅ Contradiction Scan Complete:")
        if result["symbolic_conflicts"]:
            app.log(f"⚠️ Symbolic Conflicts ({len(result['symbolic_conflicts'])}):")
            for c in result["symbolic_conflicts"]:
                app.log(f"  {c[0]} ⟷ {c[1]} → {c[2]}")
        if result["capital_conflicts"]:
            app.log(f"⚠️ Capital Conflicts ({len(result['capital_conflicts'])}):")
            for c in result["capital_conflicts"]:
                app.log(f"  {c[0]} ⟷ {c[1]} → {c[2]}")
        if result["confidence_flags"]:
            app.log(f"⚠️ Trust Conflicts (Low confidence): {', '.join(result['confidence_flags'])}")
        if not (result["symbolic_conflicts"] or result["capital_conflicts"] or result["confidence_flags"]):
            app.log("✅ No contradictions detected.")
    except Exception as e:
        app.log(f"❌ Error scanning contradictions: {e}")
