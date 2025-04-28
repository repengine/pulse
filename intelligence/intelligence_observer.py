# pulse/intelligence/intelligence_observer.py

"""
Pulse Intelligence Observer

Central learning intelligence layer for Pulse.
- Observes simulation divergences (batch contradictions, symbolic splits)
- Computes forecast-ground truth divergence
- Proposes epistemic upgrades
- Logs structured learning episodes

Merged design from original Observer Core + Divergence Analysis Extensions.

Author: Pulse Intelligence Core v0.5
"""

import json
import os
from typing import Dict, Any, List, Optional
from intelligence.function_router import FunctionRouter

# Setup dynamic router to Pulse modules
router = FunctionRouter()
router.load_modules({
    "contradiction": "forecast_output.forecast_contradiction_detector",
    "divergence": "forecast_output.forecast_divergence_detector",
    "upgrade_sandbox": "intelligence.upgrade_sandbox_manager",
})

class Observer:
    def __init__(self, memory_dir: str = "data/intelligence_observer_memory"):
        """
        Initialize the Observer Intelligence Core.
        """
        self.memory_dir = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        self.learning_log: List[Dict[str, Any]] = []
        self.learning_log_path = os.path.join(self.memory_dir, "Observer_learning_log.jsonl")
        self.sandbox = router.modules["upgrade_sandbox"].UpgradeSandboxManager()

    # --- Passive Observation from Log Files ---

    def observe_simulation_outputs(self, divergence_log_path: str) -> List[Dict[str, Any]]:
        """Load divergence logs for analysis."""
        try:
            with open(divergence_log_path, "r", encoding="utf-8") as f:
                divergence_data = [json.loads(line) for line in f if line.strip()]
            return divergence_data
        except FileNotFoundError:
            print(f"[Observer] ⚠️ No divergence log found at {divergence_log_path}")
            return []

    def analyze_divergence(self, divergences: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize divergence types and frequencies from passive logs."""
        summary = {}
        for d in divergences:
            tag = d.get("divergence_type", "unknown")
            summary[tag] = summary.get(tag, 0) + 1
        return summary

    # --- Active Batch Divergence Analysis ---

    def observe_batch_contradictions(self, forecasts: List[Dict]) -> List[Dict]:
        """Detect contradictions within a forecast batch."""
        try:
            contradictions = router.run_function("contradiction", "detect_forecast_contradictions", forecasts)
        except (KeyError, AttributeError) as e:
            print(f"[Observer] ⚠️ Contradiction detection failed: {e}")
            contradictions = []
        return contradictions

    def observe_symbolic_divergence(self, forecasts: List[Dict]) -> Dict:
        """Analyze symbolic divergence within a forecast batch."""
        return router.run_function("divergence", "generate_divergence_report", forecasts)

    def compare_forecasts_to_ground_truth(self, forecasts: List[Dict], truth_snapshots: List[Dict]) -> List[Dict]:
        """Directly compare forecasts to ground-truth snapshots."""
        """Compute mean absolute error for shared variables."""
        """Phase 2 plan: 
            Add weighted variable importance (if some variables matter more than others).
            Calculate symbolic drift delta alongside numerical error.
            Normalize error scores relative to baseline variance.
            Add a "top error variables" list per forecast for learning prioritization.
        """
        results = []
        for forecast, truth in zip(forecasts, truth_snapshots):
            forecast_vars = forecast.get("forecast", {}).get("end_variables", {})
            truth_vars = truth.get("variables", {})
            if not forecast_vars or not truth_vars:
                continue
            error = self._compute_variable_error(forecast_vars, truth_vars)
            results.append({
                "forecast_id": forecast.get("trace_id", "unknown"),
                "error_score": error
            })
        return results

    def _compute_variable_error(self, forecast_vars: Dict, truth_vars: Dict) -> float:
        """Compute mean absolute error across shared forecast variables."""
        shared_keys = set(forecast_vars.keys()) & set(truth_vars.keys())
        if not shared_keys:
            return 1.0
        error_sum = 0.0
        for key in shared_keys:
            fv = forecast_vars.get(key, 0.0)
            tv = truth_vars.get(key, 0.0)
            error_sum += abs(fv - tv)
        return error_sum / len(shared_keys)

    # --- Learning and Upgrade Proposal System ---

    def propose_upgrades(self, foreign_fingerprint_path: str) -> Dict[str, Any]:
        """Propose epistemic upgrades based on archived foreign fingerprints."""
        try:
            with open(foreign_fingerprint_path, "r", encoding="utf-8") as f:
                foreign_data = [json.loads(line) for line in f if line.strip()]
        except FileNotFoundError:
            print(f"[Observer] ⚠️ No foreign fingerprint archive found at {foreign_fingerprint_path}")
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

    def propose_symbolic_upgrades_live(self, divergence_report: Dict) -> Optional[str]:
        """Propose epistemic upgrades live based on symbolic divergence observation."""
        if divergence_report.get("divergence_score", 0) > 0.15:
            upgrade_data = {
                "proposed_corrections": divergence_report.get("symbolic_conflicts", []),
                "notes": "Auto-proposed upgrade from live symbolic divergence."
            }
            return self.sandbox.submit_upgrade(upgrade_data)
        return None

    def record_learning_episode(self, divergence_summary: Dict[str, Any], upgrade_plan: Dict[str, Any]) -> None:
        """Record a learning episode from observation."""
        episode = {
            "divergence_summary": divergence_summary,
            "upgrade_plan": upgrade_plan
        }
        self.learning_log.append(episode)
        self._persist_learning_log()

    def _persist_learning_log(self) -> None:
        """Save the current learning log to disk."""
        with open(self.learning_log_path, "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2)

# Example CLI usage for standalone testing
if __name__ == "__main__":
    print("[Observer] 🚀 Running standalone observer test...")
    dummy_forecasts = [
        {"trace_id": "f1", "forecast": {"end_variables": {"gdp_growth": 2.1, "inflation": 0.03}}, "symbolic_tag": "Hope Surge"},
        {"trace_id": "f2", "forecast": {"end_variables": {"gdp_growth": 1.8, "inflation": 0.05}}, "symbolic_tag": "Collapse Risk"},
    ]
    dummy_truth = [
        {"variables": {"gdp_growth": 2.0, "inflation": 0.04}},
        {"variables": {"gdp_growth": 1.9, "inflation": 0.045}},
    ]
    obs = Observer()
    contradictions = obs.observe_batch_contradictions(dummy_forecasts)
    divergence = obs.observe_symbolic_divergence(dummy_forecasts)
    ground_truth_errors = obs.compare_forecasts_to_ground_truth(dummy_forecasts, dummy_truth)
    print("[Observer] ❗ Contradictions:", contradictions)
    print("[Observer] 📈 Divergence:", divergence)
    print("[Observer] 📊 Ground-truth comparison:", ground_truth_errors)
