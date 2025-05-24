# Module Analysis: `memory/variable_performance_tracker.py`

## 1. Module Intent/Purpose

The primary role of the [`memory/variable_performance_tracker.py`](memory/variable_performance_tracker.py:) module is to track, score, and analyze the impact of individual variables on simulation outcomes. It logs contributions of variables to forecasts, aggregates trust and fragility scores, detects drift, and exports this data for audit, dashboarding, and meta-learning.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope. It includes functionality for logging, scoring, ranking, exporting, and drift detection. The presence of an `if __name__ == "__main__":` block with example usage ([`memory/variable_performance_tracker.py:139-146`](memory/variable_performance_tracker.py:139-146)) suggests it has been tested at a basic level. No obvious placeholders (e.g., `TODO`, `FIXME`) are visible in the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Drift/Volatility Analysis:** The docstring mentions "Drift detection and symbolic volatility analysis" ([`memory/variable_performance_tracker.py:10`](memory/variable_performance_tracker.py:10)), but the current [`detect_variable_drift()`](memory/variable_performance_tracker.py:116-125) method is relatively simple, based on fragility and certified ratio thresholds. More sophisticated symbolic volatility analysis is not explicitly implemented.
*   **Meta-Learning Integration:** While the module supports export for "meta-learning use" ([`memory/variable_performance_tracker.py:11`](memory/variable_performance_tracker.py:11)), the actual feedback loop or integration with a meta-learning system is not part of this module. This would likely be an external component that consumes the exported data.
*   **Granular Contribution Logic:** The [`log_variable_contribution()`](memory/variable_performance_tracker.py:44-68) method logs the presence and value of a variable in the input state of a forecast. It doesn't seem to perform a deeper analysis of *how* or *to what extent* each variable specifically influenced the forecast's metrics (confidence, fragility, etc.) beyond correlation.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.path_registry.PATHS`](core/path_registry.py:) ([`memory/variable_performance_tracker.py:20`](memory/variable_performance_tracker.py:20)): Used to get paths for log and export files.
*   [`core.variable_registry.VARIABLE_REGISTRY`](core/variable_registry.py:) ([`memory/variable_performance_tracker.py:21`](memory/variable_performance_tracker.py:21)): Used to check if a variable is known before logging its contribution.
*   [`core.pulse_learning_log.log_learning_event()`](core/pulse_learning_log.py:) ([`memory/variable_performance_tracker.py:22`](memory/variable_performance_tracker.py:22)): Used in the [`update_performance()`](memory/variable_performance_tracker.py:127-136) method.

### External Library Dependencies:
*   `os`: Used for path manipulation (e.g., [`os.path.dirname()`](memory/variable_performance_tracker.py:30), [`os.makedirs()`](memory/variable_performance_tracker.py:30)).
*   `json`: Used for serializing and deserializing log data and export summaries ([`memory/variable_performance_tracker.py:17`](memory/variable_performance_tracker.py:17), [`memory/variable_performance_tracker.py:67`](memory/variable_performance_tracker.py:67), [`memory/variable_performance_tracker.py:111`](memory/variable_performance_tracker.py:111)).
*   `typing` (`Dict`, `List`, `Optional`): Used for type hinting ([`memory/variable_performance_tracker.py:18`](memory/variable_performance_tracker.py:18)).
*   `datetime` (from `datetime`): Used for timestamping records ([`memory/variable_performance_tracker.py:19`](memory/variable_performance_tracker.py:19), [`memory/variable_performance_tracker.py:52`](memory/variable_performance_tracker.py:52), [`memory/variable_performance_tracker.py:135`](memory/variable_performance_tracker.py:135)).

### Interaction with Other Modules via Shared Data:
*   **ForecastMemory:** The [`aggregate_from_memory()`](memory/variable_performance_tracker.py:32-42) method can take a `ForecastMemory` instance (or a list of forecasts) to process historical forecast data. This implies an interaction pattern where this tracker consumes data produced or managed by a memory module.
*   **Log Files:**
    *   Reads from/Appends to: `logs/variable_score_log.jsonl` (configurable via `PATHS`). This file stores individual variable contribution records.
    *   Writes to: `logs/variable_score_summary.json` (configurable via `PATHS`). This file stores aggregated scores.
*   **Learning Log:** The [`update_performance()`](memory/variable_performance_tracker.py:127-136) method logs events to the pulse learning log, presumably consumed by other parts of the system.

### Input/Output Files:
*   **Input (Implicit):** Potentially `ForecastMemory` data structures if [`aggregate_from_memory()`](memory/variable_performance_tracker.py:32-42) is used.
*   **Output/Log:**
    *   [`LOG_PATH`](memory/variable_performance_tracker.py:24) (default: `logs/variable_score_log.jsonl`): A JSONL file where each line is a JSON object representing a variable's contribution to a specific forecast.
    *   [`SCORE_EXPORT_PATH`](memory/variable_performance_tracker.py:25) (default: `logs/variable_score_summary.json`): A JSON file containing an aggregated summary of scores for all tracked variables.

## 5. Function and Class Example Usages

The module defines one class, [`VariablePerformanceTracker`](memory/variable_performance_tracker.py:27-136).

**Class: `VariablePerformanceTracker`**

*   **Initialization:**
    ```python
    tracker = VariablePerformanceTracker()
    ```
*   **Logging Variable Contributions:**
    ```python
    dummy_forecast = {"trace_id": "vtest1", "confidence": 0.78, "fragility": 0.22, "certified": True, "arc_label": "Hope", "symbolic_tag": "hope"}
    dummy_state = {"hope": 0.6, "rage": 0.4, "vix_level": 0.28, "crypto_instability": 0.6}
    tracker.log_variable_contribution(dummy_forecast, dummy_state)
    ```
    This logs the contribution of "hope", "rage", "vix_level", and "crypto_instability" from `dummy_state` in the context of `dummy_forecast`.
*   **Aggregating from Memory (Conceptual):**
    ```python
    # Assuming 'forecast_memory_instance' is an instance of ForecastMemory
    # tracker.aggregate_from_memory(forecast_memory_instance)
    ```
*   **Scoring and Ranking:**
    ```python
    scores = tracker.score_variable_effectiveness()
    # print(scores)
    ranked_by_confidence = tracker.rank_variables_by_impact(key="avg_confidence")
    # print("Ranked by confidence:", ranked_by_confidence)
    ```
*   **Detecting Drift:**
    ```python
    drift_prone_vars = tracker.detect_variable_drift(threshold=0.3)
    # print("Drift-prone variables:", drift_prone_vars)
    ```
*   **Exporting Scores:**
    ```python
    tracker.export_variable_scores(path="custom_export_path.json")
    # Exports to default if path is None
    ```
*   **Updating Performance (Logging Event):**
    ```python
    tracker.update_performance(var_name="hope", new_score={"avg_confidence": 0.8, "notes": "improved after tuning"})
    ```

## 6. Hardcoding Issues

*   **Default Log Paths:**
    *   `LOG_PATH` defaults to `"logs/variable_score_log.jsonl"` ([`memory/variable_performance_tracker.py:24`](memory/variable_performance_tracker.py:24)).
    *   `SCORE_EXPORT_PATH` defaults to `"logs/variable_score_summary.json"` ([`memory/variable_performance_tracker.py:25`](memory/variable_performance_tracker.py:25)).
    While these are fetched via `PATHS.get`, the default values themselves are hardcoded strings within the `get` call. This is a common and generally acceptable pattern if `PATHS` provides sufficient configuration flexibility.
*   **Drift Detection Threshold:** The `threshold` in [`detect_variable_drift()`](memory/variable_performance_tracker.py:116-125) defaults to `0.25`. This could be made configurable if different contexts require different sensitivities.
*   **Keys for Scoring and Ranking:** String keys like `"confidence"`, `"fragility"`, `"certified"`, `"arc_label"`, `"symbolic_tag"`, `"alignment_score"`, `"confidence_status"` are used to access forecast dictionary attributes ([`memory/variable_performance_tracker.py:55-62`](memory/variable_performance_tracker.py:55-62), [`memory/variable_performance_tracker.py:85-88`](memory/variable_performance_tracker.py:85-88)). These are inherent to the expected structure of the `forecast` objects.
*   **Event Type String:** `"memory_update"` and `"variable_performance_update"` are hardcoded in [`update_performance()`](memory/variable_performance_tracker.py:131-132).

## 7. Coupling Points

*   **`core.path_registry`:** Tightly coupled for resolving log and export file paths. Changes to path management strategy could impact this module.
*   **`core.variable_registry`:** Coupled for validating variable existence. Changes to how variables are registered or identified would affect this module.
*   **`core.pulse_learning_log`:** Coupled for logging performance update events.
*   **Forecast Data Structure:** The module heavily relies on a specific dictionary structure for `forecast` objects (e.g., expecting keys like `trace_id`, `confidence`, `fragility`, `input_state`). Changes to this structure in modules producing forecasts would break this tracker.
*   **`ForecastMemory` (Optional):** If [`aggregate_from_memory()`](memory/variable_performance_tracker.py:32-42) is used, it expects `ForecastMemory` instances to have a `_memory` attribute or be iterable lists of forecast dicts.

## 8. Existing Tests

*   No dedicated test file (e.g., `tests/test_variable_performance_tracker.py`) was found during the analysis.
*   The module contains an `if __name__ == "__main__":` block ([`memory/variable_performance_tracker.py:139-146`](memory/variable_performance_tracker.py:139-146)) which provides basic example usage and can be considered a form of rudimentary, inline testing or demonstration. This block exercises [`log_variable_contribution()`](memory/variable_performance_tracker.py:44-68), [`rank_variables_by_impact()`](memory/variable_performance_tracker.py:102-104), [`detect_variable_drift()`](memory/variable_performance_tracker.py:116-125), and [`export_variable_scores()`](memory/variable_performance_tracker.py:106-115).
*   **Gaps:** Lack of formal unit tests means edge cases, error handling (e.g., for file I/O, malformed inputs), and specific calculations within scoring logic are not systematically verified.

## 9. Module Architecture and Flow

*   **Class-based:** The module is structured around the [`VariablePerformanceTracker`](memory/variable_performance_tracker.py:27-136) class.
*   **State:** The class instance maintains a list of `records` in memory ([`memory/variable_performance_tracker.py:29`](memory/variable_performance_tracker.py:29)), which are dictionaries representing individual variable contributions. These records are also appended to a JSONL log file.
*   **Primary Flow:**
    1.  Initialize `VariablePerformanceTracker`.
    2.  Log variable contributions from individual forecasts (and their states) using [`log_variable_contribution()`](memory/variable_performance_tracker.py:44-68). This appends to `self.records` and writes to `LOG_PATH`.
    3.  Optionally, populate records from a `ForecastMemory` instance using [`aggregate_from_memory()`](memory/variable_performance_tracker.py:32-42).
    4.  At any point, scores can be calculated on the current `self.records` using [`score_variable_effectiveness()`](memory/variable_performance_tracker.py:69-100). This method aggregates data like count, average confidence, average fragility, etc., per variable.
    5.  Variables can be ranked based on these scores using [`rank_variables_by_impact()`](memory/variable_performance_tracker.py:102-104).
    6.  Drift-prone variables can be identified using [`detect_variable_drift()`](memory/variable_performance_tracker.py:116-125).
    7.  The aggregated scores can be exported to a JSON file using [`export_variable_scores()`](memory/variable_performance_tracker.py:106-115).
    8.  An [`update_performance()`](memory/variable_performance_tracker.py:127-136) method exists to log an event, but it doesn't directly modify the internal scores; its primary purpose seems to be signaling an update for external systems via the learning log.

## 10. Naming Conventions

*   **Class Name:** `VariablePerformanceTracker` is descriptive and follows PascalCase, which is standard for Python classes.
*   **Method Names:** Generally follow snake_case (e.g., [`log_variable_contribution()`](memory/variable_performance_tracker.py:44-68), [`score_variable_effectiveness()`](memory/variable_performance_tracker.py:69-100)). They are descriptive of their actions.
*   **Variable Names:** Mostly snake_case (e.g., `export_path`, `avg_confidence`). Some internal dictionary keys within records/scores are also snake_case.
*   **Constants:** `LOG_PATH`, `SCORE_EXPORT_PATH` are uppercase with underscores, which is conventional for constants.
*   **PEP 8:** The module generally adheres to PEP 8 styling.
*   **Potential AI Assumption Errors/Deviations:** The naming seems consistent and human-readable. No obvious AI-like or overly generic naming patterns were observed. The author tag "Pulse v0.29" ([`memory/variable_performance_tracker.py:13`](memory/variable_performance_tracker.py:13)) suggests it might be part of a larger system with established conventions.

---
Generated by Roo-Docs-Writer