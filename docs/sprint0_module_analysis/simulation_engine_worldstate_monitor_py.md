# Module Analysis: simulation_engine/worldstate_monitor.py

## 1. Module Intent/Purpose

The primary role of [`simulation_engine/worldstate_monitor.py`](simulation_engine/worldstate_monitor.py:1) is to provide functionalities for displaying and logging various aspects of the Pulse simulation's `WorldState`. This includes:
- Symbolic overlays
- Capital exposure
- Current state of world variables
- Changes (deltas) in overlays compared to a previous state
- Optional logging of this information to files.
Additionally, the module integrates with a `gravity_explainer` component to display detailed explanations of "gravity corrections" applied during simulations, offering outputs in text, HTML, or JSON formats. It also contains a utility function to simulate running a batch of forecasts and log their summary.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- Core display functions ([`display_overlay_state`](simulation_engine/worldstate_monitor.py:50), [`display_capital_exposure`](simulation_engine/worldstate_monitor.py:55), [`display_variable_state`](simulation_engine/worldstate_monitor.py:61), [`display_deltas`](simulation_engine/worldstate_monitor.py:70), [`display_all`](simulation_engine/worldstate_monitor.py:78)) are implemented.
- Logging to files is functional.
- The integration with the `diagnostics.gravity_explainer` ([`simulation_engine/worldstate_monitor.py:25-46`](simulation_engine/worldstate_monitor.py:25)) is designed to be robust, with fallback stub functions defined in case the `gravity_explainer` module is not available. This ensures the `worldstate_monitor` can operate even if an optional dependency is missing.
- No obvious TODOs or major placeholders are visible in the core monitoring functionalities.

## 3. Implementation Gaps / Unfinished Next Steps

- **`run_batch_forecasts` Functionality:**
    - The [`run_batch_forecasts`](simulation_engine/worldstate_monitor.py:104) function uses example metadata: `metadata = {"confidence": 0.7}` ([`simulation_engine/worldstate_monitor.py:112`](simulation_engine/worldstate_monitor.py:112)). This suggests it might be a simplified placeholder for a more dynamic or externally sourced metadata generation process.
    - The `symbolic_block` parameter ([`simulation_engine/worldstate_monitor.py:104`](simulation_engine/worldstate_monitor.py:104)) is intended to be a callable for additional forecast acceptance criteria (`symbolic_block(metadata)` at [`simulation_engine/worldstate_monitor.py:113`](simulation_engine/worldstate_monitor.py:113)). However, no concrete implementation or example of such a callable is provided within this module, indicating a potential area for future extension or integration with a symbolic reasoning component.
- **Gravity Explainer Data Check:** The check `if "gravity_correction_details" in step:` ([`simulation_engine/worldstate_monitor.py:162`](simulation_engine/worldstate_monitor.py:162)) is a simple string key check. More robust validation of the `gravity_correction_details` structure itself could be beneficial.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`engine.worldstate.WorldState`](simulation_engine/worldstate.py:1) ([`simulation_engine/worldstate_monitor.py:14`](simulation_engine/worldstate_monitor.py:14))
- [`utils.log_utils.get_logger`](utils/log_utils.py:1) ([`simulation_engine/worldstate_monitor.py:15`](simulation_engine/worldstate_monitor.py:15))
- [`core.variable_accessor.get_variable`](core/variable_accessor.py:1), [`set_variable`](core/variable_accessor.py:1), [`get_overlay`](core/variable_accessor.py:1), [`set_overlay`](core/variable_accessor.py:1) ([`simulation_engine/worldstate_monitor.py:16`](simulation_engine/worldstate_monitor.py:16))
- [`core.path_registry.PATHS`](core/path_registry.py:1) ([`simulation_engine/worldstate_monitor.py:17`](simulation_engine/worldstate_monitor.py:17))
- `diagnostics.gravity_explainer` (conditionally imported, with stubs if unavailable) ([`simulation_engine/worldstate_monitor.py:26-30`](simulation_engine/worldstate_monitor.py:26))
    - [`display_correction_explanation`](diagnostics/gravity_explainer.py:1)
    - [`plot_gravity_correction_details_html`](diagnostics/gravity_explainer.py:1)
    - [`export_gravity_explanation_json`](diagnostics/gravity_explainer.py:1)

