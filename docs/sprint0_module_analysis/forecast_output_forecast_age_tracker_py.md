# Module Analysis: `forecast_output/forecast_age_tracker.py`

## 1. Module Intent/Purpose

The primary role of the [`forecast_output/forecast_age_tracker.py`](forecast_output/forecast_age_tracker.py:1) module is to manage the lifecycle and relevance of forecasts over time. It achieves this by:
*   Timestamping forecasts upon creation or first processing.
*   Calculating the age of forecasts.
*   Applying a decay function to confidence and priority scores based on age.
*   Tagging forecasts with age-related statuses (e.g., "Fresh", "Decayed", "Expired").
*   Providing functionality to prune or filter out forecasts deemed too old (stale).

This module introduces time-awareness to the forecast objects, ensuring that their perceived reliability and importance diminish as they become older.

## 2. Operational Status/Completeness

The module appears largely functional and complete for its defined scope. Key functionalities like timestamping, age calculation, confidence/priority decay, and pruning are implemented. There are no explicit "TODO" comments or obvious major placeholders in the core logic.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Age Tagging Logic:** The current age tagging in [`decay_confidence_and_priority()`](forecast_output/forecast_age_tracker.py:50) uses an `if/elif/else` structure:
    ```python
    if age > 12:
        forecast["age_tag"] = "📉 Decayed"
    elif age > 24: # This condition will not be met if age > 12 was true
        forecast["age_tag"] = "❌ Expired"
    else:
        forecast["age_tag"] = "🕒 Fresh"
    ```
    A forecast older than 24 hours will be tagged as "📉 Decayed" because the first condition (`age > 12`) will be met, and the `elif age > 24` will not be evaluated. This likely needs adjustment to ensure "❌ Expired" takes precedence for forecasts older than 24 hours.
*   **Unused Log Path:** The `AGE_LOG_PATH` ([`forecast_output/forecast_age_tracker.py:22`](forecast_output/forecast_age_tracker.py:22)) is defined using [`PATHS`](core/path_registry.py:1) but is not actively used within this module for logging specific age-related events or statistics. This might indicate an intended feature that was not fully implemented.
*   **Test Dependency:** The inline test function [`simulate_age_decay_test()`](forecast_output/forecast_age_tracker.py:81) imports `PFPA_ARCHIVE` from [`forecast_output.pfpa_logger`](forecast_output/pfpa_logger.py:1). While suitable for a quick test, this introduces a dependency on another specific module from `forecast_output` which might be undesirable if `forecast_age_tracker.py` is meant to be a more generic utility.

## 4. Connections & Dependencies

*   **Direct Project Module Imports:**
    *   [`from utils.log_utils import get_logger`](utils/log_utils.py:1): For logging.
    *   [`from core.path_registry import PATHS`](core/path_registry.py:1): For accessing configured file paths.
    *   [`from forecast_output.pfpa_logger import PFPA_ARCHIVE`](forecast_output/pfpa_logger.py:1): Used only within the [`simulate_age_decay_test()`](forecast_output/forecast_age_tracker.py:81) function.
*   **External Library Dependencies:**
    *   `datetime`: For handling timestamps and calculating age.
    *   `typing` (List, Dict): For type hinting.
*   **Interaction via Shared Data:**
    *   The module operates on `forecast` dictionaries, expecting and modifying keys such as `timestamp`, `confidence`, and `priority_score`. It adds `age_hours` and `age_tag`.
*   **Input/Output Files:**
    *   Reads configuration from [`PATHS`](core/path_registry.py:1) to determine `AGE_LOG_PATH` ([`forecast_output/forecast_age_tracker.py:22`](forecast_output/forecast_age_tracker.py:22)).
    *   No explicit file writing in the core logic, though `AGE_LOG_PATH` suggests potential intent for logging to a file.

## 5. Function and Class Example Usages

*   **[`attach_timestamp(forecast: Dict) -> Dict`](forecast_output/forecast_age_tracker.py:25):**
    ```python
    my_forecast = {"data": "some_value"}
    timestamped_forecast = attach_timestamp(my_forecast)
    # timestamped_forecast will now have a "timestamp" key
    # e.g., {"data": "some_value", "timestamp": "2023-10-27T10:30:00.123456"}
    ```
*   **[`get_forecast_age(forecast: Dict) -> float`](forecast_output/forecast_age_tracker.py:34):**
    ```python
    # Assuming forecast was timestamped 2 hours ago
    forecast_with_ts = {"timestamp": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()}
    age_in_hours = get_forecast_age(forecast_with_ts)
    # age_in_hours will be approximately 2.0
    ```
*   **[`decay_confidence_and_priority(forecast: Dict, decay_per_hour: float = 0.01, ...) -> Dict`](forecast_output/forecast_age_tracker.py:50):**
    ```python
    fresh_forecast = {"timestamp": datetime.datetime.utcnow().isoformat(), "confidence": 0.9, "priority_score": 0.8}
    # Simulate 15 hours passing
    fresh_forecast["timestamp"] = (datetime.datetime.utcnow() - datetime.timedelta(hours=15)).isoformat()
    decayed_forecast = decay_confidence_and_priority(fresh_forecast)
    # decayed_forecast["confidence"] would be 0.9 - (0.01 * 15) = 0.75 (approx)
    # decayed_forecast["priority_score"] would be 0.8 - (0.01 * 15) = 0.65 (approx)
    # decayed_forecast["age_hours"] would be 15.0
    # decayed_forecast["age_tag"] would be "📉 Decayed"
    ```
