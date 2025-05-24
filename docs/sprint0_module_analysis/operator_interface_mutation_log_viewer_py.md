# Module Analysis: `operator_interface/mutation_log_viewer.py`

## 1. Module Intent/Purpose

The primary role of the [`operator_interface/mutation_log_viewer.py`](../../operator_interface/mutation_log_viewer.py) module is to provide a human-readable summary of recent variable, overlay, and rule mutations. It is intended for Command Line Interface (CLI) diagnostics, rendering strategos digests, and auditing trust evolution within the Pulse system. It achieves this by loading and parsing data from learning and rule mutation log files.

## 2. Operational Status/Completeness

The module appears to be functional for its stated purpose of displaying summaries of log events. It successfully loads and processes JSONL log files. There are no explicit TODOs or placeholders in the provided code, suggesting it's considered complete for its current scope.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Limited Scope:** The module currently only displays the last 30 learning events and the last 10 rule mutations. This could be insufficient for thorough analysis. An enhancement could be to allow configurable numbers of entries or date-range filtering.
*   **Output Format:** The output is plain text printed to the console. For "strategos digest rendering," a more structured output (e.g., Markdown, HTML, or JSON for programmatic use) might be more beneficial or was perhaps an intended next step.
*   **Error Handling:** While there's a `try-except` block in [`load_log()`](../../operator_interface/mutation_log_viewer.py:19), error handling for malformed log entries within the rendering functions is minimal. Corrupt log lines could cause issues.
*   **No Overlay Mutation Viewing:** The docstring mentions "overlay" mutations, but the current implementation only has functions for "learning events" ([`render_learning_summary()`](../../operator_interface/mutation_log_viewer.py:29)) and "rule mutations" ([`render_rule_mutation_summary()`](../../operator_interface/mutation_log_viewer.py:46)). Functionality for overlay mutations seems to be missing or was planned and not implemented.
*   **Filtering/Querying:** There's no functionality to filter or query logs based on specific criteria (e.g., event type, specific variable names, date ranges).

## 4. Connections & Dependencies

*   **Direct Project Imports:**
    *   [`core.path_registry.PATHS`](../../core/path_registry.py): Used to get the paths for log files.
*   **External Library Dependencies:**
    *   `os`: Used for checking file existence ([`os.path.exists()`](../../operator_interface/mutation_log_viewer.py:20)).
    *   `json`: Used for loading data from JSONL files ([`json.loads()`](../../operator_interface/mutation_log_viewer.py:24)).
    *   `collections.defaultdict`: Imported but not used in the provided code. This might indicate a planned feature or a remnant from a previous version.
    *   `typing.List, Dict, Optional`: Used for type hinting.
*   **Interaction via Shared Data:**
    *   Reads from `logs/pulse_learning_log.jsonl` (via `LEARNING_LOG` path from [`PATHS`](../../core/path_registry.py)).
    *   Reads from `logs/rule_mutation_log.jsonl` (via `RULE_LOG` path from [`PATHS`](../../core/path_registry.py)).
*   **Input/Output Files:**
    *   **Input:**
        *   `logs/pulse_learning_log.jsonl`
        *   `logs/rule_mutation_log.jsonl`
    *   **Output:**
        *   Prints summaries to standard output (console).

## 5. Function and Class Example Usages

The module is primarily used as a script when `if __name__ == "__main__":` is true.

*   **[`load_log(path: str) -> List[Dict]`](../../operator_interface/mutation_log_viewer.py:19):**
    *   **Purpose:** Loads a JSONL file line by line, parsing each line as a JSON object.
    *   **Usage:**
        ```python
        learning_events = load_log(str(LEARNING_LOG))
        rule_mutations = load_log(str(RULE_LOG))
        ```

*   **[`render_learning_summary(events: List[Dict])`](../../operator_interface/mutation_log_viewer.py:29):**
    *   **Purpose:** Prints a summary of the last 30 learning events to the console.
    *   **Usage:**
        ```python
        learning_events = load_log(str(LEARNING_LOG))
        render_learning_summary(learning_events)
        ```

*   **[`render_rule_mutation_summary(log: List[Dict])`](../../operator_interface/mutation_log_viewer.py:46):**
    *   **Purpose:** Prints a summary of the last 10 rule mutations to the console.
    *   **Usage:**
        ```python
        rule_mutations = load_log(str(RULE_LOG))
        render_rule_mutation_summary(rule_mutations)
        ```

## 6. Hardcoding Issues

