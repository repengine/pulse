# pulse/intelligence/intelligence_observer.py

"""
Pulse Intelligence Observer

Central learning intelligence layer for Pulse.
Observes simulation divergences, computes forecast-ground truth divergence,
proposes epistemic upgrades, and logs structured learning episodes.

Merged design from original Observer Core + Divergence Analysis Extensions.

Author: Pulse Intelligence Core v0.5
"""

import json
import os
from typing import Dict, Any, List, Optional, Set, Union, Callable
from intelligence.function_router import FunctionRouter
from intelligence.intelligence_config import OBSERVER_MEMORY_DIR
from intelligence.upgrade_sandbox_manager import (
    UpgradeSandboxManager,
)  # Import for type hinting

# Setup dynamic router to Pulse modules
router: FunctionRouter = FunctionRouter()
router.load_modules(
    {
        "contradiction": "forecast_output.forecast_contradiction_detector",
        "divergence": "forecast_output.forecast_divergence_detector",
        "upgrade_sandbox": "intelligence.upgrade_sandbox_manager",
    }
)


class Observer:
    """
    Central learning intelligence layer for Pulse.

    Observes simulation divergences, computes forecast-ground truth divergence,
    proposes epistemic upgrades, and logs structured learning episodes.
    """

    def __init__(self, memory_dir: str = OBSERVER_MEMORY_DIR) -> None:
        """
        Initialize the Observer Intelligence Core.

        Args:
            memory_dir: Directory to store observer memory, including the learning log.
        """
        self.memory_dir: str = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        self.learning_log_path: str = os.path.join(
            self.memory_dir, "Observer_learning_log.jsonl"
        )
        # Access the loaded module and instantiate the manager
        self.sandbox: UpgradeSandboxManager = router.modules[
            "upgrade_sandbox"
        ].UpgradeSandboxManager()

    # --- Passive Observation from Log Files ---

    def observe_simulation_outputs(
        self, divergence_log_path: str
    ) -> List[Dict[str, Any]]:
        """
        Load divergence logs for analysis.

        Args:
            divergence_log_path: Path to the divergence log file (JSONL format).

        Returns:
            A list of dictionaries, where each dictionary represents a divergence entry.
            Returns an empty list if the file is not found or is empty.
        """
        try:
            with open(divergence_log_path, "r", encoding="utf-8") as f:
                divergence_data: List[Dict[str, Any]] = [
                    json.loads(line) for line in f if line.strip()
                ]
            return divergence_data
        except FileNotFoundError:
            print(f"[Observer] ⚠️ No divergence log found at {divergence_log_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"[Observer] ❌ Error decoding JSON from {divergence_log_path}: {e}")
            return []

    # --- Active Batch Divergence Analysis ---

    def observe_batch_contradictions(
        self, forecasts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions within a forecast batch.

        Args:
            forecasts: A list of forecast dictionaries.

        Returns:
            A list of dictionaries, where each dictionary represents a detected contradiction.
            Returns an empty list if contradiction detection fails or no contradictions are found.
        """
        try:
            # Assuming 'detect_forecast_contradictions' is a function that takes a list of dicts and returns a list of dicts
            func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]] = (
                router.run_function("contradiction.detect_forecast_contradictions")
            )
            contradictions: List[Dict[str, Any]] = func(forecasts)
        except (KeyError, AttributeError) as e:
            print(f"[Observer] ⚠️ Contradiction detection failed: {e}")
            contradictions = []
        except Exception as e:
            print(f"[Observer] ❌ Unexpected error during contradiction detection: {e}")
            contradictions = []
        return contradictions

    def observe_symbolic_divergence(
        self, forecasts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze symbolic divergence within a forecast batch.

        Args:
            forecasts: A list of forecast dictionaries.

        Returns:
            A dictionary representing the symbolic divergence report.
            Returns an empty dictionary if divergence analysis fails.
        """
        try:
            # Assuming 'generate_divergence_report' takes a list of dicts and returns a dict
            func: Callable[[List[Dict[str, Any]]], Dict[str, Any]] = (
                router.run_function("divergence.generate_divergence_report")
            )
            return func(forecasts)
        except (KeyError, AttributeError) as e:
            print(f"[Observer] ⚠️ Symbolic divergence analysis failed: {e}")
            return {}
        except Exception as e:
            print(
                f"[Observer] ❌ Unexpected error during symbolic divergence analysis: {e}"
            )
            return {}

    def compare_forecasts_to_ground_truth(
        self, forecasts: List[Dict[str, Any]], truth_snapshots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Directly compare forecasts to ground-truth snapshots and compute error scores.

        Args:
            forecasts: A list of forecast dictionaries.
            truth_snapshots: A list of ground-truth snapshot dictionaries.

        Returns:
            A list of dictionaries, each containing a forecast ID and its computed error score.
        """
        """Compute mean absolute error for shared variables."""
        """Phase 2 plan:
            Add weighted variable importance (if some variables matter more than others).
            Calculate symbolic drift delta alongside numerical error.
            Normalize error scores relative to baseline variance.
            Add a "top error variables" list per forecast for learning prioritization.
        """
        results: List[Dict[str, Any]] = []
        for forecast, truth in zip(forecasts, truth_snapshots):
            forecast_vars: Dict[str, Any] = forecast.get("forecast", {}).get(
                "end_variables", {}
            )
            truth_vars: Dict[str, Any] = truth.get("variables", {})
            if not forecast_vars or not truth_vars:
                continue
            error: float = self._compute_variable_error(forecast_vars, truth_vars)
            results.append(
                {
                    "forecast_id": forecast.get("trace_id", "unknown"),
                    "error_score": error,
                }
            )
        return results

    def _compute_variable_error(
        self, forecast_vars: Dict[str, Any], truth_vars: Dict[str, Any]
    ) -> float:
        """
        Compute mean absolute error across shared forecast variables.

        Args:
            forecast_vars: Dictionary of variables from a forecast.
            truth_vars: Dictionary of variables from ground truth.

        Returns:
            The mean absolute error for shared variables. Returns 1.0 if no shared keys.
        """
        shared_keys: Set[str] = set(forecast_vars.keys()) & set(truth_vars.keys())
        if not shared_keys:
            return 1.0
        error_sum: float = 0.0
        for key in shared_keys:
            # Ensure values are treated as numbers for subtraction
            fv: Union[int, float] = float(forecast_vars.get(key, 0.0))
            tv: Union[int, float] = float(truth_vars.get(key, 0.0))
            error_sum += abs(fv - tv)
        return error_sum / len(shared_keys)

    # --- Learning and Upgrade Proposal System ---

    def propose_upgrades(self, foreign_fingerprint_path: str) -> Dict[str, Any]:
        """
        Propose epistemic upgrades based on archived foreign fingerprints.

        Args:
            foreign_fingerprint_path: Path to the foreign fingerprint archive file (JSONL format).

        Returns:
            A dictionary representing the proposed upgrade plan.
        """
        try:
            with open(foreign_fingerprint_path, "r", encoding="utf-8") as f:
                foreign_data: List[Dict[str, Any]] = [
                    json.loads(line) for line in f if line.strip()
                ]
        except FileNotFoundError:
            print(
                f"[Observer] ⚠️ No foreign fingerprint archive found at {foreign_fingerprint_path}"
            )
            foreign_data = []
        except json.JSONDecodeError as e:
            print(
                f"[Observer] ❌ Error decoding JSON from {foreign_fingerprint_path}: {e}"
            )
            foreign_data = []

        proposed_variables: Set[str] = set()
        proposed_consequences: Set[str] = set()

        for fp in foreign_data:
            if fp_variable := fp.get("variable"):
                proposed_variables.add(str(fp_variable))
            if fp_consequence := fp.get("consequence"):
                proposed_consequences.add(str(fp_consequence))

        upgrade_plan: Dict[str, Any] = {
            "proposed_variables": list(proposed_variables),
            "proposed_consequences": list(proposed_consequences),
            "notes": "Proposed from foreign causal archive. Requires trust scoring before integration.",
        }
        return upgrade_plan

    def propose_symbolic_upgrades_live(
        self, divergence_report: Dict[str, Any]
    ) -> Optional[str]:
        """
        Propose epistemic upgrades live based on symbolic divergence observation.

        Args:
            divergence_report: A dictionary representing the symbolic divergence report.

        Returns:
            The unique upgrade ID if a proposal is submitted, otherwise None.
        """
        if divergence_report.get("divergence_score", 0) > 0.15:
            upgrade_data: Dict[str, Any] = {
                "proposed_corrections": divergence_report.get("symbolic_conflicts", []),
                "notes": "Auto-proposed upgrade from live symbolic divergence.",
            }
            return self.sandbox.submit_upgrade(upgrade_data)
        return None

    def record_learning_episode(
        self, divergence_summary: Dict[str, Any], upgrade_plan: Dict[str, Any]
    ) -> None:
        """
        Record a learning episode from observation.

        Args:
            divergence_summary: A summary of the observed divergence.
            upgrade_plan: The proposed upgrade plan for this episode.
        """
        episode: Dict[str, Any] = {
            "divergence_summary": divergence_summary,
            "upgrade_plan": upgrade_plan,
        }
        try:
            with open(self.learning_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(episode) + "\n")
        except IOError as e:
            print(
                f"[Observer] ❌ Error appending learning episode to {self.learning_log_path}: {e}"
            )


# Example CLI usage for standalone testing
if __name__ == "__main__":
    print("[Observer] 🚀 Running standalone observer test...")
    dummy_forecasts: List[Dict[str, Any]] = [
        {
            "trace_id": "f1",
            "forecast": {"end_variables": {"gdp_growth": 2.1, "inflation": 0.03}},
            "symbolic_tag": "Hope Surge",
        },
        {
            "trace_id": "f2",
            "forecast": {"end_variables": {"gdp_growth": 1.8, "inflation": 0.05}},
            "symbolic_tag": "Collapse Risk",
        },
    ]
    dummy_truth: List[Dict[str, Any]] = [
        {"variables": {"gdp_growth": 2.0, "inflation": 0.04}},
        {"variables": {"gdp_growth": 1.9, "inflation": 0.045}},
    ]
    obs: Observer = Observer()
    contradictions: List[Dict[str, Any]] = obs.observe_batch_contradictions(
        dummy_forecasts
    )
    divergence_report: Dict[str, Any] = obs.observe_symbolic_divergence(dummy_forecasts)
    ground_truth_errors: List[Dict[str, Any]] = obs.compare_forecasts_to_ground_truth(
        dummy_forecasts, dummy_truth
    )
    print("[Observer] ❗ Contradictions:", contradictions)
    print("[Observer] 📈 Divergence:", divergence_report)
    print("[Observer] 📊 Ground-truth comparison:", ground_truth_errors)
    upgrade_id: Optional[str] = obs.propose_symbolic_upgrades_live(divergence_report)
    if upgrade_id:
        print(f"[Observer] 🚀 Proposed upgrade with ID: {upgrade_id}")
    else:
        print("[Observer] No upgrade proposed based on divergence.")
