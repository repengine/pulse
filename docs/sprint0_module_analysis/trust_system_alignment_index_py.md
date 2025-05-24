# Analysis Report: `trust_system/alignment_index.py`

## 1. Module Intent/Purpose

The primary role of the [`trust_system/alignment_index.py`](trust_system/alignment_index.py:1) module is to calculate a "Forecast Alignment Index" (FAI). This index is an overall score for a given forecast, indicating how well it aligns with various quality and reliability metrics. It synthesizes multiple factors into a single, normalized score (0-100). The components considered are:
*   Confidence
*   Retrodiction score (1 - error)
*   Arc stability (1 - volatility)
*   Symbolic tag match
*   Novelty score (compared to historical forecasts in memory)

## 2. Operational Status/Completeness

The module appears to be operationally complete for its defined scope.
*   It implements the calculation for all listed components of the FAI.
*   It includes default weights for these components, which can also be overridden.
*   Error handling is present for each component calculation, typically defaulting to a neutral or minimal score (e.g., 0.0 or 1.0 for novelty) if expected data is missing or malformed.
*   There are no explicit `TODO` comments or obvious placeholders suggesting unfinished sections within the core logic.
*   A simple `if __name__ == "__main__":` block provides a basic test case.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensiveness:** The module is focused and seems to fulfill its specific purpose. There are no immediate signs it was intended to be significantly more extensive *for this specific task*.
*   **Logical Next Steps:**
    *   The calculation of `retrodiction` relies on an external function [`compute_retrodiction_error`](trust_system/alignment_index.py:74) from [`learning.learning`](learning/learning.py). This implies a dependency and a logical workflow where retrodiction errors are computed elsewhere.
    *   The `memory` parameter suggests integration with a system that stores and retrieves past forecasts. The novelty calculation is basic (tag count); more sophisticated novelty detection could be a future enhancement.
    *   The `trusted_tags` set is hardcoded. A more flexible system might load these from a configuration file or a shared constants module.
*   **Deviations/Stoppages:** There are no clear indications of development starting on a planned path and then deviating or stopping short within this module. The import for [`compute_retrodiction_error`](trust_system/alignment_index.py:74) is moved inside the function to avoid circular imports, which is a common refinement, not a stoppage.

## 4. Connections & Dependencies

*   **Direct Project Imports:**
    *   `from typing import Dict, Optional` (standard library)
    *   Conditional local import: `from learning.learning import compute_retrodiction_error` (line 74 in [`compute_alignment_index`](trust_system/alignment_index.py:29)). This suggests a dependency on the `learning.learning` module for calculating retrodiction scores if not directly provided in the forecast object.
*   **External Library Dependencies:**
    *   None for the main module logic.
    *   The test file [`tests/test_alignment_index.py`](tests/test_alignment_index.py:1) uses `unittest`.
*   **Interaction via Shared Data:**
    *   **Input:**
        *   `forecast` (Dict): Expects a dictionary with keys like `confidence`, `retrodiction_score` (optional), `arc_volatility_score` (optional), `symbolic_tag` (optional), `trace_id` (optional).
        *   `current_state` (Optional[Dict]): Used by the imported [`compute_retrodiction_error`](trust_system/alignment_index.py:74) function.
        *   `memory` (Optional[list]): A list of previous forecast dictionaries, used for the novelty score.
    *   **Output:** Returns a dictionary containing `alignment_score`, `components` (a breakdown of individual scores), and `forecast_id`.
*   **Input/Output Files:**
    *   The module itself does not directly read from or write to files (e.g., logs, data files, metadata).

## 5. Function and Class Example Usages

*   **[`normalize_weights(weights: Dict[str, float]) -> Dict[str, float]`](trust_system/alignment_index.py:21)**
    *   **Purpose:** Ensures that the sum of float values in the input dictionary `weights` equals 1.0. If the sum is 0, it returns the original weights.
    *   **Example:**
        ```python
        weights = {"confidence": 0.4, "retrodiction": 0.4, "novelty": 0.2}
        normalized = normalize_weights(weights)
        # normalized will be {"confidence": 0.4, "retrodiction": 0.4, "novelty": 0.2}

        weights_unnormalized = {"confidence": 1, "retrodiction": 2, "novelty": 1}
        normalized_2 = normalize_weights(weights_unnormalized)
        # normalized_2 will be {"confidence": 0.25, "retrodiction": 0.5, "novelty": 0.25}
        ```