### External Library Dependencies:
- `datetime` ([`simulation_engine/worldstate_monitor.py:19`](simulation_engine/worldstate_monitor.py:19))
- `os` ([`simulation_engine/worldstate_monitor.py:20`](simulation_engine/worldstate_monitor.py:20))
- `typing` (Optional, List, Dict, Any) ([`simulation_engine/worldstate_monitor.py:21`](simulation_engine/worldstate_monitor.py:21))
- `pathlib` (Path) ([`simulation_engine/worldstate_monitor.py:22`](simulation_engine/worldstate_monitor.py:22))

### Interaction via Shared Data:
- Uses directory paths from `PATHS` for logging and output:
    - `PATHS["WORLDSTATE_LOG_DIR"]` ([`simulation_engine/worldstate_monitor.py:92`](simulation_engine/worldstate_monitor.py:92))
    - `PATHS["BATCH_FORECAST_SUMMARY"]` ([`simulation_engine/worldstate_monitor.py:125`](simulation_engine/worldstate_monitor.py:125))
    - `PATHS.get("VIZ_DIR", "visualizations")` ([`simulation_engine/worldstate_monitor.py:183`](simulation_engine/worldstate_monitor.py:183)) (fallback for gravity explanations)
    - `PATHS.get("GRAVITY_EXPLANATIONS_DIR", default_dir)` ([`simulation_engine/worldstate_monitor.py:184`](simulation_engine/worldstate_monitor.py:184))

### Input/Output Files:
- **Output Log Files:**
    - Worldstate snapshots: `state_{turn}_{timestamp}.txt` written to `PATHS["WORLDSTATE_LOG_DIR"]` (e.g., [`simulation_engine/worldstate_monitor.py:95`](simulation_engine/worldstate_monitor.py:95)).
    - Batch forecast summaries: Written to the file specified by `PATHS["BATCH_FORECAST_SUMMARY"]` (e.g., [`simulation_engine/worldstate_monitor.py:125`](simulation_engine/worldstate_monitor.py:125)).
    - Gravity correction explanation (HTML): `gravity_{variable_name}_{timestamp}.html` written to `GRAVITY_EXPLANATIONS_DIR` or a default visualization directory (e.g., [`simulation_engine/worldstate_monitor.py:195`](simulation_engine/worldstate_monitor.py:195)).
    - Gravity correction explanation (JSON): `gravity_{variable_name}_{timestamp}.json` written to `GRAVITY_EXPLANATIONS_DIR` or a default visualization directory (e.g., [`simulation_engine/worldstate_monitor.py:201`](simulation_engine/worldstate_monitor.py:201)).
- **Input Data:**
    - The [`display_gravity_correction_details`](simulation_engine/worldstate_monitor.py:134) function expects `trace_data` which would typically be generated by the simulation core and contain gravity correction details.

## 5. Function and Class Example Usages

- **Displaying and Logging WorldState:**
  ```python
  # Assuming 'current_ws' is a WorldState object and 'previous_ws' is the WorldState from the prior turn
  from engine.worldstate_monitor import display_all
  display_all(current_ws, prev_state=previous_ws, log=True)
  ```
  This would print the current overlays, capital exposure, variable states, and deltas from the previous state to the console, and also log a snapshot to a file.

- **Running a Batch of Forecasts (Simulated):**
  ```python
  from engine.worldstate_monitor import run_batch_forecasts
  # Example symbolic block (conceptual)
  # def my_symbolic_filter(metadata):
  #     return metadata.get("priority_score", 0) > 0.8
  run_batch_forecasts(count=10, domain="market_trends", min_conf=0.6, verbose=True, export_summary=True) # symbolic_block=my_symbolic_filter
  ```
  This simulates running 10 forecasts, logs details of accepted/rejected forecasts, and saves a summary.

