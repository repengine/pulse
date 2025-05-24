# Module Analysis: `forecast_output/forecast_contradiction_detector.py`

## 1. Module Intent/Purpose

The primary role of the [`forecast_contradiction_detector.py`](forecast_output/forecast_contradiction_detector.py:1) module is to identify and flag logical contradictions across a collection of foresight forecasts. It specifically looks for:
*   Paradoxes in symbolic states (e.g., conflicting "hope" and "despair" values).
*   Significant divergence in capital movement predictions for the same asset.
*   Divergence forks, where forecasts originating from the same parent forecast show different outcomes.
The module logs detected contradictions and updates the status of involved forecasts.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
*   It contains a main function [`detect_forecast_contradictions()`](forecast_output/forecast_contradiction_detector.py:36) and a helper [`ensure_log_dir()`](forecast_output/forecast_contradiction_detector.py:33).
*   It includes basic error handling for logging operations.
*   It has an example usage block under `if __name__ == "__main__":`.
*   Comments like "🧠 Enhancement 2" and "🧠 Escalate to Trust Engine" suggest integration points and potential areas for future development but don't necessarily indicate incompleteness for the current version's functionality.
*   No obvious TODOs or `pass` statements indicating unfinished sections.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Sophistication of Contradiction Rules:**
    *   The capital conflict rule `abs(delta) > 1000` ([`forecast_output/forecast_contradiction_detector.py:69`](forecast_output/forecast_contradiction_detector.py:69)) uses a fixed threshold. This might not be suitable for all assets or scenarios; a relative threshold or configurable value per asset type could be more robust.
    *   Symbolic contradiction for "hope" and "despair" (`hope_gap > 0.6 and despair_gap > 0.6` at [`forecast_output/forecast_contradiction_detector.py:79`](forecast_output/forecast_contradiction_detector.py:79)) also uses fixed thresholds.
    *   The module could be extended to detect more nuanced types of contradictions (e.g., temporal inconsistencies, contradictions based on external knowledge or constraints).
*   **Configuration:** Thresholds and specific keys for contradiction detection are hardcoded. Externalizing these to a configuration file would improve flexibility.
*   **Granularity of "origin_turn":** Grouping by `origin_turn` ([`forecast_output/forecast_contradiction_detector.py:53`](forecast_output/forecast_contradiction_detector.py:53)) is a primary method for comparing forecasts. If `origin_turn` is not consistently or accurately populated, detection quality may suffer. The default of `-1` for missing `origin_turn` means all such forecasts are grouped together, potentially leading to many comparisons.
*   **Performance for Large Datasets:** The nested loops for comparing forecasts within a group ([`forecast_output/forecast_contradiction_detector.py:56-57`](forecast_output/forecast_contradiction_detector.py:56-57)) result in O(N^2) complexity for each group. For very large numbers of forecasts per turn, this could be a bottleneck. More optimized algorithms (e.g., using spatial indexing for certain types of data, or more advanced data structures) might be needed.
*   **"Trust Engine" Integration:** The comment "🧠 Escalate to Trust Engine" ([`forecast_output/forecast_contradiction_detector.py:88`](forecast_output/forecast_contradiction_detector.py:88)) implies a more formal interaction that might not be fully implemented or is handled externally. The current action is to set `confidence_status` directly on the forecast dictionary.
*   **Learning Log Robustness:** The `log_learning_event` ([`forecast_output/forecast_contradiction_detector.py:95`](forecast_output/forecast_contradiction_detector.py:95)) is within a `try-except Exception` block that prints an error but doesn't re-raise or have a more specific handling, which might obscure issues.

## 4. Connections & Dependencies

*   **Direct Imports from Other Project Modules:**
    *   [`core.path_registry.PATHS`](core/path_registry.py) ([`forecast_output/forecast_contradiction_detector.py:27`](forecast_output/forecast_contradiction_detector.py:27)): Used to get the path for the contradiction log.
    *   [`core.pulse_learning_log.log_learning_event`](core/pulse_learning_log.py) ([`forecast_output/forecast_contradiction_detector.py:29`](forecast_output/forecast_contradiction_detector.py:29)): Used to log contradiction detection events for learning purposes.
*   **External Library Dependencies:**
    *   `json`: For writing log entries.
    *   `os`: For directory creation (`os.makedirs`, `os.path.dirname`).
    *   `typing` (`List`, `Dict`, `Tuple`): For type hinting.
    *   `datetime`: For timestamping log entries.
    *   `collections.defaultdict`: For grouping forecasts.
*   **Interaction with Other Modules via Shared Data:**
    *   Consumes a list of forecast dictionaries. The structure of these dictionaries is critical (e.g., expecting keys like `origin_turn`, `trace_id`, `forecast`, `end_capital`, `symbolic_change`, `parent_id`).
    *   Modifies input forecast dictionaries by adding/updating the `confidence_status` key ([`forecast_output/forecast_contradiction_detector.py:92`](forecast_output/forecast_contradiction_detector.py:92)). This side effect means consuming modules will see this change.
