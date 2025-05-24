# Module Analysis: `forecast_engine/forecast_batch_runner.py`

## 1. Purpose

The [`forecast_engine/forecast_batch_runner.py`](forecast_engine/forecast_batch_runner.py:1) module is designed to run new forecast simulations in batch mode from scratch. It orchestrates the entire lifecycle of a batch of forecasts, including simulation, scoring, validation, optional license enforcement, and recursion auditing. It also serves as a Command Line Interface (CLI) entry point for initiating these batch simulations.

## 2. Key Functionalities

*   **Batch Forecast Simulation:**
    *   The core function [`run_batch_forecasts()`](forecast_engine/forecast_batch_runner.py:45) iterates a specified number of times to generate forecasts.
    *   For each forecast, it initializes a [`WorldState`](simulation_engine/worldstate.py:1) and runs a simulation turn using [`run_turn()`](simulation_engine/turn_engine.py:1).
*   **Scoring and Validation:**
    *   After simulation, each forecast is scored using [`score_forecast()`](forecast_engine/forecast_scoring.py:1).
    *   The resulting metadata is then validated by [`validate_forecast()`](forecast_engine/forecast_integrity_engine.py:1) against criteria like minimum confidence (from [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:1) or a CLI argument) and blocked symbolic drivers.
*   **Forecast Tracking and Storage:**
    *   Accepted forecasts are recorded using [`ForecastTracker`](forecast_engine/forecast_tracker.py:1). The module implies that `ForecastTracker` handles saving, though [`save_forecast_to_memory()`](forecast_engine/forecast_memory.py:1) is imported but not directly used in `run_batch_forecasts`.
*   **Summary Export:**
    *   A JSON summary of the batch run (timestamp, domain, counts of requested/accepted/rejected forecasts, and individual logs) is exported to a file specified by `PATHS["BATCH_FORECAST_SUMMARY"]`.
*   **Recursion Audit:**
    *   It collects accepted forecasts from the current batch.
    *   If a previous batch's data exists (in `data/last_forecast_batch.jsonl`), it performs a recursion audit using [`generate_recursion_report()`](learning/recursion_audit.py:1) from the `learning` module.
    *   The audit report is saved to `data/recursion_audit_log.json`.
    *   The current batch's accepted forecasts are saved to `data/last_forecast_batch.jsonl` to serve as the baseline for the next audit.
*   **License Enforcement (Optional):**
    *   If `enforce_license` is true, it uses [`annotate_forecasts()`](trust_system/license_enforcer.py:1) and [`filter_licensed()`](trust_system/license_enforcer.py:1) from [`trust_system.license_enforcer`](trust_system/license_enforcer.py:1) to process forecasts.
*   **CLI Interface:**
    *   The `if __name__ == "__main__":` block provides a CLI using `argparse` to configure and run batch forecasts, allowing users to specify parameters like count, domain, minimum confidence, blocked tags, verbosity, and license enforcement.

## 3. Role within `forecast_engine/`

This module acts as a high-level orchestrator and entry point for generating and processing new forecasts in a batch. It integrates various components from `simulation_engine/`, `forecast_engine/`, `learning/`, and `trust_system/` to provide an end-to-end batch processing pipeline. It's the primary tool for users or automated systems wanting to initiate a set of new forecast simulations and ensure they are properly evaluated and audited.

## 4. Dependencies

### Internal Pulse Modules:

