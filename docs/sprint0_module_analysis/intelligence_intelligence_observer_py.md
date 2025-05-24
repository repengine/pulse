# Module Analysis: `intelligence/intelligence_observer.py`

## 1. Module Intent/Purpose

The primary role of the [`intelligence/intelligence_observer.py`](intelligence/intelligence_observer.py:1) module is to serve as the central learning and intelligence layer for the Pulse system. Its responsibilities include:

*   Observing and analyzing divergences between simulation forecasts and actual outcomes (ground truth).
*   Detecting contradictions within forecast batches.
*   Computing error scores by comparing forecasts to ground-truth snapshots.
*   Proposing epistemic upgrades (e.g., new variables, causal relationships) based on observed divergences and foreign causal archives.
*   Managing an "upgrade sandbox" for testing proposed changes.
*   Logging structured learning episodes to facilitate system improvement.

It aims to enable the system to learn from its experiences and improve its forecasting accuracy and understanding of the observed environment.

## 2. Operational Status/Completeness

The module appears to be operational for its core defined functions. It includes:
*   Initialization of necessary components like the `FunctionRouter` and `UpgradeSandboxManager`.
*   Methods for loading and processing divergence logs.
*   Methods for active analysis of forecast batches.
*   A system for proposing and submitting upgrades.
*   Logging of learning episodes.

However, there are indications of planned future enhancements:
*   The docstring for [`compare_forecasts_to_ground_truth()`](intelligence/intelligence_observer.py:122) explicitly mentions a "Phase 2 plan" (lines 134-139) which includes:
    *   Adding weighted variable importance.
    *   Calculating symbolic drift delta.
    *   Normalizing error scores.
    *   Adding a "top error variables" list.
*   The module version is stated as "Pulse Intelligence Core v0.5" in the header comment (line 12), suggesting it's not yet a final version.

No explicit `TODO` comments are present, but the "Phase 2 plan" serves a similar purpose.

## 3. Implementation Gaps / Unfinished Next Steps

Based on the "Phase 2 plan" and the module's purpose, the following are potential implementation gaps or next steps:

*   **Weighted Variable Importance:** The current error computation in [`_compute_variable_error()`](intelligence/intelligence_observer.py:153) treats all variables equally. Implementing a system to weigh variables by importance during error calculation is a clear next step.
*   **Symbolic Drift Delta:** While numerical error is calculated, the planned "symbolic drift delta" (line 136) is not yet implemented. This would likely involve a more qualitative assessment of how symbolic tags or interpretations have diverged.
*   **Normalized Error Scores:** Error scores are currently absolute. Normalizing them (e.g., relative to baseline variance, as suggested on line 137) would provide more contextually meaningful metrics.
*   **Top Error Variables List:** Identifying and listing variables contributing most to forecast errors (line 138) would be valuable for prioritizing learning and debugging.
*   **Advanced Upgrade Proposal Logic:** The current [`propose_upgrades()`](intelligence/intelligence_observer.py:177) method simply aggregates variables and consequences from foreign fingerprints. More sophisticated logic could be developed to analyze patterns, score potential upgrades, or consider interactions.
*   **Trust Scoring for Upgrades:** The note "Requires trust scoring before integration" (line 210) for upgrades proposed from foreign archives implies a missing or separate module/feature for assessing the reliability of these proposals.
*   **Integration with Other Learning Components:** While it proposes upgrades, the full lifecycle of how these upgrades are tested, validated, and integrated back into the core system (beyond submission to the sandbox) isn't fully detailed within this module alone.

