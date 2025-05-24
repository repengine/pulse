# Module Analysis: `recursive_training.advanced_metrics.enhanced_metrics`

## 1. Module Intent/Purpose

The primary role of the [`enhanced_metrics.py`](recursive_training/advanced_metrics/enhanced_metrics.py:1) module is to extend the core metrics system within the `recursive_training` package. It introduces advanced analytics, statistical measures, and uncertainty quantification capabilities. This module aims to provide more sophisticated tools for performance evaluation and optimization of recursive training processes, including features like calibration analysis, drift detection, and advanced convergence checking.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational. It includes robust error handling, particularly for optional dependencies like NumPy, scikit-learn, and SciPy, ensuring it can function with fallbacks if these libraries are not installed.

Key functionalities such as uncertainty calculation, calibration metrics, statistical significance testing, advanced iteration tracking, drift detection, convergence checking, and offline evaluation are implemented.

There are comments indicating areas for potential future enhancements, such as a more sophisticated prediction interface within the [`evaluate_offline`](recursive_training/advanced_metrics/enhanced_metrics.py:736) method. Some logic related to test mocking (e.g., around [`track_cost`](recursive_training/advanced_metrics/enhanced_metrics.py:431) and `metric_id` returns) suggests that integrating with the testing framework required specific considerations.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Sophisticated Prediction Interface:** The [`evaluate_offline`](recursive_training/advanced_metrics/enhanced_metrics.py:736) method notes: *"This is a simplified example - in real implementation, we would have a more sophisticated prediction interface"* (lines 771-772). This suggests a planned improvement for how models make predictions during offline evaluation.
*   **Drift Correction:** The class docstring for [`EnhancedRecursiveTrainingMetrics`](recursive_training/advanced_metrics/enhanced_metrics.py:45) mentions "Drift detection and correction" (line 54). While drift detection is implemented in [`_check_for_drift`](recursive_training/advanced_metrics/enhanced_metrics.py:574), explicit drift *correction* mechanisms are not present within this module. Correction likely relies on other system components acting upon the detected drift.
*   **Cost Control Granularity:** The integration with [`CostController`](recursive_training/integration/cost_controller.py) (e.g., line 138, 797-802) is present, primarily for limiting computationally intensive operations (like bootstrap sampling) and tracking inference costs. More granular cost-aware decision-making within metric calculations could be a future enhancement.
*   **Rule Performance Analysis:** While `rule_performance` is tracked (line 72, 453-468), deeper analysis or specific actions based on this data are not detailed within this module itself.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`recursive_training.metrics.training_metrics.RecursiveTrainingMetrics`](recursive_training/metrics/training_metrics.py:40) (as base class)
*   [`recursive_training.metrics.metrics_store.get_metrics_store`](recursive_training/metrics/metrics_store.py:41)
*   [`recursive_training.integration.cost_controller.get_cost_controller`](recursive_training/integration/cost_controller.py:42)

### External Library Dependencies:
*   `logging`
*   `json`
*   `math`
*   `statistics`
*   `datetime`
*   `typing`
*   **Optional:**
    *   `numpy` (as `np`): Used extensively for numerical operations, array manipulation, and some statistical calculations. Fallbacks are implemented if not available.
    *   `sklearn.metrics` (as `sk_metrics`): Used for classification metrics (confusion matrix, classification report) and Brier score.
    *   `sklearn.calibration` (as `sk_calibration`): Used for calibration curves.
    *   `scipy.stats` (as `stats`): Used for statistical significance tests (t-test, Wilcoxon, etc.) and normal distribution functions.

### Interactions with Other Modules:
*   **Metrics Store:** Interacts heavily with the `MetricsStore` (obtained via [`get_metrics_store()`](recursive_training/metrics/metrics_store.py:41)) to persist all tracked basic and advanced metrics (e.g., lines 431, 537, 872).
*   **Cost Controller:** Interacts with the `CostController` (obtained via [`get_cost_controller()`](recursive_training/integration/cost_controller.py:42)) to track the cost of operations like model inference and to potentially limit resource-intensive calculations (e.g., line 138, 797).
*   **Configuration:** Reads configuration values passed during initialization (e.g., line 80-84 for thresholds).

### Input/Output Files:
*   **Input:** Reads configuration (passed as a dictionary).
*   **Output:**
    *   Logs messages using the `logging` module.
    *   Writes metrics data via the `MetricsStore`, which would handle the actual file/database I/O.
    *   Does not directly manage other input/output files.

