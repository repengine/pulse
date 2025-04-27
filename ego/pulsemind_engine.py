"""
PulseMind Core Engine

First generation learning intelligence layer for Pulse.
Observes simulation divergence, computes symbolic loss,
proposes epistemic upgrades, and logs learning episodes.

Author: Pulse Development Team
Date: 2025-04-27
"""

import json
import os
from typing import Dict, Any, List, Optional

# Placeholder imports (to patch when integrating)
# from dev_tools.epistemic_mirror_review import summarize_foreign_fingerprints
# from dev_tools.propose_epistemic_upgrades import propose_upgrades
# from forecast_output.forecast_memory import load_forecast_memory
# from forecast_output.forecast_divergence_detector import load_divergence_log

class PulseMind:
    def __init__(self, memory_dir: str = "data/pulsemind_memory"):
        self.memory_dir = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        self.learning_log: List[Dict[str, Any]] = []

    def observe_simulation_outputs(self, divergence_log_path: str) -> List[Dict[str, Any]]:
        """Load divergence logs for analysis."""
        try:
            with open(divergence_log_path, "r", encoding="utf-8") as f:
                divergence_data = [json.loads(line) for line in f if line.strip()]
            return divergence_data
        except FileNotFoundError:
            print(f"[PulseMind] No divergence log found at {divergence_log_path}")
            return []

    def analyze_divergence(self, divergences: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize divergence types and frequencies."""
        summary = {}
        for d in divergences:
            tag = d.get("divergence_type", "unknown")
            summary[tag] = summary.get(tag, 0) + 1
        return summary

    def propose_upgrades(self, foreign_fingerprint_path: str) -> Dict[str, Any]:
        """Propose epistemic upgrades based on foreign causal fingerprints."""
        try:
            with open(foreign_fingerprint_path, "r", encoding="utf-8") as f:
                foreign_data = [json.loads(line) for line in f if line.strip()]
        except FileNotFoundError:
            print(f"[PulseMind] No foreign fingerprint archive found at {foreign_fingerprint_path}")
            foreign_data = []

        proposed_variables = set()
        proposed_consequences = set()

        for fp in foreign_data:
            if fp.get("variable"):
                proposed_variables.add(fp["variable"])
            if fp.get("consequence"):
                proposed_consequences.add(fp["consequence"])

        upgrade_plan = {
            "proposed_variables": list(proposed_variables),
            "proposed_consequences": list(proposed_consequences),
            "notes": "Proposed from foreign causal archive. Requires trust scoring before integration."
        }
        return upgrade_plan

    def record_learning_episode(self, divergence_summary: Dict[str, int], upgrade_plan: Dict[str, Any]) -> None:
        """Record an observation-learning cycle."""
        episode = {
            "divergence_summary": divergence_summary,
            "upgrade_plan": upgrade_plan
        }
        self.learning_log.append(episode)
        self._persist_learning_log()

    def _persist_learning_log(self) -> None:
        """Save the learning log to disk."""
        path = os.path.join(self.memory_dir, "pulsemind_learning_log.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2)

# Example CLI usage (for testing)
if __name__ == "__main__":
    pm = PulseMind()
    divergences = pm.observe_simulation_outputs("GPT/gpt_forecast_divergence_log.jsonl")
    divergence_summary = pm.analyze_divergence(divergences)
    upgrade_plan = pm.propose_upgrades("GPT/foreign_causal_archive.jsonl")
    pm.record_learning_episode(divergence_summary, upgrade_plan)
    print("✅ PulseMind observation cycle complete.")
