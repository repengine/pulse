# Module Analysis: `learning/recursion_audit.py`

**Version:** v0.4.1
**Author:** Pulse AI Engine

## 1. Module Intent/Purpose

The primary role of the [`learning/recursion_audit.py`](learning/recursion_audit.py:1) module is to compare and analyze forecast batches generated across different recursive cycles of the Pulse system. Its main goal is to quantify and summarize the system's improvement trajectory by evaluating changes in key metrics such as forecast confidence, trust label distributions, retrodiction error, and shifts in symbolic arcs. This allows for an audit of how the system's predictions evolve and improve over iterations.

## 2. Operational Status/Completeness

The module appears to be operationally complete for its defined scope. It contains a set of focused functions for calculating specific metrics ([`average_confidence()`](learning/recursion_audit.py:16), [`average_retrodiction_error()`](learning/recursion_audit.py:21), [`trust_label_distribution()`](learning/recursion_audit.py:26), [`symbolic_arc_shift()`](learning/recursion_audit.py:31)) and a primary function, [`generate_recursion_report()`](learning/recursion_audit.py:50), to aggregate these into a summary. There are no evident TODO comments, placeholders (like `pass` or `NotImplementedError`), or incomplete sections within the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility:** While complete for its current functions, the module could be extended with more sophisticated statistical analyses (e.g., significance testing of metric changes).
*   **Visualization:** Capabilities for visualizing metric trends over multiple recursion cycles are not present and could be a logical next step.
*   **Broader Metric Coverage:** The module focuses on a specific set of metrics; analysis of other forecast attributes or system behaviors could be incorporated.
*   **Integration:** Deeper integration with a formal logging or reporting dashboard could enhance its utility.
*   The `math` module is imported ([`math`](learning/recursion_audit.py:13)) but not explicitly used, suggesting a potential planned feature or a remnant from previous development.

## 4. Connections & Dependencies

### Internal Project Dependencies:
*   None. The module is self-contained and does not import other custom project modules.

### External Library Dependencies:
*   [`typing`](learning/recursion_audit.py:11): (Standard Library) Used for type hints (`List`, `Dict`, `Tuple`).
*   [`collections.Counter`](learning/recursion_audit.py:12): (Standard Library) Used in [`trust_label_distribution()`](learning/recursion_audit.py:26) for efficiently counting occurrences of trust labels.
*   [`math`](learning/recursion_audit.py:13): (Standard Library) Imported but not actively used in the current version.

### Data Interaction:
*   **Input:** The module's functions, particularly [`generate_recursion_report()`](learning/recursion_audit.py:50), expect two lists of dictionaries as input: `previous` (prior forecast batch) and `current` (latest forecast batch). The structure of these dictionaries is implicitly defined by keys accessed within the functions (e.g., `confidence`, `retrodiction_error`, `trust_label`, `trace_id`, `arc_label`).
*   **Output:** The main function [`generate_recursion_report()`](learning/recursion_audit.py:50) returns a dictionary containing the summary statistics and audit metrics. It does not directly write to files, databases, or logs.

## 5. Function and Class Example Usages

The module consists of functions. Key functions include:

*   **[`average_confidence(forecasts: List[Dict]) -> float`](learning/recursion_audit.py:16):**
    Calculates the average confidence from a list of forecast dictionaries.
    ```python
    forecast_batch = [{"confidence": 0.8}, {"confidence": 0.9}, {}]
    avg_conf = average_confidence(forecast_batch)
    # avg_conf would be approximately (0.8 + 0.9 + 0.0) / 3
    ```

*   **[`average_retrodiction_error(forecasts: List[Dict]) -> float`](learning/recursion_audit.py:21):**
    Calculates the average retrodiction error from a list of forecast dictionaries.
    ```python
    forecast_batch = [{"retrodiction_error": 0.1}, {"retrodiction_error": 0.05}]
    avg_err = average_retrodiction_error(forecast_batch)
    # avg_err would be 0.075
    ```

*   **[`trust_label_distribution(forecasts: List[Dict]) -> Dict[str, int]`](learning/recursion_audit.py:26):**
    Counts the distribution of `trust_label` values in a list of forecasts.
    ```python
    forecast_batch = [{"trust_label": "High"}, {"trust_label": "Medium"}, {"trust_label": "High"}]
    dist = trust_label_distribution(forecast_batch)
    # dist would be {"High": 2, "Medium": 1}
    ```

