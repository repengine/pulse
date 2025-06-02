# Module Analysis: `memory/contradiction_resolution_tracker.py`

## 1. Module Intent/Purpose

The primary role of the [`contradiction_resolution_tracker.py`](memory/contradiction_resolution_tracker.py) module is to track the status of detected forecast contradictions. It determines whether these contradictions are later resolved, reversed, or if they persist over time. This tracking is crucial for symbolic conflict auditing, validating rules based on memory, and adjusting trust scores within the system.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined scope. It contains functions to:
*   Compare symbolic outcomes of two forecasts.
*   Track the resolution status between two forecasts by their trace IDs.
*   Log the resolution outcome to a file.
*   Summarize resolution outcomes from the log file.

There are no obvious placeholders, `TODO` comments, or unfinished sections within the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility:** While functional, the comparison logic in [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19) is based on specific dictionary keys (`"arc_label"`, `"symbolic_tag"`). Future enhancements might involve more sophisticated or configurable comparison strategies.
*   **Error Handling:** The [`summarize_resolution_outcomes()`](memory/contradiction_resolution_tracker.py:53) function has a general `except Exception:` block ([`memory/contradiction_resolution_tracker.py:62`](memory/contradiction_resolution_tracker.py:62)), which could be made more specific to handle potential `json.JSONDecodeError` or `KeyError` more gracefully.
*   **Integration with Resolution Mechanisms:** The module tracks resolutions but doesn't actively participate in the resolution process itself. Logical next steps could involve tighter integration with modules responsible for *triggering* or *enacting* contradiction resolutions.
*   **Advanced Analytics:** The current summary provides basic counts. More advanced analytics on resolution patterns, timelines, or types of contradictions could be a future extension.

There are no explicit signs that development started on a planned path and then deviated or stopped short within this specific module's code.

## 4. Connections & Dependencies

### Direct Imports from other project modules:
*   [`core.path_registry.PATHS`](core/path_registry.py:13): Used to get the path for the contradiction resolution log file.
*   [`analytics.forecast_memory.ForecastMemory`](memory/forecast_memory.py:14): Used to retrieve forecast data by trace ID.

### External Library Dependencies:
*   `os`: Used for path manipulation (e.g., [`os.path.dirname()`](memory/contradiction_resolution_tracker.py:44), [`os.makedirs()`](memory/contradiction_resolution_tracker.py:44), [`os.path.exists()`](memory/contradiction_resolution_tracker.py:54)).
*   `json`: Used for serializing log entries to JSON format ([`json.dumps()`](memory/contradiction_resolution_tracker.py:46)) and deserializing them ([`json.loads()`](memory/contradiction_resolution_tracker.py:60)).
*   `typing`: Used for type hinting (`List`, `Dict`, `Tuple`, `Optional`).

### Interaction with other modules via shared data:
*   Reads forecast data from an instance of [`ForecastMemory`](memory/forecast_memory.py:14).
*   Writes resolution outcomes to a JSONL log file, the path for which is retrieved via [`PATHS.get("CONTRADICTION_RESOLUTION_LOG", ...)`](memory/contradiction_resolution_tracker.py:16).

### Input/Output Files:
*   **Output:** [`logs/contradiction_resolution_log.jsonl`](logs/contradiction_resolution_log.jsonl) (default path). This file stores JSON line entries, each representing a resolution outcome between two trace IDs.
*   **Input (for summarization):** Reads from the same [`logs/contradiction_resolution_log.jsonl`](logs/contradiction_resolution_log.jsonl) file.

## 5. Function and Class Example Usages

The module includes a `if __name__ == "__main__":` block ([`memory/contradiction_resolution_tracker.py:66-70`](memory/contradiction_resolution_tracker.py:66-70)) that demonstrates basic usage:

```python
if __name__ == "__main__":
    mem = ForecastMemory()  # Assuming ForecastMemory is populated elsewhere or mockable
    # Example: Track resolution between forecasts identified by "T1" and "T2"
    res = track_resolution("T1", "T2", memory=mem)
    print(f"Resolution Status: {res}")
    # Example: Summarize all logged resolution outcomes
    print("Summary:", summarize_resolution_outcomes())
```

