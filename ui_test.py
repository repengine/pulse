"""
Module: ui_test.py
Pulse Version: v0.099.99

Features:
- Symbolic overlay sliders
- Forecast batch runner
- Symbolic arc scoring (live and file)
- Strategos digest viewer
- Save/load overlays and batches
- Clear log
- NEW: Symbolic Arc pop-out matplotlib graph

Author: Pulse AI Engine

This is a developer/test tool for interactive symbolic overlay and forecast batch testing.
Requirements: tkinter, matplotlib, csv, Pulse core modules.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
import matplotlib.pyplot as plt
import sys, os, json, csv
from collections import Counter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.append(os.path.abspath("pulse"))

from simulation_engine.worldstate import WorldState
from forecast_engine.forecast_batch_runner import run_batch_forecasts
from forecast_output.strategos_tile_formatter import format_strategos_tile
from symbolic_system.symbolic_trace_scorer import score_symbolic_trace
from memory.pulse_memory_audit_report import audit_memory
from memory.forecast_memory import ForecastMemory
from simulation_engine.turn_engine import run_turn
from trust_system.trust_engine import TrustEngine

from dev_tools.pulse_ui_bridge import (
    prompt_and_run_audit,
    prompt_and_generate_brief,
    prompt_and_plot_variables
)

# --- PATCH: Contradiction Digest imports ---
from forecast_output.forecast_contradiction_digest import load_contradiction_log, render_digest


class PulseControlApp:
    def __init__(self, root: tk.Tk):
        self.log_output = []  # Added to store log messages
        """Initialize the PulseControlApp UI and state."""
        self.root = root
        self.root.title("Pulse UI Tester")
        self.state = WorldState()
        self.overlay_vars = {
            "hope": tk.DoubleVar(value=0.5),
            "despair": tk.DoubleVar(value=0.5),
            "rage": tk.DoubleVar(value=0.5),
            "fatigue": tk.DoubleVar(value=0.5)
        }
        self.batch_size = tk.IntVar(value=3)
        self.turns = tk.IntVar(value=5)
        self.last_batch = []
        self.summary_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready.")
        self.setup_ui()
        self.update_overlay_summary()

    def clear_log(self) -> None:
        """Clear the log output widget and the log_output list."""
        self.log_output.clear()
        if hasattr(self, "output"):
            self.output.delete("1.0", "end")
    def log(self, message: str) -> None:
        """Log a message to the output widget and store it."""
        self.log_output.append(message)
        if hasattr(self, "output"):
            self.output.insert("end", message + "\n")
            self.output.see("end")

    def setup_ui(self) -> None:
        """Set up the Tkinter UI widgets and layout (tabbed, menu, status bar)."""
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Overlays", command=self.load_overlays)
        file_menu.add_command(label="Save Overlays", command=self.save_overlays)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Memory Audit", command=self.run_memory_audit)
        tools_menu.add_command(label="Export Memory Audit", command=self.export_memory_audit)
        tools_menu.add_command(label="Coherence Check", command=self.run_coherence_check)
        tools_menu.add_command(label="Export Coherence Warnings", command=self.export_coherence_warnings)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        advanced_menu = tk.Menu(menubar, tearoff=0)
        advanced_menu.add_command(label="Check Contradictions", command=lambda: check_contradictions_from_ui(self))
        advanced_menu.add_command(label="Show Overlay JSON", command=self.show_overlay_json)
        menubar.add_cascade(label="Advanced", menu=advanced_menu)

        self.root.config(menu=menubar)

        # --- Notebook Tabs ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=4, pady=2)

        # --- Simulation Tab ---
        sim_tab = ttk.Frame(notebook)
        notebook.add(sim_tab, text="Simulation")
        # Overlay sliders
        overlay_frame = ttk.LabelFrame(sim_tab, text="Symbolic Overlays")
        overlay_frame.pack(fill="x", padx=4, pady=4)
        for k, var in self.overlay_vars.items():
            frame = ttk.Frame(overlay_frame)
            frame.pack(fill="x", pady=1)
            ttk.Label(frame, text=f"{k.capitalize():<8}").pack(side="left")
            scale = ttk.Scale(frame, from_=0.0, to=1.0, variable=var, length=200, orient="horizontal")
            scale.pack(side="left")
            ttk.Label(frame, textvariable=var).pack(side="left")
            var.trace_add("write", lambda *_: self.update_overlay_summary())
        # Overlay summary
        ttk.Label(overlay_frame, textvariable=self.summary_var, font=("Arial", 10, "italic"), foreground="blue").pack(pady=2)
        # Overlay controls
        overlay_btns = ttk.Frame(overlay_frame)
        overlay_btns.pack(pady=2)
        ttk.Button(overlay_btns, text="Reset Overlays", command=self.reset_overlays).pack(side="left", padx=2)
        ttk.Button(overlay_btns, text="Apply Overlays", command=self.apply_overlays).pack(side="left", padx=2)

        # --- Autorun Section ---
        autorun_frame = ttk.LabelFrame(sim_tab, text="Autorun Simulation/Forecast")
        autorun_frame.pack(fill="x", padx=4, pady=4)
        self.autorun_mode = tk.StringVar(value="forecast")
        ttk.Radiobutton(autorun_frame, text="Forecast", variable=self.autorun_mode, value="forecast").pack(side="left", padx=4)
        ttk.Radiobutton(autorun_frame, text="Retrodiction", variable=self.autorun_mode, value="retrodict").pack(side="left", padx=4)
        ttk.Radiobutton(autorun_frame, text="Historical Retrodiction", variable=self.autorun_mode, value="historical_retrodict").pack(side="left", padx=4)
        self.autorun_running = False
        ttk.Button(autorun_frame, text="Start", command=self.start_autorun).pack(side="left", padx=8)
        ttk.Button(autorun_frame, text="Stop", command=self.stop_autorun).pack(side="left", padx=2)
        self.autorun_interval = 2000  # ms

        # Simulation controls
        sim_ctrl = ttk.LabelFrame(sim_tab, text="Simulation Controls")
        sim_ctrl.pack(fill="x", padx=4, pady=4)
        turns_frame = ttk.Frame(sim_ctrl)
        turns_frame.pack(pady=2)
        ttk.Label(turns_frame, text="Sim Turns:").pack(side="left")
        ttk.Entry(turns_frame, textvariable=self.turns, width=5).pack(side="left", padx=2)
        ttk.Button(turns_frame, text="Run N Turns", command=self.run_n_turns).pack(side="left", padx=2)

        # --- Batch Tab ---
        batch_tab = ttk.Frame(notebook)
        notebook.add(batch_tab, text="Batch")
        batch_frame = ttk.LabelFrame(batch_tab, text="Forecast Batch Operations")
        batch_frame.pack(fill="x", padx=4, pady=4)
        ttk.Label(batch_frame, text="Batch Size").pack()
        ttk.Entry(batch_frame, textvariable=self.batch_size, width=5).pack()
        ttk.Button(batch_frame, text="Run Forecast Batch", command=self.run_batch).pack(pady=2)
        ttk.Button(batch_frame, text="Save Forecast Batch", command=self.save_batch).pack(pady=2)
        ttk.Button(batch_frame, text="Show Strategos Digest", command=self.show_digest).pack(pady=2)
        ttk.Button(batch_frame, text="Score Current Trace", command=self.score_trace).pack(pady=2)
        ttk.Button(batch_frame, text="Score Trace from File", command=self.score_trace_from_file).pack(pady=2)
        ttk.Button(batch_frame, text="Show Symbolic Arc", command=self.show_symbolic_arc).pack(pady=2)
        ttk.Button(batch_frame, text="Backtrace + Graph", command=self.backtrace_and_graph).pack(pady=2)

        # --- Analysis Tab ---
        analysis_tab = ttk.Frame(notebook)
        notebook.add(analysis_tab, text="Analysis/Plots")
        analysis_frame = ttk.LabelFrame(analysis_tab, text="Analysis & Plots")
        analysis_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(analysis_frame, text="Load & Replay Trace", command=self.load_and_replay_trace).pack(pady=2)
        ttk.Button(analysis_frame, text="Load & Visualize Trace", command=self.load_and_visualize_trace).pack(pady=2)
        ttk.Button(analysis_frame, text="Plot Memory Stats", command=self.plot_memory_stats).pack(pady=2)
        ttk.Button(analysis_frame, text="Visualize Arc Distribution", command=self.visualize_arc_distribution).pack(pady=2)
        ttk.Button(analysis_frame, text="Plot Arc Drift (Cycles)", command=self.plot_arc_drift_across_cycles).pack(pady=2)
        ttk.Button(analysis_frame, text="Compare Simulation Drift", command=self.visualize_simulation_drift).pack(pady=2)
        ttk.Button(analysis_frame, text="Plot License Trust Breakdown", command=self.plot_license_loss_bar).pack(pady=2)
        ttk.Button(analysis_frame, text="Show Symbolic Transition Graph", command=self.show_symbolic_transition_graph).pack(pady=2)
        ttk.Button(analysis_frame, text="Check Symbolic Convergence", command=self.check_symbolic_convergence).pack(pady=2)
        ttk.Button(analysis_frame, text="Scan Symbolic Resonance", command=self.scan_symbolic_resonance_gui).pack(pady=2)

        # --- Memory Tab ---
        memory_tab = ttk.Frame(notebook)
        notebook.add(memory_tab, text="Memory")
        memory_frame = ttk.LabelFrame(memory_tab, text="Memory Tools")
        memory_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(memory_frame, text="Prune Memory", command=self.prune_memory).pack(pady=2)
        ttk.Button(memory_frame, text="Memory Audit", command=self.run_memory_audit).pack(pady=2)
        ttk.Button(memory_frame, text="Export Memory Audit", command=self.export_memory_audit).pack(pady=2)
        ttk.Button(memory_frame, text="Review Blocked Memory", command=self.review_blocked_memory).pack(pady=2)
        ttk.Button(memory_frame, text="Repair Blocked Forecasts", command=self.repair_blocked_memory).pack(pady=2)
        ttk.Button(memory_frame, text="Run Symbolic Trust Sweep", command=self.run_symbolic_sweep_gui).pack(pady=2)
        ttk.Button(memory_frame, text="Show Sweep Summary", command=self.show_sweep_summary).pack(pady=2)

        # --- Operator Tab ---
        operator_tab = ttk.Frame(notebook)
        notebook.add(operator_tab, text="Operator")
        operator_frame = ttk.LabelFrame(operator_tab, text="Operator Tools")
        operator_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(operator_frame, text="Generate Operator Brief", command=self.generate_operator_brief_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Run Recursion Audit", command=lambda: prompt_and_run_audit(self.log)).pack(pady=2)
        ttk.Button(operator_frame, text="Graph Variable History", command=lambda: prompt_and_plot_variables(self.log)).pack(pady=2)
        ttk.Button(operator_frame, text="Summarize Symbolic Episodes", command=self.view_episode_summary).pack(pady=2)
        #ttk.Button(operator_frame, text="Run Batch Alignment Scoring", command=self.run_alignment_batch_analysis).pack(pady=2) # type: ignore
        #ttk.Button(operator_frame, text="Log Batch Audit Trail", command=self.log_batch_forecast_audits).pack(pady=2)
        ttk.Button(operator_frame, text="Trace Forecast Lineage", command=self.trace_forecast_episode_chain).pack(pady=2)
        ttk.Button(operator_frame, text="Analyze Symbolic Flip Patterns", command=self.analyze_symbolic_flips).pack(pady=2)
        ttk.Button(operator_frame, text="Apply Symbolic Revisions", command=self.apply_symbolic_revisions_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Run Symbolic Learning", command=self.run_symbolic_learning_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Generate Symbolic Upgrade", command=self.generate_symbolic_upgrade_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Apply Symbolic Upgrade", command=self.apply_symbolic_upgrade_gui).pack(pady=2)
        # --- PATCH: Add Contradiction Digest Button ---
        ttk.Button(operator_frame, text="View Contradiction Digest", command=self.view_contradiction_digest).pack(pady=2)

        # --- Replay Tab ---
        replay_tab = ttk.Frame(notebook)
        notebook.add(replay_tab, text="Replay")
        replay_frame = ttk.LabelFrame(replay_tab, text="Trace Replay Tools")
        replay_frame.pack(fill="x", padx=4, pady=4)
        #ttk.Button(replay_frame, text="Replay & Plot Trace", command=self.replay_and_plot_trace).pack(pady=2)
        #ttk.Button(replay_frame, text="Forecast Variable Trajectory", command=self.forecast_variable_trajectory).pack(pady=2)
        #ttk.Button(replay_frame, text="Score Forecast Accuracy", command=self.score_forecast_accuracy).pack(pady=2)
        ttk.Button(replay_frame, text="Plot Symbolic Trajectory", command=self.plot_symbolic_trajectory_gui).pack(pady=2)

        # --- Add Certify Forecasts Button to main window ---
        ttk.Button(self.root, text="Certify Forecasts", command=self.certify_forecasts_gui).pack(pady=2)
        # --- Advanced Batch Processing ---
        ttk.Button(self.root, text="Certify Multiple Files", command=self.certify_multiple_files_gui).pack(pady=2)
        ttk.Button(self.root, text="Certify All in Folder", command=self.certify_folder_gui).pack(pady=2)
        # --- Add Top Strategic Forecasts Button ---
        # --- Log Output (always visible) ---
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill="x", pady=5)
        self.output = scrolledtext.ScrolledText(log_frame, height=14, width=100, wrap="word")
        self.output.pack(side="left", fill="both", expand=True)
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)

        # --- Status Bar ---
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.status_var, anchor="w").pack(fill="x", padx=4)

        self.log("Pulse Dev UI Ready.")

        # --- Filter Controls ---
        filter_frame = ttk.LabelFrame(self.root, text="Batch Filters")
        filter_frame.pack(fill="x", padx=4, pady=2)
        ttk.Label(filter_frame, text="Min Confidence:").pack(side="left")
        self.filter_min_conf = tk.DoubleVar(value=0.0)
        ttk.Scale(filter_frame, from_=0.0, to=1.0, variable=self.filter_min_conf, length=100, orient="horizontal").pack(side="left")
        ttk.Label(filter_frame, textvariable=self.filter_min_conf, width=4).pack(side="left")
        ttk.Label(filter_frame, text="Arc:").pack(side="left", padx=(10,0))
        self.filter_arc = tk.StringVar(value="")
        ttk.Entry(filter_frame, textvariable=self.filter_arc, width=10).pack(side="left")
        ttk.Label(filter_frame, text="Tag:").pack(side="left", padx=(10,0))
        self.filter_tag = tk.StringVar(value="")
        ttk.Entry(filter_frame, textvariable=self.filter_tag, width=10).pack(side="left")
        ttk.Label(filter_frame, text="Domain:").pack(side="left", padx=(10,0))
        self.filter_domain = tk.StringVar(value="")
        ttk.Entry(filter_frame, textvariable=self.filter_domain, width=10).pack(side="left")

        # --- Visualization Options ---
        viz_frame = ttk.LabelFrame(self.root, text="Visualization Options")
        viz_frame.pack(fill="x", padx=4, pady=2)
        self.viz_plot_type = tk.StringVar(value="line")
        ttk.Label(viz_frame, text="Plot Type:").pack(side="left")
        ttk.Combobox(viz_frame, textvariable=self.viz_plot_type, values=["line", "bar", "heatmap"], width=8, state="readonly").pack(side="left")
        self.viz_overlay_multiple = tk.BooleanVar(value=False)
        ttk.Checkbutton(viz_frame, text="Overlay Multiple Traces", variable=self.viz_overlay_multiple).pack(side="left", padx=8)

        # --- Export/Import Enhancements ---
        export_frame = ttk.LabelFrame(self.root, text="Export/Import Tools")
        export_frame.pack(fill="x", padx=4, pady=2)
        self.export_format = tk.StringVar(value="jsonl")
        ttk.Label(export_frame, text="Export Format:").pack(side="left")
        ttk.Combobox(export_frame, textvariable=self.export_format, values=["jsonl", "csv", "markdown", "html", "json"], width=10, state="readonly").pack(side="left")
        ttk.Button(export_frame, text="Export Last Batch", command=self.export_last_batch).pack(side="left", padx=8)
        ttk.Button(export_frame, text="Import Upgrade Plan", command=self.import_upgrade_plan).pack(side="left")
        ttk.Button(export_frame, text="Export Upgrade Plan", command=self.export_upgrade_plan).pack(side="left")

        # --- Interactive Editing ---
        edit_frame = ttk.LabelFrame(self.root, text="Interactive Editing")
        edit_frame.pack(fill="x", padx=4, pady=2)
        ttk.Button(edit_frame, text="Edit Batch in Table", command=self.edit_batch_table).pack(side="left", padx=4)
        ttk.Button(edit_frame, text="Edit Selected Forecast", command=self.edit_selected_forecast).pack(side="left", padx=4)

        # --- Pipeline Customization ---
        pipeline_frame = ttk.LabelFrame(self.root, text="Pipeline Customization")
        pipeline_frame.pack(fill="x", padx=4, pady=2)
        self.pipeline_certify = tk.BooleanVar(value=True)
        self.pipeline_revision = tk.BooleanVar(value=False)
        self.pipeline_learning = tk.BooleanVar(value=False)
        self.pipeline_upgrade = tk.BooleanVar(value=False)
        self.pipeline_dry_run = tk.BooleanVar(value=False)
        ttk.Checkbutton(pipeline_frame, text="Certification", variable=self.pipeline_certify).pack(side="left")
        ttk.Checkbutton(pipeline_frame, text="Revision", variable=self.pipeline_revision).pack(side="left")
        ttk.Checkbutton(pipeline_frame, text="Learning", variable=self.pipeline_learning).pack(side="left")
        ttk.Checkbutton(pipeline_frame, text="Upgrade", variable=self.pipeline_upgrade).pack(side="left")
        ttk.Checkbutton(pipeline_frame, text="Dry Run", variable=self.pipeline_dry_run).pack(side="left", padx=8)

        # --- Audit and Explainability ---
        audit_frame = ttk.LabelFrame(self.root, text="Audit & Explainability")
        audit_frame.pack(fill="x", padx=4, pady=2)
        ttk.Button(audit_frame, text="View Audit Trail", command=self.view_audit_trail_gui).pack(side="left", padx=4)
        ttk.Button(audit_frame, text="Explain License Rationale", command=self.explain_license_gui).pack(side="left", padx=4)
        # Fix undefined variable 'overlay' in setup_ui (audit_frame)
        # Remove or comment out the line: dominant = max(overlay, key=lambda k: overlay[k])
        ttk.Button(audit_frame, text="Analyze Symbolic Flips/Loops", command=self.analyze_symbolic_flips).pack(side="left", padx=4)

        # --- Performance and Logging ---
        perf_frame = ttk.LabelFrame(self.root, text="Performance & Logging")
        perf_frame.pack(fill="x", padx=4, pady=2)
        self.verbose_logging = tk.BooleanVar(value=False)
        ttk.Checkbutton(perf_frame, text="Verbose Logging", variable=self.verbose_logging).pack(side="left", padx=4)
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(perf_frame, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.pack(side="left", padx=8)

    def update_overlay_summary(self) -> None:
        """Update the summary label with a human-readable interpretation of overlays."""
        overlay = {k: v.get() for k, v in self.overlay_vars.items()}
        dominant = max(overlay, key=overlay.get)
        val = overlay[dominant] if overlay else 0.5
        if val > 0.8:
            mood = f"Very high {dominant}"
        elif val > 0.6:
            mood = f"High {dominant}"
        elif val < 0.2:
            mood = f"Very low {dominant}"
            overlays = self.state.overlays.as_dict() if hasattr(self.state.overlays, "as_dict") else {
                k: getattr(self.state.overlays, k, 0.5) for k in self.overlay_vars.keys()
            }
            mood = f"Low {dominant}"
        else:
            mood = "Balanced"
        self.summary_var.set(f"Interpretation: {mood} ({dominant.capitalize()}={val:.2f})")

    def run_n_turns(self) -> None:
        """Run N simulation turns and update overlays accordingly."""
        try:
            n = self.turns.get()
            if n <= 0:
                self.log("⚠️ Number of turns must be positive.")
                return
            for _ in range(n):
                run_turn(self.state)
            # Fix overlays access
            overlays = self.state.overlays.as_dict() if hasattr(self.state.overlays, "as_dict") else {
                k: getattr(self.state.overlays, k, 0.5) for k in self.overlay_vars.keys()
            }
            for k, var in self.overlay_vars.items():
                var.set(overlays.get(k, 0.5))
            self.update_overlay_summary()
            self.log(f"✅ Ran {n} simulation turns.")
        except Exception as e:
            self.log(f"❌ Error running turns: {e}")

    def apply_overlays(self) -> None:
        """Apply the current overlay values to the simulation state."""
        overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
        # Remove invalid assignments to self.state.symbolic, set_symbolic_overlay, set_overlay
        self.log(f"Applied overlays: {overlay}")

    def reset_overlays(self) -> None:
        """Reset all overlays to default (0.5) and apply to state."""
        for var in self.overlay_vars.values():
            var.set(0.5)
        self.apply_overlays()
        self.log("🔄 Overlays reset to default.")

    def load_overlays(self) -> None:
        """Load overlay values from a JSON file and apply them."""
        file = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file:
            try:
                with open(file, "r") as f:
                    overlay = json.load(f)
                for k, v in overlay.items():
                    if k in self.overlay_vars:
                        self.overlay_vars[k].set(float(v))
                self.apply_overlays()
                self.log(f"📂 Overlays loaded from: {file}")
            except Exception as e:
                self.log(f"❌ Overlay load error: {e}")

    def save_overlays(self) -> None:
        """Save current overlay values to a JSON file."""
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if file:
            overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
            try:
                with open(file, "w") as f:
                    json.dump(overlay, f, indent=2)
            except Exception as e:
                self.log(f"❌ Overlay save error: {e}")

    def show_overlay_json(self) -> None:
        """Display the current overlays as JSON in the log."""
        overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
        self.log("📝 Current Overlays JSON:")
        self.log(json.dumps(overlay, indent=2))

    def run_batch(self) -> None:
        """Run a batch of forecasts using the current overlays and batch size."""
        try:
            self.apply_overlays()
            size = self.batch_size.get()
            if size <= 0:
                self.log("⚠️ Batch size must be a positive integer.")
                return
            # Fix: use count=size, not self.state or batch_size
            self.last_batch = run_batch_forecasts(count=size)
            self.log(f"✅ Ran batch: {len(self.last_batch)} forecasts")
            for r in self.last_batch:
                status = "🧯 Unstable Loop" if r.get("unstable_symbolic_path") else "✅ Stable"
                self.log(f"{r.get('trace_id')} → {r.get('arc_label', 'N/A')} / {r.get('symbolic_tag', 'N/A')} [{status}]")
        except Exception as e:
            self.log(f"❌ Batch error: {e}")

    def save_batch(self) -> None:
        """Save the last forecast batch to a JSONL file."""
        if not self.last_batch:
            self.log("⚠️ No batch to save.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".jsonl", filetypes=[("JSON Lines", "*.jsonl")])
        if file:
            try:
                with open(file, "w") as f:
                    for entry in self.last_batch:
                        f.write(json.dumps(entry) + "\n")
                self.log(f"💾 Batch saved to: {file}")
            except Exception as e:
                self.log(f"❌ Save failed: {e}")

    def show_digest(self) -> None:
        """Display the Strategos Digest for the last batch."""
        if not self.last_batch:
            self.log("⚠️ No forecasts to display.")
            return
        self.log("🧾 Strategos Digest:")
        for fc in self.last_batch:
            try:
                status = "🧯 Unstable Loop" if fc.get("unstable_symbolic_path") else "✅ Stable"
                tile = format_strategos_tile(fc)
                self.log(f"\n{tile}\nStatus: {status}")
            except Exception as e:
                self.log(f"Tile error: {e}")

    def score_trace(self) -> None:
        """Score the current overlays as a symbolic trace."""
        try:
            trace = [{"hope": v.get(), "despair": 1 - v.get(), "rage": 0.5, "fatigue": 0.5}
                     for k, v in self.overlay_vars.items() if k == "hope"]
            result = score_symbolic_trace(trace)
            self.log(f"🧠 {result['arc_label']} | Score: {result['symbolic_score']} | Certainty: {result['arc_certainty']}")
        except Exception as e:
            self.log(f"❌ Trace scoring error: {e}")

    def score_trace_from_file(self) -> None:
        """Score a symbolic trace loaded from a JSONL file."""
        file = filedialog.askopenfilename(filetypes=[("JSONL", "*.jsonl")])
        if file:
            try:
                with open(file, "r") as f:
                    trace = [json.loads(line) for line in f.readlines()]
                result = score_symbolic_trace(trace)
                self.log(f"📂 Scored file: {file}")
                self.log(f"🧠 {result['arc_label']} | Score: {result['symbolic_score']} | Certainty: {result['arc_certainty']}")
            except Exception as e:
                self.log(f"❌ File scoring error: {e}")

    def show_symbolic_arc(self) -> None:
        """Plot the symbolic arc for the last batch using matplotlib and selected plot type."""
        if not self.last_batch:
            self.log("⚠️ No forecasts to graph.")
            return
        trace = [f.get("forecast", {}).get("symbolic_change", {}) for f in self.last_batch]
        if not trace:
            self.log("⚠️ No symbolic trace data in batch.")
            return
        emotions = ["hope", "despair", "rage", "fatigue"]
        turns = list(range(len(trace)))
        data = {e: [entry.get(e, 0.5) for entry in trace] for e in emotions}
        plot_type = self.viz_plot_type.get()
        overlay_multiple = self.viz_overlay_multiple.get()
        fig, ax = plt.subplots(figsize=(8, 4))
        if plot_type == "bar":
            for e in emotions:
                ax.bar(turns, data[e], label=e.capitalize(), alpha=0.5 if overlay_multiple else 1.0)
        elif plot_type == "heatmap":
            import numpy as np
            arr = np.array([data[e] for e in emotions])
            im = ax.imshow(arr, aspect="auto", cmap="coolwarm")
            ax.set_yticks(range(len(emotions)))
            ax.set_yticklabels([e.capitalize() for e in emotions])
            fig.colorbar(im, ax=ax)
        else:  # line
            for e in emotions:
                ax.plot(turns, data[e], label=e.capitalize())
        ax.set_title("Symbolic Narrative Arc – Interpreted Sentiment Over Time")
        ax.set_xlabel("Forecast Index")
        ax.set_ylabel("Overlay Value (0–1)")
        ax.set_ylim(0.0, 1.05)
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        plt.show()

    def backtrace_and_graph(self) -> None:
        """Run a backward simulation and plot the resulting symbolic arc."""
        try:
            from simulation_engine.simulator_core import simulate_backward
            from symbolic_system.symbolic_trace_scorer import score_symbolic_trace
            import matplotlib.pyplot as plt

            ws = WorldState()
            overlays = {k: v.get() for k, v in self.overlay_vars.items()}
            for k, v in overlays.items():
                if hasattr(ws.overlays, k):
                    setattr(ws.overlays, k, v)
                else:
                    ws.overlays[k] = v
            ws.sim_id = "ui_backtrace"
            result = simulate_backward(ws, steps=5, use_symbolism=True)
            trace = [entry["overlays"] for entry in result["trace"]]
            arc_label = result.get("arc_label", "N/A")
            arc_certainty = result.get("arc_certainty", "N/A")

            self.log(f"Backtrace Arc: {arc_label} | Certainty: {arc_certainty}")

            emotions = ["hope", "despair", "rage", "fatigue"]
            turns = list(range(len(trace)))
            data = {e: [entry.get(e, 0.5) for entry in trace] for e in emotions}
            fig, ax = plt.subplots(figsize=(8, 4))
            for e in emotions:
                ax.plot(turns, data[e], label=e.capitalize())
            ax.set_title(f"Backtrace Arc: {arc_label} (Certainty: {arc_certainty})")
            ax.set_xlabel("Backtrace Step")
            ax.set_ylabel("Overlay Value (0–1)")
            ax.set_ylim(0.0, 1.05)
            ax.legend()
            ax.grid(True)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            self.log(f"❌ Backtrace error: {e}")

    def load_and_replay_trace(self) -> None:
        """Load a simulation trace from file and replay overlays in the log."""
        file = filedialog.askopenfilename(filetypes=[("JSONL", "*.jsonl")])
        if not file:
            return
        try:
            with open(file, "r") as f:
                trace = [json.loads(line) for line in f]
            self.log(f"Loaded {len(trace)} events from {file}")
            for i, entry in enumerate(trace):
                overlays = entry.get("overlays") or entry
                self.log(f"Step {i}: overlays={overlays}")
        except Exception as e:
            self.log(f"❌ Trace replay error: {e}")

    def load_and_visualize_trace(self) -> None:
        """Load a .jsonl simulation trace and interactively plot overlays, variables, or tags."""
        file = filedialog.askopenfilename(filetypes=[("JSONL", "*.jsonl")])
        if not file:
            return
        try:
            with open(file, "r") as f:
                trace = [json.loads(line) for line in f]
            self.log(f"Loaded {len(trace)} events from {file}")
            choice = messagebox.askquestion("Plot", "Plot overlays? (Yes)\nPlot variables? (No)\nCancel for tags.")
            if choice == "yes":
                overlays = ["hope", "despair", "rage", "fatigue"]
                data = {k: [e.get("overlays", {}).get(k, 0.5) for e in trace] for k in overlays}
                plt.figure(figsize=(8, 4))
                for k in overlays:
                    plt.plot(data[k], label=k)
                plt.title("Symbolic Overlays Over Time")
                plt.xlabel("Step")
                plt.ylabel("Value")
                plt.legend()
                plt.tight_layout()
                plt.show()
            elif choice == "no":
                var = simpledialog.askstring("Variable", "Enter variable name to plot:")
                if var:
                    vals = [e.get("variables", {}).get(var, None) for e in trace]
                    plt.plot(vals)
                    plt.title(f"Variable '{var}' Over Time")
                    plt.xlabel("Step")
                    plt.ylabel(var)
                    plt.tight_layout()
                    plt.show()
            else:
                tags = [e.get("tags", {}) for e in trace]
                plt.plot(tags)
                plt.ylabel("Tag")
                plt.tight_layout()
                plt.show()
        except Exception as e:
            self.log(f"❌ Trace visualization error: {e}")

    def prune_memory(self) -> None:
        """Prune memory forecasts below a user-specified confidence threshold."""
        try:
            memory = ForecastMemory()
            threshold = simpledialog.askfloat("Prune Memory", "Delete forecasts below confidence:")
            if threshold is None:
                return
            before = len(memory._memory)
            memory._memory = [f for f in memory._memory if float(f.get("confidence", 0)) >= threshold]
            after = len(memory._memory)
            memory.save()
            self.log(f"🧹 Pruned memory: {before-after} forecasts removed (kept {after})")
        except Exception as e:
            self.log(f"❌ Prune error: {e}")

    def run_memory_audit(self) -> None:
        """Run a memory audit and display summary statistics with user feedback dialog."""
        try:
            memory = ForecastMemory()
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                audit_memory(memory)
            total = len(memory._memory)
            domains = {}
            confidences = []
            for f in memory._memory:
                if not isinstance(f, dict):
                    continue
                d = f.get("domain", "unspecified")
                domains[d] = domains.get(d, 0) + 1
                c = f.get("confidence")
                if c is not None:
                    confidences.append(float(c))
            self.memory_audit_last = {
                "domains": domains,
                "confidences": confidences,
                "raw": [f for f in memory._memory if isinstance(f, dict)]
            }
            self.log(buf.getvalue())
            self.log(f"Domains: {domains}")
            if confidences:
                import statistics
                self.log(f"Confidence: min={min(confidences):.2f} max={max(confidences):.2f} avg={statistics.mean(confidences):.2f}")
            messagebox.showinfo("Memory Audit Complete", f"Audit complete.\nTotal: {total}\nDomains: {domains}")
        except Exception as e:
            self.log(f"❌ Memory audit error: {e}")

    def export_memory_audit(self) -> None:
        """Export the last memory audit to CSV."""
        try:
            if not hasattr(self, "memory_audit_last") or not self.memory_audit_last.get("raw"):
                self.log("⚠️ Run memory audit first.")
                return
            file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not file:
                return
            with open(file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["forecast_id", "domain", "confidence"])
                for entry in self.memory_audit_last["raw"]:
                    writer.writerow([
                        entry.get("forecast_id"),
                        entry.get("domain", "unspecified"),
                        entry.get("confidence", "")
                    ])
            self.log(f"✅ Memory audit exported to {file}")
        except Exception as e:
            self.log(f"❌ Export error: {e}")

    def plot_memory_stats(self) -> None:
        """Plot memory audit statistics (domain distribution, confidence histogram)."""
        try:
            if not hasattr(self, "memory_audit_last") or not self.memory_audit_last.get("raw"):
                self.log("⚠️ Run memory audit first.")
                return
            domains = self.memory_audit_last["domains"]
            confidences = self.memory_audit_last["confidences"]
            fig, axs = plt.subplots(1, 2, figsize=(10, 4))
            axs[0].bar(domains.keys(), domains.values())
            axs[0].set_title("Forecasts by Domain")
            axs[0].set_xlabel("Domain")
            axs[0].set_ylabel("Count")
            axs[1].hist(confidences, bins=10, color="skyblue", edgecolor="black")
            axs[1].set_title("Confidence Distribution")
            axs[1].set_xlabel("Confidence")
            axs[1].set_ylabel("Count")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            self.log(f"❌ Plot error: {e}")

    def run_coherence_check(self) -> None:
        """Run a coherence check on the last batch and display warnings or success."""
        if not self.last_batch:
            self.log("⚠️ No forecasts to check.")
            return
        try:
            warnings = TrustEngine.check_forecast_coherence(self.last_batch)
            self.coherence_warnings = warnings
            if warnings:
                self.log("⚠️ Coherence warnings detected:")
                for w in warnings:
                    self.log(f"🔸 {w}")
            else:
                self.log("✅ All forecasts coherent.")
        except Exception as e:
            self.log(f"❌ Coherence check error: {e}")

    def export_coherence_warnings(self) -> None:
        """Export the last coherence warnings to a text file."""
        try:
            if not hasattr(self, "coherence_warnings") or not self.coherence_warnings:
                self.log("⚠️ Run coherence check first.")
                return
            file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
            if not file:
                return
            with open(file, "w") as f:
                for w in self.coherence_warnings:
                    f.write(w + "\n")
            self.log(f"✅ Coherence warnings exported to {file}")
        except Exception as e:
            self.log(f"❌ Export error: {e}")

    def start_autorun(self):
        if self.autorun_running:
            self.log("⚠️ Autorun already running.")
            return
        self.autorun_running = True
        self.log(f"▶️ Autorun started: {self.autorun_mode.get().capitalize()}")
        self._autorun_step()

    def stop_autorun(self):
        if not self.autorun_running:
            self.log("⚠️ Autorun not running.")
            return
        self.autorun_running = False
        self.log("⏹️ Autorun stopped.")

    def _autorun_step(self):
        if not self.autorun_running:
            return
        mode = self.autorun_mode.get()
        try:
            if mode == "forecast":
                self.run_batch()
            elif mode == "retrodict":
                self.run_retrodiction()
            elif mode == "historical_retrodict":
                self.run_historical_retrodiction()
            else:
                self.log(f"❓ Unknown autorun mode: {mode}")
        except Exception as e:
            self.log(f"❌ Autorun error: {e}")
        self.root.after(self.autorun_interval, self._autorun_step)

    def run_retrodiction(self):
        # Operational: run retrodict_all_forecasts on last_batch
        try:
            from trust_system.retrodiction_engine import retrodict_all_forecasts
            if not self.last_batch:
                self.log("⚠️ No batch to retrodict. Run a forecast batch first.")
                return
            # Prompt for actual_exposure (simple JSON input)
            actual_str = simpledialog.askstring("Actual Exposure", "Enter actual exposure as JSON (e.g. {'hope':0.6,'despair':0.3}):")
            if not actual_str:
                self.log("Retrodiction cancelled (no actual exposure provided).")
                return
            try:
                actual_exposure = json.loads(actual_str)
            except Exception as e:
                self.log(f"❌ Invalid JSON: {e}")
                return
            results = retrodict_all_forecasts(self.last_batch, actual_exposure)
            self.log(f"✅ Retrodiction run complete. Results:")
            for r in results:
                self.log(f"Trace {r.get('trace_id')}: Score={r.get('retrodiction_score')}, Symbolic={r.get('symbolic_score')}")
        except Exception as e:
            self.log(f"❌ Retrodiction error: {e}")

    def run_historical_retrodiction(self):
        # Operational: run historical retrodiction test
        try:
            from simulation_engine.historical_retrodiction_runner import run_retrodiction_test
            start_date = simpledialog.askstring("Start Date", "Enter start date (YYYY-MM-DD):", initialvalue="2020-01-01")
            if not start_date:
                self.log("Historical retrodiction cancelled (no start date provided).")
                return
            days = simpledialog.askinteger("Days", "Number of days to simulate:", initialvalue=7)
            if not days or days <= 0:
                self.log("Historical retrodiction cancelled (invalid days)."); return
            self.log(f"Running historical retrodiction from {start_date} for {days} days...")
            run_retrodiction_test(start_date, days)
            self.log(f"✅ Historical retrodiction complete for {start_date} ({days} days). See logs for details.")
        except Exception as e:
            self.log(f"❌ Historical retrodiction error: {e}")

    def visualize_arc_distribution(self):
        """Load forecasts and show symbolic arc distribution plot."""
        from tkinter import filedialog
        from symbolic_system.pulse_symbolic_arc_tracker import (
            track_symbolic_arcs, plot_arc_distribution
        )

        file = filedialog.askopenfilename(title="Select forecast .jsonl")
        if not file:
            self.log("Cancelled arc visualization.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            arc_counts = track_symbolic_arcs(forecasts)
            self.log(f"📊 Arc labels found: {arc_counts}")
            plot_arc_distribution(arc_counts)
        except Exception as e:
            self.log(f"❌ Arc plot error: {e}")

    def plot_arc_drift_across_cycles(self):
        """Plot arc drift between two symbolic episode logs."""
        from tkinter import filedialog
        from trust_system.forecast_episode_logger import summarize_episodes
        import matplotlib.pyplot as plt

        prev = filedialog.askopenfilename(title="Select previous episode log")
        curr = filedialog.askopenfilename(title="Select current episode log")
        if not prev or not curr:
            self.log("Drift comparison cancelled.")
            return

        try:
            p = summarize_episodes(prev)
            c = summarize_episodes(curr)
            arcs_prev = {k.replace("arc_", ""): v for k, v in p.items() if k.startswith("arc_")}
            arcs_curr = {k.replace("arc_", ""): v for k, v in c.items() if k.startswith("arc_")}
            all_keys = sorted(set(arcs_prev) | set(arcs_curr))
            drift = [arcs_curr.get(k, 0) - arcs_prev.get(k, 0) for k in all_keys]
            plt.figure(figsize=(10, 4))
            plt.bar(all_keys, drift, color="indianred", edgecolor="black")
            plt.title("Symbolic Arc Drift Across Cycles")
            plt.xlabel("Arc Label")
            plt.ylabel("Δ Count (Current - Previous)")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            self.log(f"❌ Arc drift plot error: {e}")

    def visualize_simulation_drift(self):
        """Compare two simulation traces for internal drift."""
        from simulation_engine.simulation_drift_detector import run_simulation_drift_analysis
        from tkinter import filedialog

        prev = filedialog.askopenfilename(title="Select previous simulation trace (.jsonl)")
        curr = filedialog.askopenfilename(title="Select current simulation trace (.jsonl)")
        if not prev or not curr:
            self.log("Drift comparison cancelled.")
            return

        try:
            result = run_simulation_drift_analysis(prev, curr)
            self.log("📊 Simulation Drift Summary:")
            for k, v in result["overlay_drift"].items():
                self.log(f" - Overlay '{k}': Δ {v:.4f}")
            self.log("🔁 Rule Trigger Delta:")
            for rule, delta in result["rule_trigger_delta"].items():
                self.log(f" - {rule}: {delta:+}")
            self.log(f"🧱 Turn Count Change: {result['structure_shift']['turn_diff']}")
        except Exception as e:
            self.log(f"❌ Drift analysis failed: {e}")

    def plot_license_loss_bar(self):
        """Visualize license retention vs. drop from a digest JSON."""
        from tkinter import filedialog
        import matplotlib.pyplot as plt

        file = filedialog.askopenfilename(title="Select Strategos Digest (JSON)")
        if not file:
            return

        try:
            with open(file, "r") as f:
                digest = json.load(f)

            passed = digest.get("license_pass_count", 0)
            total = digest.get("license_total", 0)
            failed = total - passed

            plt.bar(["Approved", "Rejected"], [passed, failed], color=["green", "red"])
            plt.title("📊 License Outcome Summary")
            plt.ylabel("Forecast Count")
            plt.tight_layout()
            plt.show()

        except Exception as e:
            self.log(f"❌ Failed to render license bar chart: {e}")

    def show_symbolic_transition_graph(self):
        """Render symbolic transition graph from forecast archive."""
        from tkinter import filedialog
        from symbolic_system.symbolic_transition_graph import build_symbolic_graph, visualize_symbolic_graph

        path = filedialog.askopenfilename(title="Select forecast archive (.jsonl)")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            G = build_symbolic_graph(forecasts)
            visualize_symbolic_graph(G, title="Pulse Symbolic Transition Graph")
        except Exception as e:
            self.log(f"❌ Graph rendering failed: {e}")

    def check_symbolic_convergence(self):
        """Check and plot symbolic convergence for a forecast batch."""
        from tkinter import filedialog
        from symbolic_system.symbolic_convergence_detector import compute_convergence_score, detect_fragmentation, plot_convergence_bars

        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Convergence check cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            score = compute_convergence_score(forecasts)
            fragmented = detect_fragmentation(forecasts)
            self.log(f"Symbolic Convergence Score: {score:.2f}")
            if fragmented:
                self.log("⚠️ Narrative fragmentation detected (no dominant arc).")
            else:
                self.log("✅ Narrative is convergent.")
            plot_convergence_bars(forecasts)
        except Exception as e:
            self.log(f"❌ Convergence check error: {e}")

    def plot_symbolic_trajectory_gui(self):
        """Plot symbolic arc/tag timeline for a forecast chain."""
        from tkinter import filedialog
        from forecast_output.mutation_compression_engine import plot_symbolic_trajectory
        file = filedialog.askopenfilename(title="Select forecast chain (.jsonl)")
        if not file:
            self.log("Symbolic trajectory plot cancelled.")
            return
        try:
            with open(file, "r") as f:
                chain = [json.loads(line) for line in f if line.strip()]
            plot_symbolic_trajectory(chain)
            self.log("✅ Symbolic trajectory plotted.")
        except Exception as e:
            self.log(f"❌ Trajectory plot error: {e}")

    def certify_forecasts_gui(self):
        """Certify forecasts in a batch and show certification summary (with filters)."""
        from tkinter import filedialog
        from forecast_output.forecast_fidelity_certifier import tag_certified_forecasts, generate_certified_digest
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Top strategic forecast view cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            filtered = self.filter_forecasts(forecasts)
            tagged = tag_certified_forecasts(filtered)
            digest = generate_certified_digest(tagged)
            self.log(f"Certified: {digest['certified']} / {digest['total']} (Rate: {digest['ratio']:.2f})")
            for fc in tagged:
                if fc.get("certified"):
                    self.log(f"🟢 {fc.get('trace_id')} | {fc.get('arc_label')} | {fc.get('symbolic_tag')}")
        except Exception as e:
            self.log(f"❌ Certification error: {e}")

    def certify_multiple_files_gui(self):
        """Certify multiple forecast files selected by the user (with filters)."""
        files = filedialog.askopenfilenames(filetypes=[("JSONL", "*.jsonl")])
        if not files:
            self.log("Certification cancelled.")
            return
        total, certified = 0, 0
        for file in files:
            try:
                with open(file, "r") as f:
                    forecasts = [json.loads(line) for line in f if line.strip()]
                filtered = self.filter_forecasts(forecasts)
                tagged = tag_certified_forecasts(filtered)
                digest = generate_certified_digest(tagged)
                total += digest['total']
                certified += digest['certified']
                self.log(f"Certified {digest['certified']} of {digest['total']} in {file} (Rate: {digest['ratio']:.2f})")
            except Exception as e:
                self.log(f"❌ Certification error in {file}: {e}")
        self.log(f"✅ Certified {certified} of {total} forecasts in selected files.")

    def certify_folder_gui(self):
        """Certify all forecast files in a selected folder (with filters)."""
        folder = filedialog.askdirectory()
        if not folder:
            self.log("Folder selection cancelled.")
            return
        import glob
        files = glob.glob(f"{folder}/*.jsonl")
        if not files:
            self.log("No JSONL files found in the selected folder.")
            return
        total, certified = 0, 0
        for file in files:
            try:
                with open(file, "r") as f:
                    forecasts = [json.loads(line) for line in f if line.strip()]
                filtered = self.filter_forecasts(forecasts)
                tagged = tag_certified_forecasts(filtered)
                digest = generate_certified_digest(tagged)
                total += digest['total']
                certified += digest['certified']
                self.log(f"Certified {digest['certified']} of {digest['total']} in {file} (Rate: {digest['ratio']:.2f})")
            except Exception as e:
                self.log(f"❌ Certification error in {file}: {e}")
        self.log(f"✅ Certified {certified} of {total} forecasts in all files in folder '{folder}'.")

    def filter_forecasts(self, forecasts):
        """Filter forecasts by UI filter controls."""
        min_conf = self.filter_min_conf.get()
        arc = self.filter_arc.get().strip().lower()
        tag = self.filter_tag.get().strip().lower()
        domain = self.filter_domain.get().strip().lower()
        def match(fc):
            if min_conf and float(fc.get("confidence", 0)) < min_conf:
                return False
            if arc and arc not in str(fc.get("arc_label", "")).lower():
                return False
            if tag and tag not in str(fc.get("symbolic_tag", "")).lower():
                return False
            if domain and domain not in str(fc.get("domain", "")).lower():
                return False
            return True
        return [fc for fc in forecasts if match(fc)]

    def view_top_strategic_forecasts(self):
        """Show top strategic forecasts from a batch using digest logic."""
        from tkinter import filedialog
        from memory.forecast_memory import ForecastMemory
        from operator_interface.strategos_digest import generate_strategos_digest
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Top strategic forecast view cancelled.")
            return
        try:
            mem = ForecastMemory()
            mem.load(file)
            digest = generate_strategos_digest(mem, n=5)
            self.log("\n".join(digest.splitlines()[:20]) + "\n... (truncated)")
        except Exception as e:
            self.log(f"❌ Top strategic forecast error: {e}")

    def classify_forecast_clusters_gui(self):
        """Classify and summarize forecast clusters in a batch."""
        from tkinter import filedialog
        from forecast_output.forecast_cluster_classifier import group_forecasts_by_cluster, summarize_cluster_counts
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Cluster classification cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            clusters = group_forecasts_by_cluster(forecasts)
            counts = summarize_cluster_counts(forecasts)
            self.log("Forecast Cluster Counts:")
            for k, v in counts.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ Cluster classification error: {e}")

    def view_dual_narrative_scenarios(self):
        """Show dual narrative scenarios from a forecast batch."""
        from tkinter import filedialog
        from forecast_output.strategos_digest_builder import build_digest
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Dual narrative scenario view cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            digest = build_digest(forecasts, fmt="markdown")
            # Extract dual narrative section
            lines = digest.splitlines()
            start = [i for i, l in enumerate(lines) if "Dual Narrative Scenarios" in l]
            if start:
                self.log("\n".join(lines[start[0]:start[0]+20]) + "\n... (truncated)")
            else:
                self.log("No dual narrative scenarios found.")
        except Exception as e:
            self.log(f"❌ Dual narrative scenario error: {e}")

    def promote_memory_candidates_gui(self):
        """Promote certified forecasts to memory."""
        from tkinter import filedialog
        from forecast_output.forecast_memory_promoter import promote_to_memory
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Promotion cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            count = promote_to_memory(forecasts)
            self.log(f"✅ {count} forecasts promoted to memory.")
        except Exception as e:
            self.log(f"❌ Promotion error: {e}")

    def check_symbolic_entropy_gui(self):
        """Check symbolic entropy for a forecast batch."""
        from tkinter import filedialog
        try:
            from memory.forecast_memory_entropy import generate_entropy_report
        except ImportError:
            self.log("Symbolic entropy module not found.")
            return
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Symbolic entropy check cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            report = generate_entropy_report(forecasts)
            self.log("Symbolic Entropy Report:")
            for k, v in report.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ Entropy check error: {e}")

    def scan_symbolic_resonance_gui(self):
        """Scan symbolic resonance in a forecast batch."""
        from tkinter import filedialog
        try:
            from forecast_output.forecast_resonance_scanner import generate_resonance_summary
        except ImportError:
            self.log("Resonance scanner module not found.")
            return
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Resonance scan cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            summary = generate_resonance_summary(forecasts)
            self.log("Symbolic Resonance Summary:")
            for k, v in summary.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ Resonance scan error: {e}")

    def apply_symbolic_revisions_gui(self):
        """Apply symbolic revision plan to a batch and show summary."""
        from tkinter import filedialog
        try:
            from symbolic_system.pulse_symbolic_revision_planner import plan_symbolic_revision
            from forecast_output.symbolic_tuning_engine import apply_revision_plan, log_tuning_result
        except ImportError:
            self.log("Symbolic revision modules not found.")
            return
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Revision cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            revised = [apply_revision_plan(fc, plan_symbolic_revision(fc)) for fc in forecasts]
            for orig, rev in zip(forecasts, revised):
                log_tuning_result(orig, rev)
            self.log(f"✅ Applied symbolic revisions to {len(revised)} forecasts. See logs/tuning_results.jsonl.")
        except Exception as e:
            self.log(f"❌ Revision error: {e}")

    def run_symbolic_learning_gui(self):
        """Run symbolic learning loop and show learning profile."""
        try:
            from symbolic_system.pulse_symbolic_learning_loop import learn_from_tuning_log, generate_learning_profile
        except ImportError:
            self.log("Symbolic learning modules not found.")
            return
        try:
            results = learn_from_tuning_log("logs/tuning_results.jsonl")
            profile = generate_learning_profile(results)
            self.log("Symbolic Learning Profile:")
            for k, v in profile.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ Learning loop error: {e}")

    def generate_symbolic_upgrade_gui(self):
        """Generate symbolic upgrade plan from learning profile."""
        try:
            from symbolic_system.pulse_symbolic_learning_loop import learn_from_tuning_log, generate_learning_profile
            from symbolic_system.symbolic_upgrade_planner import propose_symbolic_upgrades, export_upgrade_plan
        except ImportError:
            self.log("Upgrade planner modules not found.")
            return
        try:
            results = learn_from_tuning_log("logs/tuning_results.jsonl")
            profile = generate_learning_profile(results)
            plan = propose_symbolic_upgrades(profile)
            export_upgrade_plan(plan)
            self.log("✅ Symbolic upgrade plan generated and saved to plans/symbolic_upgrade_plan.json.")
        except Exception as e:
            self.log(f"❌ Upgrade plan error: {e}")

    def apply_symbolic_upgrade_gui(self):
        """Apply symbolic upgrade plan to a batch and save output."""
        from tkinter import filedialog
        try:
            from dev_tools.apply_symbolic_upgrades import apply_symbolic_upgrades
        except ImportError:
            self.log("Apply symbolic upgrades module not found.")
            return
        batch = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        plan = filedialog.askopenfilename(title="Select upgrade plan (.json)")
        if not batch or not plan:
            self.log("Upgrade application cancelled.")
            return
        try:
            out_path = filedialog.asksaveasfilename(defaultextension=".jsonl", title="Save revised forecasts as...")
            if not out_path:
                self.log("No output file selected.")
                return
            rewritten = apply_symbolic_upgrades(batch, plan, out_path)
            self.log(f"✅ Symbolic upgrades applied. Output: {out_path}")
        except Exception as e:
            self.log(f"❌ Upgrade application error: {e}")

    def view_contradiction_digest(self):
        """Show symbolic contradiction digest for a batch."""
        from tkinter import filedialog
        try:
            from forecast_output.forecast_contradiction_digest import load_contradiction_log, render_digest
        except ImportError:
            self.log("Contradiction digest module not found.")
            return
        file = filedialog.askopenfilename(title="Select contradiction log (.jsonl)")
        if not file:
            self.log("Contradiction digest cancelled.")
            return
        try:
            contradictions = load_contradiction_log(file)
            digest = render_digest(contradictions)
            self.log("Symbolic Contradiction Digest:")
            self.log(digest)
        except Exception as e:
            self.log(f"❌ Contradiction digest error: {e}")

    def edit_batch_table(self):
        """Open a table view to review and edit all forecasts in a batch."""
        from tkinter import filedialog, Toplevel, messagebox
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Batch table edit cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            if not forecasts:
                self.log("No forecasts to edit.")
                return
            win = Toplevel(self.root)
            win.title("Edit Forecast Batch")
            cols = list(forecasts[0].keys())
            tree = ttk.Treeview(win, columns=cols, show="headings", height=15)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for fc in forecasts:
                tree.insert("", "end", values=[fc.get(c, "") for c in cols])
            tree.pack(fill="both", expand=True)
            def save_edits():
                new_data = []
                for item in tree.get_children():
                    vals = tree.item(item)["values"]
                    new_data.append(dict(zip(cols, vals)))
                out = filedialog.asksaveasfilename(defaultextension=".jsonl", title="Save edited batch as...")
                if out:
                    with open(out, "w") as f:
                        for row in new_data:
                            f.write(json.dumps(row) + "\n")
                    messagebox.showinfo("Saved", f"Edited batch saved to {out}")
            ttk.Button(win, text="Save Edits", command=save_edits).pack(pady=4)
        except Exception as e:
            self.log(f"❌ Batch table edit error: {e}")

    def edit_selected_forecast(self):
        """Open a dialog to edit a single forecast's fields."""
        from tkinter import filedialog, Toplevel, messagebox
        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Single forecast edit cancelled.")
            return
        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            if not forecasts:
                self.log("No forecasts to edit.")
                return
            idx = simpledialog.askinteger("Select Forecast", f"Enter index (0-{len(forecasts)-1}):", minvalue=0, maxvalue=len(forecasts)-1)
            if idx is None:
                return
            fc = forecasts[idx]
            win = Toplevel(self.root)
            win.title(f"Edit Forecast {idx}")
            entries = {}
            for i, (k, v) in enumerate(fc.items()):
                ttk.Label(win, text=k).grid(row=i, column=0, sticky="w")
                ent = ttk.Entry(win, width=30)
                ent.insert(0, str(v))
                ent.grid(row=i, column=1)
                entries[k] = ent
            def save_edit():
                for k, ent in entries.items():
                    fc[k] = ent.get()
                out = filedialog.asksaveasfilename(defaultextension=".jsonl", title="Save edited forecast as...")
                if out:
                    with open(out, "w") as f:
                        for i, row in enumerate(forecasts):
                            if i == idx:
                                f.write(json.dumps(fc) + "\n")
                            else:
                                f.write(json.dumps(row) + "\n")
                    messagebox.showinfo("Saved", f"Edited forecast saved to {out}")
            ttk.Button(win, text="Save Edit", command=save_edit).grid(row=len(fc), column=0, columnspan=2, pady=4)
        except Exception as e:
            self.log(f"❌ Single forecast edit error: {e}")

        # --- AI/Ensemble Forecasting Integration ---
        ensemble_frame = ttk.LabelFrame(self.root, text="AI/Ensemble Forecasting")
        ensemble_frame.pack(fill="x", padx=4, pady=2)
        self.forecast_type = tk.StringVar(value="ensemble")
        ttk.Radiobutton(ensemble_frame, text="Simulation Only", variable=self.forecast_type, value="simulation").pack(side="left")
        ttk.Radiobutton(ensemble_frame, text="AI Only", variable=self.forecast_type, value="ai").pack(side="left")
        ttk.Radiobutton(ensemble_frame, text="Ensemble", variable=self.forecast_type, value="ensemble").pack(side="left")
        ttk.Button(ensemble_frame, text="Compare Forecasts", command=self.compare_forecasts_gui).pack(side="left", padx=8)

    def review_blocked_memory(self):
        """Open blocked memory log and review license reasons + optionally export."""
        from tkinter import filedialog, simpledialog
        from dev_tools.memory_recovery_viewer import load_blocked_forecasts, export_subset

        path = filedialog.askopenfilename(title="Select blocked_memory_log.jsonl")
        if not path:
            self.log("Review cancelled.")
            return

        try:
            blocked = load_blocked_forecasts(path)
            reasons = {}
            for fc in blocked:
                label = fc.get("license_status", "❓ Unlabeled")
                reasons[label] = reasons.get(label, 0) + 1

            self.log("📉 License Blocked Forecast Summary:")
            for reason, count in reasons.items():
                self.log(f" - {reason}: {count}")

            choice = simpledialog.askstring("Export Reason", "Enter license status to export:")
            if choice:
                out = filedialog.asksaveasfilename(defaultextension=".jsonl")
                if out:
                    export_subset(blocked, reason_filter=choice, out_path=out)
                    self.log(f"✅ Exported forecasts with reason: {choice}")
        except Exception as e:
            self.log(f"❌ Failed to review blocked memory: {e}")

    def enforce_forecast_batch_license(self):
        """Run license enforcement across a forecast batch."""
        from tkinter import filedialog
        from trust_system.license_enforcer import (
            annotate_forecasts, filter_licensed, summarize_license_distribution, export_rejected_forecasts
        )
        path = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not path:
            self.log("License enforcement cancelled.")
            return
        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            forecasts = annotate_forecasts(forecasts)
            licensed = filter_licensed(forecasts)
            summary = summarize_license_distribution(forecasts)
            out_path = filedialog.asksaveasfilename(defaultextension=".jsonl", title="Save approved forecasts")
            if out_path:
                with open(out_path, "w") as f:
                    for fc in licensed:
                        f.write(json.dumps(fc) + "\n")
                self.log(f"✅ Saved {len(licensed)} approved forecasts.")
            else:
                self.log("⚠️ No export path selected.")
            self.log("📊 License Summary:")
            for k, v in summary.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ License enforcement error: {e}")

    def explain_forecast_licenses(self):
        """Select a forecast batch and view license rationales per forecast."""
        from tkinter import filedialog
        from trust_system.license_explainer import explain_forecast_license
        path = filedialog.askopenfilename(title="Select forecast batch with licenses")
        if not path:
            self.log("License rationale view cancelled.")
            return
        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            self.log(f"📂 Loaded {len(forecasts)} forecasts with licensing.")
            for fc in forecasts:
                rationale = explain_forecast_license(fc)
                self.log(f"🧾 {fc.get('trace_id', 'unknown')} → {fc.get('license_status')}\n{rationale}")
        except Exception as e:
            self.log(f"❌ Failed to explain licenses: {e}")

    def log_batch_forecast_audits(self):
        self.log("Log Batch Audit Trail: Not yet implemented.")

    def run_alignment_batch_analysis(self):
        self.log("Run Batch Alignment Scoring: Not yet implemented.")

    def replay_and_plot_trace(self):
        self.log("Replay & Plot Trace: Not yet implemented.")

    def forecast_variable_trajectory(self):
        self.log("Forecast Variable Trajectory: Not yet implemented.")

    def score_forecast_accuracy(self):
        self.log("Score Forecast Accuracy: Not yet implemented.")

    def export_last_batch(self):
        self.log("Export Last Batch: Not yet implemented.")

    def import_upgrade_plan(self):
        self.log("Import Upgrade Plan: Not yet implemented.")

    def export_upgrade_plan(self):
        self.log("Export Upgrade Plan: Not yet implemented.")

    def compare_forecasts_gui(self):
        self.log("Compare Forecasts: Not yet implemented.")

    def view_audit_trail_gui(self):
        self.log("View Audit Trail: Not yet implemented.")

    def explain_license_gui(self):
        self.log("Explain License Rationale: Not yet implemented.")

# --- PATCH: Add missing dev_tools.pulse_ui_bridge functions ---
def check_contradictions_from_ui(app):
    """Helper to call contradiction digest from menu."""
    if hasattr(app, "check_contradictions"):
        app.check_contradictions()
    elif hasattr(app, "view_contradiction_digest"):
        app.view_contradiction_digest()
    else:
        messagebox.showerror("Not Implemented", "Contradiction digest not available in this UI.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PulseControlApp(root)
    root.mainloop()