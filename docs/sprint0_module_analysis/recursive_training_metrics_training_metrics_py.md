# Module Analysis: `recursive_training/metrics/training_metrics.py`

## 1. Module Intent/Purpose

The primary role of the module [`recursive_training/metrics/training_metrics.py`](../../recursive_training/metrics/training_metrics.py:1) is to implement comprehensive metrics calculation and tracking for the recursive training system. Its responsibilities include:
*   Calculating standard error and performance metrics (e.g., MSE, MAE, RMSE, accuracy, F1-score, R2-score, precision, recall).
*   Tracking training progress across iterations.
*   Monitoring training-related costs (API calls, token usage).
*   Assessing training convergence.
*   Comparing the performance of different models.
*   Evaluating the performance specific to different rule types (symbolic, neural, hybrid).
*   Storing and retrieving metrics via a dedicated `MetricsStore`.

## 2. Operational Status/Completeness

The module appears largely complete and operational for its defined scope.
*   It provides fallback mechanisms for metric calculations if optional dependencies like `numpy` or `scikit-learn` are unavailable.
*   The [`evaluate_rule_performance()`](../../recursive_training/metrics/training_metrics.py:630) method demonstrates robust handling for various input scenarios, including summarizing historical performance for rule types.
*   A line in [`calculate_r2_score()`](../../recursive_training/metrics/training_metrics.py:283) ([`line 296`](../../recursive_training/metrics/training_metrics.py:296)) `return float('nan')` is commented as "Should be unreachable", suggesting it might be a remnant or a way to satisfy static analysis, as valid logic follows.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Configurable Cost Estimation:** The token cost estimation in [`track_cost()`](../../recursive_training/metrics/training_metrics.py:512) ([`line 533`](../../recursive_training/metrics/training_metrics.py:533)) uses a hardcoded factor (`0.000002`). This should ideally be configurable.
*   **F1 Score 'samples' Average:** A comment in [`calculate_f1_score()`](../../recursive_training/metrics/training_metrics.py:234) ([`line 264`](../../recursive_training/metrics/training_metrics.py:264)) notes that the `'samples'` averaging method might need more robust handling or clearer documentation for its applicability.
*   **Externalized Rule Types:** The `summary_rule_types` used in [`get_performance_summary()`](../../recursive_training/metrics/training_metrics.py:785) ([`line 818`](../../recursive_training/metrics/training_metrics.py:818)) are expected from the configuration. While flexible, the module itself doesn't define or validate these types.

## 4. Connections & Dependencies

*   **Direct Project Imports:**
    *   `from recursive_training.metrics.metrics_store import get_metrics_store` ([`recursive_training/metrics/training_metrics.py:33`](../../recursive_training/metrics/training_metrics.py:33)): For interacting with the metrics persistence layer.
*   **External Library Dependencies:**
    *   `logging` (Python standard library)
    *   `json` (Python standard library)
    *   `math` (Python standard library)
    *   `datetime` (Python standard library)
    *   `typing` (Python standard library)
    *   `pandas` (Optional, type hints and some data manipulation)
    *   `numpy` (Optional, for optimized MSE, MAE calculations if `NUMPY_AVAILABLE` is true ([`recursive_training/metrics/training_metrics.py:21`](../../recursive_training/metrics/training_metrics.py:21)))
    *   `sklearn.metrics` (Optional, for accuracy, F1, R2, precision, recall if `SKLEARN_AVAILABLE` is true ([`recursive_training/metrics/training_metrics.py:27`](../../recursive_training/metrics/training_metrics.py:27)))
*   **Shared Data Interaction:**
    *   Primarily interacts with the `MetricsStore` (obtained via [`get_metrics_store()`](../../recursive_training/metrics/training_metrics.py:33)) for storing and retrieving all metrics data.
*   **Input/Output Files:**
    *   No direct file I/O beyond logging. Relies on the `MetricsStore` for data persistence.

## 5. Function and Class Example Usages

### `RecursiveTrainingMetrics` Class

