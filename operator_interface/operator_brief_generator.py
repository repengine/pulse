# pulse/operator/operator_brief_generator.py

"""
Pulse Operator Brief Generator

Generates a Markdown summary of recent simulation forecasts,
including alignment scores, symbolic arcs, tags, and risk notes.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from trust_system.forecast_episode_logger import summarize_episodes
import os

from simulation_engine.simulation_drift_detector import run_simulation_drift_analysis


def load_jsonl(path: str) -> List[Dict]:
    """Load a JSONL file as list of dicts."""
    try:
        with open(path, "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return []


def generate_operator_brief(
    alignment_file: Optional[str] = None,
    episode_log_file: Optional[str] = None,
    output_md_path: str = "operator_brief.md",
    top_k: int = 5,
    previous_episode_log: Optional[str] = None,
    prev_trace_path: Optional[str] = None,
    curr_trace_path: Optional[str] = None,
) -> None:
    """
    Generate a markdown report based on alignment scores and symbolic episodes.

    Parameters:
        alignment_file (str): JSONL of alignment-scored forecasts
        episode_log_file (str): Symbolic episode log
        output_md_path (str): Where to save the markdown output
        top_k (int): How many top forecasts to display
        previous_episode_log (str): Previous symbolic episode log for drift comparison
        prev_trace_path (str): Path to previous simulation trace for drift analysis
        curr_trace_path (str): Path to current simulation trace for drift analysis
    """
    forecasts = load_jsonl(alignment_file) if alignment_file else []
    episodes = load_jsonl(episode_log_file) if episode_log_file else []

    drift_summary = {}
    if (
        previous_episode_log
        and os.path.exists(previous_episode_log)
        and episode_log_file
    ):
        previous = summarize_episodes(previous_episode_log)
        current = summarize_episodes(episode_log_file)
        arcs_prev = {
            k.replace("arc_", ""): v
            for k, v in previous.items()
            if k.startswith("arc_")
        }
        arcs_curr = {
            k.replace("arc_", ""): v for k, v in current.items() if k.startswith("arc_")
        }
        all_arcs = set(arcs_prev) | set(arcs_curr)
        drift_summary = {
            arc: arcs_curr.get(arc, 0) - arcs_prev.get(arc, 0) for arc in all_arcs
        }

    # Simulation drift analysis
    simulation_drift = None
    if prev_trace_path and curr_trace_path:
        try:
            drift_report = run_simulation_drift_analysis(
                prev_trace_path, curr_trace_path
            )
            simulation_drift = {
                "overlay_drift": drift_report.get("overlay_drift", {}),
                "rule_trigger_deltas": drift_report.get("rule_trigger_delta", {}),
                "structural_change": drift_report.get("structure_shift", None),
            }
        except Exception as e:
            print(f"❌ Failed to run simulation drift analysis: {e}")

    try:
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write("# 🧠 Pulse Operator Brief\n")
            f.write(f"_Generated: {datetime.utcnow().isoformat()} UTC_\n\n")

            # Top N Forecasts
            if forecasts:
                top = sorted(
                    forecasts, key=lambda x: x.get("alignment_score", 0), reverse=True
                )[:top_k]
                f.write(f"## 🔝 Top {top_k} Forecasts by Alignment\n")
                for fc in top:
                    score = fc.get("alignment_score", 0)
                    tag = fc.get("symbolic_tag", "N/A")
                    arc = fc.get("arc_label", "N/A")
                    conf = fc.get("confidence", "N/A")
                    f.write(
                        f"- `{fc.get('trace_id', 'unknown')}` | Score: {score} | Tag: {tag} | Arc: {arc} | Confidence: {conf}\n"
                    )
                f.write("\n")

            # Symbolic Arc Summary
            if episodes:
                arc_counts = {}
                tag_counts = {}
                for e in episodes:
                    arc = e.get("arc_label", "unknown")
                    tag = e.get("symbolic_tag", "unknown")
                    arc_counts[arc] = arc_counts.get(arc, 0) + 1
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                f.write("## 🎭 Symbolic Arc Distribution\n")
                for arc, count in arc_counts.items():
                    f.write(f"- {arc}: {count}\n")
                f.write("\n")

                f.write("## 🏷️ Symbolic Tag Distribution\n")
                for tag, count in tag_counts.items():
                    f.write(f"- {tag}: {count}\n")
                f.write("\n")

            if drift_summary:
                f.write("## 🌀 Arc Drift Since Last Cycle\n")
                for arc, delta in drift_summary.items():
                    sign = "+" if delta > 0 else ""
                    f.write(f"- {arc}: {sign}{delta}\n")
                f.write("\n")

            # Simulation Drift Summary
            if simulation_drift:
                f.write("## 🧪 Simulation Drift Summary\n")
                overlay = simulation_drift.get("overlay_drift", {})
                if overlay:
                    for k, v in overlay.items():
                        sign = "+" if v > 0 else ""
                        f.write(f"- Overlay Δ {k}: {sign}{v:.3f}\n")
                rule_deltas = simulation_drift.get("rule_trigger_deltas", {})
                if rule_deltas:
                    f.write("- Rule trigger delta:\n")
                    for rule, delta in rule_deltas.items():
                        sign = "+" if delta > 0 else ""
                        f.write(f"  - {rule}: {sign}{delta}\n")
                struct = simulation_drift.get("structural_change", None)
                if struct is not None:
                    sign = "+" if struct > 0 else ""
                    f.write(f"- Turn count changed by: {sign}{struct}\n")
                f.write("\n")

            # Risk Summary (simple volatility cue)
            if forecasts and any("alignment_components" in f for f in forecasts):
                f.write("## ⚠️ Risk Observations\n")
                for fc in forecasts:
                    components = fc.get("alignment_components", {})
                    if components.get("arc_stability", 1.0) < 0.6:
                        f.write(
                            f"- `Volatile Arc`: {fc.get('trace_id')} → Stability: {components['arc_stability']}\n"
                        )
                    if components.get("novelty", 0.0) < 0.5:
                        f.write(
                            f"- `Low Novelty`: {fc.get('trace_id')} → Novelty: {components['novelty']}\n"
                        )
                f.write("\n")

            f.write("---\nGenerated by Pulse AI Operator Brief Generator\n")
            print(f"✅ Operator brief written to {output_md_path}")

    except Exception as e:
        print(f"❌ Failed to generate operator brief: {e}")
