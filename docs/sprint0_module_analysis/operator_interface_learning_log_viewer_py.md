# Module Analysis: `operator_interface/learning_log_viewer.py`

**Version:** As of Pulse v0.31 (from module docstring)
**Analysis Date:** 2025-05-17

## 1. Module Intent/Purpose

The primary role of [`operator_interface/learning_log_viewer.py`](operator_interface/learning_log_viewer.py) is to display and summarize the Pulse learning log, which is stored in a JSONL file (default: [`logs/pulse_learning_log.jsonl`](logs/pulse_learning_log.jsonl)). It is intended for operator review, system audits, and potentially for UI rendering of meta-evolution events within the Pulse system. It provides functionalities to load, filter, summarize, and render these learning events, primarily to the console. It also includes helper functions to display trust metrics for variables and rules using the [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:0).

## 2. Operational Status/Completeness

The module appears largely functional for its core purpose of console-based log viewing and summarization.
- It successfully loads events from a JSONL file ([`load_learning_events()`](operator_interface/learning_log_viewer.py:22)).
- It can summarize event types ([`summarize_learning_events()`](operator_interface/learning_log_viewer.py:57)).
- It can filter events by type ([`filter_events()`](operator_interface/learning_log_viewer.py:73)).
- It can render a digest of events to the console ([`render_event_digest()`](operator_interface/learning_log_viewer.py:87)).
- It includes a basic CLI interface via [`main()`](operator_interface/learning_log_viewer.py:126) with options for limiting event count, filtering by type, and running a simple self-test.
- Functions to display variable and rule trust ([`display_variable_trust()`](operator_interface/learning_log_viewer.py:109), [`display_rule_trust()`](operator_interface/learning_log_viewer.py:114)) are present.

There are no explicit "TODO" comments or obvious major placeholders for its current scope of console output.

## 3. Implementation Gaps / Unfinished Next Steps

*   **UI Rendering:** The docstring mentions "UI rendering of meta-evolution events" ([`operator_interface/learning_log_viewer.py:5`](operator_interface/learning_log_viewer.py:5)), but the current implementation is console-focused. A graphical user interface or integration with a dashboard is an implied but missing feature.
*   **Trust Display Integration:** The functions [`display_variable_trust()`](operator_interface/learning_log_viewer.py:109) and [`display_rule_trust()`](operator_interface/learning_log_viewer.py:114) are defined, and their example usage is commented out ([`operator_interface/learning_log_viewer.py:120-123`](operator_interface/learning_log_viewer.py:120-123)) with a note "Example usage in your dashboard rendering logic:". This suggests they are intended for a UI/dashboard component that is not part of this script or not yet fully integrated.
*   **Advanced Filtering/Querying:** Current filtering is basic (by event type). More advanced querying capabilities (e.g., by date range, specific data content) could be a logical next step.
*   **Error Handling in Log Parsing:** While basic `json.JSONDecodeError` is caught ([`operator_interface/learning_log_viewer.py:47`](operator_interface/learning_log_viewer.py:47)), more robust validation of event content beyond checking for `event_type` and `timestamp` keys ([`operator_interface/learning_log_viewer.py:43`](operator_interface/learning_log_viewer.py:43)) could be beneficial.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.path_registry.PATHS`](core/path_registry.py:0): Used to get the path to the learning log file ([`operator_interface/learning_log_viewer.py:16`](operator_interface/learning_log_viewer.py:16), [`operator_interface/learning_log_viewer.py:19`](operator_interface/learning_log_viewer.py:19)).
*   [`core.bayesian_trust_tracker.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:0): Used to retrieve trust scores and confidence intervals for variables and rules ([`operator_interface/learning_log_viewer.py:17`](operator_interface/learning_log_viewer.py:17), [`operator_interface/learning_log_viewer.py:110-112`](operator_interface/learning_log_viewer.py:110-112), [`operator_interface/learning_log_viewer.py:115-117`](operator_interface/learning_log_viewer.py:115-117)).

### External Library Dependencies:
*   `json`: For parsing JSONL log entries ([`operator_interface/learning_log_viewer.py:10`](operator_interface/learning_log_viewer.py:10)).
*   `os`: For file system operations like checking log file existence ([`operator_interface/learning_log_viewer.py:11`](operator_interface/learning_log_viewer.py:11)).
*   `sys`: Imported ([`operator_interface/learning_log_viewer.py:12`](operator_interface/learning_log_viewer.py:12)) but not directly used in the provided code.
*   `typing` (List, Dict, Optional, Any): For type hinting ([`operator_interface/learning_log_viewer.py:13`](operator_interface/learning_log_viewer.py:13)).
*   `collections.defaultdict`: Used in [`summarize_learning_events()`](operator_interface/learning_log_viewer.py:57) ([`operator_interface/learning_log_viewer.py:14`](operator_interface/learning_log_viewer.py:14)).
*   `datetime`: Imported ([`operator_interface/learning_log_viewer.py:15`](operator_interface/learning_log_viewer.py:15)) but not directly used; timestamps are handled as strings.
*   `argparse`: Used in [`main()`](operator_interface/learning_log_viewer.py:126) for CLI argument parsing ([`operator_interface/learning_log_viewer.py:131`](operator_interface/learning_log_viewer.py:131)).

