# Module Analysis: `scripts/legacy/runversionone.py`

**Report Generated:** May 18, 2025

## 1. Module Intent/Purpose

The primary role of the [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py) module is to serve as an executable script for:
1.  Establishing a baseline forecast accuracy using a retrodiction simulation based on historical data. This "baseline" likely represents an older or simpler version of the simulation logic.
2.  Running an optimized, parallel retrodiction training process.
3.  Comparing the performance (e.g., Mean Squared Error) of the optimized training against the established baseline.

It appears to be a legacy tool for evaluating and comparing different configurations or versions of the Pulse simulation and training mechanisms, specifically focusing on a "version one" (implied by filename) against a newer, parallelized approach.

## 2. Operational Status/Completeness

*   The module seems largely complete for its specific dual purpose of running the baseline and the parallel training comparison.
*   Comments such as `# You might want to initialize initial_state.variables...` (line 155 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:155)) and discussions around `LearningEngine` integration (lines 167-178 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:167-178)) suggest some areas might have been in flux or relied on evolving components.
*   A fallback value for `optimized_mse` (line 388 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:388): `baseline_mse * 0.9`) indicates a placeholder if actual results aren't available, suggesting it was designed to run even with partial outcomes from the parallel training.
*   The warning `logger.warning("Reached end of function without a specific return...")` (line 327 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:327)) in `establish_baseline_accuracy` points to a potential minor control flow or error handling gap, though it acts as a safeguard.

## 3. Implementation Gaps / Unfinished Next Steps

*   The "legacy" status and filename "runversionone" strongly imply the module itself is outdated, and its "next step" was the adoption of the parallel training infrastructure it utilizes and compares against.
*   The script is tailored for a specific comparison rather than a generalized framework for benchmarking arbitrary simulation versions.
*   The integration of `LearningEngine` and `EnhancedRecursiveTrainingMetrics` (lines 167-178 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:167-178)) appears somewhat ad-hoc, hinting at potential refinements that were not implemented within this script.
*   The `compute_full_state_error` function (lines 229-259 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:229-259)) is specific to 'overlays', 'variables', and 'capital' components of `WorldState`. It would require updates if `WorldState` evolved to include more data categories.
*   The import of `optimized_bayesian_trust_tracker` from [`core.optimized_trust_tracker`](core/optimized_trust_tracker.py:13) is unused in [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py).

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`simulation_engine.simulator_core`](simulation_engine/simulator_core.py:7): `simulate_forward`, `WorldState`
*   [`simulation_engine.worldstate`](simulation_engine/worldstate.py:8): `Variables`, `SymbolicOverlays`, `CapitalExposure`
*   [`recursive_training.data.data_store`](recursive_training/data/data_store.py:9): `RecursiveDataStore`
*   [`recursive_training.advanced_metrics.enhanced_metrics`](recursive_training/advanced_metrics/enhanced_metrics.py:10): `EnhancedRecursiveTrainingMetrics`
*   [`learning.learning`](learning/learning.py:11): `LearningEngine`
*   [`recursive_training.parallel_trainer`](recursive_training/parallel_trainer.py:12): `ParallelTrainingCoordinator`, `run_parallel_retrodiction_training`
*   [`core.optimized_trust_tracker`](core/optimized_trust_tracker.py:13): `optimized_bayesian_trust_tracker` (imported but not used)

### External Library Dependencies:
*   `json`
*   `logging`
*   `datetime`
*   `typing`
*   `os` (used in `if __name__ == "__main__":` block in [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:332))

### Interactions via Shared Data:
*   Loads historical data (e.g., `historical_{var_name}`) from [`RecursiveDataStore`](recursive_training/data/data_store.py:9).
*   Writes results of parallel training to `"parallel_training_results.json"` (line 371 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:371)).

### Input/Output Files:
*   **Input:** Datasets from [`RecursiveDataStore`](recursive_training/data/data_store.py:9) (e.g., `historical_spx_close`).
*   **Output:**
    *   Console logs via the `logging` module.
    *   `"parallel_training_results.json"` (line 371 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:371)).

## 5. Function and Class Example Usages

*   **`HistoricalDataLoader` Class:**
    *   Purpose: Loads and provides historical data snapshots turn-by-turn.
    *   Usage: `data_loader = HistoricalDataLoader(historical_data)` (line 141 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:141)). Methods like `get_snapshot_by_turn()` (line 213 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:213)) and `get_total_turns()` (line 144 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:144)) are then used.
*   **`load_historical_data_for_baseline(variable_names: List[str]) -> Dict`:**
    *   Purpose: Fetches historical data for specified variables from `RecursiveDataStore`.
    *   Usage: `historical_data = load_historical_data_for_baseline(baseline_variables)` (line 347 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:347)).