Development seems to have established a solid foundation, with clear pointers (the "Phase 2 plan") for future expansion.
## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`intelligence.function_router.FunctionRouter`](intelligence/function_router.py:1): Used to dynamically load and call functions from other modules (e.g., for contradiction and divergence detection).
*   [`intelligence.intelligence_config.OBSERVER_MEMORY_DIR`](intelligence/intelligence_config.py:1): Imported to define the default directory for observer memory.
*   [`intelligence.upgrade_sandbox_manager.UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:1): Used to manage and submit proposed epistemic upgrades.

### External Library Dependencies:
*   `json`: Used for reading and writing JSONL files (divergence logs, learning logs, foreign fingerprints).
*   `os`: Used for path manipulation (e.g., [`os.path.join()`](intelligence/intelligence_observer.py:46), [`os.makedirs()`](intelligence/intelligence_observer.py:45)).
*   `typing`: Used for type hinting (`Dict`, `Any`, `List`, `Optional`, `Set`, `Union`, `Callable`).

### Interaction with Other Modules via Shared Data:
*   **Input Files:**
    *   Reads divergence log files (JSONL format, path provided to [`observe_simulation_outputs()`](intelligence/intelligence_observer.py:52)).
    *   Reads foreign fingerprint archive files (JSONL format, path provided to [`propose_upgrades()`](intelligence/intelligence_observer.py:177)).
*   **Output Files:**
    *   Writes learning episodes to [`Observer_learning_log.jsonl`](intelligence/intelligence_observer.py:46) in the `memory_dir`.
*   **Function Router Calls:**
    *   Calls `detect_forecast_contradictions` from the module mapped to `"contradiction"` (specified as `"forecast_output.forecast_contradiction_detector"` in [`router.load_modules()`](intelligence/intelligence_observer.py:24)).
    *   Calls `generate_divergence_report` from the module mapped to `"divergence"` (specified as `"forecast_output.forecast_divergence_detector"` in [`router.load_modules()`](intelligence/intelligence_observer.py:24)).
*   **Upgrade Sandbox Manager:**
    *   Interacts with the `UpgradeSandboxManager` instance (`self.sandbox`) by calling its [`submit_upgrade()`](intelligence/intelligence_observer.py:229) method.

## 5. Function and Class Example Usages

The `if __name__ == "__main__":` block (lines 252-274) provides a clear example of how the `Observer` class and its key methods are intended to be used:

```python
if __name__ == "__main__":
    print("[Observer] 🚀 Running standalone observer test...")
    dummy_forecasts: List[Dict[str, Any]] = [
        {"trace_id": "f1", "forecast": {"end_variables": {"gdp_growth": 2.1, "inflation": 0.03}}, "symbolic_tag": "Hope Surge"},
        {"trace_id": "f2", "forecast": {"end_variables": {"gdp_growth": 1.8, "inflation": 0.05}}, "symbolic_tag": "Collapse Risk"},
    ]
    dummy_truth: List[Dict[str, Any]] = [
        {"variables": {"gdp_growth": 2.0, "inflation": 0.04}},
        {"variables": {"gdp_growth": 1.9, "inflation": 0.045}},
    ]
    obs: Observer = Observer() # Initialize Observer
    # Observe contradictions in a batch of forecasts
    contradictions: List[Dict[str, Any]] = obs.observe_batch_contradictions(dummy_forecasts)
    # Observe symbolic divergence in a batch of forecasts
    divergence_report: Dict[str, Any] = obs.observe_symbolic_divergence(dummy_forecasts)
    # Compare forecasts to ground truth
    ground_truth_errors: List[Dict[str, Any]] = obs.compare_forecasts_to_ground_truth(dummy_forecasts, dummy_truth)
    
    print("[Observer] ❗ Contradictions:", contradictions)
    print("[Observer] 📈 Divergence:", divergence_report)
    print("[Observer] 📊 Ground-truth comparison:", ground_truth_errors)
    
    # Propose upgrades based on live divergence
    upgrade_id: Optional[str] = obs.propose_symbolic_upgrades_live(divergence_report)
    if upgrade_id:
        print(f"[Observer] 🚀 Proposed upgrade with ID: {upgrade_id}")
    else:
        print("[Observer] No upgrade proposed based on divergence.")

    # (Implicitly) Recording a learning episode would involve:
    # obs.record_learning_episode(divergence_summary=divergence_report, upgrade_plan=some_upgrade_plan)
    
    # (Implicitly) Observing from logs:
    # obs.observe_simulation_outputs("path/to/divergence.log")
    
    # (Implicitly) Proposing upgrades from archive:
    # obs.propose_upgrades("path/to/foreign_fingerprints.jsonl")
```

## 6. Hardcoding Issues

*   **Default Memory Directory:** While [`OBSERVER_MEMORY_DIR`](intelligence/intelligence_config.py:1) is imported from a config file, its actual value within that config file might be hardcoded. The observer defaults to this path if not overridden during instantiation.
*   **Log Filename:** The learning log filename is hardcoded as `"Observer_learning_log.jsonl"` within the [`__init__()`](intelligence/intelligence_observer.py:37) method (line 46).
*   **Divergence Threshold:** The threshold `0.15` for proposing symbolic upgrades in [`propose_symbolic_upgrades_live()`](intelligence/intelligence_observer.py:214) (line 224) is hardcoded. This might be better as a configurable parameter.
*   **Default Error Value:** In [`_compute_variable_error()`](intelligence/intelligence_observer.py:153), if no shared keys are found between forecast and truth, a default error of `1.0` is returned (line 166).
*   **Default Value for Missing Variables:** In [`_compute_variable_error()`](intelligence/intelligence_observer.py:153), `0.0` is used as a default if a key is missing in `forecast_vars` or `truth_vars` during error calculation (lines 170-171).
*   **Function Router Keys & Paths:**
    *   The keys used to register modules with the [`FunctionRouter`](intelligence/function_router.py:1) (`"contradiction"`, `"divergence"`, `"upgrade_sandbox"`) are hardcoded in [`router.load_modules()`](intelligence/intelligence_observer.py:24) (lines 25-27).
    *   The module paths themselves (`"forecast_output.forecast_contradiction_detector"`, etc.) are hardcoded in [`router.load_modules()`](intelligence/intelligence_observer.py:24) (lines 25-27).
*   **Print Prefixes:** The `"[Observer]"` prefix in `print` statements for logging/status messages is consistently hardcoded (e.g., line 68, 71, 92). While consistent, using a proper logger would be more flexible.
*   **Notes in Upgrade Plan:** The string `"Proposed from foreign causal archive. Requires trust scoring before integration."` (line 210) and `"Auto-proposed upgrade from live symbolic divergence."` (line 227) are hardcoded.
## 7. Coupling Points

*   **`FunctionRouter`:** The module is tightly coupled to the [`FunctionRouter`](intelligence/function_router.py:1) for accessing functionalities in other modules. Changes to the router's API or the expected function signatures in routed modules would impact the observer.
*   **`UpgradeSandboxManager`:** Dependency on the [`UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:1) and its [`submit_upgrade()`](intelligence/intelligence_observer.py:229) method.
*   **Routed Module Contracts:**
    *   Expects a function `detect_forecast_contradictions` in the module mapped to `"contradiction"` (via [`router.run_function("contradiction.detect_forecast_contradictions")`](intelligence/intelligence_observer.py:89)).
    *   Expects a function `generate_divergence_report` in the module mapped to `"divergence"` (via [`router.run_function("divergence.generate_divergence_report")`](intelligence/intelligence_observer.py:112)).