*   **[`compare_symbolic_outcomes(fc1: Dict, fc2: Dict) -> str`](memory/contradiction_resolution_tracker.py:19):**
    *   Intended to be called with two dictionary-like objects representing forecasts.
    *   Compares their `"arc_label"` and `"symbolic_tag"` to determine if they are resolved, still contradictory, or partially aligned.
*   **[`track_resolution(trace_id_1: str, trace_id_2: str, memory: Optional[ForecastMemory] = None) -> Optional[str]`](memory/contradiction_resolution_tracker.py:32):**
    *   Takes two trace IDs and an optional [`ForecastMemory`](memory/forecast_memory.py:14) instance.
    *   Retrieves the corresponding forecasts, compares them using [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19), logs the result, and returns the outcome status.
*   **[`log_resolution_outcome(tid1: str, tid2: str, status: str)`](memory/contradiction_resolution_tracker.py:43):**
    *   Appends a JSON entry to the resolution log file with the two trace IDs and their resolution status.
*   **[`summarize_resolution_outcomes(path: str = str(RESOLUTION_LOG)) -> Dict[str, int]`](memory/contradiction_resolution_tracker.py:53):**
    *   Reads the resolution log file and returns a dictionary counting the occurrences of each resolution status.

## 6. Hardcoding Issues

*   **Default Log File Path:** The `RESOLUTION_LOG` variable defaults to `"logs/contradiction_resolution_log.jsonl"` if not found in `PATHS` ([`memory/contradiction_resolution_tracker.py:16`](memory/contradiction_resolution_tracker.py:16)).
*   **Status Strings:** The specific strings for resolution outcomes are hardcoded within [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19) (e.g., `"✅ Resolved"`, `"↔️ Still Contradictory"`, `"🌀 Partial Alignment"`) and also used as keys in the `counts` dictionary in [`summarize_resolution_outcomes()`](memory/contradiction_resolution_tracker.py:56).
*   **Dictionary Keys for Comparison:** The keys `"arc_label"` and `"symbolic_tag"` used for comparison in [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19) are hardcoded ([`memory/contradiction_resolution_tracker.py:20-23`](memory/contradiction_resolution_tracker.py:20-23)).
*   **Default Values for Missing Keys:** Default values like `"unknown"` and `"none"` are used if `"arc_label"` or `"symbolic_tag"` are missing from forecast dictionaries ([`memory/contradiction_resolution_tracker.py:20-23`](memory/contradiction_resolution_tracker.py:20-23)).
*   **Example Trace IDs:** The `if __name__ == "__main__":` block uses hardcoded example trace IDs `"T1"` and `"T2"` ([`memory/contradiction_resolution_tracker.py:68`](memory/contradiction_resolution_tracker.py:68)).

## 7. Coupling Points

*   **[`ForecastMemory`](memory/forecast_memory.py:14):** The module is tightly coupled with the [`ForecastMemory`](memory/forecast_memory.py:14) class to retrieve forecast data. Changes to how forecasts are stored or accessed in [`ForecastMemory`](memory/forecast_memory.py:14) could impact this module.
*   **[`core.path_registry`](core/path_registry.py:13):** Dependency on `PATHS` for the log file path introduces coupling to the path management system.
*   **Log File Format:** The module defines and relies on a specific JSONL format for its log file. Any external process consuming this log file would be coupled to this format.
*   **Forecast Structure:** The [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19) function expects forecasts to be dictionaries containing `"arc_label"` and `"symbolic_tag"` keys.

## 8. Existing Tests

Based on the file listing from the `tests/` directory, there is no dedicated test file specifically named `test_contradiction_resolution_tracker.py` or similar.
It's possible that:
*   Tests for this module are integrated within a broader test suite for the `memory` package (e.g., in a `tests/test_memory.py` if it existed, or within [`tests/test_forecast_memory.py`](tests/test_forecast_memory.py) if relevant functionality is tested there).
*   Functionality is covered by integration tests that involve contradiction detection and resolution processes.
*   Unit tests for this specific module are currently missing.

