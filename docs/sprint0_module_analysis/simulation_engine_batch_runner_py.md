# Module Analysis: `simulation_engine/batch_runner.py`

## Table of Contents
- [Module Intent/Purpose](#module-intentpurpose)
- [Operational Status/Completeness](#operational-statuscompleteness)
- [Implementation Gaps / Unfinished Next Steps](#implementation-gaps--unfinished-next-steps)
- [Connections & Dependencies](#connections--dependencies)
- [Function and Class Example Usages](#function-and-class-example-usages)
- [Hardcoding Issues](#hardcoding-issues)
- [Coupling Points](#coupling-points)
- [Existing Tests](#existing-tests)
- [Module Architecture and Flow](#module-architecture-and-flow)
- [Naming Conventions](#naming-conventions)

## Module Intent/Purpose
The primary role of [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py) is to execute batches of simulations based on configurations. Each batch run involves:
1.  Running a simulation (using [`simulate_forward()`](simulation_engine/simulator_core.py:simulate_forward)).
2.  Generating forecasts from the simulation's final state (using [`generate_forecast()`](forecast_output/forecast_generator.py:generate_forecast)).
3.  Processing these forecasts through a full pipeline (using [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:run_forecast_pipeline)).
4.  Summarizing and exporting the results.
It supports loading configurations from JSON files and can be run as a script with command-line arguments to control aspects like gravity correction.

## Operational Status/Completeness
The module appears to be largely operational for its core purpose of running simulation batches.
- It handles loading configurations, running simulations, generating forecasts, and processing them.
- Error handling is present for individual batch runs and for the export process.
- It includes a fallback logger if [`utils.log_utils`](utils/log_utils.py) is not found.
- Integration with `ShadowModelMonitor` is present but conditional, with fallbacks if import or initialization fails.
- The `if __name__ == "__main__":` block provides a way to run batches with sample configurations and extensive command-line arguments for controlling the `GravityEngine`.

Obvious placeholders or TODOs:
- Line 265: `"# TODO: Add CLI/config file support for batch execution."` - This indicates that while CLI arguments for gravity engine parameters are implemented, the primary mechanism for defining *which* batches to run (beyond hardcoded samples) via CLI or a main config file is still pending. Currently, it uses `sample_configs_main` when run as a script.

## Implementation Gaps / Unfinished Next Steps
- **CLI/Config File for Batch Definitions:** As noted by the TODO on line 265, the module intends to support loading batch configurations directly via CLI arguments or a main configuration file, rather than relying solely on hardcoded sample configurations when run as a script. The function [`load_batch_config()`](simulation_engine/batch_runner.py:66) exists but is not used in the `__main__` block.
- **Learning Engine Integration:** The [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) function accepts a `learning_engine` parameter, which is passed to [`simulate_forward()`](simulation_engine/simulator_core.py:simulate_forward). However, in the `__main__` block, no `learning_engine` instance is created or passed, suggesting this integration might be used by other calling modules but isn't fully demonstrated or utilized when `batch_runner.py` is run directly.
- **Extensibility of Batch Sources:** While it can load from a list of dictionaries (configs), the direct script execution only uses an inline sample. A more robust system might involve specifying multiple config files or sweep parameter definitions via the CLI.

## Connections & Dependencies
**Direct Imports from Other Project Modules:**
- [`utils.log_utils`](utils/log_utils.py) (with fallback) for logging ([`log_info()`](utils/log_utils.py:log_info)).
- [`core.path_registry.PATHS`](core/path_registry.py) for accessing predefined paths like `BATCH_OUTPUT`.
- [`core.pulse_config.SHADOW_MONITOR_CONFIG`](core/pulse_config.py) for `ShadowModelMonitor` configuration.
- [`config.gravity_config`](config/gravity_config.py) (as `grav_cfg`) for default gravity engine parameters.
- [`symbolic_system.gravity.engines.residual_gravity_engine.GravityEngineConfig`](symbolic_system/gravity/engines/residual_gravity_engine.py) for gravity engine configuration.
- [`diagnostics.shadow_model_monitor.ShadowModelMonitor`](diagnostics/shadow_model_monitor.py) (optional import) for monitoring simulation fidelity.
- [`engine.simulator_core.simulate_forward`](simulation_engine/simulator_core.py:simulate_forward) to run the core simulation.
- [`engine.worldstate.WorldState`](simulation_engine/worldstate.py:WorldState), [`SymbolicOverlays`](simulation_engine/worldstate.py:SymbolicOverlays) for managing simulation state.
- [`forecast_output.forecast_generator.generate_forecast`](forecast_output/forecast_generator.py:generate_forecast) to generate forecasts.
- [`analytics.forecast_pipeline_runner.run_forecast_pipeline`](learning/forecast_pipeline_runner.py:run_forecast_pipeline) to process forecasts.

**External Library Dependencies:**
- `json`: For loading batch configurations and dumping results.
- `os`: For path manipulations (e.g., [`os.path.abspath()`](os.path.abspath:0), [`os.path.join()`](os.path.join:0), [`os.path.dirname()`](os.path.dirname:0), [`os.makedirs()`](os.makedirs:0)).
- `traceback`: For formatting exception tracebacks.
- `tempfile`: For creating temporary files during export.
- `shutil`: For moving temporary files to final export path.
- `argparse`: For parsing command-line arguments.
- `sys`: For modifying `sys.path` to aid local imports.
- `logging`: As a fallback if [`utils.log_utils`](utils/log_utils.py) is unavailable.

**Interaction with Other Modules via Shared Data:**
- **Input:** Reads batch configurations from JSON files (via [`load_batch_config()`](simulation_engine/batch_runner.py:66), though not used in `__main__`).
- **Output:** Writes batch results to a JSONL file (e.g., [`logs/batch_output.jsonl`](logs/batch_output.jsonl) defined by `DEFAULT_BATCH_OUTPUT`).

**Input/Output Files:**
- **Input:**
    - Batch configuration JSON files (e.g., if [`load_batch_config()`](simulation_engine/batch_runner.py:66) were used by an external caller or a future CLI).
- **Output:**
    - `DEFAULT_BATCH_OUTPUT` ([`logs/batch_output.jsonl`](logs/batch_output.jsonl)): A JSON Lines file where each line is a JSON dump of the results for a single simulation configuration within the batch.

## Function and Class Example Usages
**[`load_batch_config(path: str) -> List[Dict[str, Any]]`](simulation_engine/batch_runner.py:66):**
```python
# Assuming 'my_batch_configs.json' contains:
# [
#   {"state_overrides": {"hope": 0.7}, "turns": 2},
#   {"state_overrides": {"despair": 0.8}, "turns": 3, "use_symbolism": false}
# ]
# configs = load_batch_config('my_batch_configs.json')
```
This function would load the list of dictionaries from the specified JSON file.

**[`run_batch_from_config(configs: List[Dict[str, Any]], ...) -> List[Dict[str, Any]]`](simulation_engine/batch_runner.py:71):**
```python
# sample_configs = [
#     {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
#     {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1},
# ]
# results = run_batch_from_config(
#     configs=sample_configs,
#     export_path="output/batch_run_results.jsonl",
#     gravity_enabled=True
# )
# for result in results:
#     if "error" in result:
#         print(f"Batch {result['batch_index']} failed: {result['error']['message']}")
#     else:
#         print(f"Batch {result['batch_index']} succeeded.")
```
This function takes a list of configuration dictionaries, runs a simulation and forecast pipeline for each, and optionally exports the results.

**Script Execution (`if __name__ == "__main__":`)**
```bash
python simulation_engine/batch_runner.py --enable-residual-gravity --gravity-lambda 0.75
```
When run as a script, it executes a predefined `sample_configs_main` batch. The command-line arguments primarily configure the behavior of the `GravityEngine` and whether gravity correction is applied. The results are saved to the path specified by `DEFAULT_BATCH_OUTPUT`.

## Hardcoding Issues
- **`DEFAULT_BATCH_OUTPUT = PATHS.get("BATCH_OUTPUT", "logs/batch_output.jsonl")` ([`simulation_engine/batch_runner.py:64`](simulation_engine/batch_runner.py:64)):** While it uses `PATHS` registry, it has a hardcoded fallback `"logs/batch_output.jsonl"`.
- **Sample Configurations in `__main__` ([`simulation_engine/batch_runner.py:269-272`](simulation_engine/batch_runner.py:269-272)):**
  ```python
  sample_configs_main = [
      {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
      {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1},
  ]
  ```
  These configurations are hardcoded for direct script execution. The TODO on line 265 acknowledges the need for CLI/config file support for batch execution.
- **Fallback Logger Configuration ([`simulation_engine/batch_runner.py:34-37`](simulation_engine/batch_runner.py:34-37)):** The `basicConfig` for the fallback logger has hardcoded level and format.
- **ShadowModelMonitor Initialization ([`simulation_engine/batch_runner.py:96-99`](simulation_engine/batch_runner.py:96-99)):** Relies on `SHADOW_MONITOR_CONFIG` which, if not fully populated, might lead to hardcoded defaults within `ShadowModelMonitor` itself or failure to initialize. The keys `"threshold_variance_explained"`, `"window_steps"`, and `"critical_variables"` are expected.
- **`return_mode="full"` for `simulate_forward` ([`simulation_engine/batch_runner.py:134`](simulation_engine/batch_runner.py:134)):** This is hardcoded, justified by the `ShadowModelMonitor` needing detailed state. If the monitor is not used or its needs change, this might become suboptimal.

## Coupling Points
- **[`engine.simulator_core.simulate_forward`](simulation_engine/simulator_core.py:simulate_forward):** Tightly coupled for running the actual simulations. Changes in `simulate_forward`'s signature or behavior (especially regarding state management, return values, or parameters like `gravity_enabled`) would directly impact `batch_runner`.
- **[`forecast_output.forecast_generator.generate_forecast`](forecast_output/forecast_generator.py:generate_forecast):** Used to generate forecasts from the final simulation state. Dependency on its input (simulation state snapshot) and output format.
- **[`analytics.forecast_pipeline_runner.run_forecast_pipeline`](learning/forecast_pipeline_runner.py:run_forecast_pipeline):** Processes the generated forecasts. Dependency on the format of forecasts it receives and the structure of results it returns.
- **`WorldState` and `SymbolicOverlays`:** The batch runner directly initializes and manipulates `WorldState` and its `overlays` based on configuration.
- **[`diagnostics.shadow_model_monitor.ShadowModelMonitor`](diagnostics/shadow_model_monitor.py):** Optional but significant coupling if enabled. `batch_runner` initializes and passes it to `simulate_forward`.
- **[`config.gravity_config`](config/gravity_config.py) and `GravityEngineConfig`:** Tightly coupled for configuring and enabling/disabling the gravity engine features passed to `simulate_forward`.
- **[`core.path_registry.PATHS`](core/path_registry.py) and [`core.pulse_config`](core/pulse_config.py):** For accessing global configuration like output paths and shadow monitor settings.
- **Logging ([`utils.log_utils`](utils/log_utils.py) or fallback):** Used throughout for status updates and error reporting.

## Existing Tests
- A specific test file for `batch_runner.py` (e.g., `tests/simulation_engine/test_batch_runner.py`) was not found in the `tests/simulation_engine/` directory.
- It's possible that `batch_runner.py` is tested indirectly as part of broader integration tests, but dedicated unit/functional tests for its specific logic (config loading, batch iteration, error handling per batch, CLI argument parsing, export logic) appear to be missing.

## Module Architecture and Flow
1.  **Initialization (if run as script):**
    *   Sets up `sys.path` for local imports.
    *   Initializes a logger (either [`utils.log_utils`](utils/log_utils.py) or a fallback).
    *   Parses command-line arguments, primarily for `GravityEngine` configuration.
    *   Uses hardcoded `sample_configs_main` for batch definitions.
    *   Determines `gravity_enabled` status and constructs `gravity_config` based on CLI args.
    *   Calls [`run_batch_from_config()`](simulation_engine/batch_runner.py:71).

2.  **[`run_batch_from_config()`](simulation_engine/batch_runner.py:71) Function:**
    *   Initializes `ShadowModelMonitor` if enabled and configured.
    *   Iterates through each configuration (`cfg`) in the input `configs` list:
        *   Logs batch progress.
        *   Initializes a new `WorldState()`.
        *   Applies `state_overrides` from `cfg` to `state.overlays`.
        *   Calls [`simulate_forward()`](simulation_engine/simulator_core.py:simulate_forward) with the current state, turns, and other parameters (including `gravity_enabled`, `gravity_config`, and `shadow_monitor_instance`).
        *   Extracts the `final_state_snapshot` from the simulation results.
        *   Calls [`generate_forecast()`](forecast_output/forecast_generator.py:generate_forecast) with the `final_state_snapshot`.
        *   Calls [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:run_forecast_pipeline) with the generated forecasts.
        *   Stores the pipeline result, including the original config and batch index.
        *   Handles exceptions during this process, storing error information.
    *   If `export_path` is provided, writes all results (or errors) to the specified JSONL file atomically (using a temporary file).
    *   Returns the list of results.

3.  **[`load_batch_config(path: str)`](simulation_engine/batch_runner.py:66) Function:**
    *   Opens and reads a JSON file specified by `path`.
    *   Returns the parsed list of configurations. (Currently not used in the `__main__` execution path).

**Data Flow:**
- Batch configurations (list of dicts) -> [`run_batch_from_config()`](simulation_engine/batch_runner.py:71).
- Each config -> `WorldState` initialization & `simulate_forward` -> Simulation results.
- Final simulation state -> `generate_forecast` -> Forecasts.
- Forecasts -> `run_forecast_pipeline` -> Pipeline results.
- Aggregated pipeline results -> Optional JSONL export file & return value.

## Naming Conventions
- **Module Name (`batch_runner.py`):** Clear and descriptive.
- **Function Names:**
    - [`load_batch_config()`](simulation_engine/batch_runner.py:66): Clear.
    - [`run_batch_from_config()`](simulation_engine/batch_runner.py:71): Clear.
    - [`log_info()`](simulation_engine/batch_runner.py:40) (fallback): Clear.
- **Variable Names:**
    - `configs`, `export_path`, `learning_engine`, `gravity_enabled`, `gravity_config`: Clear and follow PEP 8.
    - `shadow_monitor`, `cfg`, `state`, `num_turns`, `simulation_results`, `final_state_snapshot`, `forecasts`, `pipeline_result_data`: Generally clear.
    - `DEFAULT_BATCH_OUTPUT`: Standard for constants.
    - CLI argument names (e.g., `gravity_off`, `enable_residual_gravity`, `gravity_lambda`): Mostly clear, though long. The `dest` attributes (e.g., `gravity_enable_adaptive_lambda`) are consistent.
- **Class Names (Imported):** `WorldState`, `SymbolicOverlays`, `ShadowModelMonitor`, `GravityEngineConfig` follow PascalCase.
- **Consistency:** Generally good. Pythonic (snake_case for functions and variables, PascalCase for classes).
- **Potential AI Assumption Errors/Deviations:**
    - The comment on line 93: `# Removed type hint to fix Pylance error` for `shadow_monitor` suggests a previous type hint might have been problematic, possibly due to the conditional import of `ShadowModelMonitor`.
    - The sys.path manipulation ([`simulation_engine/batch_runner.py:24-26`](simulation_engine/batch_runner.py:24-26)) is a common pattern for making scripts runnable but can sometimes indicate underlying project structure or packaging issues if overused.
    - The fallback logger ([`simulation_engine/batch_runner.py:29-44`](simulation_engine/batch_runner.py:29-44)) is a good defensive measure.

Overall, naming conventions are quite good and adhere to Python standards.