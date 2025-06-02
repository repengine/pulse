# Module Analysis: `pulse_desktop/ui_shell.py`

## 1. Module Intent/Purpose

The module [`pulse_desktop/ui_shell.py`](../../pulse_desktop/ui_shell.py:1) serves as the primary Command Line Interface (CLI) for the Pulse application. It provides a unified entry point for users to interact with various core functionalities of the Pulse system. These functionalities include:

*   Core simulation execution.
*   Replaying and visualizing forecasts.
*   Running batch forecast generation processes.
*   Executing predefined test suites and individual rule tests.
*   Invoking dynamically loaded CLI extension modules (hooks) defined in [`dev_tools/pulse_hooks_config.json`](../../dev_tools/pulse_hooks_config.json).
*   Processing forecast data through a retrodiction and trust analysis pipeline.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its intended scope as a CLI frontend.
*   It handles multiple operational modes (`run`, `test`, `suite`, `batch`, `view`, and custom hooks) with distinct functionalities.
*   A comprehensive retrodiction and trust pipeline ([`args.retrodict`](../../pulse_desktop/ui_shell.py:161-209)) is implemented.
*   Error handling is present for critical operations like file loading (e.g., [`try_load_worldstate()`](../../pulse_desktop/ui_shell.py:105)).
*   Input validation is performed for some arguments (e.g., [`args.turns`](../../pulse_desktop/ui_shell.py:221), [`args.count`](../../pulse_desktop/ui_shell.py:224)).
*   The dynamic loading of CLI hooks suggests a design focused on extensibility.
*   No major `TODO` comments or obvious incomplete critical sections were identified in the main execution paths.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Optional Re-validation:** A comment [`# Optionally re-validate here`](../../pulse_desktop/ui_shell.py:290) within the worldstate variable validation section indicates a potential planned enhancement that is not currently implemented. This would involve re-validating the worldstate after missing variables have been estimated using defaults.
*   **Unused Visualization Function:** The function [`display_forecast_visualization()`](../../pulse_desktop/ui_shell.py:315) is defined but does not seem to be called from any part of the main CLI logic within this module. It might be a utility for other modules, intended for future integration, or a remnant of previous development.
*   **Symbolic Overlays Toggle:** The function [`toggle_symbolic_overlays()`](../../pulse_desktop/ui_shell.py:119) modifies a global configuration but is not exposed as a direct CLI argument, limiting its accessibility through this shell.
*   **Granular Hook Control:** While hooks can be executed, more advanced management or introspection of hooks via the CLI (beyond listing) could be a future extension.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`engine.turn_engine`](../../simulation_engine/turn_engine.py): For [`run_turn()`](../../pulse_desktop/ui_shell.py:33).
*   [`engine.worldstate`](../../simulation_engine/worldstate.py): For [`WorldState`](../../pulse_desktop/ui_shell.py:34).
*   [`engine.utils.worldstate_io`](../../simulation_engine/utils/worldstate_io.py): For worldstate loading/saving utilities.
*   [`core.variable_registry`](../../core/variable_registry.py): For [`validate_variables()`](../../pulse_desktop/ui_shell.py:36) and [`VARIABLE_REGISTRY`](../../pulse_desktop/ui_shell.py:45).
*   [`dev_tools.rule_dev_shell`](../../dev_tools/rule_dev_shell.py): For [`test_rules()`](../../pulse_desktop/ui_shell.py:37).
*   [`forecast_engine.forecast_log_viewer`](../../forecast_engine/forecast_log_viewer.py): For [`load_and_display_forecasts()`](../../pulse_desktop/ui_shell.py:38).
*   [`dev_tools.pulse_test_suite`](../../dev_tools/pulse_test_suite.py): For test suite functions like [`test_symbolic_shift()`](../../pulse_desktop/ui_shell.py:39).
*   [`dev_tools.pulse_forecast_test_suite`](../../dev_tools/pulse_forecast_test_suite.py): For [`run_forecast_validation()`](../../pulse_desktop/ui_shell.py:40).
*   [`forecast_engine.forecast_batch_runner`](../../forecast_engine/forecast_batch_runner.py): For [`run_batch_forecasts()`](../../pulse_desktop/ui_shell.py:41).
*   [`utils.log_utils`](../../utils/log_utils.py): For [`get_logger()`](../../pulse_desktop/ui_shell.py:42).
*   [`core.path_registry`](../../core/path_registry.py): For [`PATHS`](../../pulse_desktop/ui_shell.py:43).
*   [`core.pulse_config`](../../core/pulse_config.py): For [`MODULES_ENABLED`](../../pulse_desktop/ui_shell.py:44) and global settings like [`USE_SYMBOLIC_OVERLAYS`](../../pulse_desktop/ui_shell.py:120).
*   [`analytics.learning`](../../learning/learning.py): For [`retrospective_analysis_batch()`](../../pulse_desktop/ui_shell.py:46).
*   [`trust_system.trust_engine`](../../trust_system/trust_engine.py): For [`TrustEngine`](../../pulse_desktop/ui_shell.py:47).
*   [`trust_system.license_enforcer`](../../trust_system/license_enforcer.py): Conditionally imported for license enforcement.
*   [`forecast_output.forecast_memory_promoter`](../../forecast_output/forecast_memory_promoter.py): Conditionally imported for promoting forecasts.