```python
from recursive_training.metrics.training_metrics import RecursiveTrainingMetrics
import pandas as pd

# Minimal config, assuming metrics_store is set up elsewhere or uses defaults
config = {
    "convergence_threshold": 0.0005,
    "alert_threshold": 0.05,
    "summary_rule_types": ["symbolic", "neural"] # Example rule types for summary
}
metrics_tracker = RecursiveTrainingMetrics(config=config)

# Example data
true_values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
predicted_values = pd.Series([1.1, 1.9, 3.2, 3.8, 5.3])
true_labels = pd.Series([0, 1, 0, 1, 0])
predicted_labels = pd.Series([0, 1, 1, 1, 0])

# 1. Calculate basic metrics
mse = metrics_tracker.calculate_mse(true_values, predicted_values)
mae = metrics_tracker.calculate_mae(true_values, predicted_values)
accuracy = metrics_tracker.calculate_accuracy(true_labels, predicted_labels)
f1 = metrics_tracker.calculate_f1_score(true_labels, predicted_labels, average='weighted')

print(f"MSE: {mse}, MAE: {mae}, Accuracy: {accuracy}, F1: {f1}")

# 2. Track an iteration
iteration_data = {
    "mse": mse, "mae": mae, "accuracy": accuracy, "f1_score": f1,
    "custom_metric": 0.75
}
metrics_tracker.track_iteration(
    iteration=1,
    metrics=iteration_data,
    model_name="MyAwesomeModel_v1",
    rule_type="hybrid",
    tags=["experiment_A", "initial_run"]
)

# 3. Set a baseline for comparison
baseline_metrics = {"mse": 0.05, "mae": 0.02, "accuracy": 0.98, "f1_score": 0.97}
metrics_tracker.set_baseline(baseline_metrics)

# Simulate another iteration to check alerts and convergence
iteration_data_2 = {"mse": 0.06, "mae": 0.025, "accuracy": 0.96, "f1_score": 0.95}
metrics_tracker.track_iteration(iteration=2, metrics=iteration_data_2, model_name="MyAwesomeModel_v1", rule_type="hybrid")
# This might trigger an alert if mse 0.06 > baseline_mse 0.05 * (1 + alert_threshold 0.05)

# 4. Track costs
cost_info = metrics_tracker.track_cost(api_calls=100, token_usage=250000, cost=0.50)
print(f"Updated cost info: {cost_info}")

# 5. Check convergence
is_converged = metrics_tracker.check_convergence()
print(f"Training converged: {is_converged}")

# 6. Compare models (assuming another model's metrics were tracked)
# metrics_tracker.track_iteration(iteration=1, metrics={"mse": 0.04}, model_name="MyBetterModel_v1")
# comparison = metrics_tracker.compare_models(model_names=["MyAwesomeModel_v1", "MyBetterModel_v1"], metric_name="mse")
# print(f"Model comparison: {comparison}")

# 7. Evaluate rule performance (for a specific rule's predictions)
# rule_id_dict = {"id": "R001", "type": "symbolic"}
# rule_perf = metrics_tracker.evaluate_rule_performance(
#     rule_identifier=rule_id_dict,
#     rule_actuals=true_values,
#     rule_predictions=predicted_values
# )
# print(f"Performance for rule {rule_id_dict['id']}: {rule_perf}")

# 8. Evaluate aggregated rule type performance (based on tracked iterations)
# First, ensure some iterations for "symbolic" rule_type are tracked:
metrics_tracker.track_iteration(iteration=1, metrics={"mse": 0.1, "mae": 0.05}, model_name="SymbolicModel", rule_type="symbolic")
metrics_tracker.track_iteration(iteration=2, metrics={"mse": 0.09, "mae": 0.04}, model_name="SymbolicModel", rule_type="symbolic")

symbolic_summary = metrics_tracker.evaluate_rule_performance(rule_identifier="symbolic")
print(f"Aggregated performance for 'symbolic' rules: {symbolic_summary}")

# 9. Get summaries
cost_summary = metrics_tracker.get_cost_summary()
performance_summary = metrics_tracker.get_performance_summary()

print(f"Cost Summary: {cost_summary}")
print(f"Performance Summary: {performance_summary}")
```

## 6. Hardcoding Issues

*   **Default Thresholds:**
    *   [`convergence_threshold`](../../recursive_training/metrics/training_metrics.py:61): `0.001`
    *   [`max_iterations`](../../recursive_training/metrics/training_metrics.py:62): `100`
    *   [`early_stopping_patience`](../../recursive_training/metrics/training_metrics.py:63): `5`
    *   [`alert_threshold`](../../recursive_training/metrics/training_metrics.py:64): `0.1`
*   **Cost Estimation:**
    *   Token cost factor in [`track_cost()`](../../recursive_training/metrics/training_metrics.py:512) is `0.000002` ([`line 533`](../../recursive_training/metrics/training_metrics.py:533)), representing an assumed `$0.002 per 1000 tokens`. This is a significant magic number tied to external pricing.
*   **Metric Names (Strings):**
    *   Keys like `"mse"`, `"mae"`, `"rmse"`, `"accuracy"`, `"f1_score"` are used as string literals in multiple locations (e.g., [`_check_metrics_alerts()`](../../recursive_training/metrics/training_metrics.py:464), [`compare_models()`](../../recursive_training/metrics/training_metrics.py:584), [`get_performance_summary()`](../../recursive_training/metrics/training_metrics.py:785)).
