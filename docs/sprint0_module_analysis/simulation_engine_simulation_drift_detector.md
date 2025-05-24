# SPARC Module Analysis: simulation_engine/simulation_drift_detector.py

**Version:** 1.0.0
**Author:** Pulse AI Engine
**Date of Analysis:** 2025-05-14

## 1. Module Intent/Purpose (SPARC: Specification)

The primary role of the [`simulation_engine/simulation_drift_detector.py`](simulation_engine/simulation_drift_detector.py:1) module is to compare internal simulation artifacts from two different simulation runs. It aims to identify and quantify "drift" between these runs, which can indicate system instability, unexpected behavioral changes, or silent logic regressions.

Specifically, it compares:
*   **Rule activation patterns:** How frequently each rule was triggered.
*   **Overlay decay trajectories:** The paths of emotional/symbolic overlays (e.g., hope, despair) over time.
*   **Simulation structure:** Turn counts and the occurrence of simulation collapse states.

The module can be used as a command-line tool or its functions can be imported into other parts of the system for programmatic drift analysis.

## 2. Operational Status/Completeness

The module appears to be largely complete for its defined scope of comparing two simulation trace files and reporting differences. It includes functionality for loading traces, performing comparisons, and outputting results. A CLI interface is also provided.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Automated Testing:** The existing test function, [`_test_drift_detector()`](simulation_engine/simulation_drift_detector.py:132), is for manual validation and is not executed by default (due to a `pass` statement in the main execution block on line 149). Integrating this or more comprehensive tests into an automated testing framework (e.g., pytest) is a clear next step.
*   **Robust Error Handling in `load_trace`:** The [`load_trace()`](simulation_engine/simulation_drift_detector.py:22) function prints error messages to `stdout` (lines 32, 35). For library use, returning error information or using a dedicated logging framework would be more appropriate.
*   **Secure Temporary Files:** The test function [`_test_drift_detector()`](simulation_engine/simulation_drift_detector.py:132) uses `tempfile.mktemp()` (line 138, 139), which is insecure. It should be replaced with safer alternatives like `tempfile.NamedTemporaryFile(delete=False)` or `tempfile.TemporaryDirectory`.

## 4. Connections & Dependencies

### Direct Imports:
*   **Standard Libraries:**
    *   `json`: For loading and dumping JSON data (simulation traces and reports).
    *   `typing` ([`List`](simulation_engine/simulation_drift_detector.py:18), [`Dict`](simulation_engine/simulation_drift_detector.py:18), [`Tuple`](simulation_engine/simulation_drift_detector.py:18), [`Optional`](simulation_engine/simulation_drift_detector.py:18)): For type hinting.
    *   `collections` ([`Counter`](simulation_engine/simulation_drift_detector.py:19)): Used in [`compare_rule_patterns()`](simulation_engine/simulation_drift_detector.py:38) for counting rule activations.
    *   `os`: (Implicitly used by `open()`, though not directly imported at the top level of the script, `argparse` might use it).
    *   `argparse`: (Imported within `if __name__ == "__main__":` block on line 107) For parsing command-line arguments.
    *   `tempfile`: (Imported within `_test_drift_detector()` on line 137) For creating temporary files in the test function.

### Touched Project Files (for dependency mapping):
*   [`simulation_engine/simulation_drift_detector.py`](simulation_engine/simulation_drift_detector.py:1) (the module itself)
    *   No other project-internal Python modules are imported or directly interacted with at the code level.

### Interactions:
*   **File System:**
    *   Reads two simulation trace files in `.jsonl` format as input. These files are expected to contain a sequence of JSON objects, each representing a step in the simulation.
    *   Optionally writes the drift analysis report to a JSON file.
*   **Data Format:** The module is tightly coupled to the expected JSON structure within the `.jsonl` trace files. Specifically, it looks for keys like:
    *   `"fired_rules"` (a list of rule IDs) within each step for [`compare_rule_patterns()`](simulation_engine/simulation_drift_detector.py:38).
    *   `"overlays"` (a dictionary of overlay keys to values) within each step for [`compare_overlay_trajectories()`](simulation_engine/simulation_drift_detector.py:54).
    *   The presence of a `"collapse"` key in any step for [`compare_simulation_structure()`](simulation_engine/simulation_drift_detector.py:73).

