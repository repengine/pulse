# Module Analysis: `learning/diagnose_pulse.py`

## 1. Module Intent/Purpose

The primary role of the [`learning/diagnose_pulse.py`](../../../learning/diagnose_pulse.py) module is to provide a diagnostic summary of the Pulse system's current operational state. It focuses on retrieving and displaying key metrics related to:

*   Symbolic overlays
*   Symbolic fragility score
*   Capital exposure state (summary and percentages)
*   Current simulation turn

This information is intended to help users and developers validate the readiness of the Pulse system and assess the stability of ongoing simulations.

## 2. Operational Status/Completeness

*   **Status:** The module appears to be functional and operational for its defined scope.
*   **Completeness:** It delivers the core diagnostic information it promises.
*   **Placeholders:** No obvious `TODO`, `FIXME`, or `pass` statements indicating unfinished work within the main diagnostic logic.
*   **Docstrings:** The module and its primary function [`run_diagnostics()`](../../../learning/diagnose_pulse.py:24) are documented with docstrings explaining their purpose.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extended Diagnostics:** The module could be expanded to include a broader range of diagnostic checks, such as:
    *   Memory usage profiling.
    *   Performance metrics (e.g., turn processing time).
    *   Configuration validation against a schema.
    *   Data integrity checks for key `WorldState` components.
    *   Status of connected services or data feeds.
*   **Output Mechanism:**
    *   Currently, the primary output is to `stdout` via `print` statements. While a dictionary of results is returned, structured logging to a dedicated diagnostic file (using the configured `logger` and `LOG_PATH`) would be more robust for automated analysis and historical tracking. The existing `logger` is initialized but not used for the diagnostic output itself.
*   **Error Handling:** The module assumes successful retrieval of all diagnostic data. More robust error handling (e.g., `try-except` blocks around calls to external modules) could prevent the entire script from failing if one piece of diagnostic information is unavailable.
*   **Configurability:** The diagnostics performed are fixed. Future enhancements could allow users to specify which diagnostics to run.

## 4. Connections & Dependencies

### Direct Project Module Imports:

*   [`simulation_engine.worldstate.WorldState`](../../../simulation_engine/worldstate.py:10): Used to access the current state of the simulation.
*   [`symbolic_system.symbolic_utils.get_overlay_snapshot`](../../../symbolic_system/symbolic_utils.py:11): To retrieve symbolic overlay data.
*   [`symbolic_system.symbolic_utils.symbolic_fragility_index`](../../../symbolic_system/symbolic_utils.py:11): To calculate the symbolic fragility.
*   [`capital_engine.capital_layer.summarize_exposure`](../../../capital_engine/capital_layer.py:12): To get a summary of capital exposure.
*   [`capital_engine.capital_layer.exposure_percentages`](../../../capital_engine/capital_layer.py:12): To get capital exposure percentages.
*   [`utils.log_utils.get_logger`](../../../utils/log_utils.py:14): For setting up a logger instance.
*   [`core.path_registry.PATHS`](../../../core/path_registry.py:15): To access centrally defined file paths, specifically for `DIAGNOSTICS_LOG`.

### External Library Dependencies:

*   `typing` (Python standard library): For type hinting (`Dict`, `Any`).

### Interactions via Shared Data:

*   **`WorldState` Object:** The module heavily relies on the `WorldState` object passed to (or instantiated and then passed to) various imported functions to fetch the necessary data.
*   **`PATHS` Dictionary:** Uses the `PATHS` dictionary from [`core.path_registry`](../../../core/path_registry.py:15) to look up the path for diagnostic logs.

### Input/Output Files:

*   **Input:**
    *   Implicitly relies on the current, in-memory `WorldState` of the simulation.
    *   Reads the `DIAGNOSTICS_LOG` key from the `PATHS` dictionary.
*   **Output:**
    *   Prints a formatted diagnostic report to `stdout`.
    *   Returns a dictionary containing the raw diagnostic data.
    *   A `LOG_PATH` is defined as `PATHS["DIAGNOSTICS_LOG"]` ([`learning/diagnose_pulse.py:19`](../../../learning/diagnose_pulse.py:19)), but the script does not explicitly write the diagnostic report to this file using the initialized `logger`.

## 5. Function and Class Example Usages

The module contains one primary function:

*   **[`run_diagnostics() -> Dict[str, Any]`](../../../learning/diagnose_pulse.py:24):**
    *   **Purpose:** Performs the diagnostic checks and prints a summary.
    *   **Usage:** Intended to be called as a script or imported and invoked.
        ```python
        from learning.diagnose_pulse import run_diagnostics

        # To run diagnostics and print to console, then get the data
        diagnostic_data = run_diagnostics()

        # Example of accessing data after the call
        # current_turn = diagnostic_data["turn"]
        # fragility = diagnostic_data["symbolic_fragility"]
        ```
    *   The script includes a standard `if __name__ == "__main__":` block that calls [`run_diagnostics()`](../../../learning/diagnose_pulse.py:24) and prints the returned dictionary.