*   **Rule Types:**
    *   The strings `"symbolic"`, `"neural"`, `"hybrid"` are used as keys for `self.rule_performance` ([`recursive_training/metrics/training_metrics.py:77`](../../recursive_training/metrics/training_metrics.py:77)).
*   **Scikit-learn `zero_division` Parameter:**
    *   Set to `0` in calls to `f1_score`, `precision_score`, `recall_score` (e.g., [`calculate_f1_score()`](../../recursive_training/metrics/training_metrics.py:255)). This defines behavior when a class has no predicted or true samples.

## 7. Coupling Points

*   **`MetricsStore`:** Tightly coupled with the `MetricsStore` abstraction, obtained via [`get_metrics_store()`](../../recursive_training/metrics/training_metrics.py:33) from [`recursive_training.metrics.metrics_store`](../../recursive_training/metrics/metrics_store.py:1). All metric persistence and some retrieval operations depend on this store.
*   **Configuration Dictionary:** The behavior of the `RecursiveTrainingMetrics` class is influenced by the configuration dictionary passed during initialization (e.g., for default thresholds, `summary_rule_types`).
*   **Optional Libraries (`numpy`, `sklearn`):** The module's performance and set of available metrics are enhanced by these optional libraries, but it maintains basic functionality without them.

## 8. Existing Tests

*   A corresponding test file, [`tests/recursive_training/test_training_metrics.py`](../../tests/recursive_training/test_training_metrics.py), exists, indicating that unit tests are in place for this module.
*   The code contains comments suggesting test awareness, such as handling for pandas Series inputs in scikit-learn calls and providing default structures in [`evaluate_rule_performance()`](../../recursive_training/metrics/training_metrics.py:630) to prevent errors in tests (e.g., [`line 679`](../../recursive_training/metrics/training_metrics.py:679), [`line 733`](../../recursive_training/metrics/training_metrics.py:733)).
*   The exact coverage and nature of test gaps cannot be determined without inspecting the test file itself.

## 9. Module Architecture and Flow

The module is structured around the `RecursiveTrainingMetrics` class:

1.  **Initialization (`__init__`)**:
    *   Sets up logging, stores the provided configuration.
    *   Initializes an instance of `MetricsStore` using [`get_metrics_store()`](../../recursive_training/metrics/training_metrics.py:33).
    *   Sets default values for various thresholds (convergence, max iterations, early stopping, alert).
    *   Initializes internal state variables: `current_metrics`, `baseline_metrics`, `iteration_history`, `training_costs`, and `rule_performance` (a dictionary to store metrics per rule type per iteration).

2.  **Core Metric Calculation Methods** (e.g., [`calculate_mse()`](../../recursive_training/metrics/training_metrics.py:126), [`calculate_mae()`](../../recursive_training/metrics/training_metrics.py:155), [`calculate_accuracy()`](../../recursive_training/metrics/training_metrics.py:205), etc.):
    *   Perform input validation using the internal [`_validate_data()`](../../recursive_training/metrics/training_metrics.py:83) method (checks for length mismatch and empty data).
    *   Use the internal [`_safe_calculation()`](../../recursive_training/metrics/training_metrics.py:104) wrapper to execute the actual metric computation, which handles potential exceptions and returns a default value (often `float('nan')`) on error.
    *   Prioritize using `numpy` or `scikit-learn` for calculations if these libraries are available (checked by `NUMPY_AVAILABLE` and `SKLEARN_AVAILABLE` flags).
    *   Provide pure Python fallback implementations if the optional libraries are not found.

3.  **Tracking Methods:**
    *   [`track_iteration()`](../../recursive_training/metrics/training_metrics.py:412):
        *   Takes iteration number, a dictionary of metrics, model name, optional rule type, and tags.
        *   Constructs a metrics record with a timestamp.
        *   Stores this record using `self.metrics_store.store_metric()`.
        *   Appends the record to `self.iteration_history`.
        *   Updates `self.current_metrics`.
        *   If `rule_type` is provided, updates `self.rule_performance[rule_type][iteration]` with the metrics.
        *   Calls [`_check_metrics_alerts()`](../../recursive_training/metrics/training_metrics.py:464) to compare against baseline.
    *   [`set_baseline()`](../../recursive_training/metrics/training_metrics.py:493):
        *   Copies the provided metrics into `self.baseline_metrics`.
        *   Stores these baseline metrics in the `metrics_store` with a specific `metric_type` tag.
    *   [`track_cost()`](../../recursive_training/metrics/training_metrics.py:512):
        *   Updates internal `self.training_costs` (api_calls, token_usage, total_cost).
        *   Estimates cost from token usage if direct cost is not provided (using a hardcoded rate).
        *   Stores cost details in the `metrics_store`.
        *   Calls `self.metrics_store.track_cost()` to potentially update a centralized cost tracker in the store.