*   **Data Structures:**
    *   Relies on specific dictionary structures for forecasts (e.g., `{"trace_id": ..., "forecast": {"end_variables": ...}}`), truth snapshots (e.g., `{"variables": ...}`), divergence reports, and foreign fingerprints. Changes to these structures in other parts of the system could break the observer's processing.
*   **File Formats:** Assumes JSONL format for input divergence logs and foreign fingerprint archives, and outputs its learning log in JSONL.
*   **Configuration (`OBSERVER_MEMORY_DIR`):** Depends on the availability and correctness of this configuration variable from [`intelligence.intelligence_config`](intelligence/intelligence_config.py:1).

## 8. Existing Tests

*   **No Dedicated Test File:** A dedicated test file at the expected location [`tests/test_intelligence_observer.py`](tests/test_intelligence_observer.py) was **not found**.
*   **Standalone Test Script:** The module includes a standalone test script within the `if __name__ == "__main__":` block (lines 252-274). This script provides basic smoke tests for:
    *   [`observe_batch_contradictions()`](intelligence/intelligence_observer.py:76)
    *   [`observe_symbolic_divergence()`](intelligence/intelligence_observer.py:99)
    *   [`compare_forecasts_to_ground_truth()`](intelligence/intelligence_observer.py:122)
    *   [`propose_symbolic_upgrades_live()`](intelligence/intelligence_observer.py:214)
*   **Coverage & Nature:**
    *   The standalone script uses `dummy_forecasts` and `dummy_truth` data.
    *   It covers happy paths for the tested methods.
    *   It does not test file I/O operations extensively (e.g., reading various malformed files, handling I/O errors beyond `FileNotFoundError` and `JSONDecodeError` which are caught).
    *   It does not test the [`propose_upgrades()`](intelligence/intelligence_observer.py:177) method (which reads from a file) or the [`record_learning_episode()`](intelligence/intelligence_observer.py:232) method (which writes to a file) directly in the example, though their functionality is implied.
    *   Error handling paths (e.g., `KeyError`, `AttributeError` in router calls) are covered by `try-except` blocks but not explicitly tested in the example.
*   **Gaps:**
    *   Lack of formal unit tests using a testing framework like `pytest`.
    *   No tests for edge cases or error conditions in file processing.
    *   No tests for interactions with a mocked `FunctionRouter` or `UpgradeSandboxManager` to isolate `Observer` logic.

## 9. Module Architecture and Flow

The module is architected around the `Observer` class.