*   **[`compute_alignment_index(forecast: Dict, ..., weights: Optional[Dict[str, float]] = None) -> Dict[str, object]`](trust_system/alignment_index.py:29)**
    *   **Purpose:** Calculates the overall Forecast Alignment Index.
    *   **Example (derived from the module's `if __name__ == "__main__":` block):**
        ```python
        test_forecast = {
            "trace_id": "fc_test_001",
            "confidence": 0.85,
            "retrodiction_score": 0.9,  # Directly provided
            "arc_volatility_score": 0.1, # Lower volatility is better
            "symbolic_tag": "Hope"
        }
        # Using default weights
        result = compute_alignment_index(test_forecast)
        # result would be like:
        # {
        #     "alignment_score": 78.5, # Example value, depends on exact default weights and logic
        #     "components": {
        #         "confidence": 0.85,
        #         "retrodiction": 0.9,
        #         "arc_stability": 0.9, # 1.0 - 0.1
        #         "tag_match": 1.0,     # "hope" is a trusted tag
        #         "novelty": 1.0        # Assuming empty memory or no prior "hope" tags
        #     },
        #     "forecast_id": "fc_test_001"
        # }

        # Example with custom weights and other parameters
        custom_weights = {
            "confidence": 0.5,
            "retrodiction": 0.1,
            "arc_stability": 0.1,
            "tag_match": 0.15,
            "novelty": 0.15
        }
        memory_forecasts = [
            {"symbolic_tag": "Neutral"},
            {"symbolic_tag": "Hope"} # One previous "Hope"
        ]
        result_custom = compute_alignment_index(
            forecast=test_forecast,
            current_state={"some_actual_value": 10}, # For retrodiction if score not provided
            memory=memory_forecasts,
            arc_volatility=0.15, # Can be passed directly
            tag_match=0.8,       # Can be passed directly
            weights=custom_weights
        )
        # Novelty for "Hope" would be 1.0 - (1/2) = 0.5 if memory_forecasts is used
        ```

## 6. Hardcoding Issues

*   **Default Weights:** The `default_weights` dictionary within [`compute_alignment_index`](trust_system/alignment_index.py:54) is hardcoded:
    ```python
    default_weights = {
        "confidence": 0.3,
        "retrodiction": 0.2,
        "arc_stability": 0.2,
        "tag_match": 0.15,
        "novelty": 0.15
    }
    ```
    While these are defaults and can be overridden by passing a `weights` argument, centralizing such configurations might be preferable in a larger system.
*   **Trusted Tags:** The set of `trusted_tags` for the `tag_match` component is hardcoded within [`compute_alignment_index`](trust_system/alignment_index.py:100):
    ```python
    trusted_tags = {"hope", "trust", "recovery", "neutral"}
    ```
    This limits flexibility without code changes. Ideally, these would come from a configuration file or a shared constants module.
*   **Scaling Factor:** The final `alignment_score` is scaled by `100` (line 128 in [`compute_alignment_index`](trust_system/alignment_index.py:29)). This is a "magic number" representing the scale (0-100).
*   **Default/Fallback Values:** Various default values (e.g., `0.0` for scores if data is missing/invalid, `1.0` for novelty initially) are embedded in the logic. These are generally reasonable fallbacks.

## 7. Coupling Points

*   **Input Data Structure:** The module is tightly coupled to the expected structure of the `forecast` dictionary. It relies on specific keys (`confidence`, `retrodiction_score`, `arc_volatility_score`, `symbolic_tag`, `trace_id`). Changes to these key names or data types in upstream modules would break this module.
*   **`learning.learning` Module:** The conditional import and use of [`compute_retrodiction_error`](trust_system/alignment_index.py:74) from [`learning.learning`](learning/learning.py) creates a functional dependency. The `alignment_index` module's behavior for retrodiction scoring depends on this external function if `retrodiction_score` is not directly provided.
*   **`current_state` and `memory`:** The structure and content of `current_state` (for retrodiction) and `memory` (list of past forecasts for novelty) are implicitly defined by how they are used.

## 8. Existing Tests

*   **Test File:** [`tests/test_alignment_index.py`](tests/test_alignment_index.py:1)
*   **Framework:** Uses the standard Python `unittest` framework.
*   **Test Class:** [`TestForecastAlignmentIndex(unittest.TestCase)`](tests/test_alignment_index.py:6)
*   **Structure:**
    *   A [`setUp`](tests/test_alignment_index.py:8) method initializes a `self.base_forecast` dictionary.
    *   Three test methods are defined:
        *   [`test_confidence_only(self)`](tests/test_alignment_index.py:14): Tests a basic case where only confidence might be available or dominant. It checks if `alignment_score` is present, within the 0-100 range, and if `forecast_id` is correctly passed.
        *   [`test_with_all_components(self)`](tests/test_alignment_index.py:20): Tests a scenario providing `current_state`, `arc_volatility`, `tag_match`, and `memory`. It asserts that the `components` dictionary is in the result and specifically checks for the `novelty` key.
        *   [`test_extreme_values(self)`](tests/test_alignment_index.py:31): Tests a forecast with low confidence (0.0), high arc volatility (1.0), and low tag match (0.0). It asserts that the resulting `alignment_score` is below 60.
*   **Coverage and Gaps:**
    *   The tests cover basic functionality and some edge/extreme cases.
    *   They verify the presence of key output fields and basic range checks for the score.
    *   **Gaps:**
        *   The tests do not explicitly check the correctness of the `normalize_weights` function.
        *   The impact of different custom `weights` on the final score is not tested.
        *   The retrodiction calculation path that uses the imported [`compute_retrodiction_error`](trust_system/alignment_index.py:74) (when `retrodiction_score` is missing and `current_state` is provided) is not explicitly tested with controlled inputs for `current_state` to verify the subtraction `1.0 - error`. The current test passes an empty dict `{}` for `current_state`, relying on graceful fallback.
        *   Various scenarios for `symbolic_tag` (e.g., not in `trusted_tags`, case variations if not already handled by `.lower()`) are not exhaustively tested for the `tag_match` component.
        *   Different states of `memory` (e.g., non-empty, multiple occurrences of the same tag) are only lightly touched upon for the `novelty` score.
        *   Error handling for malformed inputs (e.g., non-numeric confidence) is not explicitly tested, though the main code has `try-except` blocks and type checks.

## 9. Module Architecture and Flow

1.  **[`normalize_weights`](trust_system/alignment_index.py:21) function:**
    *   Takes a dictionary of weights.
    *   Calculates the sum of all weight values.
    *   If the total is not zero, divides each weight by the total sum to normalize them (so they sum to 1.0).
    *   Returns the normalized weights dictionary.

2.  **[`compute_alignment_index`](trust_system/alignment_index.py:29) function:**
    *   **Initialization:**
        *   Sets `default_weights` if no `weights` are provided by the caller.
        *   Normalizes the `weights` using the [`normalize_weights`](trust_system/alignment_index.py:21) function.
    *   **Component Score Calculation (each clamped between 0.0 and 1.0):**
        *   **Confidence:** Retrieves `confidence` from the `forecast` dictionary. Defaults to 0.0 if missing or not a number.
        *   **Retrodiction:**
            *   Uses `forecast["retrodiction_score"]` if available.
            *   Else, if `current_state` is provided, it imports and calls [`compute_retrodiction_error(forecast, current_state)`](trust_system/alignment_index.py:74) from `learning.learning` and calculates `1.0 - error`.
            *   Defaults to 0.0 otherwise or on error.
        *   **Arc Stability:**
            *   Uses `1.0 - arc_volatility` if `arc_volatility` is passed directly.
            *   Else, uses `1.0 - forecast["arc_volatility_score"]` if available.
            *   Defaults to 0.0 otherwise or on error.
        *   **Tag Match:**
            *   Uses `tag_match` if passed directly.
            *   Else, retrieves `forecast.get("symbolic_tag")`, converts to lowercase, and checks if it's in the hardcoded `trusted_tags` set (1.0 if match, 0.0 otherwise).
            *   Defaults to 0.0 on error.
        *   **Novelty Score:**
            *   Defaults to 1.0.
            *   If `memory` (list of past forecasts) is provided, it counts occurrences of the current forecast's `symbolic_tag` in `memory` and calculates novelty as `1.0 - (count / total_in_memory)`.
            *   Defaults to 1.0 on error or if memory is not a list.
    *   **Weighted Sum:**
        *   Calculates the final `alignment_score` by summing each component score multiplied by its corresponding normalized weight.
        *   Scales the score by 100 and rounds to 2 decimal places.
    *   **Return Value:** Returns a dictionary containing `alignment_score`, the `components` dictionary (with individual scores), and `forecast_id`.

## 10. Naming Conventions

*   **Functions:** `normalize_weights`, `compute_alignment_index` (snake_case, PEP 8 compliant).
*   **Variables:** `total`, `weights`, `default_weights`, `confidence`, `retrodiction`, `arc_stability`, `tag_match_val`, `novelty`, `alignment_score`, `components` (snake_case, PEP 8 compliant).
*   **Constants/Defaults:** `default_weights` is descriptive. `trusted_tags` is also clear.
*   **Clarity:** Names are generally descriptive and easy to understand.
*   **AI Assumption Errors:** No obvious errors stemming from AI assumptions in naming. The abbreviation "FAI" (Forecast Alignment Index) is defined in the module docstring.
*   **Consistency:** Consistent use of snake_case for variables and functions.
*   The module uses `object` in the return type hint for [`compute_alignment_index`](trust_system/alignment_index.py:36) (`Dict[str, object]`). While technically correct as dictionary values can be of mixed types (float for score, dict for components, string for id), a more specific `Union` or `Any` might be used, or even `Dict[str, Union[float, Dict[str, float], Optional[str]]]` if being very precise, though `object` is acceptable.