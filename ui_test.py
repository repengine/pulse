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
from tkinter import ttk, filedialog, scrolledtext, messagebox
import matplotlib.pyplot as plt
import sys, os, json

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.append(os.path.abspath("pulse"))

from simulation_engine.worldstate import WorldState
from forecast_output.forecast_batch_runner import run_forecast_batch
from forecast_output.strategos_tile_formatter import format_strategos_tile
from symbolic_system.symbolic_trace_scorer import score_symbolic_trace


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

    def log(self, text):
        self.output.insert("end", text + "\n")
        self.output.see("end")

    def clear_log(self):
        self.output.delete("1.0", "end")
        self.log("🧹 Log cleared.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PulseControlApp(root)
    root.mainloop()