4.  **Evaluation and Analysis Logic:**
    *   [`_check_metrics_alerts()`](../../recursive_training/metrics/training_metrics.py:464): Compares specified metrics (MSE, MAE, RMSE, accuracy, F1) against `self.baseline_metrics`. Logs a warning if a metric degrades beyond `self.alert_threshold`.
    *   [`check_convergence()`](../../recursive_training/metrics/training_metrics.py:552):
        *   Checks if there are enough historical iterations (at least `self.early_stopping_patience`).
        *   Compares the MSE of recent iterations. If the absolute difference between consecutive MSEs is within `self.convergence_threshold` for all recent pairs, it returns `True`.
    *   [`compare_models()`](../../recursive_training/metrics/training_metrics.py:584):
        *   Queries the `metrics_store` for the latest metrics of specified model names.
        *   Compares them based on a given `metric_name` (defaults to "mse").
        *   Determines the "best" model (lower is better for error metrics, higher for others).
    *   [`evaluate_rule_performance()`](../../recursive_training/metrics/training_metrics.py:630):
        *   If `rule_predictions` and `rule_actuals` (expected as pandas Series) are provided, it calculates a standard set of metrics (MSE, MAE, R2, F1, accuracy, precision, recall) for these specific inputs.
        *   If `rule_identifier` is a string (e.g., "symbolic") and predictions/actuals are `None`, it attempts to summarize performance for that rule type using data stored in `self.rule_performance`. This involves:
            *   Retrieving historical metrics for the rule type.
            *   Identifying the latest iteration's metrics.
            *   Calculating percentage improvement from the first to the latest iteration for common metrics.
            *   Returns a dictionary including latest metrics, historical list, and improvement.
        *   Includes error handling and default return structures for invalid arguments or missing data.

5.  **Summary Methods:**
    *   [`get_cost_summary()`](../../recursive_training/metrics/training_metrics.py:767): Returns a dictionary summarizing total API calls, token usage, estimated cost, and configured cost thresholds from the `metrics_store`.
    *   [`get_performance_summary()`](../../recursive_training/metrics/training_metrics.py:785):
        *   Provides an overview if iteration history exists.
        *   Calculates overall improvement in key metrics from the first to the latest recorded iteration.
        *   Includes convergence status by calling [`check_convergence()`](../../recursive_training/metrics/training_metrics.py:552).
        *   Includes performance summaries for specific rule types (defined in config `summary_rule_types`) by calling [`evaluate_rule_performance()`](../../recursive_training/metrics/training_metrics.py:630) for each.
        *   Appends the cost summary from [`get_cost_summary()`](../../recursive_training/metrics/training_metrics.py:767).

**Data Flow:**
*   External data (true values, predicted values, configuration) is passed to the `RecursiveTrainingMetrics` instance.
*   Metrics are calculated internally.
*   Iteration data, baseline metrics, and cost data are sent to the `MetricsStore` for persistence.
*   Comparative analysis and summaries may query the `MetricsStore` or use internally aggregated data (`self.iteration_history`, `self.rule_performance`).
*   Results are returned as dictionaries.

## 10. Naming Conventions

*   **Class Name:** `RecursiveTrainingMetrics` follows PascalCase (PEP 8).
*   **Method Names:** snake_case (e.g., [`calculate_mse()`](../../recursive_training/metrics/training_metrics.py:126), [`track_iteration()`](../../recursive_training/metrics/training_metrics.py:412)), adhering to PEP 8.
*   **Variable Names:** snake_case (e.g., `true_values`, `predicted_values`, `convergence_threshold`), adhering to PEP 8.
*   **Internal Methods:** Prefixed with a single underscore (e.g., [`_validate_data()`](../../recursive_training/metrics/training_metrics.py:83), [`_safe_calculation()`](../../recursive_training/metrics/training_metrics.py:104)), as per convention for internal use.
*   **Constants:** Uppercase for library availability flags (`NUMPY_AVAILABLE`, `SKLEARN_AVAILABLE`).
*   The naming is generally consistent and follows Python community standards (PEP 8). No significant deviations or AI-induced naming errors were observed.
*   Local variables like `_true` and `_predicted` are used in some methods (e.g. [`calculate_r2_score()`](../../recursive_training/metrics/training_metrics.py:302)) to handle potential type conversions from pandas Series before passing to scikit-learn functions, which is a clear and understandable local convention.