## 5. Function and Class Example Usages

*   **`EnhancedRecursiveTrainingMetrics(config: Optional[Dict[str, Any]] = None)`**
    *   **Usage:** Initializes the advanced metrics tracker.
    *   **Example:** `metrics_tracker = EnhancedRecursiveTrainingMetrics(config={"calibration_threshold": 0.05})`

*   **`calculate_uncertainty(predictions: List[Union[int, float, Any]], method: str = "bootstrap", confidence: float = 0.95, n_samples: int = 1000) -> Dict[str, Any]`**
    *   **Usage:** Calculates uncertainty estimates (mean, std, confidence interval) for a list of numeric predictions.
    *   **Example:** `uncertainty_info = metrics_tracker.calculate_uncertainty(predictions=[1.0, 1.2, 0.9, 1.1], method="bootstrap")`

*   **`calculate_calibration(true_values: List[Any], predicted_probs: List[List[float]], n_bins: int = 10) -> Dict[str, Any]`**
    *   **Usage:** Calculates calibration metrics (Expected Calibration Error, Brier score, reliability diagram data) for probabilistic predictions.
    *   **Example:** `cal_metrics = metrics_tracker.calculate_calibration(true_labels, predicted_probabilities)`

*   **`statistical_significance_test(method_a_errors: List[float], method_b_errors: List[float], test_type: str = "ttest") -> Dict[str, Any]`**
    *   **Usage:** Performs a statistical test (e.g., t-test, Wilcoxon) to compare error distributions from two methods.
    *   **Example:** `test_results = metrics_tracker.statistical_significance_test(model1_errors, model2_errors, test_type="wilcoxon")`

*   **`track_advanced_iteration(iteration: int, metrics: Dict[str, Any], predictions: Optional[List], true_values: Optional[List], predicted_probs: Optional[List[List[float]]], ...)`**
    *   **Usage:** Main method to log metrics for a training iteration, including base metrics and newly calculated advanced metrics like uncertainty and calibration.
    *   **Example:** `metrics_tracker.track_advanced_iteration(iteration=5, metrics={"loss": 0.1}, predictions=preds, true_values=actuals, predicted_probs=probs)`

*   **`evaluate_offline(model, dataset_name: str, dataset: Dict[str, Any], metrics_list: Optional[List[str]] = None) -> Dict[str, Any]`**
    *   **Usage:** Evaluates a given model on a held-out dataset and calculates specified metrics.
    *   **Example:** `eval_results = metrics_tracker.evaluate_offline(my_model, "validation_set", {"inputs": X_val, "targets": y_val})`

*   **`get_advanced_performance_summary() -> Dict[str, Any]`**
    *   **Usage:** Retrieves a comprehensive summary including basic and advanced metrics like calibration, rule performance, uncertainty, drift, and convergence status.
    *   **Example:** `summary = metrics_tracker.get_advanced_performance_summary()`

*   **`compare_models_advanced(model_names: List[str], metric_names: Optional[List[str]], statistical_test: str = "ttest") -> Dict[str, Any]`**
    *   **Usage:** Compares multiple models based on specified metrics, including statistical significance testing between model pairs.
    *   **Example:** `comparison = metrics_tracker.compare_models_advanced(model_names=["model_A", "model_B"], metric_names=["mse", "accuracy"])`

## 6. Hardcoding Issues

*   **Default Configuration Values:**
    *   `calibration_threshold`: `0.1` (line 80)
    *   `statistical_significance`: `0.05` (line 81)
    *   `uncertainty_threshold`: `0.2` (line 82)
    *   `stability_window_size`: `10` (line 83)
    *   `convergence_threshold`: `0.01` (line 84)
*   **Adaptive Threshold Parameters:** Initial values, min/max, decay/growth rates for adaptive thresholds (e.g., `mse: {"initial": 0.1, "current": 0.1, "min": 0.001, "decay_rate": 0.95}`) are hardcoded (lines 88-92).
*   **Computational Limits:**
    *   Bootstrap sample limit for cost control: `1e7` (line 138). This value is used to cap `n_samples * len(numeric_predictions)`.
*   **Drift Detection Thresholds:**
    *   Percentage change for drift detection: `1.1` (10% increase for error metrics, line 632) and `0.9` (10% decrease for accuracy metrics, line 638).