### Input/Output Files:
*   **Input:**
    *   `prev_path` (str): Path to the previous simulation trace file (e.g., `run1_trace.jsonl`).
    *   `curr_path` (str): Path to the current simulation trace file (e.g., `run2_trace.jsonl`).
    *   These files are expected to be in JSON Lines format (`.jsonl`).
*   **Output:**
    *   A dictionary containing the drift analysis results.
    *   If the CLI is used with the `--export` argument, this dictionary is saved as a JSON file.

## 5. Function and Class Example Usages

*   **`load_trace(path: str) -> List[Dict]`**
    *   Loads a `.jsonl` trace file into a list of dictionaries.
    ```python
    # trace_content will be a list of dicts, e.g., [{'step': 1, ...}, {'step': 2, ...}]
    trace_content = load_trace("path/to/simulation_trace.jsonl")
    ```

*   **`compare_rule_patterns(prev: List[Dict], curr: List[Dict]) -> Dict[str, int]`**
    *   Compares the frequency of rule activations between two traces.
    ```python
    prev_data = [{"fired_rules": ["R1", "R2"]}, {"fired_rules": ["R1"]}]
    curr_data = [{"fired_rules": ["R1"]}, {"fired_rules": ["R2", "R3"]}]
    rule_delta = compare_rule_patterns(prev_data, curr_data)
    # Expected: rule_delta = {'R1': -1, 'R2': 0, 'R3': 1}
    print(rule_delta)
    ```

*   **`compare_overlay_trajectories(prev: List[Dict], curr: List[Dict], keys: Optional[List[str]] = None) -> Dict[str, float]`**
    *   Compares the average difference in overlay values over time.
    ```python
    prev_data = [{"overlays": {"hope": 0.5, "trust": 0.8}}, {"overlays": {"hope": 0.4, "trust": 0.7}}]
    curr_data = [{"overlays": {"hope": 0.6, "trust": 0.85}}, {"overlays": {"hope": 0.3, "trust": 0.75}}]
    overlay_drift = compare_overlay_trajectories(prev_data, curr_data, keys=["hope", "trust"])
    # Expected: overlay_drift = {'hope': 0.1, 'trust': 0.05} (approx)
    print(overlay_drift)
    ```

*   **`compare_simulation_structure(prev: List[Dict], curr: List[Dict]) -> Dict`**
    *   Compares high-level structural aspects like turn count and collapse events.
    ```python
    prev_data = [{}, {}, {"collapse": True}] # 3 turns, collapse occurred
    curr_data = [{}, {}] # 2 turns, no collapse
    structure_diff = compare_simulation_structure(prev_data, curr_data)
    # Expected: {'turn_count_prev': 3, 'turn_count_curr': 2, 'turn_diff': -1, 
    #            'collapse_trigger_prev': True, 'collapse_trigger_curr': False}
    print(structure_diff)
    ```

*   **`run_simulation_drift_analysis(prev_path: str, curr_path: str, overlay_keys: Optional[List[str]] = None) -> Dict`**
    *   Orchestrates the full drift analysis.
    ```python
    # Assuming prev_trace.jsonl and curr_trace.jsonl exist and are valid
    # report = run_simulation_drift_analysis("prev_trace.jsonl", "curr_trace.jsonl", overlay_keys=["hope"])
    # print(json.dumps(report, indent=2))

    # CLI Example:
    # python simulation_engine/simulation_drift_detector.py --prev prev_run.jsonl --curr current_run.jsonl --export drift_report.json --overlays hope,despair
    ```

## 6. Hardcoding Issues (SPARC Critical)

