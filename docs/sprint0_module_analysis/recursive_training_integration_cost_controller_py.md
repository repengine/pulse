# Module Analysis: `recursive_training.integration.cost_controller`

**File Path:** [`recursive_training/integration/cost_controller.py`](../../recursive_training/integration/cost_controller.py)

## 1. Module Intent/Purpose

The `cost_controller.py` module provides a central service for monitoring, tracking, and limiting API and token usage costs within the Recursive Training System. Its primary role is to prevent exceeding budgetary thresholds by enforcing configurable daily, monthly, and total cost limits. The module also aims to offer features such as rate limiting for API calls, cost estimation for planned operations, generation of cost reports and forecasts, and triggering alerts or system shutdowns when cost thresholds are critically breached.

## 2. Operational Status/Completeness

The module appears largely complete and operational for its core responsibilities of cost tracking, limit enforcement, and rate limiting. Key functionalities like initialization with configuration, loading historical cost data from a metrics store, updating cost status (OK, WARNING, CRITICAL, SHUTDOWN), and basic cost estimation are implemented.

However, some features mentioned in docstrings are either placeholders or not fully realized:
*   The `track_operation` method ([`recursive_training/integration/cost_controller.py:310`](../../recursive_training/integration/cost_controller.py:310)) is a placeholder and requires full implementation for detailed tracking of specific operations beyond general API calls/token usage.
*   Alerting mechanisms are mentioned but not implemented; the module updates status but doesn't actively send notifications.
*   The "shutdown" enforcement relies on other system components checking the status rather than the module actively halting operations.

## 3. Implementation Gaps / Unfinished Next Steps

*   **`track_operation` Method:** The method [`track_operation(operation_type: str, data_size: int = 0, duration: float = 0.0, cost: float = 0.0)`](../../recursive_training/integration/cost_controller.py:310) is currently a placeholder. It logs the call but doesn't perform actual metric updates or storage. This needs to be implemented to track costs associated with specific, potentially complex operations.
*   **Alerting System:** The module's docstring ([`recursive_training/integration/cost_controller.py:48`](../../recursive_training/integration/cost_controller.py:48)) mentions triggering alerts. While `CostStatus` can change to `WARNING`, `CRITICAL`, or `SHUTDOWN`, there's no implemented mechanism to actively send notifications (e.g., email, Slack messages) to operators.
*   **Shutdown Enforcement:** The module sets a `CostStatus.SHUTDOWN` ([`recursive_training/integration/cost_controller.py:182`](../../recursive_training/integration/cost_controller.py:182)), and `can_make_api_call` ([`recursive_training/integration/cost_controller.py:399`](../../recursive_training/integration/cost_controller.py:399)) will return `False`. However, the broader system-level actions for a shutdown (e.g., gracefully stopping ongoing tasks, preventing new ones system-wide) are not handled within this module and would depend on other components respecting this status.
*   **Advanced Cost Estimation:** The docstring mentions "Offer cost estimation for planned operations" ([`recursive_training/integration/cost_controller.py:46`](../../recursive_training/integration/cost_controller.py:46)). The current cost estimation within `track_cost` ([`recursive_training/integration/cost_controller.py:260-269`](../../recursive_training/integration/cost_controller.py:260-269)) and `can_make_api_call` ([`recursive_training/integration/cost_controller.py:390`](../../recursive_training/integration/cost_controller.py:390)) is basic (fixed rate per token/call). A more sophisticated feature for proactively estimating costs of complex, planned operations could be beneficial.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   `from recursive_training.metrics.metrics_store import get_metrics_store` ([`recursive_training/integration/cost_controller.py:18`](../../recursive_training/integration/cost_controller.py:18))

### External Library Dependencies:
*   `logging`: For application logging.
*   `json`: Imported ([`recursive_training/integration/cost_controller.py:10`](../../recursive_training/integration/cost_controller.py:10)) but not explicitly used in the provided code; potentially for future configuration or data handling.
*   `threading`: Used for `self.call_history_lock` ([`recursive_training/integration/cost_controller.py:117`](../../recursive_training/integration/cost_controller.py:117)) to ensure thread-safe updates to API call timestamps.
*   `time`: Imported ([`recursive_training/integration/cost_controller.py:12`](../../recursive_training/integration/cost_controller.py:12)) but `datetime` is primarily used for time-related operations.
*   `datetime` (from `datetime`): Extensively used for managing timestamps, daily/monthly cost periods, and rate limit windows.
*   `Enum` (from `enum`): Used to define `CostStatus` ([`recursive_training/integration/cost_controller.py:21`](../../recursive_training/integration/cost_controller.py:21)).

