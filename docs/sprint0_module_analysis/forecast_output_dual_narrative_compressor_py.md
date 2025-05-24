# Module Analysis: `forecast_output/dual_narrative_compressor.py`

## 1. Module Intent/Purpose

The [`dual_narrative_compressor.py`](../forecast_output/dual_narrative_compressor.py:1) module is designed to identify symbolic narrative forks (e.g., "Hope" vs. "Collapse") within a list of forecasts. It then compresses these diverging narratives into "Scenario A / Scenario B" summaries, presumably for easier operator understanding. The module also includes functionality to export these dual scenarios to a JSON file.

## 2. Operational Status/Completeness

The module appears to be largely functional for its described purpose:
*   It can group forecasts by their "arc_label".
*   It can score forecasts based on "alignment_score" and "confidence".
*   It can take a list of forecasts and two opposing arc labels, then select the top-scoring forecast from each arc to form a "Scenario A / Scenario B" pair.
*   It uses an external function [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1) to find pairs of opposing arcs and then generates these dual scenarios for all such pairs.
*   It provides a function to export the generated scenarios to a JSON file.
*   A basic test function `_test_dual_narrative_compressor` is included and called in the `if __name__ == "__main__":` block, though its assertions are minimal and it relies on `detect_symbolic_opposition` which is not mocked or controlled within this test.

No obvious `TODO` or `FIXME` comments indicate unfinished core logic for the compression and export.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Robustness of `detect_symbolic_opposition`:** The effectiveness of this module heavily relies on the quality and correctness of the `pairs` returned by [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1). If that function doesn't accurately identify meaningful opposing arcs, the "dual scenarios" might not be useful. The current test in this module doesn't validate the behavior of `detect_symbolic_opposition`.
*   **Handling of No Opposing Arcs:** If [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1) returns an empty list of pairs, [`generate_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:55) will correctly return an empty list. This is handled, but the operational implications (e.g., how an operator is informed that no dual narratives were found) are outside this module's scope.
*   **Forecast Data Structure Dependency:** The module assumes forecasts are dictionaries containing keys like `"arc_label"`, `"alignment_score"`, and `"confidence"`. Changes to this structure could break the module. Default values (e.g., 0 for scores) provide some robustness.
*   **Tie-Breaking in Scoring:** The [`score_forecast`](../forecast_output/dual_narrative_compressor.py:31) function sums `alignment_score` and `confidence`. If multiple forecasts within the same arc have the same top score, the one appearing first after sorting (which can be arbitrary if scores are identical and Python's sort isn't stable for all original orderings) will be chosen. This might not be an issue but is a subtle behavior.
*   **Definition of "Arc":** The concept of an "arc_label" is central. The module assumes these labels exist and are meaningful for identifying narratives.
*   **Test Coverage:** The internal test `_test_dual_narrative_compressor` is very basic. It would benefit from:
    *   Testing edge cases (e.g., no forecasts, forecasts with missing keys, no opposing arcs found).
    *   Mocking [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1) to provide controlled input for `generate_dual_scenarios`.
    *   Asserting the content of the generated scenarios, not just the type.

## 4. Connections & Dependencies

*   **Direct Project Module Imports:**
    *   `from forecast_output.forecast_divergence_detector import detect_symbolic_opposition`: Imports a key function for identifying opposing narrative arcs from another module within the same directory.
*   **External Library Dependencies:**
    *   `json`: Standard Python library for JSON processing (used for exporting).
    *   `logging`: Standard Python library for logging.
    *   `typing` (List, Dict, Tuple): Standard Python library for type hinting.
    *   `collections.Counter`: Imported but **not used** in the provided code. This might be a remnant of previous development or an intended future use.
*   **Interaction via Shared Data:**
    *   The primary input is a `List[Dict]` representing forecasts. The structure of these dictionaries is a key dependency.
*   **Input/Output Files:**
    *   **Output:** The [`export_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:66) function writes a JSON file to a specified `path`. The content is a list of the generated dual scenario dictionaries.

## 5. Function and Class Example Usages

*   **[`group_by_arc(forecasts: List[Dict]) -> Dict[str, List[Dict]]`](../forecast_output/dual_narrative_compressor.py:23):**
    Groups forecasts by their `arc_label`.
    ```python
    forecast_list = [
        {"arc_label": "Hope", "data": "details1"},
        {"arc_label": "Collapse", "data": "details2"},
        {"arc_label": "Hope", "data": "details3"},
    ]
    grouped = group_by_arc(forecast_list)
    # grouped would be:
    # {
    #     "Hope": [{"arc_label": "Hope", "data": "details1"}, {"arc_label": "Hope", "data": "details3"}],
    #     "Collapse": [{"arc_label": "Collapse", "data": "details2"}]
    # }
    ```