**Initialization (`__init__`)**:
1.  Takes an optional `memory_dir` (defaults to [`OBSERVER_MEMORY_DIR`](intelligence/intelligence_config.py:1)).
2.  Creates the `memory_dir` if it doesn't exist using [`os.makedirs()`](intelligence/intelligence_observer.py:45).
3.  Sets up the path for `Observer_learning_log.jsonl` using [`os.path.join()`](intelligence/intelligence_observer.py:46).
4.  Initializes a [`FunctionRouter`](intelligence/function_router.py:1) instance (`router`).
5.  Loads module mappings into the router for `"contradiction"`, `"divergence"`, and `"upgrade_sandbox"` using [`router.load_modules()`](intelligence/intelligence_observer.py:24).
6.  Instantiates an [`UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:1) by accessing it through the router (`router.modules["upgrade_sandbox"].UpgradeSandboxManager()`) and stores it as `self.sandbox`.

**Core Operations (Methods)**:

1.  **Passive Observation ([`observe_simulation_outputs()`](intelligence/intelligence_observer.py:52))**:
    *   Reads a JSONL divergence log file.
    *   Returns a list of divergence entries.
    *   Handles `FileNotFoundError` and `json.JSONDecodeError`.

2.  **Active Batch Analysis**:
    *   [`observe_batch_contradictions()`](intelligence/intelligence_observer.py:76):
        *   Uses the `router` to call `detect_forecast_contradictions` from the "contradiction" module.
        *   Returns a list of detected contradictions.
    *   [`observe_symbolic_divergence()`](intelligence/intelligence_observer.py:99):
        *   Uses the `router` to call `generate_divergence_report` from the "divergence" module.
        *   Returns a symbolic divergence report.
    *   [`compare_forecasts_to_ground_truth()`](intelligence/intelligence_observer.py:122):
        *   Iterates through forecasts and corresponding truth snapshots.
        *   Calls [`_compute_variable_error()`](intelligence/intelligence_observer.py:153) to calculate Mean Absolute Error for shared variables.
        *   Returns a list of forecast IDs and their error scores.
    *   [`_compute_variable_error()`](intelligence/intelligence_observer.py:153):
        *   Helper method to calculate error between two sets of variables.

3.  **Learning and Upgrade Proposal**:
    *   [`propose_upgrades()`](intelligence/intelligence_observer.py:177):
        *   Reads a JSONL foreign fingerprint archive.
        *   Aggregates unique variables and consequences.
        *   Returns an upgrade plan dictionary.
    *   [`propose_symbolic_upgrades_live()`](intelligence/intelligence_observer.py:214):
        *   Takes a symbolic divergence report.
        *   If `divergence_score` > `0.15` (hardcoded threshold), prepares upgrade data.
        *   Submits the upgrade to `self.sandbox.submit_upgrade()`.
        *   Returns the upgrade ID or `None`.

4.  **Recording Learning ([`record_learning_episode()`](intelligence/intelligence_observer.py:232))**:
    *   Takes a divergence summary and an upgrade plan.
    *   Constructs a learning episode dictionary.
    *   Appends the episode as a JSON string to `self.learning_log_path`.

**Data Flow**:
*   Data primarily flows from input files (logs, fingerprints) or direct forecast/truth data into the `Observer` methods.
*   Internal processing involves calling out to other modules via the `FunctionRouter`.
*   Results are either returned directly, written to the learning log, or submitted to the `UpgradeSandboxManager`.

## 10. Naming Conventions

*   **Classes:** `Observer`, `FunctionRouter`, `UpgradeSandboxManager` use CapWords (PEP 8).
*   **Methods & Functions:** `observe_simulation_outputs`, `_compute_variable_error`, `propose_upgrades` use snake_case (PEP 8). Private helper methods like `_compute_variable_error` are prefixed with an underscore.
*   **Variables:** `memory_dir`, `learning_log_path`, `divergence_data`, `forecast_vars` use snake_case (PEP 8).
*   **Constants:** [`OBSERVER_MEMORY_DIR`](intelligence/intelligence_config.py:1) (imported) is in UPPER_SNAKE_CASE.
*   **Module Name:** `intelligence_observer.py` is in snake_case.
*   **String Literals for Keys/Paths:** Keys like `"trace_id"`, `"forecast"`, `"end_variables"`, and router keys like `"contradiction"` are descriptive.
*   **Clarity:** Names are generally descriptive and convey their purpose well (e.g., `divergence_log_path`, `proposed_variables`).
*   **AI Assumption Errors/Deviations:**
    *   No obvious AI-generated naming errors are apparent. The naming seems human-driven and consistent.
    *   The module largely adheres to PEP 8 naming conventions.
    *   The author tag "Pulse Intelligence Core v0.5" (line 12) in [`intelligence/intelligence_observer.py`](intelligence/intelligence_observer.py:12) might be a placeholder or an internal versioning tag rather than a specific person.

Overall, the naming conventions are clear, consistent, and follow Python best practices.