### Interactions via Shared Data:
*   **MetricsStore:** The module is tightly coupled with the `MetricsStore` (obtained via `get_metrics_store()`). It uses the store to:
    *   Load historical cost data upon initialization ([`_load_historical_data`](../../recursive_training/integration/cost_controller.py:131)).
    *   Persist new cost data via `metrics_store.track_cost()` ([`recursive_training/integration/cost_controller.py:295`](../../recursive_training/integration/cost_controller.py:295)).
    *   Query metrics for forecasting ([`get_cost_forecast`](../../recursive_training/integration/cost_controller.py:466)).

### Input/Output Files:
*   **Logs:** Generates logs via the `logging` module. The destination of these logs depends on the logging configuration of the broader system.
*   **Metrics Data:** Relies on the `MetricsStore` for persistence. The actual files or database backing the `MetricsStore` are abstracted.

## 5. Function and Class Example Usages

### `CostController` Class
The `CostController` is designed as a singleton.

**Initialization:**
```python
from recursive_training.integration.cost_controller import get_cost_controller

# Configuration (optional, defaults are provided in the class)
config = {
    "daily_cost_limit_usd": 15.0,
    "monthly_cost_limit_usd": 200.0,
    "warning_threshold_percentage": 75,
    # ... other config options
}

cost_ctrl = get_cost_controller(config)
# or to get existing instance:
# cost_ctrl = get_cost_controller()
```

**Tracking Costs:**
```python
# Track cost based on API calls and token usage
cost_info = cost_ctrl.track_cost(api_calls=1, token_usage=1500)
print(f"Cost tracked: {cost_info['cost_usd']:.4f} USD, Status: {cost_info['status']}")

# Track a direct cost
cost_info = cost_ctrl.track_cost(direct_cost=0.05)
```
See [`track_cost()`](../../recursive_training/integration/cost_controller.py:242).

**Checking if an API Call Can Be Made:**
```python
if cost_ctrl.can_make_api_call(count=1, token_estimate=500):
    print("API call allowed.")
    # Proceed with API call
    cost_ctrl.track_cost(api_calls=1, token_usage=500) # Remember to track after successful call
else:
    print("API call rejected due to rate or cost limits.")
```
See [`can_make_api_call()`](../../recursive_training/integration/cost_controller.py:369).

**Checking Cost Limits Before an Operation:**
```python
from recursive_training.integration.cost_controller import CostLimitException

estimated_operation_cost = 2.50  # USD
try:
    cost_ctrl.check_cost_limit(estimated_cost=estimated_operation_cost)
    print(f"Operation with estimated cost ${estimated_operation_cost:.2f} is within limits.")
    # Proceed with operation
except CostLimitException as e:
    print(f"Operation rejected: {e}")
```
See [`check_cost_limit()`](../../recursive_training/integration/cost_controller.py:324).

**Getting Cost Summary:**
```python
summary = cost_ctrl.get_cost_summary()
print(f"Current Status: {summary['current_status']}")
print(f"Daily Cost: ${summary['daily']['cost_usd']:.2f} / ${summary['daily']['limit_usd']:.2f}")
# ... and so on for monthly, total, etc.
```
See [`get_cost_summary()`](../../recursive_training/integration/cost_controller.py:405).

**Getting Cost Forecast:**
```python
forecast = cost_ctrl.get_cost_forecast(days_ahead=7)
print(f"Projected cost for next 7 days: ${forecast['projected_cost_usd']:.2f}")
```
See [`get_cost_forecast()`](../../recursive_training/integration/cost_controller.py:452).

### `CostStatus` Enum
Used internally to represent the operational status concerning costs.
```python
from recursive_training.integration.cost_controller import CostStatus

current_status = cost_ctrl.current_status # Accessing the status
if current_status == CostStatus.CRITICAL:
    print("Cost status is CRITICAL!")
```
Defined at [`recursive_training/integration/cost_controller.py:21`](../../recursive_training/integration/cost_controller.py:21).

### `CostLimitException` Exception
Raised by `check_cost_limit` when an operation would exceed a defined cost threshold.
```python
# Example shown in "Checking Cost Limits Before an Operation"
```
Defined at [`recursive_training/integration/cost_controller.py:29`](../../recursive_training/integration/cost_controller.py:29).

## 6. Hardcoding Issues

The module uses default values for limits and thresholds if they are not provided in the configuration dictionary during initialization. These defaults are hardcoded:

*   **Default Cost Limits:**
    *   `daily_cost_limit_usd`: `10.0` ([`recursive_training/integration/cost_controller.py:83`](../../recursive_training/integration/cost_controller.py:83))
    *   `monthly_cost_limit_usd`: `100.0` ([`recursive_training/integration/cost_controller.py:84`](../../recursive_training/integration/cost_controller.py:84))
    *   `total_cost_limit_usd`: `1000.0` ([`recursive_training/integration/cost_controller.py:85`](../../recursive_training/integration/cost_controller.py:85))