- **Displaying Gravity Correction Details:**
  ```python
  from engine.worldstate_monitor import display_gravity_correction_details
  # Assuming 'simulation_trace' is a list of dicts from a simulation run
  # and 'problematic_variable' is the name of a variable of interest.
  # Ensure diagnostics.gravity_explainer is available and simulation ran with gravity.
  html_report_path = display_gravity_correction_details(
      trace_data=simulation_trace,
      variable_name="problematic_variable",
      output_format="html",
      output_dir="docs/reports/gravity_analysis"
  )
  if html_report_path:
      print(f"Gravity explanation HTML report generated at: {html_report_path}")
  
  display_gravity_correction_details(
      trace_data=simulation_trace,
      variable_name="another_variable",
      output_format="text" # Prints to console
  )
  ```

## 6. Hardcoding Issues

- **`run_batch_forecasts` function:**
    - Forecast ID generation: `forecast_id = f"forecast_{i}"` ([`simulation_engine/worldstate_monitor.py:111`](simulation_engine/worldstate_monitor.py:111)) is a simple, potentially non-unique scheme for larger or distributed systems.
    - Example metadata: `metadata = {"confidence": 0.7}` ([`simulation_engine/worldstate_monitor.py:112`](simulation_engine/worldstate_monitor.py:112)) is explicitly an example.
    - Default minimum confidence: `min_conf=0.5` ([`simulation_engine/worldstate_monitor.py:104`](simulation_engine/worldstate_monitor.py:104)).
    - Rejection reasons: Strings "low_confidence" and "blocked_symbolic" ([`simulation_engine/worldstate_monitor.py:120`](simulation_engine/worldstate_monitor.py:120)) are hardcoded. These might be better as enums or constants if used elsewhere.
- **`display_gravity_correction_details` function:**
    - Default visualization directory fallback: `"visualizations"` string used in `default_dir = os.path.join(str(PATHS.get("VIZ_DIR", "visualizations")), "gravity_explanations")` ([`simulation_engine/worldstate_monitor.py:183`](simulation_engine/worldstate_monitor.py:183)).
- **File Naming Conventions:**
    - Log file names like `state_{state.turn}_{ts}.txt` ([`simulation_engine/worldstate_monitor.py:95`](simulation_engine/worldstate_monitor.py:95)) and `gravity_{variable_name}_{timestamp}.html/.json` ([`simulation_engine/worldstate_monitor.py:195`](simulation_engine/worldstate_monitor.py:195), [`simulation_engine/worldstate_monitor.py:201`](simulation_engine/worldstate_monitor.py:201)) follow a pattern but the base names ("state", "gravity") are hardcoded.
- **CLI Messages:** Various print statements for warnings or errors (e.g., "Gravity explainer module not available.", "No gravity correction data found...") are hardcoded.

## 7. Coupling Points

- **`WorldState` Object:** The module is tightly coupled to the structure and methods of the [`WorldState`](simulation_engine/worldstate.py:1) object (e.g., `state.overlays.as_dict()`, `state.capital.as_dict()`, `state.variables`, `state.turn`).
- **`core.variable_accessor`:** Relies on this module for accessing variable and overlay data from the `WorldState`.
- **`core.path_registry.PATHS`:** Dependent on this global dictionary for resolving file system paths for logging and output. Changes to keys in `PATHS` would require updates here.
- **`diagnostics.gravity_explainer`:** While the import is conditional, the [`display_gravity_correction_details`](simulation_engine/worldstate_monitor.py:134) function's primary purpose is to facade this module. Its API (function names, parameters) is directly used.
- **`utils.log_utils.get_logger`:** Standard coupling for logging.
- **File System:** Directly interacts with the file system for creating directories and writing files.

## 8. Existing Tests