*   **Logger Name:** `"EnhancedRecursiveTrainingMetrics"` (line 65).
*   **Default Metrics List:** In [`evaluate_offline`](recursive_training/advanced_metrics/enhanced_metrics.py:736), the default `metrics_list` is `["mse", "mae", "rmse", "accuracy", "f1_score"]` (line 757).
*   **Test Compatibility Strings:** The string `"metric_id"` is used in several places (lines 422, 541-542) for compatibility with test mocks. This is a pragmatic solution but indicates a slight divergence between test setup and production code behavior for the `metric_id` returned by `track_iteration`.
*   **Default Model Name:** In [`track_advanced_iteration`](recursive_training/advanced_metrics/enhanced_metrics.py:388), `model_name` defaults to `"default"` (line 392).
*   **Metric Types/Tags:** Strings like `"advanced_metrics"`, `"offline_evaluation"`, `"training_iteration"` are used as metric types or tags when storing data.

## 7. Coupling Points

*   **Inheritance:** Tightly coupled to its base class, [`RecursiveTrainingMetrics`](recursive_training/metrics/training_metrics.py:40). Changes in the base class's `track_iteration` method or other core functionalities could impact this module.
*   **MetricsStore:** Significant dependency on the `MetricsStore` interface for all metric persistence. The functionality of this module relies on `get_metrics_store()` providing a compliant store.
*   **CostController:** Depends on `get_cost_controller()` to provide a `CostController` instance for tracking operational costs.
*   **External Libraries:** While it has fallbacks, the full advanced functionality (especially for statistical tests, complex uncertainty, and calibration) relies on `numpy`, `scikit-learn`, and `scipy`. If these are unavailable, the module's capabilities are reduced.
*   **Configuration Structure:** Assumes a certain structure for the configuration dictionary passed during initialization and for the `adaptive_thresholds` dictionary.
*   **Model Interface for Evaluation:** The [`evaluate_offline`](recursive_training/advanced_metrics/enhanced_metrics.py:736) method expects the passed `model` object to have a `predict` method and optionally a `predict_proba` method (lines 773, 781).

## 8. Existing Tests

*   A corresponding test file exists at [`tests/recursive_training/advanced_metrics/test_enhanced_metrics.py`](tests/recursive_training/advanced_metrics/test_enhanced_metrics.py).
*   The module's source code contains comments regarding test compatibility, specifically around the behavior of mocked objects for `MetricsStore.track_cost` (lines 426-446) and the `metric_id` returned by `track_iteration` (lines 421-424, 539-544). This suggests that testing the interactions, particularly with `MetricsStore`, required careful mocking strategies. For instance, the mock for `track_cost` in tests might not expect a `cost` argument, while the actual implementation requires it, leading to conditional logic in the source to handle both scenarios.
*   The presence of these test-specific workarounds implies that ensuring test coverage for all paths, especially those involving external dependencies and their mocks, might be complex. The actual coverage and nature of tests would require inspecting the test file itself.

## 9. Module Architecture and Flow

The module is structured around the [`EnhancedRecursiveTrainingMetrics`](recursive_training/advanced_metrics/enhanced_metrics.py:45) class, which extends [`RecursiveTrainingMetrics`](recursive_training/metrics/training_metrics.py:40).

**Initialization (`__init__`)**:
*   Calls the parent constructor.
*   Initializes internal dictionaries to store advanced metric data over time (e.g., `uncertainty_estimates`, `calibration_metrics`, `convergence_status`).
*   Sets various thresholds (calibration, significance, uncertainty, stability, convergence) from the provided configuration or defaults.
*   Initializes `adaptive_thresholds` with default structures for common metrics like MSE, MAE, and accuracy.
*   Gets an instance of the `CostController`.

**Core Advanced Metric Calculation Methods**:
*   [`calculate_uncertainty`](recursive_training/advanced_metrics/enhanced_metrics.py:100): Computes confidence intervals and standard deviation for predictions using methods like bootstrap, standard deviation, or quartiles. Handles cases with/without NumPy/SciPy.
*   [`calculate_calibration`](recursive_training/advanced_metrics/enhanced_metrics.py:188): Calculates ECE, Brier score, and reliability diagram data using scikit-learn if available. Handles different `predicted_probs` formats.
*   [`statistical_significance_test`](recursive_training/advanced_metrics/enhanced_metrics.py:305): Performs statistical tests (t-test, Wilcoxon, etc.) using SciPy to compare two sets of errors.