### Interaction via Shared Data:
*   **Learning Log File:** Reads from `logs/pulse_learning_log.jsonl` (default path). This file is presumably written by other components of the Pulse system that log learning events.
*   **Bayesian Trust Tracker Data:** Implicitly relies on the data managed by the `bayesian_trust_tracker` module.

### Input/Output Files:
*   **Input:** `logs/pulse_learning_log.jsonl` (JSON Lines format).
*   **Output:** Primarily console output (summaries, event digests, trust information). No files are written by this module.

## 5. Function and Class Example Usages

*   **`load_learning_events(limit: Optional[int] = None) -> List[Dict[str, Any]]`** ([`operator_interface/learning_log_viewer.py:22`](operator_interface/learning_log_viewer.py:22))
    *   Loads events from the log file.
    ```python
    # Load the last 10 events
    recent_events = load_learning_events(limit=10)
    # Load all events
    all_events = load_learning_events()
    ```

*   **`summarize_learning_events(events: List[Dict[str, Any]]) -> Dict[str, int]`** ([`operator_interface/learning_log_viewer.py:57`](operator_interface/learning_log_viewer.py:57))
    *   Counts events by `event_type`.
    ```python
    summary = summarize_learning_events(events_list)
    # Example: {'model_trained': 5, 'rule_updated': 10}
    ```

*   **`filter_events(events: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]`** ([`operator_interface/learning_log_viewer.py:73`](operator_interface/learning_log_viewer.py:73))
    *   Filters events for a specific type.
    ```python
    model_trained_events = filter_events(events_list, "model_trained")
    ```

*   **`render_event_digest(events: List[Dict[str, Any]]) -> None`** ([`operator_interface/learning_log_viewer.py:87`](operator_interface/learning_log_viewer.py:87))
    *   Prints a formatted digest of events to the console.
    ```python
    render_event_digest(recent_events)
    ```

*   **`display_variable_trust(variable_id)`** ([`operator_interface/learning_log_viewer.py:109`](operator_interface/learning_log_viewer.py:109))
    *   Prints trust information for a variable.
    ```python
    display_variable_trust("var_A")
    # Output: Variable var_A: Trust=0.850, 95% CI=(0.750, 0.950)
    ```

*   **`display_rule_trust(rule_id)`** ([`operator_interface/learning_log_viewer.py:114`](operator_interface/learning_log_viewer.py:114))
    *   Prints trust information for a rule.
    ```python
    display_rule_trust("rule_123")
    # Output: Rule rule_123: Trust=0.920, 95% CI=(0.880, 0.960)
    ```

*   **`main()`** ([`operator_interface/learning_log_viewer.py:126`](operator_interface/learning_log_viewer.py:126))
    *   CLI entry point.
    ```bash
    python operator_interface/learning_log_viewer.py --limit 10 --filter "NEW_RULE_PROPOSED"
    python operator_interface/learning_log_viewer.py --test
    ```

## 6. Hardcoding Issues

*   **Default Log Path:** The fallback path `"logs/pulse_learning_log.jsonl"` for `LEARNING_LOG` is hardcoded in the `PATHS.get()` call ([`operator_interface/learning_log_viewer.py:19`](operator_interface/learning_log_viewer.py:19)). While `PATHS` provides configurability, this default is embedded.
*   **Console Messages:** Various informational and error messages printed to the console are hardcoded strings (e.g., `"[LearningLog] No log found."` ([`operator_interface/learning_log_viewer.py:33`](operator_interface/learning_log_viewer.py:33)), `"[LearningLogViewer] Skipping malformed event..."` ([`operator_interface/learning_log_viewer.py:46`](operator_interface/learning_log_viewer.py:46))).
*   **CLI Argument Defaults:** Default values for CLI arguments, such as `default=20` for `--limit` ([`operator_interface/learning_log_viewer.py:133`](operator_interface/learning_log_viewer.py:133)), are hardcoded.
*   **Event Structure Keys:** The expected keys in event dictionaries (e.g., `"event_type"`, `"timestamp"`, `"data"`) are implicitly hardcoded by their usage in [`load_learning_events()`](operator_interface/learning_log_viewer.py:43) and [`render_event_digest()`](operator_interface/learning_log_viewer.py:97-99).
*   **Digest Formatting:** The formatting strings and separators (e.g., `"-" * 60`) in [`render_event_digest()`](operator_interface/learning_log_viewer.py:87) are hardcoded.

## 7. Coupling Points

*   **Log File Format:** Tightly coupled to the JSONL format and the specific schema (expected keys like `event_type`, `timestamp`, `data`) of the learning log entries. Changes to this format by log producers would break the viewer.
*   **`core.path_registry`:** Dependency for resolving the log file path. Changes in how `PATHS` works or if the `"LEARNING_LOG"` key is altered could impact the module.
*   **`core.bayesian_trust_tracker`:** Dependency for fetching trust information. Changes to the API of `bayesian_trust_tracker` (e.g., method names, return values) would require updates here.
*   **Console Output:** The module is primarily designed for console output. Adapting it for other output forms (e.g., a GUI, web service) would require significant changes.