*   [`simulation_engine.worldstate`](simulation_engine/worldstate.py:1) (specifically `WorldState` class)
*   [`simulation_engine.turn_engine`](simulation_engine/turn_engine.py:1) (specifically [`run_turn()`](simulation_engine/turn_engine.py:1) function)
*   [`forecast_engine.forecast_tracker`](forecast_engine/forecast_tracker.py:1) (specifically `ForecastTracker` class)
*   [`forecast_engine.forecast_scoring`](forecast_engine/forecast_scoring.py:1) (specifically [`score_forecast()`](forecast_engine/forecast_scoring.py:1) function)
*   [`forecast_engine.forecast_integrity_engine`](forecast_engine/forecast_integrity_engine.py:1) (specifically [`validate_forecast()`](forecast_engine/forecast_integrity_engine.py:1) function)
*   [`forecast_engine.forecast_memory`](forecast_engine/forecast_memory.py:1) (specifically [`save_forecast_to_memory()`](forecast_engine/forecast_memory.py:1) - imported but not directly used in the main function)
*   [`utils.log_utils`](utils/log_utils.py:1) (specifically [`get_logger()`](utils/log_utils.py:1) function)
*   [`core.path_registry`](core/path_registry.py:1) (specifically `PATHS` dictionary)
*   [`core.pulse_config`](core/pulse_config.py:1) (specifically `CONFIDENCE_THRESHOLD`)
*   [`learning.recursion_audit`](learning/recursion_audit.py:1) (specifically [`generate_recursion_report()`](learning/recursion_audit.py:1) function)
*   [`trust_system.license_enforcer`](trust_system/license_enforcer.py:1) (conditionally imports [`annotate_forecasts()`](trust_system/license_enforcer.py:1) and [`filter_licensed()`](trust_system/license_enforcer.py:1))

### External Libraries:

*   `os`: Standard Python library for operating system interactions (path manipulation, creating directories).
*   `json`: Standard Python library for JSON encoding and decoding.
*   `argparse`: Standard Python library for parsing command-line arguments.
*   `datetime`: Standard Python library for date and time operations.

## 5. Adherence to SPARC Principles

*   **Simplicity:** The main workflow in [`run_batch_forecasts()`](forecast_engine/forecast_batch_runner.py:45) is a clear loop that processes each forecast through distinct stages. The CLI interface is also straightforward.
*   **Iterate:** The module processes forecasts one by one in a loop. The recursion audit feature inherently compares current batch results against previous ones, implying an iterative improvement or monitoring cycle.
*   **Focus:** The module is clearly focused on the task of running and processing batches of new forecasts.
*   **Quality:**
    *   The code includes docstrings at the module and function levels.
    *   It uses logging for informational messages and errors.
    *   Configuration values (like `CONFIDENCE_THRESHOLD` and file paths) are imported from central config modules.
    *   The CLI provides helpful descriptions for its arguments.
    *   Error handling for file operations (e.g., collecting forecasts for audit) is present with a `try-except pass` block, which might be too broad.
*   **Collaboration:** The module collaborates by orchestrating components from different parts of the Pulse system (simulation, scoring, validation, learning, trust).

## 6. Overall Assessment

*   **Completeness:** The module provides a comprehensive workflow for batch forecast generation, including simulation, scoring, validation, summary reporting, and recursion auditing. The optional license enforcement adds another layer of processing.
*   **Clarity:** The code is generally clear and well-structured. The flow of operations within [`run_batch_forecasts()`](forecast_engine/forecast_batch_runner.py:45) is logical. The purpose of the module and its CLI usage are well-explained in the module-level docstring.
*   **Quality:** The quality is good. It leverages centralized configurations and utility functions. The separation of concerns by calling out to other modules for specific tasks (scoring, validation) is good practice. The recursion audit and license enforcement are valuable additions.
    *   One minor point is the broad `except Exception: pass` ([`forecast_engine/forecast_batch_runner.py:113-114`](forecast_engine/forecast_batch_runner.py:113-114)) when loading forecasts for the audit, which could silently ignore issues. More specific exception handling or logging would be better.
    *   The import of [`save_forecast_to_memory()`](forecast_engine/forecast_memory.py:1) without direct usage in [`run_batch_forecasts()`](forecast_engine/forecast_batch_runner.py:45) might indicate an old or planned feature, or that `ForecastTracker` handles this internally.

## 7. Recommendations

*   Refine the exception handling around line [`forecast_engine/forecast_batch_runner.py:113`](forecast_engine/forecast_batch_runner.py:113) to be more specific or to log errors if loading forecast data for the audit fails.
*   Clarify the role of the imported but unused [`save_forecast_to_memory()`](forecast_engine/forecast_memory.py:1) or remove the import if it's truly redundant.
*   Ensure file paths used for recursion audit (`data/last_forecast_batch.jsonl`, `data/recursion_audit_log.json`) are also managed via [`core.path_registry`](core/path_registry.py:1) for consistency, if not already covered by a broader "data" directory path.
*   Consider adding more detailed logging for the license enforcement steps when active.