**Main Tracking Method (`track_advanced_iteration`)**:
1.  Calls `super().track_iteration()` to log basic metrics.
2.  Handles cost tracking via `MetricsStore` (with test mock compatibility logic).
3.  Stores rule-specific performance if `rule_type` is provided.
4.  If `predictions` and `true_values` are available:
    *   Calculates scikit-learn classification metrics (confusion matrix, report) if applicable.
    *   Calls [`calculate_uncertainty`](recursive_training/advanced_metrics/enhanced_metrics.py:100) for numeric predictions.
    *   Calls [`calculate_calibration`](recursive_training/advanced_metrics/enhanced_metrics.py:188) if `predicted_probs` are available.
5.  Updates adaptive thresholds using [`_update_adaptive_thresholds`](recursive_training/advanced_metrics/enhanced_metrics.py:546).
6.  Checks for performance drift using [`_check_for_drift`](recursive_training/advanced_metrics/enhanced_metrics.py:574).
7.  Checks for training convergence using [`_check_advanced_convergence`](recursive_training/advanced_metrics/enhanced_metrics.py:653).
8.  Stores all calculated advanced metrics in the `MetricsStore`.

**Helper Methods for Tracking**:
*   [`_update_adaptive_thresholds`](recursive_training/advanced_metrics/enhanced_metrics.py:546): Adjusts performance thresholds (e.g., for MSE, accuracy) based on decay or growth rates.
*   [`_check_for_drift`](recursive_training/advanced_metrics/enhanced_metrics.py:574): Analyzes recent metric values to detect significant performance degradation or unexpected changes.
*   [`_check_advanced_convergence`](recursive_training/advanced_metrics/enhanced_metrics.py:653): Uses criteria like stability of recent metrics (normalized standard deviation), lack of significant improvement, and rate of change to determine if training has converged.

**Offline Evaluation and Reporting**:
*   [`evaluate_offline`](recursive_training/advanced_metrics/enhanced_metrics.py:736): Takes a model and dataset to perform evaluation, calculating a list of standard and advanced metrics. Stores results in `MetricsStore`.
*   [`get_advanced_performance_summary`](recursive_training/advanced_metrics/enhanced_metrics.py:890): Consolidates basic and latest advanced metrics (calibration, uncertainty, drift, convergence, offline evaluations) into a single summary.
*   [`compare_models_advanced`](recursive_training/advanced_metrics/enhanced_metrics.py:943): Compares multiple models based on selected metrics, including pairwise statistical significance tests.

**Data Flow**:
*   Input data (predictions, true values, probabilities) flows into `track_advanced_iteration` and `evaluate_offline`.
*   Configuration data flows into `__init__`.
*   Calculated metrics and state (convergence status, adaptive thresholds) are stored internally within the class instance and persisted externally via `MetricsStore`.
*   Summaries and comparisons are generated on demand from the stored and internal data.

## 10. Naming Conventions

*   **Class Names:** `EnhancedRecursiveTrainingMetrics` uses PascalCase, which is standard (PEP 8).
*   **Method Names:** `calculate_uncertainty`, `track_advanced_iteration`, `_check_for_drift` use snake_case, which is standard. Private/internal helper methods are correctly prefixed with a single underscore.
*   **Variable Names:** Generally descriptive and use snake_case (e.g., `numeric_predictions`, `bootstrap_means`, `prob_true_cal`, `stability_window_size`).
*   **Constants:** Flags for library availability like `NUMPY_AVAILABLE`, `SKLEARN_AVAILABLE`, `SCIPY_AVAILABLE` are in UPPER_SNAKE_CASE, which is correct.
*   **Docstrings:** Present for the class and public methods, explaining their purpose, arguments, and return values.
*   **Consistency:** Naming is largely consistent throughout the module.
*   **Potential AI Assumption Errors/Deviations:**
    *   No obvious AI-generated naming errors are apparent. The names seem human-generated and follow common Python conventions.
    *   Some local variables within methods are short (e.g., `cm` for confusion matrix, `ece` for expected calibration error, `p_val` for p-value), but these are common abbreviations in their respective contexts (machine learning, statistics) and are generally understandable.
    *   The use of `y_true_np`, `y_prob_np` alongside `current_y_true`, `current_y_prob` in [`calculate_calibration`](recursive_training/advanced_metrics/enhanced_metrics.py:188) (lines 217-230) is a bit verbose but aims to handle NumPy arrays and lists explicitly.

Overall, the naming conventions adhere well to PEP 8 and project standards, promoting readability and maintainability.