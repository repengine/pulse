# SPARC Analysis: engine.batch_runner

**Date of Analysis:** 2025-05-14
**Analyst:** Roo
**Version:** Pulse v0.24 (as per module docstring)

## 1. Module Intent/Purpose (Specification)

The [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py:1) module is designed to run batches of simulations based on configuration files or sweep inputs. For each simulation configuration in a batch, it performs the following sequence of operations:
1.  Initializes or updates a `WorldState` object.
2.  Runs the simulation forward for a specified number of turns using [`engine.simulator_core.simulate_forward()`](simulation_engine/simulator_core.py:581).
3.  Optionally utilizes a `ShadowModelMonitor` to track critical variables.
4.  Optionally applies gravity corrections via a `GravityEngineConfig`.
5.  Generates forecasts based on the final simulation state using [`forecast_output.forecast_generator.generate_forecast()`](forecast_output/forecast_generator.py:28).
6.  Processes these forecasts through the full forecast pipeline using [`analytics.forecast_pipeline_runner.run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:54).
7.  Collects and optionally exports the results to a JSONL file.

The module can be run as a script, providing command-line arguments to control gravity correction parameters and load sample configurations.

## 2. Operational Status/Completeness

*   **Operational:** The module appears to be operational for its core purpose of running simulation batches and processing their outputs.
*   **Completeness:**
    *   It includes a fallback logging mechanism if [`utils.log_utils`](utils/log_utils.py:1) is not found.
    *   It handles the absence of `ShadowModelMonitor` gracefully.
    *   The `if __name__ == "__main__":` block provides a runnable example with sample configurations and extensive command-line argument parsing for gravity engine settings.
    *   **TODOs:**
        *   Line 265: `TODO: Add CLI/config file support for batch execution.` - Currently, it uses hardcoded `sample_configs_main` when run as a script.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Configuration Loading:** As noted in the TODO, the script execution part relies on hardcoded sample configurations ([`sample_configs_main`](simulation_engine/batch_runner.py:269)) rather than loading batch configurations from a file or more flexible CLI inputs. The function [`load_batch_config()`](simulation_engine/batch_runner.py:66) exists but is not used in the `__main__` block.
*   **Learning Engine Integration:** The `learning_engine` parameter in [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) is optional and not instantiated or used in the `__main__` block, suggesting this integration might be incomplete or intended for external callers.

## 4. Connections & Dependencies

### Direct Imports (Project Modules):

*   [`utils.log_utils`](utils/log_utils.py:1) (specifically [`log_info`](utils/log_utils.py:46)) - For logging. Includes a fallback if import fails.
*   [`core.path_registry`](core/path_registry.py:1) (specifically `PATHS`) - For accessing predefined file paths like `BATCH_OUTPUT`.
*   [`core.pulse_config`](core/pulse_config.py:1) (specifically `SHADOW_MONITOR_CONFIG`) - For configuring the `ShadowModelMonitor`.
*   [`config.gravity_config`](config/gravity_config.py:1) (as `grav_cfg`) - For default gravity engine parameters used in CLI help strings and default `GravityEngineConfig` values.
*   [`symbolic_system.gravity.engines.residual_gravity_engine`](symbolic_system/gravity/engines/residual_gravity_engine.py:1) (specifically [`GravityEngineConfig`](symbolic_system/gravity/engines/residual_gravity_engine.py:26)) - For configuring the gravity engine.
*   [`diagnostics.shadow_model_monitor`](diagnostics/shadow_model_monitor.py:1) (specifically [`ShadowModelMonitor`](diagnostics/shadow_model_monitor.py:6)) - For monitoring shadow model performance. Import is optional.
*   [`engine.simulator_core`](simulation_engine/simulator_core.py:1) (specifically [`simulate_forward`](simulation_engine/simulator_core.py:581)) - The core function for running a single simulation.
*   [`engine.worldstate`](simulation_engine/worldstate.py:1) (specifically [`WorldState`](simulation_engine/worldstate.py:471), [`SymbolicOverlays`](simulation_engine/worldstate.py:31)) - For representing and manipulating the simulation state.
*   [`forecast_output.forecast_generator`](forecast_output/forecast_generator.py:1) (specifically [`generate_forecast`](forecast_output/forecast_generator.py:28)) - For generating forecasts from a simulation state.
*   [`analytics.forecast_pipeline_runner`](learning/forecast_pipeline_runner.py:1) (specifically [`run_forecast_pipeline`](learning/forecast_pipeline_runner.py:54)) - For processing generated forecasts.

### Direct Imports (External Libraries):

*   `json`
*   `os`
*   `traceback`
*   `tempfile`
*   `shutil`
*   `argparse`
*   `sys`
*   `logging` (used in fallback)
*   `typing` (Dict, List, Optional, Any)

### Touched Project Files (for dependency mapping):

*   [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py:1) (self)
*   [`utils/log_utils.py`](utils/log_utils.py:1)
*   [`core/path_registry.py`](core/path_registry.py:1)
*   [`core/pulse_config.py`](core/pulse_config.py:1)
*   [`config/gravity_config.py`](config/gravity_config.py:1)
*   [`symbolic_system/gravity/engines/residual_gravity_engine.py`](symbolic_system/gravity/engines/residual_gravity_engine.py:1)
*   [`diagnostics/shadow_model_monitor.py`](diagnostics/shadow_model_monitor.py:1)
*   [`simulation_engine/simulator_core.py`](simulation_engine/simulator_core.py:1)
*   [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1)
*   [`forecast_output/forecast_generator.py`](forecast_output/forecast_generator.py:1)
*   [`learning/forecast_pipeline_runner.py`](learning/forecast_pipeline_runner.py:1)

### Interactions:

*   **File System (Input):**
    *   Potentially JSON configuration files via [`load_batch_config()`](simulation_engine/batch_runner.py:66) (though not used in `__main__`).
*   **File System (Output):**
    *   Exports batch results to a JSONL file (default: [`logs/batch_output.jsonl`](simulation_engine/batch_runner.py:64), path retrieved from `PATHS`). Uses `tempfile` and `shutil.move` for atomic writes.
*   **Logging:**
    *   Uses [`log_info()`](utils/log_utils.py:46) for standardized logging.
*   **Shared Data Structures/Objects:**
    *   Passes `WorldState` objects to [`simulate_forward()`](simulation_engine/simulator_core.py:581).
    *   Passes simulation results (final state snapshot) to [`generate_forecast()`](forecast_output/forecast_generator.py:28).
    *   Passes generated forecasts to [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:54).
    *   Receives configuration dictionaries.
    *   Uses `GravityEngineConfig` to configure gravity aspects of [`simulate_forward()`](simulation_engine/simulator_core.py:581).
    *   Uses `ShadowModelMonitor` instance with [`simulate_forward()`](simulation_engine/simulator_core.py:581).

### Input/Output Files:

*   **Input:**
    *   Batch configuration JSON files (intended, via [`load_batch_config()`](simulation_engine/batch_runner.py:66)).
*   **Output:**
    *   JSONL file containing results for each configuration in the batch (e.g., [`logs/batch_output.jsonl`](simulation_engine/batch_runner.py:64)). Each line is a JSON dump of the `pipeline_result_data` for a config.

## 5. Function and Class Example Usages

### [`load_batch_config(path: str) -> List[Dict[str, Any]]`](simulation_engine/batch_runner.py:66)
```python
# Assuming 'my_batch_configs.json' contains:
# [
#   {"state_overrides": {"hope": 0.7}, "turns": 2},
#   {"state_overrides": {"despair": 0.6}, "turns": 3, "use_symbolism": false}
# ]
configs = load_batch_config("my_batch_configs.json")
# configs would be a list of two dictionaries.
```

### [`run_batch_from_config(configs: List[Dict[str, Any]], ...) -> List[Dict[str, Any]]`](simulation_engine/batch_runner.py:71)
```python
from engine.worldstate import WorldState, SymbolicOverlays
from symbolic_system.gravity.engines.residual_gravity_engine import GravityEngineConfig

sample_configs = [
    {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
    {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1, "use_symbolism": False},
]

# Example with gravity enabled and custom config
custom_gravity_config = GravityEngineConfig(lambda_=0.1, learning_rate=0.005)

results = run_batch_from_config(
    configs=sample_configs,
    export_path="output/batch_run_results.jsonl",
    gravity_enabled=True,
    gravity_config=custom_gravity_config
)

for result in results:
    if "error" in result:
        print(f"Batch config {result['config']} failed: {result['error']['message']}")
    else:
        print(f"Batch config {result['config']} succeeded. Output keys: {list(result.keys())}")
```

### Script Execution (`if __name__ == "__main__":`)
```bash
python simulation_engine/batch_runner.py --gravity-lambda 0.15 --gravity-learning-rate 0.01
# This would run the hardcoded sample_configs_main with gravity enabled
# and the specified lambda and learning rate for the GravityEngine.
# Results would be saved to logs/batch_output.jsonl.

python simulation_engine/batch_runner.py --gravity-off
# This would run the hardcoded sample_configs_main with gravity disabled.
```

## 6. Hardcoding Issues (SPARC Critical)

*   **Default Batch Output Path:** [`DEFAULT_BATCH_OUTPUT`](simulation_engine/batch_runner.py:64) is defined as `PATHS.get("BATCH_OUTPUT", "logs/batch_output.jsonl")`. While it uses `PATHS` (good), it still has a hardcoded fallback `"logs/batch_output.jsonl"`. This path should ideally be fully configurable or derived.
*   **Sample Configurations in `__main__`:** The [`sample_configs_main`](simulation_engine/batch_runner.py:269) variable within the `if __name__ == "__main__":` block is hardcoded. This is acceptable for a simple script example but limits flexibility for direct script execution without code modification. The TODO on line 265 acknowledges this.
*   **Shadow Monitor Critical Variables:** The `critical_variables` for `ShadowModelMonitor` are fetched from `SHADOW_MONITOR_CONFIG` ([`core/pulse_config.py`](core/pulse_config.py:1)). While centralized in `pulse_config`, these are still effectively hardcoded within that configuration file (e.g., `["var1", "var2"]`). This is less of an issue for `batch_runner.py` itself but a point for the overall system configuration.

## 7. Coupling Points

*   **High Coupling with `engine.simulator_core`:** Directly calls [`simulate_forward()`](simulation_engine/simulator_core.py:581), relying on its specific signature and behavior.
*   **High Coupling with `forecast_output.forecast_generator`:** Directly calls [`generate_forecast()`](forecast_output/forecast_generator.py:28).
*   **High Coupling with `analytics.forecast_pipeline_runner`:** Directly calls [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:54).
*   **High Coupling with `WorldState` and `SymbolicOverlays`:** Directly instantiates and manipulates these objects.
*   **Configuration Objects:** Tightly coupled to the structure of `GravityEngineConfig` and `SHADOW_MONITOR_CONFIG`.
*   **`PATHS` dictionary:** Relies on specific keys like `"BATCH_OUTPUT"` being present in [`core/path_registry.py`](core/path_registry.py:1).
*   **Error Handling:** The error reporting structure (`{"error": {"type": ..., "message": ..., "traceback": ...}}`) is specific to this module.

## 8. Existing Tests (SPARC Refinement)

*   No dedicated unit tests for [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py:1) are apparent in the provided file structure or typical project layouts (e.g., a `tests/simulation_engine/test_batch_runner.py`).
*   The `if __name__ == "__main__":` block ([`simulation_engine/batch_runner.py:192`](simulation_engine/batch_runner.py:192)) serves as a basic integration test or runnable example, exercising the main functionality with sample data and CLI arguments.
*   **Testability Gaps:**
    *   The `run_batch_from_config` function is large and performs many steps. Testing individual components of this process (e.g., state initialization, forecast generation call, pipeline call, result aggregation, export) in isolation would be difficult without refactoring.
    *   Dependencies like `simulate_forward`, `generate_forecast`, and `run_forecast_pipeline` are directly called, making them hard to mock for unit testing `run_batch_from_config`'s logic.
    *   File I/O for export could be made more testable by abstracting file writing.

## 9. Module Architecture and Flow (SPARC Architecture)

*   **Overall Flow:**
    1.  Load batch configurations (intended, but `__main__` uses hardcoded).
    2.  Initialize `ShadowModelMonitor` if enabled and configured.
    3.  Iterate through each configuration:
        a.  Initialize `WorldState` and apply `state_overrides`.
        b.  Call [`simulate_forward()`](simulation_engine/simulator_core.py:581) with the state, turns, and other parameters (including gravity settings and shadow monitor instance).
        c.  Extract final state snapshot from simulation results.
        d.  Call [`generate_forecast()`](forecast_output/forecast_generator.py:28) with the final state.
        e.  Call [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:54) with the generated forecasts.
        f.  Store pipeline results, including original config and error info if any.
    4.  If an `export_path` is provided, write all results to a JSONL file.
    5.  Return the list of results.
*   **CLI Entry Point (`__main__`):**
    1.  Parses command-line arguments, primarily for controlling gravity engine parameters.
    2.  Uses hardcoded `sample_configs_main`.
    3.  Determines `gravity_enabled` status based on CLI flags.
    4.  Constructs a `GravityEngineConfig` object if gravity parameters are specified via CLI.
    5.  Calls [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) with the sample configs and derived gravity settings.
*   **Modularity:**
    *   The module delegates core simulation, forecast generation, and pipeline processing to other specialized modules, which is good.
    *   The [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) function encapsulates the main batch processing logic.
    *   [`load_batch_config()`](simulation_engine/batch_runner.py:66) provides a dedicated way to load configurations.
*   **Error Handling:**
    *   Includes `try-except` blocks for `ShadowModelMonitor` initialization, individual batch config processing, and results export.
    *   Stores detailed error information (type, message, traceback) in the results list if a batch item fails.
    *   Fallback logger for `utils.log_utils` import failure.
    *   Graceful handling of `ShadowModelMonitor` import failure.

## 10. Naming Conventions (SPARC Maintainability)

*   **Module Name:** `batch_runner.py` is clear and descriptive.
*   **Function Names:**
    *   [`load_batch_config()`](simulation_engine/batch_runner.py:66): Clear.
    *   [`run_batch_from_config()`](simulation_engine/batch_runner.py:71): Clear.
*   **Variable Names:**
    *   `configs`, `export_path`, `learning_engine`, `gravity_enabled`, `gravity_config`: Clear and follow Python conventions (snake_case).
    *   `results`, `shadow_monitor`, `cfg`, `state`, `num_turns`, `simulation_results`, `final_state_snapshot`, `forecasts`, `pipeline_result_data`: Generally clear.
    *   `DEFAULT_BATCH_OUTPUT`: Clear constant naming (UPPER_SNAKE_CASE).
    *   CLI argument destinations (e.g., `gravity_enable_adaptive_lambda`) are descriptive.
*   **Docstrings:** Present for the module and key functions, explaining purpose, args, and returns. The module docstring also includes a TODO list.
*   **Comments:** Used effectively to explain non-obvious code sections, CLI arguments, and fallback logic.

## 11. SPARC Compliance Summary

*   **Specification:** The module's primary purpose is well-defined in its docstring and generally met by the implementation. The CLI part has a clear specification gap (loading configs from file).
*   **Modularity/Architecture:**
    *   Good delegation to other modules for core tasks (simulation, forecasting).
    *   The main processing loop in [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) is somewhat monolithic but follows a logical flow.
    *   Configuration for gravity and shadow monitoring is handled through dedicated config objects/dictionaries.
*   **Refinement Focus:**
    *   **Testability:** Significant gaps exist. No dedicated unit tests. The main function [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) would be hard to unit test without refactoring or extensive mocking due to direct calls to complex external functions and file I/O.
    *   **Security (Hardcoding):**
        *   `DEFAULT_BATCH_OUTPUT` fallback path is hardcoded.
        *   `sample_configs_main` in `__main__` is hardcoded.
        *   No direct hardcoding of secrets, API keys, or highly sensitive paths was observed within this module itself. Path management relies on `core.path_registry` and `core.pulse_config` for some configurations, which centralizes but doesn't eliminate potential hardcoding in those modules.
    *   **Maintainability:**
        *   Code clarity is generally good with descriptive names and comments.
        *   The `__main__` block is quite long due to extensive `argparse` setup for gravity parameters. This could potentially be refactored for better readability if script functionality grows.
        *   The handling of `SymbolicOverlays` initialization and updates within [`run_batch_from_config()`](simulation_engine/batch_runner.py:71) (lines 116-126) is a bit complex and could be encapsulated further within the `WorldState` or `SymbolicOverlays` classes if this pattern is common.
*   **No Hardcoding (SPARC Critical):** Partially compliant. While it avoids hardcoding secrets, it does have hardcoded fallback paths and sample data as noted above.

**Overall SPARC Assessment:**
The module is functional and demonstrates good separation of concerns by leveraging other specialized modules. Key areas for SPARC-aligned improvement include enhancing testability through refactoring and dependency injection, and addressing the hardcoded configurations in the script execution part to improve flexibility. The error handling and logging are reasonably robust.