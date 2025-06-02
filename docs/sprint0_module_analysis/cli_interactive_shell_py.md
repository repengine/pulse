# Module Analysis: cli/interactive_shell.py

## Module Intent/Purpose

The primary role of the `cli/interactive_shell.py` module is to provide an interactive command-line interface for interacting with the Pulse system. It serves as a strategist shell, enabling operations related to symbolic mutation, forecast management, and module orchestration.

## Operational Status/Completeness

The module appears partially complete. While the basic shell loop and command dispatching are implemented, several core commands (`run-turns`, `load-worldstate`, `show-forecast`, `compare-drift`) are marked as stubs, indicating that their full functionality is not yet implemented.

## Implementation Gaps / Unfinished Next Steps

The presence of multiple "[Stub]" commands clearly indicates that the module was intended to be more extensive. Logical next steps include implementing the full functionality for:

*   Running simulation turns (`run-turns`)
*   Loading saved worldstates (`load-worldstate`)
*   Generating and displaying forecasts (`show-forecast`)
*   Comparing forecast drifts (`compare-drift`)

The docstring also mentions "Stub hooks for external module integration," suggesting that integrating with other Pulse modules or external systems is a planned but incomplete feature.

## Connections & Dependencies

*   **Direct Imports:**
    *   `json`
    *   `os`
    *   `readline`
    *   `datetime`
    *   `typing`
    *   [`utils.log_utils`](utils/log_utils.py)
    *   [`core.path_registry`](core/path_registry.py)
    *   [`core.pulse_config`](core/pulse_config.py)
    *   [`analytics.pulse_memory_audit_report`](memory/pulse_memory_audit_report.py)
    *   [`analytics.forecast_memory`](memory/forecast_memory.py)
    *   [`trust_system.trust_engine`](trust_system/trust_engine.py)
    *   [`engine.utils.simulation_trace_viewer`](simulation_engine/utils/simulation_trace_viewer.py)
*   **External Library Dependencies:** `json`, `os`, `readline`, `datetime`, `typing`.
*   **Interaction with other modules:**
    *   Retrieves paths from [`core.path_registry.PATHS`](core/path_registry.py:41).
    *   Accesses configuration from [`core.pulse_config`](core/pulse_config.py).
    *   Performs memory audits using [`analytics.pulse_memory_audit_report.audit_memory()`](memory/pulse_memory_audit_report.py:45) and [`analytics.forecast_memory.ForecastMemory`](memory/forecast_memory.py:46).
    *   Checks forecast coherence using [`trust_system.trust_engine.TrustEngine.check_forecast_coherence()`](trust_system/trust_engine.py:164).
    *   Views simulation traces using [`engine.utils.simulation_trace_viewer.load_trace()`](simulation_engine/utils/simulation_trace_viewer.py:181).
*   **Input/output files:** Logs shell interactions to `logs/interactive_shell_log.jsonl` (path determined by `INTERACTIVE_LOG_PATH`).

## Function and Class Example Usages

The module defines several command handler functions, each demonstrating the intended usage of a specific shell command. For example:

*   `cmd_help()`: Displays available commands.
*   `cmd_set_overlay(['hope', '0.7'])`: Sets the 'hope' overlay value to 0.7.
*   `cmd_show_overlays()`: Displays current overlay values.
*   `cmd_memory_audit()`: Triggers a memory audit.
*   `cmd_view_trace(['path/to/trace.jsonl'])`: Loads and displays a simulation trace.

## Hardcoding Issues

*   The default value for `INTERACTIVE_LOG_PATH` (`"logs/interactive_shell_log.jsonl"`) is hardcoded, although it attempts to load from `PATHS`.
*   The initial values for `symbolic_overlays` are hardcoded to `0.5`.
*   The version string `"v0.22.2"` is hardcoded in the log entries and the shell's welcome message.

## Coupling Points

Significant coupling exists with:

*   [`core.path_registry`](core/path_registry.py) and [`core.pulse_config`](core/pulse_config.py) for core system configuration and paths.
*   The `memory` modules ([`analytics.pulse_memory_audit_report`](memory/pulse_memory_audit_report.py), [`analytics.forecast_memory`](memory/forecast_memory.py)) for memory-related operations.
*   [`trust_system.trust_engine`](trust_system/trust_engine.py) for coherence checks.
*   [`engine.utils.simulation_trace_viewer`](simulation_engine/utils/simulation_trace_viewer.py) for trace visualization.

## Existing Tests

Based on the project file structure, there is no dedicated test file (e.g., `tests/cli/test_interactive_shell.py`) for this module. This suggests a lack of specific unit or integration tests.

## Module Architecture and Flow

The module follows a command-router architecture. A dictionary `COMMANDS` maps string commands to corresponding handler functions. The main `run_shell()` function contains an infinite loop that:

1.  Prompts the user for input.
2.  Parses the input into a command and arguments.
3.  Looks up the command in the `COMMANDS` dictionary.
4.  If a handler is found, it is called with the arguments.
5.  User interactions and errors are logged to a JSONL file.

The shell utilizes Python's `readline` module for command history and editing.

## Naming Conventions