*   **Default Overlay Keys:** In [`compare_overlay_trajectories()`](simulation_engine/simulation_drift_detector.py:54) (line 59), the default list of overlay keys to compare is hardcoded: `keys = keys or ["hope", "despair", "rage", "fatigue", "trust"]`.
    *   **Severity:** Minor.
    *   **Reason:** While hardcoded, this list serves as a sensible default. The keys can be overridden via the `overlay_keys` parameter in [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:83) and the `--overlays` CLI argument. This makes the behavior configurable.
    *   **Recommendation:** For greater flexibility, these default keys could potentially be loaded from a configuration file if the set of standard overlays is expected to change frequently or vary across different simulation types. However, for its current purpose, the existing mechanism is acceptable.

No other significant hardcoding of secrets, API keys, absolute paths, or sensitive data was identified in the core logic.

## 7. Coupling Points

*   **Input Data Structure:** The module is tightly coupled to the specific JSON structure of the input `.jsonl` trace files. Any changes to the key names (e.g., `"fired_rules"`, `"overlays"`) or data types within these files would necessitate code changes in this module.
*   **Error Handling in `load_trace`:** As mentioned, [`load_trace()`](simulation_engine/simulation_drift_detector.py:22) prints errors directly. This couples its error reporting mechanism to `stdout`, which might not be desirable if used as a library component within a larger system that has a centralized logging strategy.
*   **CLI Argument Parsing:** The CLI functionality is embedded within the `if __name__ == "__main__":` block. While common, this means the argument parsing logic is specific to this script's direct execution.

## 8. Existing Tests (SPARC Refinement)

*   **Test Function:** A single test function, [`_test_drift_detector()`](simulation_engine/simulation_drift_detector.py:132), is present (lines 132-146).
*   **Nature:** This is a basic manual validation test. It creates two dummy trace files with minimal data and then calls [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:83), printing the result.
*   **Execution:** It is not run automatically when the script is executed as main; line 149 contains `pass`, so the test function call is effectively disabled by default.
*   **Coverage & Quality (Low):**
    *   **Minimal Coverage:** The test covers only a very simple, happy-path scenario.
    *   **No Assertions:** The test prints the output but does not perform any assertions to verify the correctness of the results. A proper test should assert that the output matches expected values.
    *   **Edge Cases Not Covered:** It does not test for:
        *   Empty trace files.
        *   Traces with missing keys (e.g., no `"fired_rules"` or `"overlays"`).
        *   Traces of different lengths.
        *   Various scenarios for simulation collapse.
        *   Malformed JSON lines within the trace files (though [`load_trace()`](simulation_engine/simulation_drift_detector.py:22) has some handling for this).
        *   Different sets of overlay keys.
    *   **Security of Test Utility:** Uses `tempfile.mktemp()`, which is insecure.
*   **SPARC Testability Assessment:** The module's current testability is low due to the lack of automated, comprehensive unit tests with assertions. The functions themselves are relatively pure and testable if provided with appropriate input data.

## 9. Module Architecture and Flow (SPARC Architecture)

*   **Structure:** The module consists of a set of standalone functions. There are no classes defined.
*   **Core Functions:**
    *   [`load_trace()`](simulation_engine/simulation_drift_detector.py:22): Input data ingestion and parsing.
    *   [`compare_rule_patterns()`](simulation_engine/simulation_drift_detector.py:38): Logic for comparing rule activation frequencies.
    *   [`compare_overlay_trajectories()`](simulation_engine/simulation_drift_detector.py:54): Logic for comparing overlay value trajectories.
    *   [`compare_simulation_structure()`](simulation_engine/simulation_drift_detector.py:73): Logic for comparing high-level simulation structural elements.
    *   [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:83): Orchestrator function that calls the individual comparison functions and aggregates their results into a final report.