*   **Default Threshold Percentages:**
    *   `warning_threshold_percentage`: `70` ([`recursive_training/integration/cost_controller.py:88`](../../recursive_training/integration/cost_controller.py:88))
    *   `critical_threshold_percentage`: `90` ([`recursive_training/integration/cost_controller.py:89`](../../recursive_training/integration/cost_controller.py:89))
*   **Default Rate Limits:**
    *   `max_calls_per_minute`: `60` ([`recursive_training/integration/cost_controller.py:93`](../../recursive_training/integration/cost_controller.py:93))
    *   `max_calls_per_hour`: `500` ([`recursive_training/integration/cost_controller.py:94`](../../recursive_training/integration/cost_controller.py:94))
    *   `max_calls_per_day`: `5000` ([`recursive_training/integration/cost_controller.py:95`](../../recursive_training/integration/cost_controller.py:95))
*   **Cost Estimation Factors (Magic Numbers):**
    *   Token cost: `0.000002` (implying $0.002 per 1000 tokens) ([`recursive_training/integration/cost_controller.py:262`](../../recursive_training/integration/cost_controller.py:262), also used in [`recursive_training/integration/cost_controller.py:390`](../../recursive_training/integration/cost_controller.py:390)).
    *   API call cost: `0.001` (implying $0.001 per API call) ([`recursive_training/integration/cost_controller.py:266`](../../recursive_training/integration/cost_controller.py:266), also used in [`recursive_training/integration/cost_controller.py:390`](../../recursive_training/integration/cost_controller.py:390)).
    While the primary limits are configurable via the `config` dict, these specific per-token/per-call rates for *estimation* are hardcoded within the methods. For a system dealing with multiple types of APIs or evolving costs, these might need to be more flexible or part of the configuration.
*   **Metrics Store Interaction Details:**
    *   Metric type for queries: `metric_types=["cost"]` (e.g., [`recursive_training/integration/cost_controller.py:140`](../../recursive_training/integration/cost_controller.py:140)).
    *   Keys for metrics summary: `summary["cost_tracking"]["total_cost"]`, etc. (e.g., [`recursive_training/integration/cost_controller.py:164`](../../recursive_training/integration/cost_controller.py:164)). These assume a fixed structure from the `MetricsStore`.

## 7. Coupling Points

*   **`MetricsStore`:** The `CostController` is tightly coupled to the `MetricsStore` interface (obtained via `get_metrics_store()`). It relies on specific methods like `query_metrics`, `get_metrics_summary`, and `track_cost`, and expects particular data structures in return. Changes to the `MetricsStore` API or data format could break the `CostController`.
*   **Configuration Dictionary:** The module's behavior (limits, thresholds) is heavily dependent on the structure and keys within the `config` dictionary passed at initialization. Missing or misspelled keys would lead to default (hardcoded) values being used.
*   **External System Components:** There's an implicit coupling with other parts of the system that are expected to:
    *   Correctly instantiate and use the `CostController` singleton.
    *   Reliably call `track_cost()` after incurring costs.
    *   Proactively check `can_make_api_call()` or `check_cost_limit()` before potentially costly operations.
    *   Monitor and react to the `CostStatus`, especially `SHUTDOWN`.

## 8. Existing Tests

Based on the provided file list in the initial environment details, there is no specific test file named `test_cost_controller.py` within the `tests/recursive_training/integration/` directory or a similar relevant location.

**Conclusion:** There appear to be **no dedicated unit tests** for the `cost_controller.py` module. This is a significant gap, as the logic for cost calculation, limit enforcement, status changes, and rate limiting is critical and complex enough to warrant thorough testing.

## 9. Module Architecture and Flow

### Architecture:
*   **Singleton Pattern:** The `CostController` class ([`recursive_training/integration/cost_controller.py:38`](../../recursive_training/integration/cost_controller.py:38)) is implemented as a singleton using a class method `get_instance()` ([`recursive_training/integration/cost_controller.py:55`](../../recursive_training/integration/cost_controller.py:55)) and a private class variable `_instance`.
*   **State Management:** Uses an enumeration `CostStatus` ([`recursive_training/integration/cost_controller.py:21`](../../recursive_training/integration/cost_controller.py:21)) to define and manage its operational state regarding cost limits.
*   **Exception Handling:** Defines a custom exception `CostLimitException` ([`recursive_training/integration/cost_controller.py:29`](../../recursive_training/integration/cost_controller.py:29)) for clear error signaling when limits are exceeded.
*   **Data Persistence Abstraction:** Interacts with a `MetricsStore` for loading historical data and saving ongoing cost metrics, abstracting the actual storage mechanism.
*   **Concurrency Control:** Uses a `threading.Lock` ([`recursive_training/integration/cost_controller.py:117`](../../recursive_training/integration/cost_controller.py:117)) to protect access to `self.call_timestamps`, ensuring thread safety for rate limiting checks.
*   **Configuration Driven:** Key parameters like cost limits and thresholds are configurable via a dictionary at initialization.