## 6. Hardcoding Issues

*   **Path Keys:** The dictionary key `"DIAGNOSTICS_LOG"` ([`learning/diagnose_pulse.py:19`](../../../learning/diagnose_pulse.py:19)) used to fetch the log path from `PATHS` is hardcoded. If this key changes in [`core.path_registry`](../../../core/path_registry.py:15), the module will fail to get the correct path.
*   **Print Formatting Strings:** All strings used for formatting the `stdout` report (e.g., `"\n📋 PULSE SYSTEM DIAGNOSTICS\n"`, `"{k.capitalize():<8}: {v:.3f}"`) are hardcoded. This is generally acceptable for a command-line diagnostic tool but offers less flexibility for internationalization or output format changes.
*   **Author Tag:** The "Author: Pulse v3.5" ([`learning/diagnose_pulse.py:7`](../../../learning/diagnose_pulse.py:7)) in the module docstring might be a placeholder or an internal versioning note that could become outdated.

## 7. Coupling Points

*   **`WorldState`:** Tightly coupled to the `WorldState` object's structure and the data it provides. Changes in `WorldState` could break this module.
*   **Service Modules:** Directly coupled to specific functions within:
    *   [`symbolic_system.symbolic_utils`](../../../symbolic_system/symbolic_utils.py:11)
    *   [`capital_engine.capital_layer`](../../../capital_engine/capital_layer.py:12)
    Changes to the signatures or behavior of these imported functions would impact this module.
*   **`core.path_registry`:** Depends on the `PATHS` dictionary and the existence of the `"DIAGNOSTICS_LOG"` key within it.

## 8. Existing Tests

*   **Dedicated Tests:** Based on the provided file listing, there does not appear to be a dedicated test file (e.g., `tests/learning/test_diagnose_pulse.py`).
*   **Runtime Assertions:** An `assert isinstance(PATHS, dict)` ([`learning/diagnose_pulse.py:17`](../../../learning/diagnose_pulse.py:17)) exists, which acts as a basic runtime sanity check but is not a substitute for comprehensive unit or integration tests.
*   **Testability:** The main function [`run_diagnostics()`](../../../learning/diagnose_pulse.py:24) returns a dictionary, which makes its core logic testable (i.e., one could mock `WorldState` and its dependencies, call the function, and assert the contents of the returned dictionary). However, testing the `print` outputs would require capturing `stdout`.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Imports necessary modules and functions from other parts of the Pulse system (`simulation_engine`, `symbolic_system`, `capital_engine`, `utils`, `core`).
    *   Retrieves the `DIAGNOSTICS_LOG` path string from the `PATHS` registry.
    *   Initializes a logger instance via [`get_logger(__name__)`](../../../utils/log_utils.py:14).
2.  **[`run_diagnostics()`](../../../learning/diagnose_pulse.py:24) Function Execution:**
    *   An empty dictionary `report` is created.
    *   An instance of `WorldState` is created to access current simulation data.
    *   The `report` dictionary is populated with:
        *   `turn`: Current simulation turn from `state.turn`.
        *   `symbolic_overlays`: Result of calling [`get_overlay_snapshot(state)`](../../../symbolic_system/symbolic_utils.py:11).
        *   `symbolic_fragility`: Result of calling [`symbolic_fragility_index(state)`](../../../symbolic_system/symbolic_utils.py:11).
        *   `capital_exposure`: Result of calling [`summarize_exposure(state)`](../../../capital_engine/capital_layer.py:12).
        *   `capital_percentages`: Result of calling [`exposure_percentages(state)`](../../../capital_engine/capital_layer.py:12).
    *   A formatted summary of the `report` contents is printed to `stdout`.
    *   The populated `report` dictionary is returned.
3.  **Script Execution (`if __name__ == "__main__":`)**
    *   If the module is run as the main script, it calls [`run_diagnostics()`](../../../learning/diagnose_pulse.py:24).
    *   The dictionary returned by [`run_diagnostics()`](../../../learning/diagnose_pulse.py:24) is printed to `stdout`.

## 10. Naming Conventions

*   **Module Name:** `diagnose_pulse.py` (snake_case, standard).
*   **Function Names:** [`run_diagnostics()`](../../../learning/diagnose_pulse.py:24) (snake_case, standard and descriptive).
*   **Variable Names:** `report`, `state`, `k`, `v`, `asset`, `val`, `pct` are generally clear for their scope. `LOG_PATH` uses uppercase for a constant-like variable, which is conventional.
*   **Consistency:** Naming conventions appear consistent with PEP 8 guidelines.
*   **AI Assumption Errors:** No obvious errors in naming that would suggest misinterpretation by an AI or significant deviation from common Python practices. The "Author: Pulse v3.5" tag is a metadata point rather than a code naming convention.