*   **[`score_forecast(fc: Dict) -> float`](../forecast_output/dual_narrative_compressor.py:31):**
    Calculates a score for a forecast.
    ```python
    forecast = {"alignment_score": 0.7, "confidence": 0.2, "arc_label": "Hope"}
    score = score_forecast(forecast) # score would be 0.9
    forecast_missing_keys = {"arc_label": "Hope"}
    score_missing = score_forecast(forecast_missing_keys) # score would be 0.0
    ```

*   **[`compress_dual_pair(forecasts: List[Dict], arc_a: str, arc_b: str) -> Dict`](../forecast_output/dual_narrative_compressor.py:35):**
    Selects the top-scoring forecast for each of two specified arcs.
    ```python
    forecast_list = [
        {"arc_label": "Hope", "alignment_score": 0.8, "confidence": 0.1, "id": 1}, # score 0.9
        {"arc_label": "Collapse", "alignment_score": 0.7, "confidence": 0.1, "id": 2}, # score 0.8
        {"arc_label": "Hope", "alignment_score": 0.6, "confidence": 0.1, "id": 3}, # score 0.7
    ]
    pair = compress_dual_pair(forecast_list, "Hope", "Collapse")
    # pair would be:
    # {
    #     "scenario_a": {"arc": "Hope", "forecast": {"arc_label": "Hope", "alignment_score": 0.8, "confidence": 0.1, "id": 1}},
    #     "scenario_b": {"arc": "Collapse", "forecast": {"arc_label": "Collapse", "alignment_score": 0.7, "confidence": 0.1, "id": 2}}
    # }
    ```

*   **[`generate_dual_scenarios(forecasts: List[Dict]) -> List[Dict]`](../forecast_output/dual_narrative_compressor.py:55):**
    Generates all Scenario A/B structures based on detected opposing arcs.
    ```python
    # Assuming detect_symbolic_opposition(forecast_list) returns [("Hope", "Collapse")]
    # and forecast_list is as above:
    scenarios = generate_dual_scenarios(forecast_list)
    # scenarios would be a list containing one dictionary, similar to 'pair' above.
    ```

*   **[`export_dual_scenarios(scenarios: List[Dict], path: str)`](../forecast_output/dual_narrative_compressor.py:66):**
    Saves the list of scenarios to a JSON file.
    ```python
    # scenarios = [...] # from generate_dual_scenarios
    # export_dual_scenarios(scenarios, "output/dual_narratives.json")
    # This would create 'output/dual_narratives.json' with the scenarios.
    ```

## 6. Hardcoding Issues

*   **Default `arc_label`:** In [`group_by_arc`](../forecast_output/dual_narrative_compressor.py:23), if a forecast lacks an `"arc_label"`, it defaults to `"unknown"` ([`forecast_output/dual_narrative_compressor.py:26`](../forecast_output/dual_narrative_compressor.py:26)).
*   **Default Scores:** In [`score_forecast`](../forecast_output/dual_narrative_compressor.py:31), if `"alignment_score"` or `"confidence"` are missing, they default to `0` ([`forecast_output/dual_narrative_compressor.py:32`](../forecast_output/dual_narrative_compressor.py:32)).
*   **Logger Name:** The logger is named `"dual_narrative_compressor"` ([`forecast_output/dual_narrative_compressor.py:19`](../forecast_output/dual_narrative_compressor.py:19)).
*   **Logging Configuration:** `logging.basicConfig(level=logging.INFO)` ([`forecast_output/dual_narrative_compressor.py:20`](../forecast_output/dual_narrative_compressor.py:20)) is a global configuration that might affect logging in other parts of the application if this module is imported early. It's generally better for libraries/modules to get a logger and let the main application configure handlers and levels.
*   **Encoding for Export:** `"utf-8"` is hardcoded for file export ([`forecast_output/dual_narrative_compressor.py:69`](../forecast_output/dual_narrative_compressor.py:69)), which is a good default.
*   **JSON Indent Level:** `indent=2` is hardcoded for JSON export ([`forecast_output/dual_narrative_compressor.py:70`](../forecast_output/dual_narrative_compressor.py:70)).