*   **CLI Interface:** The `if __name__ == "__main__":` block (lines 106-130) implements a command-line interface using `argparse`, allowing the script to be run directly to perform drift analysis between two specified trace files.
*   **Data Flow:**
    1.  User provides paths to two `.jsonl` trace files (previous and current).
    2.  [`load_trace()`](simulation_engine/simulation_drift_detector.py:22) is called for each path to load data.
    3.  The loaded data (lists of dictionaries) is passed to:
        *   [`compare_rule_patterns()`](simulation_engine/simulation_drift_detector.py:38)
        *   [`compare_overlay_trajectories()`](simulation_engine/simulation_drift_detector.py:54)
        *   [`compare_simulation_structure()`](simulation_engine/simulation_drift_detector.py:73)
    4.  [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:83) collects the results from these comparison functions.
    5.  The aggregated results are returned as a dictionary, which is then typically printed to `stdout` or saved to a JSON file via the CLI.
*   **Modularity:** The module is well-contained and focuses on the single responsibility of drift detection. Functions are relatively small and focused.

## 10. Naming Conventions (SPARC Maintainability)

*   **Functions:** Names are generally descriptive and follow Python's `snake_case` convention (e.g., [`load_trace`](simulation_engine/simulation_drift_detector.py:22), [`compare_rule_patterns`](simulation_engine/simulation_drift_detector.py:38), [`run_simulation_drift_analysis`](simulation_engine/simulation_drift_detector.py:83)). The internal test function [`_test_drift_detector`](simulation_engine/simulation_drift_detector.py:132) correctly uses a leading underscore.
*   **Variables:** Variable names are mostly clear and `snake_case` (e.g., `prev_counts`, `curr_counts`, `avg_diff`, `overlay_keys`). Single-letter variables (`f`, `c`, `r`, `k`, `e`, `i`) are used in limited scopes (e.g., loop iterators, file handles, exception objects), which is generally acceptable in Python for brevity.
*   **Constants/Defaults:** Default overlay keys are stored in a list within the function where they are used.
*   **Overall:** Naming conventions are consistent and contribute to code readability.

## 11. SPARC Compliance Summary

*   **Specification (✅ High):**
    *   The module's purpose is clearly defined in its top-level docstring (lines 3-15) and through its functional decomposition. It has a specific, well-understood goal: to detect and report drift between simulation runs based on predefined artifact comparisons.

*   **Modularity/Architecture (✅ Good):**
    *   The module exhibits good modularity with distinct functions for different aspects of the drift detection process (loading, comparing rules, overlays, structure).
    *   It is self-contained with respect to project-internal dependencies, relying only on standard Python libraries.
    *   The main orchestration function, [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:83), provides a clear entry point.
    *   The CLI interface is a useful addition for standalone operation.

*   **Refinement Focus:**
    *   **Testability (⚠️ Low):**
        *   A significant gap. The existing [`_test_drift_detector()`](simulation_engine/simulation_drift_detector.py:132) is manual, not run by default, lacks assertions, and has minimal coverage. No automated unit tests (e.g., pytest) are present. This makes it difficult to verify correctness or refactor with confidence.
    *   **Security (✅ Good):**
        *   No hardcoded secrets, API keys, or credentials.
        *   File paths are user-supplied.
        *   The use of `tempfile.mktemp()` in the (currently disabled) test function is a minor security concern for testing environments but doesn't affect the core runtime logic if the test is not run or is fixed.
    *   **Maintainability (✅ Good):**
        *   Code is generally clear, well-structured, and uses descriptive naming.
        *   Functions are relatively small and focused.
        *   Docstrings are present for public functions, explaining their purpose, arguments, and return types (though argument types are primarily via type hints).
        *   The primary area for improvement regarding maintainability would be enhancing testability.

*   **No Hardcoding (✅ Good):**
    *   The main critical items (paths, sensitive data) are not hardcoded.
    *   The default overlay keys in [`compare_overlay_trajectories()`](simulation_engine/simulation_drift_detector.py:54) are hardcoded but are configurable and not sensitive, representing a minor and acceptable instance.

**Overall SPARC Assessment:**
The module is well-specified and has a decent modular architecture for its intended purpose. Maintainability is good due to clear code and naming. The primary weakness from a SPARC perspective is in **Testability** (Refinement). The lack of robust, automated tests is a significant concern for ensuring reliability and enabling safe future modifications. Security is generally good.