## 8. Existing Tests

*   **Inline Self-Test:** The module contains a simple self-test feature accessible via the `--test` CLI argument ([`operator_interface/learning_log_viewer.py:135`](operator_interface/learning_log_viewer.py:135), [`operator_interface/learning_log_viewer.py:138-149`](operator_interface/learning_log_viewer.py:138-149)). This test:
    *   Creates a small, hardcoded list of test events.
    *   Calls [`summarize_learning_events()`](operator_interface/learning_log_viewer.py:57) and prints the summary.
    *   Calls [`render_event_digest()`](operator_interface/learning_log_viewer.py:87) to display them.
*   **Gaps in Testing:**
    *   No dedicated test file (e.g., `tests/operator_interface/test_learning_log_viewer.py`) is apparent.
    *   The self-test does not cover file loading ([`load_learning_events()`](operator_interface/learning_log_viewer.py:22)) from an actual or mock file.
    *   Error handling for malformed log files or entries is not explicitly tested by the self-test.
    *   The trust display functions ([`display_variable_trust()`](operator_interface/learning_log_viewer.py:109), [`display_rule_trust()`](operator_interface/learning_log_viewer.py:114)) are not covered by the self-test.
    *   Filtering logic ([`filter_events()`](operator_interface/learning_log_viewer.py:73)) is not directly part of the self-test, though it's used in the main CLI path.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Imports necessary standard libraries and project-specific modules (`PATHS`, `bayesian_trust_tracker`).
    *   Defines `LOG_PATH` using `PATHS.get()`.
2.  **Core Functions:**
    *   [`load_learning_events()`](operator_interface/learning_log_viewer.py:22): Reads the log file line by line, parses JSON, validates basic structure, and returns a list of event dictionaries. Handles file not found and JSON decoding errors.
    *   [`summarize_learning_events()`](operator_interface/learning_log_viewer.py:57): Iterates through events, counting them by `event_type` using a `defaultdict`.
    *   [`filter_events()`](operator_interface/learning_log_viewer.py:73): Filters a list of events based on a provided `event_type`.
    *   [`render_event_digest()`](operator_interface/learning_log_viewer.py:87): Iterates through events and prints formatted details (timestamp, type, data) to the console.
    *   [`display_variable_trust()`](operator_interface/learning_log_viewer.py:109) / [`display_rule_trust()`](operator_interface/learning_log_viewer.py:114): Fetch and print trust information using `bayesian_trust_tracker`.
3.  **CLI Entry Point (`main()`):**
    *   Uses `argparse` to define and parse command-line arguments (`--limit`, `--filter`, `--test`).
    *   **Test Mode (`--test`):** If specified, runs a predefined self-test with hardcoded events, prints a summary and digest, then exits.
    *   **Normal Mode:**
        *   Calls [`load_learning_events()`](operator_interface/learning_log_viewer.py:22) (with optional `limit`).
        *   If `--filter` is provided, calls [`filter_events()`](operator_interface/learning_log_viewer.py:73).
        *   If events are found:
            *   Calls [`summarize_learning_events()`](operator_interface/learning_log_viewer.py:57) and prints the summary.
            *   Calls [`render_event_digest()`](operator_interface/learning_log_viewer.py:87) to display the events.
        *   If no events are found, prints a "No learning events logged yet" message.
4.  **Execution Guard:** The `if __name__ == "__main__":` block calls [`main()`](operator_interface/learning_log_viewer.py:126).

## 10. Naming Conventions

*   **Consistency:** Generally follows Python's PEP 8 guidelines.
    *   Functions and variables use `snake_case` (e.g., [`load_learning_events`](operator_interface/learning_log_viewer.py:22), `event_type`).
    *   Constants like `LOG_PATH` use `UPPER_SNAKE_CASE` ([`operator_interface/learning_log_viewer.py:19`](operator_interface/learning_log_viewer.py:19)).
*   **Clarity:**
    *   Function names are descriptive and clearly indicate their purpose (e.g., [`summarize_learning_events`](operator_interface/learning_log_viewer.py:57), [`render_event_digest`](operator_interface/learning_log_viewer.py:87)).
    *   Variable names are mostly clear (e.g., `events`, `summary`).
    *   Some short variable names are used in loops (`ev` in [`operator_interface/learning_log_viewer.py:68`](operator_interface/learning_log_viewer.py:68), `e` in [`operator_interface/learning_log_viewer.py:84`](operator_interface/learning_log_viewer.py:84) & [`operator_interface/learning_log_viewer.py:96`](operator_interface/learning_log_viewer.py:96)) or local contexts (`t`, `typ`, `dat` in [`operator_interface/learning_log_viewer.py:97-99`](operator_interface/learning_log_viewer.py:97-99)), which is acceptable for limited scopes but could be slightly more descriptive.
*   **Type Hinting:** The module makes good use of type hints (e.g., `List[Dict[str, Any]]`).
*   **AI Assumption Errors:** No obvious errors in naming that would suggest misinterpretation by an AI or significant deviation from common Python practices.