*   **`establish_baseline_accuracy(variable_names: List[str], simulation_turns: int) -> Dict`:**
    *   Purpose: Runs the baseline retrodiction simulation and calculates accuracy metrics.
    *   Usage: `baseline_results = establish_baseline_accuracy(baseline_variables, baseline_simulation_turns)` (line 347 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:347)).
*   **`run_parallel_retrodiction_training(**training_config)` (from [`recursive_training.parallel_trainer`](recursive_training/parallel_trainer.py:12)):**
    *   Purpose: Executes the optimized parallel retrodiction training.
    *   Usage: `training_results = run_parallel_retrodiction_training(**training_config)` (line 376 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:376)).

## 6. Hardcoding Issues

*   **Variable Names for Baseline:** `baseline_variables` list (e.g., `"spx_close"`) is hardcoded (line 337 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:337)).
*   **Simulation Parameters:** `baseline_simulation_turns = 100` (line 339 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:339)).
*   **Training Data Period:** `timedelta(days=3*365)` for 3 years (line 362 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:362)).
*   **Batch Processing:** `batch_size_days = 30` (line 370 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:370)).
*   **Output Filename:** `"parallel_training_results.json"` (line 371 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:371)).
*   **Dataset Naming Convention:** The prefix `"historical_"` for datasets in `RecursiveDataStore` (lines 94, 114 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:94)).
*   **Fallback MSE Improvement:** A 10% improvement (`baseline_mse * 0.9`) is a hardcoded fallback (line 388 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:388)).

## 7. Coupling Points

*   Strongly coupled to the data structures of `WorldState` and its components (`Variables`, `SymbolicOverlays`, `CapitalExposure`) from [`simulation_engine.worldstate`](simulation_engine/worldstate.py:8).
*   Dependent on the API and expected data format of [`RecursiveDataStore`](recursive_training/data/data_store.py:9).
*   Relies on the specific behavior and signature of `simulate_forward` from [`simulation_engine.simulator_core`](simulation_engine/simulator_core.py:7).
*   Depends on [`EnhancedRecursiveTrainingMetrics`](recursive_training/advanced_metrics/enhanced_metrics.py:10) and [`LearningEngine`](learning/learning.py:11), though their integration for baseline metrics seems somewhat indirect.
*   Crucially dependent on the `run_parallel_retrodiction_training` function from [`recursive_training.parallel_trainer`](recursive_training/parallel_trainer.py:12).

## 8. Existing Tests

*   No dedicated test file (e.g., `tests/scripts/legacy/test_runversionone.py`) is apparent in the project structure.
*   The script itself functions as a high-level integration test or benchmarking tool for the components it orchestrates. Formal unit tests for this script's logic may be limited due to its nature as an executable.

## 9. Module Architecture and Flow

The script operates in two main steps within its `if __name__ == "__main__":` block (line 332 of [`scripts/legacy/runversionone.py`](scripts/legacy/runversionone.py:332)):

1.  **Establish Baseline Accuracy (`establish_baseline_accuracy`):**
    *   Loads historical data for specified variables using `HistoricalDataLoader`.
    *   Initializes a `WorldState` based on the first historical snapshot.
    *   Iteratively simulates forward, turn by turn. For each turn `i`:
        *   The simulation starts from the *actual historical state* of turn `i-1`.
        *   `simulate_forward` advances this state by one turn.
        *   The resulting simulated state is compared against the *actual historical ground truth* for turn `i`.
        *   Error metrics (MSE for variables, overlays, capital) are computed via `compute_full_state_error`.
    *   Averages the error metrics over all simulated turns.
    *   Logs these baseline metrics.

2.  **Run Optimized Parallel Training (`run_parallel_retrodiction_training`):**
    *   Defines training configuration (variables, time period, parallelism, batch size, output file).
    *   Calls `run_parallel_retrodiction_training` from the [`recursive_training.parallel_trainer`](recursive_training/parallel_trainer.py:12) module.
    *   Logs performance metrics (speedup, batch success rate) from the parallel training.
    *   Compares the final MSE from parallel training (or a fallback) to the baseline MSE and logs the percentage improvement.

The `HistoricalDataLoader` class is a key component, responsible for fetching data via `RecursiveDataStore` and providing it in a turn-based manner for the baseline simulation.

## 10. Naming Conventions

*   The module generally adheres to PEP 8 styling (snake_case for functions/variables, PascalCase for classes).
*   Class names (`HistoricalDataLoader`) and function names (`establish_baseline_accuracy`, `load_historical_data_for_baseline`) are descriptive and clear.
*   Variable names (`historical_data`, `turns_to_simulate`, `ground_truth_snapshot`) are intuitive.
*   The filename `runversionone.py` and its location in `scripts/legacy/` clearly communicate its purpose and status.
*   No significant deviations from project standards or AI-induced naming errors are apparent.