### External Library Dependencies:
*   `argparse`: For command-line argument parsing.
*   `json`: For loading/dumping JSON data (hooks config, worldstate, forecasts).
*   `os`: For file system operations (checking file existence).
*   `importlib`: For dynamically importing hook modules.
*   `typing`: For type hints (`Any`, `Optional`).

### Shared Data Interactions:
*   **Configuration Files:**
    *   Reads CLI hook configurations from [`dev_tools/pulse_hooks_config.json`](../../dev_tools/pulse_hooks_config.json) (path sourced from [`PATHS`](../../pulse_desktop/ui_shell.py:52)).
*   **Data Files:**
    *   Loads initial worldstate from a JSON file (default: [`simulation_engine/worldstate_input.json`](../../simulation_engine/worldstate_input.json)).
    *   Saves final worldstate to a JSON file (default: [`simulation_engine/worldstate_output.json`](../../simulation_engine/worldstate_output.json)).
    *   Reads forecast data from user-specified JSONL files for the retrodiction pipeline.
    *   Writes processed forecast data to a user-specified JSONL file (default: [`retrodicted_output.jsonl`](../../pulse_desktop/ui_shell.py:139)).
*   **Registries/Global State:**
    *   Uses [`core.variable_registry.VARIABLE_REGISTRY`](../../core/variable_registry.py) for variable definitions and validation.
    *   Uses [`core.path_registry.PATHS`](../../core/path_registry.py) for resolving file paths.
    *   Uses [`core.pulse_config.MODULES_ENABLED`](../../core/pulse_config.py) for feature flags.
    *   Modifies/reads [`core.pulse_config.USE_SYMBOLIC_OVERLAYS`](../../core/pulse_config.py:120).

### Input/Output Files:
*   **Input:**
    *   [`dev_tools/pulse_hooks_config.json`](../../dev_tools/pulse_hooks_config.json)
    *   `simulation_engine/worldstate_input.json` (or path from `PATHS`)
    *   User-provided forecast files (`.jsonl`) via `--retrodict` argument.
    *   User-provided current state file (`.json`) via `--state` argument.
*   **Output:**
    *   `simulation_engine/worldstate_output.json` (or path from `PATHS`)
    *   `retrodicted_output.jsonl` (or path from `--retrodict-output` argument).
    *   Log files (managed by [`utils.log_utils`](../../utils/log_utils.py)).
    *   Forecast logs in `forecast_output/` (relevant for `view` mode).

## 5. Function and Class Example Usages

*   **`main()`**: Entry point of the CLI.
    *   Run simulation: `python pulse_ui_shell.py --mode run --turns 5`
    *   Run rule tests: `python pulse_ui_shell.py --mode test`
    *   View forecasts: `python pulse_ui_shell.py --mode view --domain capital --top 10`
    *   Run batch forecasts: `python pulse_ui_shell.py --mode batch --count 20 --domain sports`
    *   Run retrodiction: `python pulse_ui_shell.py --retrodict forecasts.jsonl --state current_state.json`
    *   Execute a hook: `python pulse_ui_shell.py --my_custom_hook_name` (if `my_custom_hook_name` is defined in hooks config and added as an argument) or `python pulse_ui_shell.py --mode my_custom_hook_name`.
*   **`list_domains()`**: Invoked by `python pulse_ui_shell.py --list_domains`. Prints available simulation domains based on [`VARIABLE_REGISTRY`](../../core/variable_registry.py:61).
*   **`safe_hook_import(hook_name)`**: Used internally to load and run `main()` from hook modules specified by name.
*   **`print_active_hooks()`**: Invoked by `python pulse_ui_shell.py --help_hooks`. Lists CLI hooks from [`dev_tools/pulse_hooks_config.json`](../../dev_tools/pulse_hooks_config.json).
*   **`compress_forecasts(forecasts, top_k)`**: Used internally in the retrodiction pipeline ([`args.compress_topk`](../../pulse_desktop/ui_shell.py:186)) to filter forecasts by confidence.

## 6. Hardcoding Issues