A specific test file for this module (e.g., `tests/test_worldstate_monitor.py` or `tests/simulation_engine/test_worldstate_monitor.py`) was not found in the provided file listing of the `tests` directory. This suggests that dedicated unit tests for `worldstate_monitor.py` may be missing or located elsewhere not immediately apparent.

It's possible that functionalities of this module are tested indirectly through integration tests of the broader simulation engine or via tests for the `diagnostics.gravity_explainer` (as [`test_gravity_explainer.py`](tests/test_gravity_explainer.py:1) exists). However, without specific unit tests, direct coverage of all display functions, logging logic, and the `run_batch_forecasts` utility within `worldstate_monitor.py` cannot be confirmed.

## 9. Module Architecture and Flow

- The module is primarily procedural, consisting of a collection of functions.
- **Display Functions:** A set of functions ([`display_overlay_state`](simulation_engine/worldstate_monitor.py:50), [`display_capital_exposure`](simulation_engine/worldstate_monitor.py:55), [`display_variable_state`](simulation_engine/worldstate_monitor.py:61), [`display_deltas`](simulation_engine/worldstate_monitor.py:70)) each handle a specific aspect of `WorldState` visualization.
- **Aggregator Function:** [`display_all`](simulation_engine/worldstate_monitor.py:78) calls the individual display functions and manages optional logging of the combined state to a timestamped file.
- **Batch Forecast Simulation:** [`run_batch_forecasts`](simulation_engine/worldstate_monitor.py:104) provides a utility to simulate a batch forecasting process, applying simple acceptance criteria and logging a summary. This seems somewhat distinct from the core "monitoring" role but could be used for testing or generating sample log data.
- **Gravity Explanation Facade:** [`display_gravity_correction_details`](simulation_engine/worldstate_monitor.py:134) serves as an entry point to the `diagnostics.gravity_explainer` module. It handles:
    - Checking for the availability of the `gravity_explainer`.
    - Verifying if the input `trace_data` contains necessary gravity correction information.
    - Dispatching to the appropriate `gravity_explainer` function based on the `output_format` (text, HTML, JSON).
    - Managing output file paths and directory creation for HTML/JSON outputs.
- **Error Handling/Robustness:** The conditional import of `gravity_explainer` with fallback stubs ([`simulation_engine/worldstate_monitor.py:25-46`](simulation_engine/worldstate_monitor.py:25)) is a key architectural feature for robustness, allowing the module to function even if optional dependencies are missing. Error messages are printed to the console for issues like missing modules or data.
- **Configuration:** Relies on `core.path_registry.PATHS` for external configuration of storage locations.

## 10. Naming Conventions

- **Functions:** Generally follow Python's `snake_case` convention (e.g., [`display_overlay_state`](simulation_engine/worldstate_monitor.py:50), [`run_batch_forecasts`](simulation_engine/worldstate_monitor.py:104)). This is consistent and good.
- **Variables:** Local variables also use `snake_case` (e.g., `prev_state`, `summary_file`).
- **Constants:** `PATHS`, `GRAVITY_EXPLAINER_AVAILABLE`, `logger` are appropriately cased (though `logger` is an object instance, its module-level scope makes uppercase common).
- **Module Name:** `worldstate_monitor.py` is descriptive.
- **Docstrings:** Present for the module and most functions, explaining their purpose.
- **Author Tag:** The docstring contains `Author: Pulse v0.4` ([`simulation_engine/worldstate_monitor.py:11`](simulation_engine/worldstate_monitor.py:11)), which is a bit unconventional for an author field but likely indicates the AI version that generated or last significantly modified the boilerplate.
- **Type Hinting:** Used effectively (e.g., `state: WorldState`, `Optional[WorldState]`).
- **Assert Statement:** [`assert isinstance(PATHS, dict)`](simulation_engine/worldstate_monitor.py:18) is a good runtime check for an essential configuration dependency.

Overall, naming conventions are clear, consistent with Python best practices (PEP 8), and do not show obvious AI-related errors.