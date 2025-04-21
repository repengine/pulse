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
        self.turns = tk.IntVar(value=5)  # Add turns variable
        self.last_batch = []

        self.summary_var = tk.StringVar(value="")  # For overlay interpretation

        self.setup_ui()
        self.update_overlay_summary()  # Initialize summary

    def setup_ui(self) -> None:
        """Set up the Tkinter UI widgets and layout."""
        ttk.Label(self.root, text="Symbolic Overlays", font=("Arial", 12, "bold")).pack(pady=5)
        for k, var in self.overlay_vars.items():
            frame = ttk.Frame(self.root)
            frame.pack()
            ttk.Label(frame, text=f"{k.capitalize():<8}").pack(side="left")
            scale = ttk.Scale(frame, from_=0.0, to=1.0, variable=var, length=200, orient="horizontal")
            scale.pack(side="left")
            ttk.Label(frame, textvariable=var).pack(side="left")
            # Update summary when overlays change
            var.trace_add("write", lambda *_: self.update_overlay_summary())

        # Overlay control buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=2)
        ttk.Button(btn_frame, text="Reset Overlays", command=self.reset_overlays).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Load Overlays", command=self.load_overlays).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Save Overlays", command=self.save_overlays).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Show Overlay JSON", command=self.show_overlay_json).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Check Contradictions", command=lambda: check_contradictions_from_ui(self)).pack(side="left", padx=2)

        # Overlay summary/interpretation
        ttk.Label(self.root, textvariable=self.summary_var, font=("Arial", 10, "italic"), foreground="blue").pack(pady=4)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=5)
        # Simulation turn controls
        turns_frame = ttk.Frame(self.root)
        turns_frame.pack(pady=2)
        ttk.Label(turns_frame, text="Sim Turns:").pack(side="left")
        ttk.Entry(turns_frame, textvariable=self.turns, width=5).pack(side="left", padx=2)
        ttk.Button(turns_frame, text="Run N Turns", command=self.run_n_turns).pack(side="left", padx=2)

        ttk.Label(self.root, text="Batch Size").pack()
        ttk.Entry(self.root, textvariable=self.batch_size, width=5).pack()

        # Action buttons
        ttk.Button(self.root, text="Run Forecast Batch", command=self.run_batch).pack(pady=5)
        ttk.Button(self.root, text="Save Forecast Batch", command=self.save_batch).pack(pady=5)
        ttk.Button(self.root, text="Show Strategos Digest", command=self.show_digest).pack(pady=5)
        ttk.Button(self.root, text="Score Current Trace", command=self.score_trace).pack(pady=5)
        ttk.Button(self.root, text="Score Trace from File", command=self.score_trace_from_file).pack(pady=5)
        ttk.Button(self.root, text="Show Symbolic Arc", command=self.show_symbolic_arc).pack(pady=5)
        ttk.Button(self.root, text="Backtrace + Graph", command=self.backtrace_and_graph).pack(pady=5)
        ttk.Button(self.root, text="Load & Replay Trace", command=self.load_and_replay_trace).pack(pady=5)
        ttk.Button(self.root, text="Load & Visualize Trace", command=self.load_and_visualize_trace).pack(pady=5)
        ttk.Button(self.root, text="Prune Memory", command=self.prune_memory).pack(pady=2)
        ttk.Button(self.root, text="Memory Audit", command=self.run_memory_audit).pack(pady=5)
        ttk.Button(self.root, text="Export Memory Audit", command=self.export_memory_audit).pack(pady=2)
        ttk.Button(self.root, text="Plot Memory Stats", command=self.plot_memory_stats).pack(pady=2)
        ttk.Button(self.root, text="Coherence Check", command=self.run_coherence_check).pack(pady=5)
        ttk.Button(self.root, text="Export Coherence Warnings", command=self.export_coherence_warnings).pack(pady=2)

        # --- Operator Tools ---
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(self.root, text="Operator Tools", font=("Arial", 12, "bold")).pack(pady=3)
        ttk.Button(self.root, text="Run Recursion Audit", command=lambda: prompt_and_run_audit(self.log)).pack(pady=2)
        ttk.Button(self.root, text="Generate Operator Brief", command=lambda: prompt_and_generate_brief(self.log)).pack(pady=2)
        ttk.Button(self.root, text="Graph Variable History", command=lambda: prompt_and_plot_variables(self.log)).pack(pady=2)
        ttk.Button(self.root, text="Visualize Arc Distribution", command=self.visualize_arc_distribution).pack(pady=2)
        ttk.Button(self.root, text="Run Batch Alignment Scoring", command=self.run_alignment_batch_analysis).pack(pady=2)
        ttk.Button(self.root, text="Log Batch Audit Trail", command=self.log_batch_forecast_audits).pack(pady=2)
        # Add button for episode summary
        ttk.Button(self.root, text="Summarize Symbolic Episodes", command=self.view_episode_summary).pack(pady=2)

        # --- Trace Replay Tools ---
        ttk.Label(self.root, text="🧠 Trace Replay Tools", font=("Arial", 11, "bold")).pack(pady=3)
        ttk.Button(self.root, text="Replay & Plot Trace", command=self.replay_and_plot_trace).pack(pady=2)
        ttk.Button(self.root, text="Forecast Variable Trajectory", command=self.forecast_variable_trajectory).pack(pady=2)
        ttk.Button(self.root, text="Score Forecast Accuracy", command=self.score_forecast_accuracy).pack(pady=2)

        # Log + clear
        log_frame = ttk.Frame(self.root)
        log_frame.pack(pady=5)
        self.output = scrolledtext.ScrolledText(log_frame, height=22, width=100, wrap="word")
        self.output.pack(side="left")
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)

        self.log("Pulse Dev UI Ready.")

    def update_overlay_summary(self) -> None:
        """Update the summary label with a human-readable interpretation of overlays."""
        overlay = {k: v.get() for k, v in self.overlay_vars.items()}
        # Simple interpretation logic
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
        # Add more nuance if needed
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
            # Update overlay_vars from state
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
                summary = f"{r['trace_id']} | Conf: {r['confidence']} | Tag: {r.get('symbolic_tag', 'N/A')}"
                self.log(summary)
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
                tile = format_strategos_tile(fc)
                self.log("\n" + tile)
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

            # Use current overlays as starting point
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

            # Log arc label + certainty
            self.log(f"Backtrace Arc: {arc_label} | Certainty: {arc_certainty}")

            # Plot
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
            # Ask user what to plot
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
                # Plot variables (ask user for variable name)
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
                # Plot tags
                tags = [e.get("symbolic_tag", "N/A") for e in trace]
                plt.plot(tags)
                plt.title("Symbolic Tags Over Time")
                plt.xlabel("Step")
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
            # Add summary statistics
            total = len(memory._memory)
            domains = {}
            confidences = []
            for f in memory._memory:
                if not isinstance(f, dict):
                    continue  # skip if not a dict
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
            # User feedback dialog
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
            # Domain distribution
            axs[0].bar(domains.keys(), domains.values())
            axs[0].set_title("Forecasts by Domain")
            axs[0].set_xlabel("Domain")
            axs[0].set_ylabel("Count")
            # Confidence histogram
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
        from pulse.symbolic_analysis.pulse_symbolic_arc_tracker import (
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
        from pulse.trust.alignment_index import compute_alignment_index

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

    def clear_log(self) -> None:
        """Clear the log output window."""
        self.output.delete("1.0", "end")
        self.log("🧹 Log cleared.")

    def log(self, text: str) -> None:
        """Append a line of text to the log output window."""
        self.output.insert("end", text + "\n")
        self.output.see("end")


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
