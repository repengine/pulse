"""
RecursiveTrainingMetrics

Implements core metrics calculation for the recursive training system.
Responsible for tracking training progress, calculating error metrics,
and providing performance insights for model evaluation.
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
import pandas as pd

try:
    # import numpy as np # F401: unused

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    # import sklearn.metrics as sk_metrics # F401: unused

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Local imports
from recursive_training.metrics.metrics_store import get_metrics_store


class RecursiveTrainingMetrics:
    """
    Core metrics tracking and calculation for recursive training.

    Features:
    - Standard error metrics calculation (MSE, MAE, RMSE)
    - Progress tracking for training iterations
    - Training cost monitoring
    - Convergence analysis
    - Performance comparison across models
    - Support for hybrid rule approach evaluation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RecursiveTrainingMetrics.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("RecursiveTrainingMetrics")
        self.config = config or {}
        self.metrics_store = get_metrics_store(config)

        # Configure default thresholds
        self.convergence_threshold = self.config.get("convergence_threshold", 0.001)
        self.max_iterations = self.config.get("max_iterations", 100)
        self.early_stopping_patience = self.config.get("early_stopping_patience", 5)
        self.alert_threshold = self.config.get("alert_threshold", 0.1)

        # Initialize tracking variables
        self.current_metrics = {}
        self.baseline_metrics = {}
        self.iteration_history = []
        self.training_costs = {"api_calls": 0, "token_usage": 0, "total_cost": 0.0}

        # Track performance by rule type
        self.rule_performance = {"symbolic": {}, "neural": {}, "hybrid": {}}

    def _validate_data(
        self,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
    ) -> bool:
        """
        Validate input data for metrics calculation.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values

        Returns:
            Whether the data is valid
        """
        if len(true_values) != len(predicted_values):
            self.logger.error(
                f"Length mismatch: true values ({
                    len(true_values)}) != predicted values ({
                    len(predicted_values)})")
            return False

        if len(true_values) == 0:
            self.logger.error("Empty data provided for metrics calculation")
            return False

        return True

    def _safe_calculation(
        self,
        metric_func: Callable,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
        default_value: Any = None,
    ) -> Any:
        """
        Safely calculate a metric with error handling.

        Args:
            metric_func: Function to calculate the metric
            true_values: List of true/expected values
            predicted_values: List of predicted values
            default_value: Value to return if calculation fails

        Returns:
            Calculated metric value or default value on error
        """
        try:
            return metric_func(true_values, predicted_values)
        except Exception as e:
            self.logger.error(f"Error calculating metric: {e}")
            return default_value

    def calculate_mse(
        self,
        true_values: Union[List[float], "pd.Series"],
        predicted_values: Union[List[float], "pd.Series"],
    ) -> float:
        """
        Calculate Mean Squared Error.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values

        Returns:
            MSE value or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")

        if NUMPY_AVAILABLE:
            import numpy as np

            return self._safe_calculation(
                lambda x, y: np.mean(np.square(np.array(x) - np.array(y))),
                true_values,
                predicted_values,
                float("nan"),
            )
        else:
            # Fallback calculation
            try:
                squared_errors = [
                    (t - p) ** 2 for t, p in zip(true_values, predicted_values)
                ]
                return sum(squared_errors) / len(squared_errors)
            except Exception as e:
                self.logger.error(f"Error calculating MSE: {e}")
                return float("nan")

    def calculate_mae(
        self,
        true_values: Union[List[float], "pd.Series"],
        predicted_values: Union[List[float], "pd.Series"],
    ) -> float:
        """
        Calculate Mean Absolute Error.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values

        Returns:
            MAE value or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")

        if NUMPY_AVAILABLE:
            import numpy as np

            return self._safe_calculation(
                lambda x, y: np.mean(np.abs(np.array(x) - np.array(y))),
                true_values,
                predicted_values,
                float("nan"),
            )
        else:
            # Fallback calculation
            try:
                absolute_errors = [
                    abs(t - p) for t, p in zip(true_values, predicted_values)
                ]
                return sum(absolute_errors) / len(absolute_errors)
            except Exception as e:
                self.logger.error(f"Error calculating MAE: {e}")
                return float("nan")

    def calculate_rmse(
        self,
        true_values: Union[List[float], "pd.Series"],
        predicted_values: Union[List[float], "pd.Series"],
    ) -> float:
        """
        Calculate Root Mean Squared Error.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values

        Returns:
            RMSE value or None on error
        """
        mse = self.calculate_mse(true_values, predicted_values)
        if math.isnan(mse):
            return float("nan")

        try:
            return math.sqrt(mse)
        except Exception as e:
            self.logger.error(f"Error calculating RMSE: {e}")
            return float("nan")

    def calculate_accuracy(
        self,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
    ) -> float:
        """
        Calculate classification accuracy.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values

        Returns:
            Accuracy value or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")

        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics

            return self._safe_calculation(
                sk_metrics.accuracy_score, true_values, predicted_values, float("nan")
            )
        else:
            # Fallback calculation
            try:
                correct = sum(
                    1 for t, p in zip(true_values, predicted_values) if t == p
                )
                return correct / len(true_values)
            except Exception as e:
                self.logger.error(f"Error calculating accuracy: {e}")
                return float("nan")

    def calculate_f1_score(
        self,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
        average: str = "weighted",
    ) -> float:
        """
        Calculate F1 score for classification.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            average: Method for averaging ('micro', 'macro', 'weighted')

        Returns:
            F1 score or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")

        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics  # Local import

            # Handle each average type explicitly to satisfy type checking
            if average == "micro":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(
                        x, y, average="micro", zero_division=0
                    ),
                    true_values,
                    predicted_values,
                    float("nan"),
                )
            elif average == "macro":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(
                        x, y, average="macro", zero_division=0
                    ),
                    true_values,
                    predicted_values,
                    float("nan"),
                )
            elif average == "samples":
                # Note: 'samples' average might not be applicable for all scenarios or pd.Series inputs directly
                # depending on sklearn version and data structure. Test mocks should
                # cover this.
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(
                        x, y, average="samples", zero_division=0
                    ),
                    true_values,
                    predicted_values,
                    float("nan"),
                )
            elif average == "binary":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(
                        x, y, average="binary", zero_division=0
                    ),
                    true_values,
                    predicted_values,
                    float("nan"),
                )
            else:  # Default to weighted
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(
                        x, y, average="weighted", zero_division=0
                    ),
                    true_values,
                    predicted_values,
                    float("nan"),
                )
        else:
            self.logger.warning("scikit-learn not available for F1 calculation")
            return float("nan")

    def calculate_r2_score(
        self,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
    ) -> float:
        """
        Calculate R2 (coefficient of determination) regression score.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values

        Returns:
            R2 score or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")
        return float("nan")  # Should be unreachable, but to satisfy Pylance

        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics  # Local import

            # Ensure inputs are list-like for sklearn if they are pd.Series
            # This is a general precaution; mocks in tests might handle Series directly.
            _true = (
                true_values.tolist()
                if isinstance(true_values, pd.Series)
                else true_values
            )
            _predicted = (
                predicted_values.tolist()
                if isinstance(predicted_values, pd.Series)
                else predicted_values
            )
            return self._safe_calculation(
                sk_metrics.r2_score, _true, _predicted, float("nan")
            )
        else:
            self.logger.warning("scikit-learn not available for R2 score calculation")
            return float("nan")

    def calculate_precision(
        self,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
        average: str = "weighted",
    ) -> float:
        """
        Calculate precision for classification.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            average: Method for averaging ('micro', 'macro', 'weighted', 'binary')

        Returns:
            Precision score or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")

        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics  # Local import

            _true = (
                true_values.tolist()
                if isinstance(true_values, pd.Series)
                else true_values
            )
            _predicted = (
                predicted_values.tolist()
                if isinstance(predicted_values, pd.Series)
                else predicted_values
            )

            if average == "micro":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.precision_score(
                        x, y, average="micro", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            elif average == "macro":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.precision_score(
                        x, y, average="macro", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            elif average == "samples":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.precision_score(
                        x, y, average="samples", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            elif average == "binary":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.precision_score(
                        x, y, average="binary", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            else:  # Default to weighted
                return self._safe_calculation(
                    lambda x, y: sk_metrics.precision_score(
                        x, y, average="weighted", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
        else:
            self.logger.warning("scikit-learn not available for Precision calculation")
            return float("nan")

    def calculate_recall(
        self,
        true_values: Union[List[Any], "pd.Series"],
        predicted_values: Union[List[Any], "pd.Series"],
        average: str = "weighted",
    ) -> float:
        """
        Calculate recall for classification.

        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            average: Method for averaging ('micro', 'macro', 'weighted', 'binary')

        Returns:
            Recall score or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float("nan")

        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics  # Local import

            _true = (
                true_values.tolist()
                if isinstance(true_values, pd.Series)
                else true_values
            )
            _predicted = (
                predicted_values.tolist()
                if isinstance(predicted_values, pd.Series)
                else predicted_values
            )

            if average == "micro":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.recall_score(
                        x, y, average="micro", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            elif average == "macro":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.recall_score(
                        x, y, average="macro", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            elif average == "samples":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.recall_score(
                        x, y, average="samples", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            elif average == "binary":
                return self._safe_calculation(
                    lambda x, y: sk_metrics.recall_score(
                        x, y, average="binary", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
            else:  # Default to weighted
                return self._safe_calculation(
                    lambda x, y: sk_metrics.recall_score(
                        x, y, average="weighted", zero_division=0
                    ),
                    _true,
                    _predicted,
                    float("nan"),
                )
        else:
            self.logger.warning("scikit-learn not available for Recall calculation")
            return float("nan")

    def track_iteration(
        self,
        iteration: int,
        metrics: Dict[str, Any],
        model_name: str = "default",
        rule_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Track metrics for a training iteration.

        Args:
            iteration: Training iteration number
            metrics: Dictionary of metric values
            model_name: Name of the model
            rule_type: Type of rule (symbolic, neural, hybrid)
            tags: Optional list of tags

        Returns:
            ID of the stored metrics record
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Prepare metrics data
        metrics_data = {
            "timestamp": timestamp,
            "metric_type": "training_iteration",
            "iteration": iteration,
            "model": model_name,
            "metrics": metrics,
            "tags": tags or [],
        }

        # Add rule type if provided
        if rule_type:
            metrics_data["rule_type"] = rule_type
            metrics_data["tags"].append(f"rule_type:{rule_type}")

        # Store in metrics store
        metric_id = self.metrics_store.store_metric(metrics_data)

        # Update iteration history
        self.iteration_history.append(metrics_data)

        # Update current metrics
        self.current_metrics = metrics

        # Track by rule type if provided
        if rule_type and rule_type in self.rule_performance:
            self.rule_performance[rule_type][iteration] = metrics

        # Check for significant changes or issues
        self._check_metrics_alerts(metrics)

        return metric_id

    def _check_metrics_alerts(self, metrics: Dict[str, Any]) -> None:
        """
        Check for significant changes or issues in metrics.

        Args:
            metrics: Dictionary of metric values
        """
        # Skip if no baseline or current metrics
        if not self.baseline_metrics or not metrics:
            return

        # Check for significant degradation in key metrics
        for key in ["mse", "rmse", "mae"]:
            if key in metrics and key in self.baseline_metrics:
                # For error metrics, higher is worse
                if metrics[key] > self.baseline_metrics[key] * (
                    1 + self.alert_threshold
                ):
                    self.logger.warning(
                        f"Metric {key} degraded: {
                            metrics[key]:.4f} vs baseline {
                            self.baseline_metrics[key]:.4f}")

        # Check for accuracy or f1 regression
        for key in ["accuracy", "f1_score"]:
            if key in metrics and key in self.baseline_metrics:
                # For these metrics, lower is worse
                if metrics[key] < self.baseline_metrics[key] * (
                    1 - self.alert_threshold
                ):
                    self.logger.warning(
                        f"Metric {key} degraded: {
                            metrics[key]:.4f} vs baseline {
                            self.baseline_metrics[key]:.4f}")

    def set_baseline(self, metrics: Dict[str, Any]) -> None:
        """
        Set baseline metrics for comparison.

        Args:
            metrics: Dictionary of baseline metric values
        """
        self.baseline_metrics = metrics.copy()

        # Store baseline in metrics store
        baseline_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metric_type": "baseline",
            "metrics": metrics,
            "tags": ["baseline"],
        }

        self.metrics_store.store_metric(baseline_data)

    def track_cost(
        self, api_calls: int = 0, token_usage: int = 0, cost: float = 0.0
    ) -> Dict[str, Any]:
        """
        Track API and token usage costs.

        Args:
            api_calls: Number of API calls
            token_usage: Number of tokens used
            cost: Direct cost in USD

        Returns:
            Updated cost tracking information
        """
        # Update local tracking
        self.training_costs["api_calls"] += api_calls
        self.training_costs["token_usage"] += token_usage
        self.training_costs["total_cost"] += cost

        # Calculate cost if not provided directly
        if cost == 0.0 and token_usage > 0:
            # Basic estimation using typical token costs
            estimated_cost = token_usage * 0.000002  # $0.002 per 1000 tokens
            self.training_costs["total_cost"] += estimated_cost
            cost = estimated_cost

        # Track in metrics store
        cost_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metric_type": "cost",
            "api_calls": api_calls,
            "token_usage": token_usage,
            "cost": cost,
            "tags": ["cost"],
        }

        self.metrics_store.store_metric(cost_data)

        # Also update the metrics store's cost tracking
        return self.metrics_store.track_cost(cost, api_calls, token_usage)

    def check_convergence(self, tolerance: Optional[float] = None) -> bool:
        """
        Check if training has converged based on recent iterations.

        Args:
            tolerance: Convergence tolerance (if None, use default)

        Returns:
            Whether training has converged
        """
        if len(self.iteration_history) < 2:
            return False

        tolerance = tolerance or self.convergence_threshold

        # Get the key error metrics from recent iterations
        recent_metrics = []
        for record in sorted(
            self.iteration_history, key=lambda x: x["iteration"], reverse=True
        )[: self.early_stopping_patience]:
            if "metrics" in record and "mse" in record["metrics"]:
                recent_metrics.append(record["metrics"]["mse"])

        # Not enough data points to check convergence
        if len(recent_metrics) < 2:
            return False

        # Check if the change between iterations is below tolerance
        for i in range(len(recent_metrics) - 1):
            if abs(recent_metrics[i] - recent_metrics[i + 1]) > tolerance:
                return False

        return True

    def compare_models(
        self, model_names: List[str], metric_name: str = "mse"
    ) -> Dict[str, Any]:
        """
        Compare multiple models based on a specific metric.

        Args:
            model_names: List of model names to compare
            metric_name: Name of the metric to use for comparison

        Returns:
            Dictionary with comparison results
        """
        comparison = {}

        for model_name in model_names:
            # Query metrics for this model
            metrics = self.metrics_store.query_metrics(
                models=[model_name],
                metric_types=["training_iteration"],
                limit=1,  # Get the most recent
            )

            if (
                metrics
                and "metrics" in metrics[0]
                and metric_name in metrics[0]["metrics"]
            ):
                comparison[model_name] = metrics[0]["metrics"][metric_name]
            else:
                comparison[model_name] = None

        # Find the best model
        valid_models = {k: v for k, v in comparison.items() if v is not None}

        if not valid_models:
            best_model = None
        else:
            # For error metrics, lower is better
            if metric_name in ["mse", "rmse", "mae"]:
                best_model = min(valid_models.items(), key=lambda x: x[1])[0]
            else:
                # For accuracy, f1, etc., higher is better
                best_model = max(valid_models.items(), key=lambda x: x[1])[0]

        return {"metric": metric_name, "values": comparison, "best_model": best_model}

    def evaluate_rule_performance(
        self,
        rule_identifier: Union[Dict, str],
        rule_predictions: Optional["pd.Series"] = None,
        rule_actuals: Optional["pd.Series"] = None,
    ) -> Dict[str, Any]:
        """
        Calculate various performance metrics.
        If rule_predictions and rule_actuals are provided, evaluates them.
        If rule_identifier is a string and predictions/actuals are None,
        this indicates a potential call for aggregated metrics (currently returns defaults).
        """
        metrics: Dict[str, Any] = {}

        if rule_predictions is not None and rule_actuals is not None:
            # Standard evaluation path when predictions and actuals are provided
            # The 'rule_identifier' (if a Dict) could be used for context if needed.
            metrics["mse"] = self.calculate_mse(rule_actuals, rule_predictions)
            metrics["mae"] = self.calculate_mae(rule_actuals, rule_predictions)
            metrics["r2_score"] = self.calculate_r2_score(
                rule_actuals, rule_predictions
            )
            metrics["f1_score"] = self.calculate_f1_score(
                rule_actuals, rule_predictions
            )  # Uses default average='weighted'
            metrics["accuracy"] = self.calculate_accuracy(
                rule_actuals, rule_predictions
            )
            metrics["precision"] = self.calculate_precision(
                rule_actuals, rule_predictions
            )
            metrics["recall"] = self.calculate_recall(rule_actuals, rule_predictions)
        elif (
            isinstance(rule_identifier, str)
            and rule_predictions is None
            and rule_actuals is None
        ):
            # This case handles calls like evaluate_rule_performance("symbolic"),
            # expecting a summary for that rule type based on self.rule_performance.
            if (
                rule_identifier in self.rule_performance
                and self.rule_performance[rule_identifier]
            ):
                rule_specific_history = self.rule_performance[rule_identifier]
                history_to_use = (
                    rule_specific_history  # Initialize with the original history
                )

                # Ensure iteration keys are integers for correct sorting if they are not
                # already
                try:
                    # Attempt to convert keys to int if they are strings, common in JSON-loaded data
                    # If keys are already int, this will mostly be a pass-through
                    # If keys are mixed or non-convertible, it might raise an error,
                    # which indicates a different problem with how rule_performance is
                    # populated.
                    int_keyed_history = {
                        int(k): v for k, v in rule_specific_history.items()
                    }
                    sorted_iterations = sorted(int_keyed_history.keys())
                    history_to_use = int_keyed_history  # Update if conversion and sorting are successful
                except ValueError:
                    self.logger.error(
                        f"Non-integer iteration keys found in rule_performance for '{rule_identifier}'. Cannot sort iterations.")
                    # Fallback to treating keys as they are, hoping they are sortable or
                    # test setup handles it
                    sorted_iterations = sorted(rule_specific_history.keys())
                    # history_to_use remains rule_specific_history

                if not sorted_iterations:
                    self.logger.warning(
                        f"Rule type '{rule_identifier}' has no iteration data in rule_performance.")
                    metrics["error"] = (
                        f"No iteration data for rule type '{rule_identifier}'."
                    )
                    # Populate with default structure to avoid KeyErrors in tests
                    metrics.update(
                        {
                            "mse": float("nan"),
                            "mae": float("nan"),
                            "r2_score": float("nan"),
                            "f1_score": float("nan"),
                            "accuracy": float("nan"),
                            "precision": float("nan"),
                            "recall": float("nan"),
                            "latest_iteration": 0,
                            "latest_metrics": {},
                            "historical": [],
                            "improvement": {},
                        }
                    )
                    metrics["rule_type"] = rule_identifier
                    return metrics

                latest_iteration_num = sorted_iterations[-1]
                latest_metrics_dict = history_to_use.get(latest_iteration_num, {})

                historical_list = [
                    history_to_use[it]
                    for it in sorted_iterations
                    if it in history_to_use
                ]

                improvement_dict = {}
                if len(sorted_iterations) > 0:
                    first_iteration_num = sorted_iterations[0]
                    first_metrics_dict = history_to_use.get(first_iteration_num, {})

                    if first_metrics_dict and latest_metrics_dict:
                        common_metric_keys = set(first_metrics_dict.keys()) & set(
                            latest_metrics_dict.keys()
                        )
                        for metric_key in common_metric_keys:
                            # Ensure values are numeric and first_metric is not zero for
                            # division
                            if (
                                isinstance(
                                    first_metrics_dict.get(metric_key), (int, float)
                                )
                                and isinstance(
                                    latest_metrics_dict.get(metric_key), (int, float)
                                )
                                and first_metrics_dict[metric_key] != 0
                            ):
                                improvement_value = (
                                    (
                                        latest_metrics_dict[metric_key]
                                        - first_metrics_dict[metric_key]
                                    )
                                    / first_metrics_dict[metric_key]
                                    * 100
                                )
                                improvement_dict[metric_key] = improvement_value

                metrics.update(
                    {
                        "mse": latest_metrics_dict.get("mse", float("nan")),
                        "mae": latest_metrics_dict.get("mae", float("nan")),
                        "r2_score": latest_metrics_dict.get("r2_score", float("nan")),
                        "f1_score": latest_metrics_dict.get("f1_score", float("nan")),
                        "accuracy": latest_metrics_dict.get("accuracy", float("nan")),
                        "precision": latest_metrics_dict.get("precision", float("nan")),
                        "recall": latest_metrics_dict.get("recall", float("nan")),
                    }
                )
                metrics["rule_type"] = rule_identifier
                metrics["latest_iteration"] = latest_iteration_num
                metrics["latest_metrics"] = latest_metrics_dict
                metrics["historical"] = historical_list
                metrics["improvement"] = improvement_dict
            else:
                self.logger.info(
                    f"evaluate_rule_performance called for rule_identifier='{rule_identifier}' "
                    "which was not found or has no data. Returning error structure."
                )
                metrics["error"] = (
                    f"Rule type '{rule_identifier}' not found or no data."
                )
                metrics.update(
                    {
                        "mse": float("nan"),
                        "mae": float("nan"),
                        "r2_score": float("nan"),
                        "f1_score": float("nan"),
                        "accuracy": float("nan"),
                        "precision": float("nan"),
                        "recall": float("nan"),
                        "latest_iteration": 0,
                        "latest_metrics": {},  # Default for test expectations
                        "historical": [],
                        "improvement": {},
                    }
                )
                metrics["rule_type"] = rule_identifier
        else:
            # Handle other unexpected argument combinations
            self.logger.error(
                "Invalid or incomplete arguments for evaluate_rule_performance. "
                "Expected (rule_identifier: Dict, rule_predictions, rule_actuals) or "
                "(rule_identifier: str with no predictions/actuals) or "
                "(rule_identifier: Any, rule_predictions, rule_actuals)."
            )
            # Fallback to returning a full default structure to prevent KeyErrors.
            metrics = {
                "mse": float("nan"),
                "mae": float("nan"),
                "r2_score": float("nan"),
                "f1_score": float("nan"),
                "accuracy": float("nan"),
                "precision": float("nan"),
                "recall": float("nan"),
                "latest_iteration": 0,
                "latest_metrics": {},
                "historical": [],
                "improvement": {},
                "error": "Invalid arguments for evaluate_rule_performance.",
            }
            if isinstance(rule_identifier, str):
                metrics["rule_type"] = rule_identifier
            elif (
                isinstance(rule_identifier, dict) and "rule_type" in rule_identifier
            ):  # Check if dict and has 'rule_type'
                metrics["rule_type"] = rule_identifier.get(
                    "rule_type", "unknown_dict_type"
                )
            else:
                metrics["rule_type"] = "unknown"
            # Consider raising TypeError for truly unhandled cases if stricter behavior is preferred.
            # raise TypeError("Invalid arguments for evaluate_rule_performance.")

        return metrics

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get a summary of cost-related metrics.

        Returns:
            Dictionary of cost metrics
        """
        return {
            "api_calls": self.training_costs["api_calls"],
            "token_usage": self.training_costs["token_usage"],
            "estimated_cost_usd": self.training_costs["total_cost"],
            "cost_thresholds": {
                "warning": self.metrics_store.cost_thresholds["warning_threshold"],
                "critical": self.metrics_store.cost_thresholds["critical_threshold"],
                "shutdown": self.metrics_store.cost_thresholds["shutdown_threshold"],
            },
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.

        Returns:
            Dictionary with performance summary
        """
        if not self.iteration_history:
            return {"error": "No training iterations recorded"}

        # Get the first and most recent iterations
        first_iteration = min(self.iteration_history, key=lambda x: x["iteration"])
        latest_iteration = max(self.iteration_history, key=lambda x: x["iteration"])

        # Calculate improvement for key metrics
        improvement = {}

        if "metrics" in first_iteration and "metrics" in latest_iteration:
            first_metrics = first_iteration["metrics"]
            latest_metrics = latest_iteration["metrics"]

            # For error metrics, negative percentages mean improvement
            for key in ["mse", "rmse", "mae"]:
                if (
                    key in first_metrics
                    and key in latest_metrics
                    and first_metrics[key] != 0
                ):
                    improvement[key] = (
                        (latest_metrics[key] - first_metrics[key])
                        / first_metrics[key]
                        * 100
                    )

            # For accuracy metrics, positive percentages mean improvement
            for key in ["accuracy", "f1_score"]:
                if (
                    key in first_metrics
                    and key in latest_metrics
                    and first_metrics[key] != 0
                ):
                    improvement[key] = (
                        (latest_metrics[key] - first_metrics[key])
                        / first_metrics[key]
                        * 100
                    )

        # Get rule type performance
        rule_performance = {}
        for rule_type in self.config.get("summary_rule_types", []):
            evaluated_data = self.evaluate_rule_performance(rule_type)
            if evaluated_data and not evaluated_data.get("error"):
                rule_performance[rule_type] = evaluated_data
            else:
                self.logger.warning(
                    f"Evaluation for rule type '{rule_type}' returned no data or an error for summary, and will not be included.")
        return {
            "total_iterations": len(self.iteration_history),
            "latest_iteration": latest_iteration["iteration"],
            "latest_metrics": latest_iteration.get("metrics", {}),
            "improvement": improvement,
            "convergence": self.check_convergence(),
            "rule_performance": rule_performance,
            "cost": self.get_cost_summary(),
        }
