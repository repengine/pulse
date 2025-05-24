# Module Analysis: `forecast_output/forecast_contradiction_digest.py`

## 1. Module Intent/Purpose

The primary role of the [`forecast_contradiction_digest.py`](forecast_output/forecast_contradiction_digest.py:1) module is to load, process, and display a summary (digest) of recently detected forecast contradictions. This digest is intended for use in trust diagnostics, UI summary panes, and for review within the learning loop, helping operators and the system understand patterns of contradictory forecasts.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its stated purpose of loading and rendering a digest of contradiction logs.
*   It includes functions to load log entries ([`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19)), group them by reason ([`group_by_reason()`](forecast_output/forecast_contradiction_digest.py:31)), and render a textual digest ([`render_digest()`](forecast_output/forecast_contradiction_digest.py:38)).
*   It handles the case where the log file might not exist or if there are errors during loading.
*   An example usage is provided in the `if __name__ == "__main__":` block.
*   No "TODO" comments or `pass` statements suggest obviously unfinished sections.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Digest Format and Output:**
    *   The current [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38) function prints directly to standard output. For UI integration or use in other systems, returning a structured data format (e.g., a list of strings, a more complex dictionary) would be more flexible than relying on `print()`.
    *   The digest is purely textual. For UI panes, a more structured (e.g., HTML, JSON for a web UI) or graphical representation might be beneficial.
*   **Log Loading and Filtering:**
    *   [`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19) loads all lines and then slices the last `limit` entries. For very large log files, this could be memory-intensive. A more efficient approach might read the file in reverse or use other methods to get trailing lines.
    *   Filtering capabilities (e.g., by date range, specific trace IDs, specific reasons beyond the current grouping) are not present but could be useful.
*   **Error Handling:** The `except Exception as e:` ([`forecast_output/forecast_contradiction_digest.py:26`](forecast_output/forecast_contradiction_digest.py:26)) in [`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19) is broad. More specific exception handling could be implemented.
*   **Configuration:** The `limit` in [`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19) is a parameter, but other aspects like the log path (though sourced from `PATHS`) are relatively fixed within this module's direct operation.
*   **No "Clear Log" or Log Rotation Awareness:** The module only reads from the log. It doesn't have functionality to manage the log file itself (e.g., archive, clear, check size). This would likely be handled by a separate logging utility or process.

## 4. Connections & Dependencies

*   **Direct Imports from Other Project Modules:**
    *   [`core.path_registry.PATHS`](core/path_registry.py) ([`forecast_output/forecast_contradiction_digest.py:14`](forecast_output/forecast_contradiction_digest.py:14)): Used to get the path for the contradiction log file.
*   **External Library Dependencies:**
    *   `os` (specifically `os.path.exists`): To check if the log file exists.
    *   `json` (`json.loads`): To parse JSON lines from the log file.
    *   `collections.defaultdict`: Used in [`group_by_reason()`](forecast_output/forecast_contradiction_digest.py:31) to group log entries.
    *   `typing` (`List`, `Dict`): For type hinting.
*   **Interaction with Other Modules via Shared Data:**
    *   **Consumes Log File:** This module's primary interaction is reading the contradiction log file (e.g., [`logs/forecast_contradiction_log.jsonl`](logs/forecast_contradiction_log.jsonl)) which is produced by [`forecast_output/forecast_contradiction_detector.py`](forecast_output/forecast_contradiction_detector.py:1). It relies on the structure of the JSON objects within this log file (expecting keys like "reason", "trace_id_1", "trace_id_2").
*   **Input/Output Files:**
    *   **Input:** Reads the contradiction log file (e.g., [`logs/forecast_contradiction_log.jsonl`](logs/forecast_contradiction_log.jsonl)).
    *   **Output (Standard Output):** The [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38) function prints a textual summary to the console.

## 5. Function and Class Example Usages

### Function: [`load_contradiction_log(limit: int = 20) -> List[Dict]`](forecast_output/forecast_contradiction_digest.py:19)
**Purpose:** Loads the most recent `limit` entries from the contradiction log file.
**Example Usage:**
```python
# Assuming CONTRADICTION_LOG_PATH points to a valid log file
recent_contradictions = load_contradiction_log(limit=10)
# for entry in recent_contradictions:
#     print(entry)
```

### Function: [`group_by_reason(logs: List[Dict]) -> Dict[str, List[Dict]]`](forecast_output/forecast_contradiction_digest.py:31)
**Purpose:** Groups a list of log entries (dictionaries) by their "reason" key.
**Example Usage:**
```python
sample_logs = [
    {"reason": "Symbolic paradox", "trace_id_1": "T1", "trace_id_2": "T2"},
    {"reason": "Capital conflict", "trace_id_1": "T3", "trace_id_2": "T4"},
    {"reason": "Symbolic paradox", "trace_id_1": "T5", "trace_id_2": "T6"}
]
grouped_logs = group_by_reason(sample_logs)
# Expected:
# {
#     "Symbolic paradox": [
#         {"reason": "Symbolic paradox", "trace_id_1": "T1", "trace_id_2": "T2"},
#         {"reason": "Symbolic paradox", "trace_id_1": "T5", "trace_id_2": "T6"}
#     ],
#     "Capital conflict": [
#         {"reason": "Capital conflict", "trace_id_1": "T3", "trace_id_2": "T4"}
#     ]
# }
# print(grouped_logs)
```

### Function: [`render_digest(logs: List[Dict])`](forecast_output/forecast_contradiction_digest.py:38)
**Purpose:** Prints a formatted digest of contradiction logs to the console, grouped by reason.
**Example Usage:** (Uses the output of `load_contradiction_log`)
```python
# Assuming CONTRADICTION_LOG_PATH has some entries
loaded_logs = load_contradiction_log(limit=5)
render_digest(loaded_logs)
# Output would be like:
# 🚨 Forecast Contradiction Digest (latest entries):
#
# ❗ Symbolic paradox (2 pair(s))
#  - T1 vs T2
#  - T5 vs T6
# ---
# ❗ Capital conflict (1 pair(s))
#  - T3 vs T4
# ---
```

## 6. Hardcoding Issues

*   **Log Path Default:** `CONTRADICTION_LOG_PATH` defaults to `"logs/forecast_contradiction_log.jsonl"` ([`forecast_output/forecast_contradiction_digest.py:16`](forecast_output/forecast_contradiction_digest.py:16)) if not found in `PATHS`.
*   **Default Reason:** `entry.get("reason", "unknown")` ([`forecast_output/forecast_contradiction_digest.py:34`](forecast_output/forecast_contradiction_digest.py:34)) in [`group_by_reason()`](forecast_output/forecast_contradiction_digest.py:31). If a log entry is missing a "reason", it's grouped under "unknown".
*   **Print Statements:** The text formatting in [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38) (e.g., "🚨 Forecast Contradiction Digest...", "❗", "---") is hardcoded.
*   **Dictionary Keys:** String literals for expected keys in log entries: `"reason"`, `"trace_id_1"`, `"trace_id_2"`.

## 7. Coupling Points

*   **[`core.path_registry.PATHS`](core/path_registry.py):** Relies on this global dictionary for the log path.
*   **Contradiction Log File Format:** Tightly coupled to the JSON structure and specific keys (e.g., `reason`, `trace_id_1`, `trace_id_2`) of the log file generated by [`forecast_output/forecast_contradiction_detector.py`](forecast_output/forecast_contradiction_detector.py:1). Changes in the log format would break this module.
*   **Output Consumer (if any beyond console):** If the `print` statements in [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38) were intended to be machine-parsable, any change to that text format would be a breaking change for the consumer.

## 8. Existing Tests

*   The module includes an `if __name__ == "__main__":` block ([`forecast_output/forecast_contradiction_digest.py:50`](forecast_output/forecast_contradiction_digest.py:50)) that demonstrates loading and rendering the digest. This serves as a basic integration test.
*   Based on the file listing of the `tests/` directory, there does not appear to be a dedicated test file such as `test_forecast_contradiction_digest.py`.
*   **Assessment:** A dedicated unit test file should be created. Tests should cover:
    *   Log file not existing.
    *   Empty log file.
    *   Log file with malformed JSON entries.
    *   Correct loading and limiting of entries.
    *   Correct grouping by reason, including the "unknown" reason.
    *   Correct rendering of the digest for various scenarios (no logs, single entry, multiple entries, multiple reasons).
    *   Behavior with very large log files (if performance of `readlines()` becomes a concern, though this might be more of an integration/performance test).

## 9. Module Architecture and Flow

*   **Architecture:** A simple, single-file module with three public functions. No classes are defined.
*   **Key Components:**
    *   [`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19): Reads and parses the log file.
    *   [`group_by_reason()`](forecast_output/forecast_contradiction_digest.py:31): Organizes loaded logs.
    *   [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38): Prints the summary.
*   **Primary Data/Control Flow (when run as script):**
    1.  The `if __name__ == "__main__":` block is executed.
    2.  [`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19) is called (with `limit=25`).
        a.  Checks if `CONTRADICTION_LOG_PATH` exists. Returns `[]` if not.
        b.  Opens the log file, reads all lines, parses each line as JSON.
        c.  Returns the last `limit` parsed log entries. Handles exceptions by printing an error and returning `[]`.
    3.  The returned `logs` are passed to [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38).
        a.  If `logs` is empty, prints "No contradictions found." and returns.
        b.  Prints a header.
        c.  Calls [`group_by_reason()`](forecast_output/forecast_contradiction_digest.py:31) with `logs`.
            i.  Iterates through `logs`, appending each entry to a list within a `defaultdict` keyed by the entry's "reason" (or "unknown").
            ii. Returns the `defaultdict` as a regular `dict`.
        d.  Iterates through the `grouped` logs by `reason` and `items`.
            i.  Prints the reason and count of items.
            ii. Iterates through `items` for that reason, printing the `trace_id_1` and `trace_id_2`.
            iii. Prints a separator "---".

## 10. Naming Conventions

*   **Module Name:** [`forecast_contradiction_digest.py`](forecast_output/forecast_contradiction_digest.py:1) - Clear, PEP 8 compliant.
*   **Function Names:** [`load_contradiction_log()`](forecast_output/forecast_contradiction_digest.py:19), [`group_by_reason()`](forecast_output/forecast_contradiction_digest.py:31), [`render_digest()`](forecast_output/forecast_contradiction_digest.py:38) - Clear, action-oriented, PEP 8 compliant.
*   **Constants:** `CONTRADICTION_LOG_PATH` - Uppercase, clear.
*   **Variable Names:** `limit`, `lines`, `entry`, `grouped`, `reason`, `items` - Generally clear and follow PEP 8.
*   **Print Output:** Strings like "🚨 Forecast Contradiction Digest..." are user-facing and clear for a console digest.

Naming conventions are good and follow Python standards. No obvious AI assumption errors or major deviations from PEP 8 are apparent.