## 7. Coupling Points

*   **`forecast_output.forecast_divergence_detector.detect_symbolic_opposition`:** This is a strong coupling point. The entire logic of [`generate_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:55) depends on the output of this function.
*   **Forecast Data Structure:** The module is tightly coupled to the expected dictionary structure of individual forecasts (keys like `arc_label`, `alignment_score`, `confidence`).
*   **File System:** The [`export_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:66) function directly interacts with the file system.

## 8. Existing Tests

*   An internal test function `_test_dual_narrative_compressor` ([`forecast_output/dual_narrative_compressor.py:76`](../forecast_output/dual_narrative_compressor.py:76)) is present and run when the script is executed directly.
*   This test uses a small, hardcoded `dummy` list of forecasts.
*   It calls [`generate_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:55) and asserts that the result is a list.
*   **Limitation:** This test implicitly relies on the behavior of the imported [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1) function with the dummy data. To properly unit test [`generate_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:55) in isolation, [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1) should be mocked.
*   No separate test file (e.g., `tests/test_dual_narrative_compressor.py`) is immediately visible.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Imports `json`, `logging`, `typing` helpers, and `Counter` (unused).
    *   Imports [`detect_symbolic_opposition`](../forecast_output/forecast_divergence_detector.py:1).
    *   Initializes a logger named "dual_narrative_compressor".
    *   **Sets global logging basicConfig to INFO level.**
2.  **Core Logic Functions:**
    *   [`group_by_arc`](../forecast_output/dual_narrative_compressor.py:23): Iterates through forecasts, creating a dictionary where keys are `arc_label`s and values are lists of forecasts belonging to that arc.
    *   [`score_forecast`](../forecast_output/dual_narrative_compressor.py:31): Retrieves `alignment_score` and `confidence` from a forecast dictionary (defaulting to 0 if keys are missing) and returns their sum.
    *   [`compress_dual_pair`](../forecast_output/dual_narrative_compressor.py:35):
        *   Groups input `forecasts` by arc using [`group_by_arc`](../forecast_output/dual_narrative_compressor.py:23).
        *   Retrieves and sorts forecasts for `arc_a` and `arc_b` based on [`score_forecast`](../forecast_output/dual_narrative_compressor.py:31) (descending).
        *   Returns a dictionary with `scenario_a` and `scenario_b`, each containing the arc label and the top forecast (or `None` if no forecasts for that arc).
    *   [`generate_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:55):
        *   Calls [`detect_symbolic_opposition(forecasts)`](../forecast_output/forecast_divergence_detector.py:1) to get pairs of opposing arc labels.
        *   Uses a list comprehension to call [`compress_dual_pair`](../forecast_output/dual_narrative_compressor.py:35) for each identified pair, returning a list of these scenario dictionaries.
3.  **Export Function:**
    *   [`export_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:66): Opens the given `path` in write mode, dumps the `scenarios` list to it as JSON (indented), and logs success or error.
4.  **Test Function (`_test_dual_narrative_compressor`)**:
    *   Creates a `dummy` list of forecast-like dictionaries.
    *   Calls [`generate_dual_scenarios`](../forecast_output/dual_narrative_compressor.py:55) with the dummy data.
    *   Asserts the result is a list.
    *   Logs a success message.
5.  **Main Execution Block (`if __name__ == "__main__":`)**:
    *   Calls `_test_dual_narrative_compressor()`.

## 10. Naming Conventions

*   **Module Name:** `dual_narrative_compressor.py` (snake_case) - Adheres to PEP 8.
*   **Function Names:** `group_by_arc`, `score_forecast`, `compress_dual_pair`, `generate_dual_scenarios`, `export_dual_scenarios`, `_test_dual_narrative_compressor` (snake_case) - Adheres to PEP 8. The leading underscore in `_test_dual_narrative_compressor` conventionally suggests it's intended for internal use/testing.
*   **Variables:** `forecasts`, `groups`, `fc`, `arc`, `a_set`, `b_set`, `pairs`, `scenarios`, `path`, `dummy` (snake_case) - Adheres to PEP 8.
*   **Constants/Globals:** `logger` (lowercase).
*   **Docstrings:** Present for the module and most public functions. They are generally informative.
*   **Author/Version:** The module docstring includes "Author: Pulse AI Engine" and "Version: v1.0.0".

Naming conventions are consistent and largely follow Python standards. The unused `Counter` import should ideally be removed.