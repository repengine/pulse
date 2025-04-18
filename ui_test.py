"""
Module: pulse_ui_tester_expanded_with_graph.py
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
from trust_system.pulse_mirror_core import check_coherence


class PulseControlApp:
    def __init__(self, root):
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
        self.last_batch = []

        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.root, text="Symbolic Overlays", font=("Arial", 12, "bold")).pack(pady=5)
        for k, var in self.overlay_vars.items():
            frame = ttk.Frame(self.root)
            frame.pack()
            ttk.Label(frame, text=f"{k.capitalize():<8}").pack(side="left")
            scale = ttk.Scale(frame, from_=0.0, to=1.0, variable=var, length=200, orient="horizontal")
            scale.pack(side="left")
            ttk.Label(frame, textvariable=var).pack(side="left")

        # Overlay control buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=2)
        ttk.Button(btn_frame, text="Reset Overlays", command=self.reset_overlays).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Load Overlays", command=self.load_overlays).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Save Overlays", command=self.save_overlays).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Show Overlay JSON", command=self.show_overlay_json).pack(side="left", padx=2)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=5)
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

        # Log + clear
        log_frame = ttk.Frame(self.root)
        log_frame.pack(pady=5)
        self.output = scrolledtext.ScrolledText(log_frame, height=22, width=100, wrap="word")
        self.output.pack(side="left")
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)

        self.log("Pulse Dev UI Ready.")

    def apply_overlays(self):
        overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
        try:
            self.state.symbolic = overlay
        except:
            if hasattr(self.state, "set_symbolic_overlay"):
                self.state.set_symbolic_overlay(overlay)
            elif hasattr(self.state, "set_overlay"):
                self.state.set_overlay(overlay)
        self.log(f"Applied overlays: {overlay}")

    def reset_overlays(self):
        for var in self.overlay_vars.values():
            var.set(0.5)
        self.apply_overlays()
        self.log("🔄 Overlays reset to default.")

    def load_overlays(self):
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

    def save_overlays(self):
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if file:
            overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
            try:
                with open(file, "w") as f:
                    json.dump(overlay, f, indent=2)
                self.log(f"💾 Overlays saved to: {file}")
            except Exception as e:
                self.log(f"❌ Overlay save error: {e}")

    def show_overlay_json(self):
        overlay = {k: round(v.get(), 3) for k, v in self.overlay_vars.items()}
        self.log("📝 Current Overlays JSON:")
        self.log(json.dumps(overlay, indent=2))

    def run_batch(self):
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

    def save_batch(self):
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

    def show_digest(self):
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

    def score_trace(self):
        try:
            trace = [{"hope": v.get(), "despair": 1 - v.get(), "rage": 0.5, "fatigue": 0.5}
                     for k, v in self.overlay_vars.items() if k == "hope"]
            result = score_symbolic_trace(trace)
            self.log(f"🧠 {result['arc_label']} | Score: {result['symbolic_score']} | Certainty: {result['arc_certainty']}")
        except Exception as e:
            self.log(f"❌ Trace scoring error: {e}")

    def score_trace_from_file(self):
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

    def show_symbolic_arc(self):
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

    def backtrace_and_graph(self):
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

    def load_and_replay_trace(self):
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

    def load_and_visualize_trace(self):
        """
        Load a .jsonl simulation trace and interactively plot overlays, variables, or tags.
        """
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

    def prune_memory(self):
        """
        Prune memory forecasts below a user-specified confidence threshold.
        """
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

    def run_memory_audit(self):
        """
        Runs a memory audit and displays summary statistics, with user feedback dialog.
        """
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

    def export_memory_audit(self):
        """
        Export the last memory audit to CSV.
        """
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

    def plot_memory_stats(self):
        """
        Plot memory audit statistics (domain distribution, confidence histogram).
        """
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

    def run_coherence_check(self):
        """
        Runs a coherence check on the last batch and displays warnings or success, with user feedback dialog.
        """
        if not self.last_batch:
            self.log("⚠️ No forecasts to check.")
            return
        try:
            warnings = check_coherence(self.last_batch)
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

    def export_coherence_warnings(self):
        """
        Export the last coherence warnings to a text file.
        """
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

    def clear_log(self):
        self.output.delete("1.0", "end")
        self.log("🧹 Log cleared.")

    def log(self, text):
        self.output.insert("end", text + "\n")
        self.output.see("end")


if __name__ == "__main__":
    root = tk.Tk()
    app = PulseControlApp(root)
    root.mainloop()