*   **[`symbolic_arc_shift(previous: List[Dict], current: List[Dict]) -> Dict[str, int]`](learning/recursion_audit.py:31):**
    Compares `arc_label` for forecasts with the same `trace_id` between two batches.
    ```python
    prev = [{"trace_id": "t1", "arc_label": "A"}]
    curr = [{"trace_id": "t1", "arc_label": "B"}] # Changed
    shift = symbolic_arc_shift(prev, curr)
    # shift would be {"same": 0, "changed": 1, "missing": 0}
    ```

*   **[`generate_recursion_report(previous: List[Dict], current: List[Dict]) -> Dict`](learning/recursion_audit.py:50):**
    The main function that aggregates metrics from the helper functions.
    ```python
    prev_batch = [{"confidence": 0.7, "retrodiction_error": 0.2, "trust_label": "Low", "trace_id": "t1", "arc_label": "X"}]
    curr_batch = [{"confidence": 0.8, "retrodiction_error": 0.1, "trust_label": "Medium", "trace_id": "t1", "arc_label": "Y"}]
    report = generate_recursion_report(prev_batch, curr_batch)
    # report contains keys like 'confidence_delta', 'retrodiction_error_delta', etc.
    ```

## 6. Hardcoding Issues

*   **Default Values:**
    *   `0.0` is used as a default for missing or invalid `confidence` ([`learning/recursion_audit.py:17`](learning/recursion_audit.py:17)) and `retrodiction_error` ([`learning/recursion_audit.py:22`](learning/recursion_audit.py:22)) values.
    *   `"None"` is used as a default for missing `trust_label` ([`learning/recursion_audit.py:27`](learning/recursion_audit.py:27)).
    These are considered reasonable defaults for handling potentially incomplete data.
*   **Dictionary Keys:** String literals like `"confidence"`, `"retrodiction_error"`, `"trust_label"`, `"trace_id"`, and `"arc_label"` are used to access dictionary values. These define the expected data structure and are not problematic hardcodings.
*   **Output Keys:** Strings like `"same"`, `"changed"`, `"missing"` in [`symbolic_arc_shift()`](learning/recursion_audit.py:36) are keys for the returned dictionary and are acceptable.
*   The module does not contain hardcoded file paths, API keys, secrets, or other sensitive information.

## 7. Coupling Points

*   **Data Structure Coupling:** The module is tightly coupled to the specific structure (keys and expected data types) of the input `forecasts` dictionaries. Any changes to this structure in the modules that generate these forecasts would require corresponding updates in [`learning/recursion_audit.py`](learning/recursion_audit.py:1).
*   **Consumer Coupling:** Modules that consume the report generated by [`generate_recursion_report()`](learning/recursion_audit.py:50) are coupled to the structure and keys of the output dictionary.

## 8. Existing Tests

*   A corresponding test file, [`tests/test_recursion_audit.py`](tests/test_recursion_audit.py:), exists in the project structure.
*   The specific coverage, nature, and thoroughness of these tests cannot be determined without examining the contents of [`tests/test_recursion_audit.py`](tests/test_recursion_audit.py:).

## 9. Module Architecture and Flow

*   **Architecture:** The module follows a simple functional programming paradigm, consisting of a set of independent utility functions that perform specific calculations and one main function that orchestrates them.
*   **Control Flow:**
    1.  The [`generate_recursion_report()`](learning/recursion_audit.py:50) function is the primary entry point.
    2.  It takes `previous` and `current` forecast batches (lists of dictionaries) as input.
    3.  It calls helper functions ([`average_confidence()`](learning/recursion_audit.py:16), [`average_retrodiction_error()`](learning/recursion_audit.py:21), [`trust_label_distribution()`](learning/recursion_audit.py:26), [`symbolic_arc_shift()`](learning/recursion_audit.py:31)) with these batches.
    4.  Each helper function processes the data and returns a specific metric or analysis.
    5.  The results are aggregated into a summary dictionary, which is then returned by [`generate_recursion_report()`](learning/recursion_audit.py:50).

## 10. Naming Conventions

*   **Functions and Variables:** Adhere to PEP 8 standards, using `snake_case` (e.g., [`average_confidence`](learning/recursion_audit.py:16), `retrodiction_error_delta`).
*   **Clarity:** Names are generally descriptive and clearly convey the purpose of functions and variables (e.g., `trust_label_distribution`, `arc_shift_summary`).
*   **Module Name:** [`recursion_audit.py`](learning/recursion_audit.py:1) accurately reflects the module's functionality.
*   No significant deviations from standard Python naming conventions or potential AI assumption errors in naming were observed.
*   The author is noted as "Pulse AI Engine" ([`learning/recursion_audit.py:7`](learning/recursion_audit.py:7)).