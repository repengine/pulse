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
from forecast_output.forecast_batch_runner import run_forecast_batch
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


class PulseControlApp:
    def __init__(self, root: tk.Tk):
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

    def setup_ui(self) -> None:
        """Set up the Tkinter UI widgets and layout (tabbed, menu, status bar)."""
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Overlays", command=self.load_overlays)
        file_menu.add_command(label="Save Overlays", command=self.save_overlays)
        file_menu.add_separator()
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
        ttk.Button(operator_frame, text="Run Recursion Audit", command=lambda: prompt_and_run_audit(self.log)).pack(pady=2)
        ttk.Button(operator_frame, text="Generate Operator Brief", command=lambda: prompt_and_generate_brief(self.log)).pack(pady=2)
        ttk.Button(operator_frame, text="Graph Variable History", command=lambda: prompt_and_plot_variables(self.log)).pack(pady=2)
        ttk.Button(operator_frame, text="Summarize Symbolic Episodes", command=self.view_episode_summary).pack(pady=2)
        ttk.Button(operator_frame, text="Generate Operator Brief", command=self.generate_operator_brief_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Run Batch Alignment Scoring", command=self.run_alignment_batch_analysis).pack(pady=2)
        ttk.Button(operator_frame, text="Log Batch Audit Trail", command=self.log_batch_forecast_audits).pack(pady=2)
        ttk.Button(operator_frame, text="Trace Forecast Lineage", command=self.trace_forecast_episode_chain).pack(pady=2)
        ttk.Button(operator_frame, text="Analyze Symbolic Flip Patterns", command=self.analyze_symbolic_flips).pack(pady=2)
        ttk.Button(operator_frame, text="Apply Symbolic Revisions", command=self.apply_symbolic_revisions_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Run Symbolic Learning", command=self.run_symbolic_learning_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Generate Symbolic Upgrade", command=self.generate_symbolic_upgrade_gui).pack(pady=2)
        ttk.Button(operator_frame, text="Apply Symbolic Upgrade", command=self.apply_symbolic_upgrade_gui).pack(pady=2)

        # --- Replay Tab ---
        replay_tab = ttk.Frame(notebook)
        notebook.add(replay_tab, text="Replay")
        replay_frame = ttk.LabelFrame(replay_tab, text="Trace Replay Tools")
        replay_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(replay_frame, text="Replay & Plot Trace", command=self.replay_and_plot_trace).pack(pady=2)
        ttk.Button(replay_frame, text="Forecast Variable Trajectory", command=self.forecast_variable_trajectory).pack(pady=2)
        ttk.Button(replay_frame, text="Score Forecast Accuracy", command=self.score_forecast_accuracy).pack(pady=2)
        ttk.Button(replay_frame, text="Plot Symbolic Trajectory", command=self.plot_symbolic_trajectory_gui).pack(pady=2)

        # --- Add Certify Forecasts Button to main window ---
        ttk.Button(self.root, text="Certify Forecasts", command=self.certify_forecasts_gui).pack(pady=2)
        # --- Add Top Strategic Forecasts Button ---
        ttk.Button(self.root, text="View Top Strategic Forecasts", command=self.view_top_strategic_forecasts).pack(pady=2)
        # --- Add Classify Forecast Clusters Button ---
        ttk.Button(self.root, text="Classify Forecast Clusters", command=self.classify_forecast_clusters_gui).pack(pady=2)
        # --- Add Show Dual Narrative Scenarios Button ---
        ttk.Button(self.root, text="Show Dual Narrative Scenarios", command=self.view_dual_narrative_scenarios).pack(pady=2)
        # --- Add Promote Memory Candidates Button ---
        ttk.Button(self.root, text="Promote Memory Candidates", command=self.promote_memory_candidates_gui).pack(pady=2)

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

    def update_overlay_summary(self) -> None:
        """Update the summary label with a human-readable interpretation of overlays."""
        overlay = {k: v.get() for k, v in self.overlay_vars.items()}
        dominant = max(overlay, key=overlay.get)
        val = overlay[dominant]
        if val > 0.8:
            mood = f"Very high {dominant}"
        elif val > 0.6:
            mood = f"High {dominant}"
        elif val < 0.2:
            mood = f"Very low {dominant}"
        elif val < 0.4:
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
            overlays = self.state.overlays.as_dict() if hasattr(self.state.overlays, "as_dict") else dict(self.state.overlays)
            for k, var in self.overlay_vars.items():
                var.set(overlays.get(k, 0.5))
            self.update_overlay_summary()
            self.log(f"✅ Ran {n} simulation turns.")
        except Exception as e:
            self.log(f"❌ Error running turns: {e}")

    def apply_overlays(self) -> None:
        """Apply the current overlay values to the simulation state."""
        overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
        try:
            self.state.symbolic = overlay
        except:
            if hasattr(self.state, "set_symbolic_overlay"):
                self.state.set_symbolic_overlay(overlay)
            elif hasattr(self.state, "set_overlay"):
                self.state.set_overlay(overlay)
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
                self.log(f"💾 Overlays saved to: {file}")
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
            self.last_batch = run_forecast_batch(self.state, batch_size=size)
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
        """Plot the symbolic arc for the last batch using matplotlib."""
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

        fig, ax = plt.subplots(figsize=(8, 4))
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
                tags = [e.get("symbolic_tag", "N/A") for e in trace]
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
            self.coherence_warnings_last = warnings
            if warnings:
                self.log("⚠️ Coherence Warnings:")
                for w in warnings:
                    self.log(f" - {w}")
                messagebox.showwarning("Coherence Check", f"{len(warnings)} warnings found.")
            else:
                self.log("✅ All forecasts are coherent.")
                messagebox.showinfo("Coherence Check", "All forecasts are coherent.")
        except Exception as e:
            self.log(f"❌ Coherence check error: {e}")

    def export_coherence_warnings(self) -> None:
        """Export the last coherence warnings to a text file."""
        try:
            if not hasattr(self, "coherence_warnings_last"):
                self.log("⚠️ Run coherence check first.")
                return
            file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
            if not file:
                return
            with open(file, "w") as f:
                for w in self.coherence_warnings_last:
                    f.write(w + "\n")
            self.log(f"✅ Coherence warnings exported to {file}")
        except Exception as e:
            self.log(f"❌ Export error: {e}")

    def replay_and_plot_trace(self) -> None:
        """Load a trace and plot a variable/overlay timeline."""
        from dev_tools.pulse_ui_replay import replay_trace
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(filetypes=[("JSONL files", "*.jsonl")])
        if not path:
            self.log("Trace selection cancelled.")
            return

        mode = simpledialog.askstring("Mode", "Enter mode: 'variables' or 'overlays'")
        if mode not in ["variables", "overlays"]:
            self.log("Invalid mode. Use 'variables' or 'overlays'.")
            return

        key = simpledialog.askstring("Key", f"Enter the {mode} key to plot:")
        if not key:
            self.log("Key input cancelled.")
            return

        try:
            self.log(f"📈 Replaying trace for {mode}:{key}")
            replay_trace(path, mode=mode, key=key)
        except Exception as e:
            self.log(f"❌ Replay error: {e}")

    def forecast_variable_trajectory(self):
        """GUI wrapper for pulse_variable_forecaster logic."""
        from simulation_engine.utils.pulse_variable_forecaster import simulate_forward, plot_forecast
        from tkinter import simpledialog, filedialog

        var = simpledialog.askstring("Variable", "Enter variable name to forecast:")
        if not var:
            self.log("⚠️ Forecast cancelled.")
            return

        try:
            horizon = int(simpledialog.askinteger("Steps", "Forecast horizon (steps):", initialvalue=12))
            runs = int(simpledialog.askinteger("Runs", "Number of simulations:", initialvalue=10))
        except (ValueError, TypeError):
            self.log("⚠️ Invalid input for steps or runs.")
            return

        self.log(f"📈 Forecasting: {var} for {horizon} steps × {runs} runs")
        try:
            results = simulate_forward(var, horizon, runs)
            export = filedialog.asksaveasfilename(defaultextension=".png", title="Export forecast plot?")
            plot_forecast(results["average"], results["trajectories"], var, export=export)
        except Exception as e:
            self.log(f"❌ Forecast error: {e}")

    def score_forecast_accuracy(self):
        """Compare Pulse forecast vs real data using tag and variable alignment."""
        from dev_tools.pulse_forecast_evaluator import evaluate_forecast
        from tkinter import filedialog, simpledialog

        forecast_path = filedialog.askopenfilename(title="Select Pulse forecast trace (.jsonl)")
        real_path = filedialog.askopenfilename(title="Select real-world trace (.jsonl)")
        if not forecast_path or not real_path:
            self.log("⚠️ Forecast evaluation cancelled.")
            return

        var = simpledialog.askstring("Variable", "Enter variable/overlay name to evaluate (e.g. 'hope'):")
        if not var:
            self.log("⚠️ No variable selected.")
            return

        mode = simpledialog.askstring("Mode", "Enter mode: 'variables' or 'overlays'")
        if mode not in ["variables", "overlays"]:
            self.log("⚠️ Invalid mode. Use 'variables' or 'overlays'.")
            return

        try:
            self.log(f"🔍 Evaluating forecast accuracy for {var} ({mode})...")
            result = evaluate_forecast(real_path, forecast_path, variable=var, mode=mode)
            self.log("📊 Forecast Evaluation Summary:")
            for k, v in result.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ Forecast evaluator error: {e}")

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

    def run_alignment_batch_analysis(self):
        """Run alignment scoring on a forecast batch via CLI bridge."""
        from tkinter import filedialog
        from trust_system.alignment_index import compute_alignment_index

        path = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not path:
            self.log("⚠️ Cancelled.")
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line) for line in f if line.strip()]
            self.log(f"📂 Loaded {len(forecasts)} forecasts.")

            scored = []
            for fc in forecasts:
                align = compute_alignment_index(fc)
                fc["alignment_score"] = align["alignment_score"]
                scored.append(fc)

            scored = sorted(scored, key=lambda x: x["alignment_score"], reverse=True)

            self.log("🏆 Top 5 forecasts by alignment:")
            for fc in scored[:5]:
                self.log(f" - {fc.get('trace_id')}: {fc['alignment_score']}")

        except Exception as e:
            self.log(f"❌ Alignment analysis error: {e}")

    def log_batch_forecast_audits(self):
        """GUI wrapper to audit and log all forecasts in a batch."""
        from tkinter import filedialog
        from trust.forecast_audit_trail import generate_forecast_audit, log_forecast_audit

        file = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not file:
            self.log("Audit logging cancelled.")
            return

        try:
            with open(file, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            self.log(f"📂 Loaded {len(forecasts)} forecasts. Logging...")

            for fc in forecasts:
                audit = generate_forecast_audit(fc)
                log_forecast_audit(audit)

            self.log(f"✅ Audit trail updated for {len(forecasts)} forecasts.")
        except Exception as e:
            self.log(f"❌ Audit logging failed: {e}")

    def view_episode_summary(self):
        """Display a symbolic episode summary from memory log."""
        from trust.forecast_episode_logger import summarize_episodes
        from tkinter import filedialog

        file = filedialog.askopenfilename(title="Select episode log (JSONL)")
        if not file:
            return
        try:
            summary = summarize_episodes(file)
            self.log("🧠 Episode Summary:")
            for k, v in summary.items():
                self.log(f" - {k}: {v}")
        except Exception as e:
            self.log(f"❌ Episode summary error: {e}")

    def generate_operator_brief_gui(self):
        """Select alignment + episode log and generate operator markdown brief."""
        from operator.operator_brief_generator import generate_operator_brief
        from tkinter import filedialog

        alignment = filedialog.askopenfilename(title="Select alignment-scored forecasts (.jsonl)")
        episodes = filedialog.askopenfilename(title="Select symbolic episode log (.jsonl)")
        output = filedialog.asksaveasfilename(defaultextension=".md", title="Save operator brief as")

        if not alignment or not episodes or not output:
            self.log("⚠️ Operator brief generation cancelled.")
            return

        try:
            generate_operator_brief(alignment_file=alignment, episode_log_file=episodes, output_md_path=output)
            self.log(f"✅ Brief saved to: {output}")
        except Exception as e:
            self.log(f"❌ Brief generation failed: {e}")

    def plot_arc_drift_across_cycles(self):
        """Plot arc drift between two symbolic episode logs."""
        from tkinter import filedialog
        from trust.forecast_episode_logger import summarize_episodes
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

    def evaluate_forecast_licenses(self):
        from tkinter import filedialog
        from trust_system.forecast_licensing_shell import license_forecast

        path = filedialog.askopenfilename(title="Select forecast batch")
        if not path:
            self.log("License check cancelled.")
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            approved = 0
            for fc in forecasts:
                fc["license_status"] = license_forecast(fc)
                if fc["license_status"] == "✅ Approved":
                    approved += 1
            self.log(f"✅ {approved}/{len(forecasts)} forecasts approved for license.")
        except Exception as e:
            self.log(f"❌ License evaluation failed: {e}")

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

    def review_blocked_memory(self):
        """Open blocked memory log and review license reasons + optionally export."""
        from tkinter import filedialog, simpledialog
        from tools.memory_recovery_viewer import load_blocked_forecasts, export_subset

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

    def repair_blocked_memory(self):
        """Retry licensing for previously blocked forecasts."""
        from tkinter import filedialog
        from memory.memory_repair_queue import load_blocked_memory, retry_licensing, export_recovered

        path = filedialog.askopenfilename(title="Select blocked_memory_log.jsonl")
        if not path:
            self.log("Repair cancelled.")
            return

        try:
            blocked = load_blocked_memory(path)
            recovered = retry_licensing(blocked)

            self.log(f"✅ {len(recovered)} forecasts passed re-licensing.")

            out = filedialog.asksaveasfilename(defaultextension=".jsonl")
            if out:
                export_recovered(recovered, out)
                self.log(f"📤 Saved recovered forecasts to: {out}")
        except Exception as e:
            self.log(f"❌ Repair failed: {e}")

    def run_symbolic_sweep_gui(self):
        """GUI wrapper to run symbolic sweep and log results."""
        from scheduler.symbolic_sweep_scheduler import run_sweep_now
        try:
            result = run_sweep_now()
            self.log(f"🧠 Sweep recovered {result['recovered']} of {result['total_blocked']} forecasts.")
        except Exception as e:
            self.log(f"❌ Symbolic sweep error: {e}")

    def show_sweep_summary(self):
        """Show symbolic trust sweep summary from history log."""
        from scheduler.symbolic_sweep_scheduler import summarize_sweep_log
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Select sweep log", initialfile="symbolic_sweep_log.jsonl")
        if not path:
            return
        try:
            with open(path, "r") as f:
                entries = [json.loads(line.strip()) for line in f if line.strip()]
            self.log(f"📊 Sweep History ({len(entries)}):")
            for entry in entries[-10:]:
                self.log(f"{entry['timestamp']} → Recovered {entry['recovered']} of {entry['total_blocked']}")
        except Exception as e:
            self.log(f"❌ Failed to read sweep log: {e}")

    def trace_forecast_episode_chain(self):
        """Stub for Trace Forecast Lineage button."""
        self.log("Trace Forecast Lineage: Not yet implemented.")

    def analyze_symbolic_flips(self):
        """Analyze symbolic arc/tag transitions for loop patterns."""
        from tkinter import filedialog
        from symbolic.symbolic_flip_classifier import analyze_flip_patterns, detect_loops_or_cycles
        from memory.forecast_episode_tracer import build_episode_chain

        path = filedialog.askopenfilename(title="Select forecast archive")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            ids = [f.get("trace_id") for f in forecasts if "lineage" in f]
            chains = [build_episode_chain(forecasts, root_id=tid) for tid in ids]

            result = analyze_flip_patterns(chains)
            loops = detect_loops_or_cycles(result["all_flips"])

            self.log("🔁 Top Symbolic Flips:")
            for (a, b), count in result["top_flips"]:
                self.log(f" - {a} → {b}: {count}x")

            if loops:
                self.log("♻️ Symbolic Loops:")
                for l in loops:
                    self.log(f" - {l}")
        except Exception as e:
            self.log(f"❌ Flip analysis error: {e}")

    def show_symbolic_transition_graph(self):
        """Render symbolic transition graph from forecast archive."""
        from tkinter import filedialog
        from symbolic.symbolic_transition_graph import build_symbolic_graph, visualize_symbolic_graph

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

    def plot_symbolic_trajectory_gui(self):
        """Prompt for a forecast archive and trace ID to plot symbolic arc/tag evolution."""
        from forecasting.mutation_compression_engine import plot_symbolic_trajectory
        from memory.forecast_episode_tracer import build_episode_chain
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(title="Select forecast archive (.jsonl)")
        if not path:
            self.log("Trajectory plot cancelled.")
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            root_id = simpledialog.askstring("Trace ID", "Enter root forecast ID for trajectory:")
            if not root_id:
                return
            chain = build_episode_chain(forecasts, root_id=root_id)
            plot_symbolic_trajectory(chain, title=f"Trajectory for {root_id}")
        except Exception as e:
            self.log(f"❌ Failed to plot symbolic trajectory: {e}")

    def check_symbolic_convergence(self):
        """Compute symbolic convergence score across forecast archive."""
        from symbolic.symbolic_convergence_detector import (
            compute_convergence_score,
            identify_dominant_arcs,
            detect_fragmentation,
            plot_convergence_bars
        )
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(title="Select forecast archive (.jsonl)")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]

            key = simpledialog.askstring("Symbolic Field", "Score by: 'arc_label' or 'symbolic_tag'")
            if not key or key not in {"arc_label", "symbolic_tag"}:
                self.log("Invalid symbolic field.")
                return

            score = compute_convergence_score(forecasts, key=key)
            dom = identify_dominant_arcs(forecasts, key=key)
            frag = detect_fragmentation(forecasts, key=key)

            self.log(f"📊 Symbolic Convergence Score ({key}): {score:.3f}")
            self.log("🔝 Top Symbols:")
            for k, v in dom.items():
                self.log(f" - {k}: {v}")
            if frag:
                self.log("⚠️ Narrative fragmentation detected.")

            plot_convergence_bars(forecasts, key=key)

        except Exception as e:
            self.log(f"❌ Convergence analysis failed: {e}")

    def apply_symbolic_revisions_gui(self):
        """Apply symbolic tuning plans to forecast batch interactively."""
        from symbolic.symbolic_tuning_engine import simulate_revised_forecast, compare_scores, log_tuning_result
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Select forecast batch")
        plan_path = filedialog.askopenfilename(title="Select revision plan JSON")

        if not path or not plan_path:
            self.log("Revision cancelled.")
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            with open(plan_path, "r") as f:
                plans = json.load(f)

            applied = 0
            for fc in forecasts:
                tid = fc.get("trace_id")
                plan = next((p["plan"] for p in plans if p["trace_id"] == tid), None)
                if not plan:
                    continue
                revised = simulate_revised_forecast(fc, plan)
                delta = compare_scores(fc, revised)
                self.log(f"🔁 {tid} → Δ Alignment: {delta['alignment_score']} | {delta['license_status_change']}")
                revised["revision_plan"] = plan
                log_tuning_result(fc, revised)
                applied += 1

            self.log(f"✅ Simulated {applied} symbolic revisions.")
        except Exception as e:
            self.log(f"❌ Tuning error: {e}")

    def run_symbolic_learning_gui(self):
        from symbolic.pulse_symbolic_learning_loop import (
            learn_from_tuning_log, generate_learning_profile, log_symbolic_learning
        )
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Select tuning log")
        if not path:
            return
        try:
            results = learn_from_tuning_log(path)
            profile = generate_learning_profile(results)
            log_symbolic_learning(profile)
            self.log("✅ Symbolic learning profile updated.")
        except Exception as e:
            self.log(f"❌ Learning failed: {e}")

    def generate_symbolic_upgrade_gui(self):
        from symbolic.symbolic_upgrade_planner import (
            propose_symbolic_upgrades, export_upgrade_plan
        )
        from symbolic.pulse_symbolic_learning_loop import (
            learn_from_tuning_log, generate_learning_profile
        )
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Select tuning results")
        if not path:
            return
        try:
            results = learn_from_tuning_log(path)
            profile = generate_learning_profile(results)
            plan = propose_symbolic_upgrades(profile)
            export_upgrade_plan(plan)
            self.log(f"✅ Upgrade plan created.")
        except Exception as e:
            self.log(f"❌ Upgrade planning failed: {e}")

    def apply_symbolic_upgrade_gui(self):
        from symbolic.symbolic_executor import rewrite_forecast_symbolics, log_symbolic_mutation
        from tkinter import filedialog
        batch_path = filedialog.askopenfilename(title="Select forecast batch")
        plan_path = filedialog.askopenfilename(title="Select upgrade plan")

        if not batch_path or not plan_path:
            return

        try:
            with open(batch_path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            with open(plan_path, "r") as f:
                plan = json.load(f)

            updated = rewrite_forecast_symbolics(forecasts, plan)
            for fc in updated:
                log_symbolic_mutation(fc)
            self.log(f"✅ Applied symbolic upgrades to {len(updated)} forecasts.")
        except Exception as e:
            self.log(f"❌ Symbolic upgrade failed: {e}")

    def scan_symbolic_resonance_gui(self):
        """Analyze symbolic convergence and clustering across a forecast batch."""
        from forecast_output.forecast_resonance_scanner import generate_resonance_summary
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Select forecast batch")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            # --- PATCH: Validate input is a list of dicts ---
            if not isinstance(forecasts, list) or not all(isinstance(fc, dict) for fc in forecasts):
                self.log("❌ Input file does not contain a list of forecast dicts.")
                return
            result = generate_resonance_summary(forecasts, key="arc_label")

            self.log("🔗 Symbolic Resonance Summary:")
            self.log(f" - Resonance Score: {result['resonance_score']}")
            self.log(f" - Dominant Arc: {result['dominant_arc']}")
            if result.get("top_themes"):
                self.log(f" - Top Themes: {', '.join(result['top_themes'])}")
            if result.get("cluster_sizes"):
                self.log(" - Cluster Sizes:")
                for k, v in result["cluster_sizes"].items():
                    self.log(f"   * {k}: {v}")
        except Exception as e:
            self.log(f"❌ Resonance scan failed: {e}")

    def certify_forecasts_gui(self):
        """Certify a forecast batch and log summary."""
        from forecast_output.forecast_fidelity_certifier import (
            tag_certified_forecasts, generate_certified_digest
        )
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Select forecast batch")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            certified = tag_certified_forecasts(forecasts)
            report = generate_certified_digest(certified)
            self.log(f"✅ Certified: {report['certified']} / {report['certified'] + report['uncertified']}")
            self.log(f"📊 Certification Ratio: {report['certified_ratio']}")
        except Exception as e:
            self.log(f"❌ Certification failed: {e}")

    def view_top_strategic_forecasts(self):
        """Display top-ranked certified forecasts by strategic priority."""
        from forecast_output.forecast_prioritization_engine import select_top_forecasts
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Select certified forecast batch")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            top = select_top_forecasts(forecasts, top_n=5)
            self.log("🧭 Top Strategic Forecasts:")
            for fc in top:
                self.log(f" - {fc.get('trace_id')} → {fc.get('arc_label')} | {fc.get('symbolic_tag')} | Align: {fc.get('alignment_score')} | Conf: {fc.get('confidence')}")
        except Exception as e:
            self.log(f"❌ Strategic preview failed: {e}")

    def classify_forecast_clusters_gui(self):
        """Show narrative cluster composition of a forecast batch."""
        from forecast_output.forecast_cluster_classifier import classify_forecast_cluster, summarize_cluster_counts
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Select forecast batch")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            summary = summarize_cluster_counts(forecasts)
            self.log("🧠 Narrative Cluster Summary:")
            for cluster, count in summary.items():
                self.log(f" - {cluster}: {count}")
        except Exception as e:
            self.log(f"❌ Cluster classification failed: {e}")

    def view_dual_narrative_scenarios(self):
        """Show symbolic narrative forks as paired scenarios."""
        from forecast_output.dual_narrative_compressor import generate_dual_scenarios
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Select forecast batch")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            duals = generate_dual_scenarios(forecasts)
            for pair in duals:
                a, b = pair["scenario_a"]["forecast"], pair["scenario_b"]["forecast"]
                self.log(f"🔀 {pair['scenario_a']['arc']} vs {pair['scenario_b']['arc']}")
                self.log(f" A: {a.get('symbolic_tag')} | Align: {a.get('alignment_score')} | Conf: {a.get('confidence')}")
                self.log(f" B: {b.get('symbolic_tag')} | Align: {b.get('alignment_score')} | Conf: {b.get('confidence')}")
        except Exception as e:
            self.log(f"❌ Dual scenario display failed: {e}")

    def promote_memory_candidates_gui(self):
        """Retain certified, fork-winning forecasts into final memory."""
        from tkinter import filedialog
        import json
        from memory.forecast_memory_promoter import select_promotable_forecasts, export_promoted

        path = filedialog.askopenfilename(title="Select forecast batch (.jsonl)")
        if not path:
            return

        try:
            with open(path, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            selected = select_promotable_forecasts(forecasts)
            export_promoted(selected)
            self.log(f"✅ Promoted {len(selected)} forecasts to final memory.")
        except Exception as e:
            self.log(f"❌ Memory promotion failed: {e}")

    def clear_log(self) -> None:
        """Clear the log output window."""
        self.output.delete("1.0", "end")
        self.log("🧹 Log cleared.")

    def log(self, text: str) -> None:
        """Append a line of text to the log output window and update status bar."""
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.status_var.set(text[:120])  # Show last log line in status bar


def check_contradictions_from_ui(app):
    file_path = filedialog.askopenfilename(filetypes=[("JSONL files", "*.jsonl")])
    if not file_path:
        app.log("No file selected.")
        return
    try:
        with open(file_path, "r") as f:
            forecasts = [json.loads(line.strip()) for line in f if line.strip()]
        result = TrustEngine.scan_forecast_batch(forecasts)
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


if __name__ == "__main__":
    root = tk.Tk()
    app = PulseControlApp(root)
    root.mainloop()