### Key Components:
*   **`CostController` Class:** The central component managing all logic.
*   **Cost Accumulators:** Internal variables track `current_day_cost`, `current_month_cost`, `total_cost`, and corresponding API call/token usage counts.
*   **Limit Definitions:** Stores `daily_limit`, `monthly_limit`, `total_limit`, and warning/critical thresholds.
*   **Rate Limiting Mechanism:** `call_timestamps` list and `_check_rate_limits()` method ([`recursive_training/integration/cost_controller.py:210`](../../recursive_training/integration/cost_controller.py:210)).
*   **Status Management:** `current_status` variable and `_update_status()` method ([`recursive_training/integration/cost_controller.py:176`](../../recursive_training/integration/cost_controller.py:176)).
*   **Temporal Logic:** `_check_day_change()` method ([`recursive_training/integration/cost_controller.py:190`](../../recursive_training/integration/cost_controller.py:190)) handles resets for daily and monthly counters.

### Primary Data/Control Flows:
1.  **Initialization (`__init__`, `get_instance`):**
    *   Singleton instance is created/retrieved.
    *   Logger and `MetricsStore` are initialized.
    *   Configuration is loaded (limits, thresholds, rate limits).
    *   Internal cost/usage counters are initialized.
    *   Historical data is loaded from `MetricsStore` via `_load_historical_data()`.
    *   Initial `current_status` is determined via `_update_status()`.
2.  **Cost Tracking (`track_cost`):**
    *   `_check_day_change()` is called to reset counters if a new day/month has begun.
    *   Cost is calculated (either direct or estimated from tokens/API calls).
    *   Daily, monthly, and total cost/usage accumulators are updated.
    *   API call timestamps are recorded for rate limiting.
    *   `_update_status()` is called to reflect new totals.
    *   The new cost entry is persisted to `MetricsStore`.
    *   A summary of the tracking event is returned.
3.  **Pre-emptive Checks (`check_cost_limit`, `can_make_api_call`):**
    *   `_check_day_change()` is called.
    *   For `can_make_api_call()`:
        *   `_check_rate_limits()` is invoked. If limits exceeded, returns `False`.
        *   If `check_cost` is `True`, an estimated cost is calculated.
        *   `check_cost_limit()` is called with this estimate. If `CostLimitException` is raised, returns `False`.
        *   If `current_status` is `SHUTDOWN`, returns `False`.
        *   Otherwise, returns `True`.
    *   For `check_cost_limit()`:
        *   Checks if `estimated_cost` plus current daily/monthly/total costs would exceed their respective limits.
        *   Raises `CostLimitException` if any limit is breached.
        *   Returns `True` if all limits are respected.
4.  **Reporting (`get_cost_summary`, `get_cost_forecast`):**
    *   `_check_day_change()` is called.
    *   `get_cost_summary()`: Compiles current costs, limits, usage statistics, and status into a dictionary.
    *   `get_cost_forecast()`: Queries recent metrics from `MetricsStore`, calculates an average daily cost, and projects costs for a specified future period.

## 10. Naming Conventions

*   **Classes:** `CostController`, `CostStatus`, `CostLimitException`. Follow PascalCase, are descriptive, and adhere to PEP 8.
*   **Methods:** `get_instance`, `track_cost`, `_load_historical_data`, `_check_day_change`. Use snake_case, are action-oriented, and adhere to PEP 8. Internal/protected methods are correctly prefixed with a single underscore.
*   **Variables & Attributes:** `daily_limit`, `current_day_cost`, `api_calls`, `call_history_lock`. Use snake_case, are descriptive, and adhere to PEP 8.
*   **Enum Members:** `CostStatus.OK`, `CostStatus.WARNING`. Uppercase, which is a common and clear convention for enum members.
*   **Configuration Keys (expected in `config` dict):** `daily_cost_limit_usd`, `warning_threshold_percentage`. snake_case and descriptive.
*   **Overall Consistency:** Naming is highly consistent throughout the module and aligns well with Python community standards (PEP 8). The names are generally self-documenting, and there are no apparent AI assumption errors or significant deviations from standard practices.