Without examining the content of other test files, the exact state and coverage of tests for this module cannot be definitively ascertained from the file list alone. However, the absence of a dedicated file suggests a potential gap in focused unit testing for this module.

## 9. Module Architecture and Flow

The module's architecture is straightforward and function-based:

1.  **Input:** Two trace IDs identifying forecasts that were previously deemed contradictory.
2.  **Data Retrieval:** The [`track_resolution()`](memory/contradiction_resolution_tracker.py:32) function fetches the full forecast objects from an instance of [`ForecastMemory`](memory/forecast_memory.py:14) using these trace IDs.
3.  **Comparison:** The [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19) function is called with the two forecast objects. It compares their respective `"arc_label"` and `"symbolic_tag"` attributes.
    *   If both `arc_label` and `symbolic_tag` match, the status is "✅ Resolved".
    *   If both `arc_label` and `symbolic_tag` differ, the status is "↔️ Still Contradictory".
    *   Otherwise (one matches, one differs), the status is "🌀 Partial Alignment".
4.  **Logging:** The outcome status, along with the original trace IDs, is logged as a JSON line entry into the file specified by `RESOLUTION_LOG` (default: [`logs/contradiction_resolution_log.jsonl`](logs/contradiction_resolution_log.jsonl)) by the [`log_resolution_outcome()`](memory/contradiction_resolution_tracker.py:43) function. The directory for the log file is created if it doesn't exist.
5.  **Summarization (Optional):** The [`summarize_resolution_outcomes()`](memory/contradiction_resolution_tracker.py:53) function can be called to read the log file, parse each JSON line, and count the occurrences of each resolution status, returning a summary dictionary.

The primary control flow involves retrieving data, comparing it based on predefined symbolic attributes, and logging the result.

## 10. Naming Conventions

*   **Module Name:** [`contradiction_resolution_tracker.py`](memory/contradiction_resolution_tracker.py) is descriptive and follows Python's snake_case convention.
*   **Function Names:** [`compare_symbolic_outcomes()`](memory/contradiction_resolution_tracker.py:19), [`track_resolution()`](memory/contradiction_resolution_tracker.py:32), [`log_resolution_outcome()`](memory/contradiction_resolution_tracker.py:43), [`summarize_resolution_outcomes()`](memory/contradiction_resolution_tracker.py:53) are clear, action-oriented, and use snake_case.
*   **Constant Variables:** `RESOLUTION_LOG` ([`memory/contradiction_resolution_tracker.py:16`](memory/contradiction_resolution_tracker.py:16)) is in `UPPER_SNAKE_CASE`, which is standard for constants.
*   **Local Variables:**
    *   `fc1`, `fc2` ([`memory/contradiction_resolution_tracker.py:19`](memory/contradiction_resolution_tracker.py:19)): Short, but their scope is limited to the `compare_symbolic_outcomes` function where their meaning (forecast 1, forecast 2) is clear.
    *   `arc1`, `arc2`, `tag1`, `tag2` ([`memory/contradiction_resolution_tracker.py:19`](memory/contradiction_resolution_tracker.py:19)): Similarly short but clear within their small functional scope.
    *   `tid1`, `tid2` (in [`log_resolution_outcome()`](memory/contradiction_resolution_tracker.py:43)): Abbreviation for "trace ID 1" and "trace ID 2", clear in context.
    *   Other variables like `memory`, `f1`, `f2`, `outcome`, `path`, `counts`, `f`, `line`, `entry` are generally descriptive.
*   **String Literals:** The status strings (e.g., `"✅ Resolved"`) use emojis, which might be an intentional choice for readability in logs or UI, but could present issues if simple ASCII is required elsewhere.

Overall, the naming conventions are largely consistent with PEP 8 and project standards. The short variable names are used in very localized contexts, minimizing potential confusion. There are no obvious AI assumption errors in naming.