*   **Default File Paths:**
    *   [`HOOKS_JSON`](../../pulse_desktop/ui_shell.py:52): Default path `"dev_tools/pulse_hooks_config.json"` is used if not found in `PATHS`.
    *   [`retrodict_output`](../../pulse_desktop/ui_shell.py:139): Argument default is `"retrodicted_output.jsonl"`.
    *   Worldstate input/output paths ([`input_path`](../../pulse_desktop/ui_shell.py:266), [`output_path`](../../pulse_desktop/ui_shell.py:267)) have fallback defaults if not in `PATHS`.
*   **Default Values for CLI Arguments:**
    *   `--mode`: `"run"` ([`default="run"`](../../pulse_desktop/ui_shell.py:125))
    *   `--turns`: `1` ([`default=1`](../../pulse_desktop/ui_shell.py:126))
    *   `--top`: `5` ([`default=5`](../../pulse_desktop/ui_shell.py:128))
    *   `--count`: `5` ([`default=5`](../../pulse_desktop/ui_shell.py:130))
    *   `--retrodict-threshold`: `1.5` ([`default=1.5`](../../pulse_desktop/ui_shell.py:140))
*   **Magic Strings & Values:**
    *   Mode names (`"run"`, `"test"`, `"suite"`, `"batch"`, `"view"`) are used for dispatching logic.
    *   Default domain for batch mode: `"capital"` ([`args.domain or "capital"`](../../pulse_desktop/ui_shell.py:249)).
    *   Log directory for `view` mode: `"forecast_output"` ([`load_and_display_forecasts(log_dir="forecast_output", ...)`](../../pulse_desktop/ui_shell.py:255)).
    *   Trust label string: `"\U0001F7E2 Trusted"` ([`args.filter_trusted`](../../pulse_desktop/ui_shell.py:177)).
    *   Various UI print messages containing emojis and specific text (e.g., `"\U0001F501 Loading forecast batch..."`, `"\u2705 Retrodiction + trust tagging complete."`).
*   **Hook Metadata Defaults:**
    *   Default label for hooks: `"hooked module"` ([`hook_data["metadata"] ... .get("label", "hooked module")`](../../pulse_desktop/ui_shell.py:101)).
    *   Default category for hooks: `"tool"` ([`hook_data["metadata"] ... .get("category", "tool")`](../../pulse_desktop/ui_shell.py:151)).

## 7. Coupling Points

*   **Configuration Objects:**
    *   [`core.pulse_config`](../../core/pulse_config.py): Tightly coupled for `MODULES_ENABLED` and `USE_SYMBOLIC_OVERLAYS`.
    *   [`core.path_registry.PATHS`](../../core/path_registry.py): Essential for resolving most file paths.
    *   [`core.variable_registry.VARIABLE_REGISTRY`](../../core/variable_registry.py): Critical for variable validation and domain listing.
*   **External Files:**
    *   [`dev_tools/pulse_hooks_config.json`](../../dev_tools/pulse_hooks_config.json): The structure and content of this file directly influence CLI behavior and available hooks.
    *   Worldstate JSON files: Assumes a specific structure for loading and saving.
    *   Forecast JSONL files: Assumes a specific structure for processing.
*   **Imported Module Interfaces:**
    *   Relies on the specific function signatures and behaviors of imported functions from `simulation_engine`, `dev_tools`, `forecast_engine`, `learning`, and `trust_system`.
*   **Data Structures:**
    *   Assumes a particular structure for the `WorldState` object (attributes like `variables`, `turn`, methods like `snapshot()`, `get_log()`).
    *   Assumes forecast objects are dictionaries with keys like `confidence`, `trust_label`, etc.

## 8. Existing Tests

*   This module (`ui_shell.py`) does not contain its own unit tests within the file.
*   It acts as an **invoker** of test functionalities from other modules:
    *   `test` mode calls [`test_rules()`](../../pulse_desktop/ui_shell.py:237) from [`dev_tools.rule_dev_shell`](../../dev_tools/rule_dev_shell.py).
    *   `suite` mode calls:
        *   [`test_symbolic_shift()`](../../pulse_desktop/ui_shell.py:241) and [`test_capital_shift()`](../../pulse_desktop/ui_shell.py:242) from [`dev_tools.pulse_test_suite`](../../dev_tools/pulse_test_suite.py).
        *   [`run_forecast_validation()`](../../pulse_desktop/ui_shell.py:243) from [`dev_tools.pulse_forecast_test_suite`](../../dev_tools/pulse_forecast_test_suite.py).
*   A dedicated test file like `tests/test_pulse_desktop_ui_shell.py` is not immediately apparent from the provided context and would be needed for direct unit/integration testing of the CLI shell itself. Testing would likely involve running the script with various arguments and asserting outputs, exit codes, or file modifications.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Imports modules and initializes a logger.
    *   Loads CLI hook configurations from [`HOOKS_JSON`](../../pulse_desktop/ui_shell.py:52) (defaulting to [`dev_tools/pulse_hooks_config.json`](../../dev_tools/pulse_hooks_config.json)).
