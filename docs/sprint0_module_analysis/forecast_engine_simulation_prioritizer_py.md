# Module Analysis: `forecast_engine/simulation_prioritizer.py`

## 1. Purpose

The [`simulation_prioritizer.py`](../../forecast_engine/simulation_prioritizer.py:1) module is designed to rank "foresight scenarios," which can be forecasts or simulation forks, based on their strategic urgency. This ranking helps prioritize simulation efforts and identify which potential future paths (forks) are most valuable or critical to explore further. The prioritization considers factors like symbolic fragility, novelty of symbolic changes, and the magnitude of capital impact.

## 2. Key Functionalities

The module provides several functions to achieve this ranking:

*   **`symbolic_delta_magnitude(symbolic_change: Dict[str, float]) -> float`**:
    *   Calculates the overall "symbolic novelty" of a forecast.
    *   It takes a dictionary representing changes in symbolic overlays (where keys are symbols and values are their change magnitudes).
    *   Computes the Euclidean norm (vector magnitude) of these changes.
    *   Returns a rounded float representing the total magnitude of symbolic change.

*   **`capital_delta_magnitude(start: Dict[str, float], end: Dict[str, float]) -> float`**:
    *   Calculates the magnitude of total capital movement across different assets between a start and end state.
    *   It takes two dictionaries representing capital distribution at the start and end of a forecast.
    *   Sums the absolute differences for each asset.
    *   Normalizes this sum (divides by 1000) and caps it at 1.0, returning a rounded float. This suggests a scaling or capping mechanism for capital impact.

*   **`rank_forecasts(forecasts: List[Dict], weights: Optional[Dict] = None, debug: bool = False) -> List[Dict]`**:
    *   This is the main function for scoring and ranking a list of forecast dictionaries.
    *   **Inputs**:
        *   `forecasts`: A list of dictionaries, where each dictionary represents a forecast and is expected to contain keys like `fragility`, and nested dictionaries for `symbolic_change`, `start_capital`, and `end_capital`.
        *   `weights` (optional): A dictionary to specify the weighting for different scoring components. Defaults are: `fragility: 0.5`, `novelty: 0.3`, `capital: 0.2`.
        *   `debug` (optional): A boolean flag to print score breakdowns for each forecast.
    *   **Processing**:
        *   For each forecast:
            *   Extracts `fragility` (defaulting to 0.5 if not present).
            *   Calculates `novelty` using `symbolic_delta_magnitude()`.
            *   Calculates `capital` impact using `capital_delta_magnitude()`.
            *   Computes a weighted `score` based on these three factors and the provided or default weights.
            *   Retrieves the forecast's age using [`forecast_output.forecast_age_tracker.get_forecast_age()`](../../forecast_output/forecast_age_tracker.py:0).
            *   Applies an age-based penalty to the score (older forecasts get a slight reduction, with a floor of 0.05).
            *   Stores the final `priority_score` in the forecast dictionary.
            *   Optionally prints debug information.
    *   **Output**: Returns the list of forecast dictionaries, sorted in descending order based on their `priority_score`.

*   **`simulate_priority_test()`**:
    *   A local test function (intended to be run when `if __name__ == "__main__":`).
    *   Imports `PFPA_ARCHIVE` from [`forecast_output.pfpa_logger`](../../forecast_output/pfpa_logger.py:0).
    *   If forecasts are available in the archive, it ranks the last 10 forecasts with `debug=True`.
    *   Prints the top 5 prioritized forecasts along with their trace ID, priority score, and confidence.

## 3. Role within `forecast_engine/`

This module plays a crucial decision-support role within the `forecast_engine/`. By evaluating forecasts on multiple dimensions of strategic importance (fragility, novelty, capital impact, age), it provides a mechanism to guide the allocation of computational resources for further simulation or deeper analysis. It helps the engine focus on the most "interesting" or "concerning" future possibilities.

## 4. Dependencies

### External Libraries:
*   `typing.List`, `typing.Dict`: For type hinting.
*   `math.sqrt`: For calculating the square root in `symbolic_delta_magnitude`.

### Internal Pulse Modules:
*   [`forecast_output.forecast_age_tracker.get_forecast_age`](../../forecast_output/forecast_age_tracker.py:0): Used to factor in the age of a forecast into its priority.
*   [`forecast_output.pfpa_logger.PFPA_ARCHIVE`](../../forecast_output/pfpa_logger.py:0): Used only in the local `simulate_priority_test()` function to fetch example forecasts for testing the ranking logic.

## 5. Adherence to SPARC Principles

*   **Simplicity**: The core logic for calculating individual components (novelty, capital impact) and the weighted score is relatively straightforward. The `rank_forecasts` function, while handling multiple factors, is well-structured.
*   **Iterate**: The module builds upon other components like `forecast_age_tracker`. The weighting system allows for iteration and tuning of how different factors contribute to the overall priority.
*   **Focus**: The module is clearly focused on ranking forecasts based on a defined set of strategic criteria. It doesn't delve into generating these forecasts or acting upon them, only prioritizing them.
*   **Quality**:
    *   Good use of type hinting.
    *   Docstrings are present for all public functions, explaining their purpose, parameters, and return values.
    *   Default weights are provided, making the `rank_forecasts` function usable out-of-the-box.
    *   The inclusion of a `debug` flag is helpful for understanding the scoring process.
    *   The age penalty introduces a sensible heuristic (older, unaddressed high-priority items might still be relevant but slightly less urgent than new ones).
    *   The local test hook (`simulate_priority_test`) is a good practice for module-level testing and demonstration.
*   **Collaboration**: The module is designed to consume forecast data (dictionaries with an expected structure) produced by other parts of the `forecast_engine` or `simulation_engine`. Its output (ranked list) is intended for other components that might decide which simulations to run next or which forecasts to highlight.

## 6. Overall Assessment

*   **Completeness**: The module seems complete for its defined task of prioritizing forecasts based on the specified criteria. It provides a flexible weighting mechanism and considers multiple relevant factors.
*   **Clarity**: The code is generally clear and readable. Function names are descriptive. The mathematical calculations are straightforward. The structure of the `rank_forecasts` function is logical.
*   **Quality**: The module demonstrates good quality through clear function definitions, type hinting, docstrings, and the inclusion of a test function. The logic for scoring and ranking is sound and incorporates several dimensions of "urgency." The normalization/capping in `capital_delta_magnitude` and the age penalty are thoughtful additions.

This module provides an intelligent mechanism for guiding the Pulse system's attention and resources towards the most strategically significant foresight scenarios.