*   **[`prune_stale_forecasts(forecasts: List[Dict], max_age_hours: float = 24.0) -> List[Dict]`](forecast_output/forecast_age_tracker.py:74):**
    ```python
    list_of_forecasts = [
        {"timestamp": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()}, # Fresh
        {"timestamp": (datetime.datetime.utcnow() - datetime.timedelta(hours=30)).isoformat()}  # Stale
    ]
    active_forecasts = prune_stale_forecasts(list_of_forecasts, max_age_hours=24.0)
    # active_forecasts will only contain the first forecast
    ```

## 6. Hardcoding Issues

*   **Default Decay Parameters:** In [`decay_confidence_and_priority()`](forecast_output/forecast_age_tracker.py:50):
    *   `decay_per_hour: float = 0.01`
    *   `min_confidence: float = 0.1`
    *   `min_priority: float = 0.05`
    These values are hardcoded as default arguments. For greater flexibility, they could be sourced from a configuration file.
*   **Age Thresholds for Tagging:** In [`decay_confidence_and_priority()`](forecast_output/forecast_age_tracker.py:50):
    *   `12` hours for "📉 Decayed" tag.
    *   `24` hours for "❌ Expired" tag (though current logic might prevent this tag from being applied correctly, see section 3).
    These thresholds are magic numbers and could be configurable.
*   **Default Pruning Age:** In [`prune_stale_forecasts()`](forecast_output/forecast_age_tracker.py:74):
    *   `max_age_hours: float = 24.0` is a hardcoded default.
*   **Age Tags:** The strings "📉 Decayed", "❌ Expired", "🕒 Fresh" are hardcoded. While likely stable, making them constants or configurable could be considered for i18n or thematic changes.

## 7. Coupling Points

*   **Forecast Dictionary Structure:** The module is tightly coupled to the expected structure of forecast dictionaries (presence of `timestamp`, `confidence`, `priority_score` keys). Changes to this structure elsewhere could break this module.
*   **[`core.path_registry.PATHS`](core/path_registry.py:1):** Dependency for `AGE_LOG_PATH` configuration.
*   **[`forecast_output.pfpa_logger`](forecast_output/pfpa_logger.py:1):** The test/simulation function [`simulate_age_decay_test()`](forecast_output/forecast_age_tracker.py:81) directly imports and uses `PFPA_ARCHIVE` from this module.

## 8. Existing Tests

*   An inline test/simulation function [`simulate_age_decay_test()`](forecast_output/forecast_age_tracker.py:81) is present, executed when the script is run directly (`if __name__ == "__main__":`). This function demonstrates the decay logic using data from `PFPA_ARCHIVE`.
*   This is not a formal unit test suite (e.g., using `pytest` or `unittest`).
*   No separate test file (e.g., `tests/forecast_output/test_forecast_age_tracker.py`) is immediately evident from the provided file listing, suggesting a potential gap in formal, isolated unit testing for this module.

## 9. Module Architecture and Flow

*   **Architecture:** The module follows a procedural programming paradigm, providing a collection of utility functions that operate on forecast data (dictionaries). It does not define any classes.
*   **Key Components:**
    *   Timestamping function: [`attach_timestamp()`](forecast_output/forecast_age_tracker.py:25)
    *   Age calculation function: [`get_forecast_age()`](forecast_output/forecast_age_tracker.py:34)
    *   Decay and tagging function: [`decay_confidence_and_priority()`](forecast_output/forecast_age_tracker.py:50)
    *   Pruning function: [`prune_stale_forecasts()`](forecast_output/forecast_age_tracker.py:74)
*   **Primary Data/Control Flows:**
    1.  A forecast dictionary is created or received.
    2.  [`attach_timestamp()`](forecast_output/forecast_age_tracker.py:25) can be called to add a `timestamp` if missing.
    3.  Periodically, or before use, [`decay_confidence_and_priority()`](forecast_output/forecast_age_tracker.py:50) is called on a forecast. This function internally calls [`get_forecast_age()`](forecast_output/forecast_age_tracker.py:34) to determine the age, then updates `confidence`, `priority_score`, adds `age_hours`, and sets an `age_tag`.
    4.  A list of forecasts can be passed to [`prune_stale_forecasts()`](forecast_output/forecast_age_tracker.py:74), which uses [`get_forecast_age()`](forecast_output/forecast_age_tracker.py:34) for each forecast to filter out those exceeding `max_age_hours`.
    *   Error handling for `datetime.fromisoformat` in [`get_forecast_age()`](forecast_output/forecast_age_tracker.py:34) returns `0.0`, effectively treating malformed timestamps as fresh forecasts.

## 10. Naming Conventions

*   **Functions:** Names like [`attach_timestamp`](forecast_output/forecast_age_tracker.py:25), [`get_forecast_age`](forecast_output/forecast_age_tracker.py:34), [`decay_confidence_and_priority`](forecast_output/forecast_age_tracker.py:50), and [`prune_stale_forecasts`](forecast_output/forecast_age_tracker.py:74) are descriptive, use `snake_case`, and adhere to PEP 8.
*   **Variables:** Local variables (e.g., `ts`, `then`, `now`, `delta`, `age`) and parameters (e.g., `forecast`, `decay_per_hour`, `min_confidence`) also use `snake_case` and are generally clear.
*   **Constants:** `AGE_LOG_PATH` ([`forecast_output/forecast_age_tracker.py:22`](forecast_output/forecast_age_tracker.py:22)) is in `UPPER_SNAKE_CASE`, which is conventional for constants.
*   **Overall:** Naming conventions are consistent and follow Python best practices (PEP 8). There are no obvious AI-generated or unconventional naming patterns. The names appear to be human-readable and semantically appropriate.