2.  **Argument Parsing (`main()` function):**
    *   [`argparse.ArgumentParser`](../../pulse_desktop/ui_shell.py:124) is used to define CLI arguments for modes, simulation parameters, retrodiction options, etc.
    *   Arguments for active CLI hooks are dynamically added based on the loaded hook configuration.
3.  **Primary Dispatch Logic (within `main()`):**
    *   **Help/Information:** Handles `--help`, `--help_hooks`, `--list_domains`.
    *   **Retrodiction Pipeline:** If `--retrodict` and `--state` are present, executes a sequence:
        *   Load forecasts and current state.
        *   Run [`retrospective_analysis_batch()`](../../pulse_desktop/ui_shell.py:170).
        *   Apply trust tagging via [`TrustEngine.apply_all()`](../../pulse_desktop/ui_shell.py:173).
        *   Optionally filter trusted, generate trust summary, compress forecasts, enforce licenses, and promote to memory.
        *   Save processed forecasts.
    *   **Hook Execution (by dedicated flag):** Iterates through configured hooks and executes if its corresponding flag (e.g., `--some_hook_name`) is set.
    *   **Predefined Mode Execution:**
        *   `--mode test`: Calls [`test_rules()`](../../pulse_desktop/ui_shell.py:237).
        *   `--mode suite`: Calls several test suite functions.
        *   `--mode batch`: Calls [`run_batch_forecasts()`](../../pulse_desktop/ui_shell.py:247).
        *   `--mode view`: Calls [`load_and_display_forecasts()`](../../pulse_desktop/ui_shell.py:255).
    *   **Hook Execution (by `--mode <hook_name>`):** If `args.mode` matches an active hook name.
    *   **Default Simulation Mode (`--mode run` or no mode specified):**
        *   Loads worldstate using [`try_load_worldstate()`](../../pulse_desktop/ui_shell.py:269).
        *   Validates worldstate variables using [`validate_variables()`](../../pulse_desktop/ui_shell.py:276), with an option to estimate missing ones if `MODULES_ENABLED["estimate_missing_variables"]` is true.
        *   Iteratively calls [`run_turn()`](../../pulse_desktop/ui_shell.py:295) for the specified number of turns.
        *   Prints final state snapshot and log.
        *   Saves the final worldstate.
4.  **Utility Functions:**
    *   [`list_domains()`](../../pulse_desktop/ui_shell.py:59): Prints simulation domains.
    *   [`safe_hook_import()`](../../pulse_desktop/ui_shell.py:84): Imports and runs hook modules.
    *   [`print_active_hooks()`](../../pulse_desktop/ui_shell.py:95): Lists active hooks.
    *   [`try_load_worldstate()`](../../pulse_desktop/ui_shell.py:105): Loads worldstate with error handling.
    *   [`compress_forecasts()`](../../pulse_desktop/ui_shell.py:113): Filters forecasts.
    *   [`toggle_symbolic_overlays()`](../../pulse_desktop/ui_shell.py:119): Toggles a global config (not CLI exposed).
    *   [`display_forecast_visualization()`](../../pulse_desktop/ui_shell.py:315): Defined for visualization but unused in the main flow.

## 10. Naming Conventions

*   **Functions:** Predominantly `snake_case` (e.g., [`list_domains`](../../pulse_desktop/ui_shell.py:59), [`safe_hook_import`](../../pulse_desktop/ui_shell.py:84)), adhering to PEP 8.
*   **Variables:** Mostly `snake_case` (e.g., `hook_data`, `input_path`, `current_state`).
*   **Constants:** `UPPER_SNAKE_CASE` (e.g., [`HOOKS_JSON`](../../pulse_desktop/ui_shell.py:52), [`ESTIMATE_MISSING`](../../pulse_desktop/ui_shell.py:274)), adhering to PEP 8.
*   **Classes:** Imported classes use `PascalCase` (e.g., [`WorldState`](../../pulse_desktop/ui_shell.py:34), [`TrustEngine`](../../pulse_desktop/ui_shell.py:47)).
*   **Module Name:** `snake_case` ([`pulse_desktop/ui_shell.py`](../../pulse_desktop/ui_shell.py:1)), which is standard.
*   **CLI Arguments:** Use hyphens for flags (e.g., `--list-domains`, `--retrodict-output`), which `argparse` converts to `snake_case` attributes (e.g., `args.list_domains`, `args.retrodict_output`).
*   **Author Tag:** The line [`Author: Pulse v0.20`](../../pulse_desktop/ui_shell.py:12) in the initial docstring appears to be a placeholder or an AI-generated artifact rather than a conventional author name.
*   Overall, naming conventions are largely consistent with Python community standards (PEP 8).
