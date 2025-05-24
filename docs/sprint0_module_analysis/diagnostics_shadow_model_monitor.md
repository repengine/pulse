# Analysis: `diagnostics/shadow_model_monitor.py`

## 1. File Overview

*   **File Path:** [`diagnostics/shadow_model_monitor.py`](diagnostics/shadow_model_monitor.py:1)
*   **Purpose:** This module provides the `ShadowModelMonitor` class, designed to monitor and assess the influence of the "gravity model" corrections on a predefined set of critical variables within a simulation. It does this by tracking the proportion of variance in variable changes that is attributable to gravity corrections versus the original causal model predictions.
*   **Key Functionalities:**
    *   Initialization with a variance threshold, a rolling window size (in simulation steps), and a list of critical variables to monitor.
    *   Recording of causal deltas (changes predicted by the core causal model) and gravity deltas (adjustments made by the gravity model) at each simulation step.
    *   Calculation of the proportion of variance explained by gravity for any monitored variable over the current rolling window.
    *   Checking for a "trigger" condition: if the variance explained by gravity for any critical variable consistently exceeds the defined threshold over the window.

## 2. Module Structure and Components

*   **`ShadowModelMonitor` Class:**
    *   **`__init__(self, threshold, window_steps, critical_variables)`:** Constructor that initializes the monitor's parameters. It validates inputs (threshold between 0 and 1, positive window steps). Stores deltas in a `collections.deque` to maintain the rolling window.
    *   **`record_step(self, causal_deltas, gravity_deltas, current_step)`:** Adds the deltas for the current simulation step to the rolling window. It filters the input deltas to only store those relevant to the `critical_variables`.
    *   **`_sum_of_squares(self, values)`:** A private helper method to calculate the sum of squares of a list of values, used in variance calculation.
    *   **`calculate_variance_explained(self, variable)`:** Calculates the proportion of variance explained by gravity for a specific variable. The formula used is `SumSq(GravityDeltas) / (SumSq(GravityDeltas) + SumSq(CausalDeltas))`. Returns `0.0` if the denominator is zero or if there's no data, and `-1.0` if the variable is not in the critical list.
    *   **`check_trigger(self)`:** Determines if the gravity model's influence has exceeded the configured `threshold` for any of the `critical_variables` within the current `window_steps`. Returns a boolean indicating if the trigger is met and a list of problematic variables.

*   **`if __name__ == '__main__':` block:** Contains a basic test and usage example that simulates several steps of data, records them with the monitor, and checks for triggers. This demonstrates the class's functionality and includes some edge case testing (e.g., all zero deltas, causal-only, gravity-only).

## 3. Dependencies

*   **Internal Pulse Modules:** None are directly imported. The module is self-contained in its logic but is intended to be integrated into a larger simulation loop that provides it with causal and gravity delta data.
*   **External Libraries:**
    *   `logging`: For module-level logging.
    *   `collections.deque`: Used for efficiently managing the rolling window of delta data.

## 4. SPARC Principles Assessment

*   **Specification & Simplicity:** The module has a very clear and specific purpose: to monitor the gravity model's influence. The logic for variance calculation and threshold checking is straightforward.
*   **Architecture & Modularity:** The `ShadowModelMonitor` class is a well-encapsulated component. Its methods provide a clear interface for recording data and checking status.
*   **Testability:** The module includes an `if __name__ == '__main__':` block that serves as a good inline test suite, covering basic functionality and some edge cases. For more rigorous testing, this could be expanded into a dedicated test file (e.g., [`tests/test_shadow_model_monitor.py`](tests/test_shadow_model_monitor.py:1)).
*   **Maintainability & Readability:** The code is well-commented with docstrings for the class and its methods. Variable names are descriptive. The logic is easy to follow.
*   **Security (Hardcoding Secrets):** No hardcoded secrets are present.
*   **Hardcoding (Other):**
    *   The configuration parameters (threshold, window_steps, critical_variables) are passed during instantiation, which is good practice and avoids hardcoding these operational parameters within the class logic itself. The example in `if __name__ == '__main__':` uses a hardcoded dictionary for `monitor_config_example`, which is acceptable for an example.
*   **No `print` for Logging:** Uses the `logging` module appropriately.

## 5. Overall Assessment

*   **Completeness:** The module appears to be functionally complete for its defined purpose. It correctly implements the logic for tracking deltas, calculating variance explained, and checking for threshold breaches.
*   **Quality:** The code is of good quality: it's clear, well-documented, includes basic validation for inputs, and uses appropriate data structures (`deque`). The inline tests demonstrate a consideration for correctness.
*   **Potential Improvements:**
    *   While the inline tests are useful, creating a separate test file using a testing framework like `pytest` (e.g., in [`tests/test_shadow_model_monitor.py`](tests/test_shadow_model_monitor.py:1)) would allow for more structured and extensive testing.
    *   The `calculate_variance_explained` method returns `-1.0` if a variable is not found. Raising a `ValueError` or `KeyError` might be more explicit, or consistently returning `0.0` and logging a warning could also be considered, depending on the desired error handling strategy by the caller.

## 6. Role in `diagnostics/` Directory

This module plays a critical monitoring role within the `diagnostics/` toolkit. It provides a quantitative way to assess whether the symbolic gravity model is exerting an excessive influence on the simulation, potentially overshadowing the primary causal model. This is vital for maintaining model balance and identifying when the gravity corrections might require recalibration or further investigation.

## 7. Summary Note for Main Report

The [`diagnostics/shadow_model_monitor.py`](diagnostics/shadow_model_monitor.py:1) module provides a `ShadowModelMonitor` class to track and flag when the "gravity model" unduly influences critical simulation variables by exceeding a defined variance-explained threshold.