*   **Input/Output Files:**
    *   **Output Log:** Writes to a JSONL file specified by `CONTRADICTION_LOG_PATH` (default: [`logs/forecast_contradiction_log.jsonl`](logs/forecast_contradiction_log.jsonl)). Each line is a JSON object detailing a detected contradiction.

## 5. Function and Class Example Usages

### Function: [`ensure_log_dir(path: str)`](forecast_output/forecast_contradiction_detector.py:33)
**Purpose:** Ensures that the directory for the given log file path exists, creating it if necessary.
**Example Usage:**
```python
ensure_log_dir("logs/forecast_contradiction_log.jsonl")
# This would create the 'logs' directory if it doesn't exist.
```

### Function: [`detect_forecast_contradictions(forecasts: List[Dict]) -> List[Tuple[str, str, str]]`](forecast_output/forecast_contradiction_detector.py:36)
**Purpose:** Analyzes a list of forecast dictionaries to find contradictions based on capital divergence, symbolic paradoxes, and divergence forks. Logs findings and updates forecast statuses.
**Example Usage:** (Adapted from the module's `if __name__ == "__main__":` block)
```python
f1 = {
    "trace_id": "F001",
    "origin_turn": 5,
    "forecast": {
        "end_capital": {"nvda": 10000},
        "symbolic_change": {"hope": 0.8, "despair": 0.1}
    },
    "parent_id": "P000"
}
f2 = {
    "trace_id": "F002",
    "origin_turn": 5,
    "forecast": {
        "end_capital": {"nvda": 8700}, # Capital conflict: 10000 vs 8700 (delta > 1000)
        "symbolic_change": {"hope": 0.1, "despair": 0.9} # Symbolic conflict: hope/despair diverge > 0.6
    },
    "parent_id": "P000" # Divergence fork
}
f3 = { # No conflict with f1 or f2 initially
    "trace_id": "F003",
    "origin_turn": 5,
    "forecast": {
        "end_capital": {"aapl": 5000},
        "symbolic_change": {"hope": 0.6, "despair": 0.3}
    },
    "parent_id": "P001"
}

forecast_list = [f1, f2, f3]
contradictions_found = detect_forecast_contradictions(forecast_list)

for c_tuple in contradictions_found:
    print(f"❗ Contradiction: Trace1={c_tuple[0]}, Trace2={c_tuple[1]}, Reason='{c_tuple[2]}'")

# Check updated status
# print(f1.get("confidence_status")) # Expected: "❌ Contradictory"
# print(f2.get("confidence_status")) # Expected: "❌ Contradictory"
# print(f3.get("confidence_status")) # Expected: None or original status
```

## 6. Hardcoding Issues

*   **Log Path Default:** `CONTRADICTION_LOG_PATH` defaults to `"logs/forecast_contradiction_log.jsonl"` ([`forecast_output/forecast_contradiction_detector.py:31`](forecast_output/forecast_contradiction_detector.py:31)) if not found in `PATHS`.
*   **Default `origin_turn`:** `f.get("origin_turn", -1)` ([`forecast_output/forecast_contradiction_detector.py:53`](forecast_output/forecast_contradiction_detector.py:53)). Using `-1` as a default for a missing turn might lead to unintended grouping.
*   **Default `trace_id`:** `f1.get("trace_id", f"f_{i}")` ([`forecast_output/forecast_contradiction_detector.py:60`](forecast_output/forecast_contradiction_detector.py:60)). Generating default trace_ids like `f_0`, `f_1` might be okay for internal processing but could be confusing if these IDs propagate.
*   **Capital Conflict Threshold:** `abs(delta) > 1000` ([`forecast_output/forecast_contradiction_detector.py:69`](forecast_output/forecast_contradiction_detector.py:69)). This is a magic number.
*   **Symbolic Conflict Thresholds:** `hope_gap > 0.6` and `despair_gap > 0.6` ([`forecast_output/forecast_contradiction_detector.py:79`](forecast_output/forecast_contradiction_detector.py:79)). These are magic numbers.
*   **Default Symbolic Values:** `sym1.get("hope", 0.5)` ([`forecast_output/forecast_contradiction_detector.py:77`](forecast_output/forecast_contradiction_detector.py:77)). Defaulting to `0.5` for missing hope/despair values is an assumption.
*   **Status String:** `"❌ Contradictory"` ([`forecast_output/forecast_contradiction_detector.py:92`](forecast_output/forecast_contradiction_detector.py:92)).
*   **Log Metadata:** Source and version strings in log output ([`forecast_output/forecast_contradiction_detector.py:113-114`](forecast_output/forecast_contradiction_detector.py:113-114)). The version `v0.019.0` is hardcoded.
*   **Dictionary Keys:** Numerous string literals for dictionary keys (e.g., `"forecast"`, `"end_capital"`, `"symbolic_change"`, `"hope"`, `"despair"`, `"parent_id"`, `"confidence_status"`).

## 7. Coupling Points

*   **[`core.path_registry.PATHS`](core/path_registry.py):** Relies on this global dictionary for the log path. Changes to `PATHS` or the `CONTRADICTION_LOG_PATH` key could affect behavior.
*   **[`core.pulse_learning_log.log_learning_event`](core/pulse_learning_log.py):** Coupled to the API and expected behavior of this logging function.
*   **Forecast Dictionary Structure:** Tightly coupled to the specific keys and expected data types within the forecast dictionaries it processes. This is the most significant coupling.
*   **Implicit Contract with Consumers:** Modules consuming the output forecasts expect the `confidence_status` field to be updated for contradictory items.
*   **Log File Consumers:** Any system or process that reads the `forecast_contradiction_log.jsonl` is coupled to its format.

## 8. Existing Tests

*   The module includes an `if __name__ == "__main__":` block ([`forecast_output/forecast_contradiction_detector.py:123`](forecast_output/forecast_contradiction_detector.py:123)) with a basic example test case. This is good for quick validation but not a substitute for a formal test suite.
*   Based on the file listing of the `tests/` directory, there does not appear to be a dedicated test file such as `test_forecast_contradiction_detector.py`.
*   **Assessment:** A dedicated unit test file should be created. Tests should cover:
    *   No forecasts provided.
    *   Forecasts with no contradictions.
    *   Each type of contradiction individually (capital, symbolic, divergence fork).
    *   Multiple contradictions.
    *   Cases with missing keys in forecast dictionaries (e.g., missing `origin_turn`, `trace_id`, `forecast` sub-dictionary, `end_capital`, `symbolic_change`, `parent_id`).
    *   Edge cases for thresholds (e.g., delta exactly 1000).
    *   Correct logging to both the contradiction log and the learning log.
    *   Correct update of `confidence_status`.

## 9. Module Architecture and Flow

*   **Architecture:** Single file module with two functions.
*   **Key Components:**
    *   [`ensure_log_dir()`](forecast_output/forecast_contradiction_detector.py:33): Utility to create log directory.
    *   [`detect_forecast_contradictions()`](forecast_output/forecast_contradiction_detector.py:36): Core logic.
*   **Primary Data/Control Flow:**
    1.  [`detect_forecast_contradictions()`](forecast_output/forecast_contradiction_detector.py:36) is called with a list of `forecasts`.
    2.  Log directory is ensured using [`ensure_log_dir()`](forecast_output/forecast_contradiction_detector.py:33).
    3.  Forecasts are grouped by `origin_turn` into a `defaultdict`.
    4.  Iterate through each group of forecasts:
        a.  Nested loops compare every pair of forecasts (`f1`, `f2`) within the group.
        b.  **Capital Contradiction Check:**
            i.  Extract `end_capital` for `f1` and `f2`.
            ii. For each common `asset`, if the absolute difference in predicted capital is `> 1000`, a contradiction is recorded.
        c.  **Symbolic Contradiction Check:**
            i.  Extract `symbolic_change` (hope, despair) for `f1` and `f2`.
            ii. If both `hope_gap` and `despair_gap` are `> 0.6`, a "Symbolic paradox" is recorded.
        d.  **Divergence Fork Check:**
            i.  If `f1` and `f2` share the same `parent_id` but have different `trace_id`s, a "Divergence fork" is recorded.
    5.  For each identified contradiction pair:
        a.  The `confidence_status` of both involved forecasts in the input list is updated to `"❌ Contradictory"`.
        b.  A learning event is logged via [`log_learning_event()`](core/pulse_learning_log.py:29).
    6.  All recorded contradictions are written to the `CONTRADICTION_LOG_PATH` as JSON lines.
    7.  The list of contradiction tuples `(id1, id2, reason)` is returned.

## 10. Naming Conventions

*   **Module Name:** [`forecast_contradiction_detector.py`](forecast_output/forecast_contradiction_detector.py:1) - Clear, PEP 8 compliant.
*   **Function Names:** [`ensure_log_dir()`](forecast_output/forecast_contradiction_detector.py:33), [`detect_forecast_contradictions()`](forecast_output/forecast_contradiction_detector.py:36) - Clear, action-oriented, PEP 8 compliant.
*   **Constants:** `CONTRADICTION_LOG_PATH` - Uppercase, clear.
*   **Variable Names:** `forecasts`, `contradictions`, `contradiction_pairs`, `grouped`, `turn`, `group`, `f1`, `f2`, `id1`, `id2`, `end1`, `end2`, `asset`, `delta`, `sym1`, `sym2`, `hope_gap`, `despair_gap` - Generally clear and follow PEP 8. `f1`, `f2` are common iterators.
*   **Comments:** "🧠 Enhancement 2", "🧠 Escalate to Trust Engine" - These seem like internal development tags/notes.
*   **Log Messages/Reasons:** Strings like `"Conflict on {asset} (${delta:.2f})"`, `"Symbolic paradox: Hope vs Despair divergence"`, `"Divergence fork from same parent"` are descriptive.

Naming conventions are generally good. The "🧠" comments are unusual for production code but might be part of a specific development methodology within this project.