*   **Log File Paths (Default Values):**
    *   `LEARNING_LOG` defaults to `"logs/pulse_learning_log.jsonl"` if not found in [`PATHS`](../../core/path_registry.py).
    *   `RULE_LOG` defaults to `"logs/rule_mutation_log.jsonl"` if not found in [`PATHS`](../../core/path_registry.py).
    While these are retrieved from `PATHS`, the default values within the [`get()`](../../core/path_registry.py) method act as hardcoded fallbacks.
*   **Number of Events to Display:**
    *   [`render_learning_summary()`](../../operator_interface/mutation_log_viewer.py:29) displays `events[-30:]` (last 30 events).
    *   [`render_rule_mutation_summary()`](../../operator_interface/mutation_log_viewer.py:46) displays `log[-10:]` (last 10 entries).
    These limits are hardcoded.
*   **Print Statements:** UI elements like "📜 Pulse Learning Event Summary:" and "🔧 Rule Mutation Summary:" are hardcoded strings.

## 7. Coupling Points

*   **`core.path_registry`:** Tightly coupled for retrieving log file paths. Changes to `PATHS` keys or the structure of [`path_registry`](../../core/path_registry.py) could break this module.
*   **Log File Format (JSONL):** The module expects specific JSONL formats for both learning and rule mutation logs. Any change in the structure or key names within these log files will break the parsing and rendering logic (e.g., `e.get("timestamp", "?")`, `mut['rule']`).
*   **Specific Event Types:** The [`render_learning_summary()`](../../operator_interface/mutation_log_viewer.py:29) function has specific handling for `event_type == "volatile_cluster_mutation"`. New event types would get generic rendering unless the function is updated.

## 8. Existing Tests

No dedicated test file (e.g., `test_mutation_log_viewer.py`) was found in the `tests/` or `tests/operator_interface/` directories. It's possible that tests for this module are integrated elsewhere, or they do not exist. Given its nature as a CLI diagnostic tool, testing might involve capturing and comparing stdout, or testing the [`load_log()`](../../operator_interface/mutation_log_viewer.py:19) function with mock file systems and various log contents (valid, empty, malformed).

## 9. Module Architecture and Flow

The module follows a simple script-like architecture:
1.  **Initialization:** Imports necessary libraries and defines global constants for log file paths using [`core.path_registry.PATHS`](../../core/path_registry.py).
2.  **Log Loading:** The [`load_log()`](../../operator_interface/mutation_log_viewer.py:19) function handles reading and parsing JSONL files. It checks for file existence and includes basic error handling for file loading.
3.  **Summary Rendering:**
    *   [`render_learning_summary()`](../../operator_interface/mutation_log_viewer.py:29) processes a list of learning events, formatting and printing the last 30. It has special formatting for "volatile_cluster_mutation" events.
    *   [`render_rule_mutation_summary()`](../../operator_interface/mutation_log_viewer.py:46) processes a list of rule mutation log entries, formatting and printing details of the last 10 mutations.
4.  **Main Execution Block (`if __name__ == "__main__":`):**
    *   Loads learning events using [`load_log()`](../../operator_interface/mutation_log_viewer.py:19).
    *   Renders the learning summary using [`render_learning_summary()`](../../operator_interface/mutation_log_viewer.py:29).
    *   Loads rule mutations using [`load_log()`](../../operator_interface/mutation_log_viewer.py:19).
    *   Renders the rule mutation summary using [`render_rule_mutation_summary()`](../../operator_interface/mutation_log_viewer.py:46).

The primary flow is sequential: load logs, then render summaries to the console.

## 10. Naming Conventions

*   **Constants:** `LEARNING_LOG` and `RULE_LOG` are in `UPPER_SNAKE_CASE`, which is appropriate for constants.
*   **Functions:** [`load_log()`](../../operator_interface/mutation_log_viewer.py:19), [`render_learning_summary()`](../../operator_interface/mutation_log_viewer.py:29), [`render_rule_mutation_summary()`](../../operator_interface/mutation_log_viewer.py:46) use `snake_case`, adhering to PEP 8.
*   **Variables:** Variable names like `events`, `path`, `typ`, `dat`, `mut` are generally clear within their context. Some short variable names (`e`, `t`, `k`, `v`) are used in loops, which is acceptable for simple iterations.
*   **Docstrings:** The module has a good top-level docstring explaining its purpose. Functions also have brief explanations or rely on descriptive names.
*   **File Name:** `mutation_log_viewer.py` is descriptive.

No significant deviations from PEP 8 or obvious AI assumption errors in naming were observed. The unused import `defaultdict` from `collections` is a minor issue but not a naming convention problem.