"""
EnhancedRecursiveTrainingMetrics

Extends the core metrics system with advanced analytics, statistical measures,
and uncertainty quantification. This module provides more sophisticated 
performance evaluation and training optimization capabilities.
"""

import logging
import json
import math
import statistics
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Callable, Sequence

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import sklearn.metrics as sk_metrics
    import sklearn.calibration as sk_calibration
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import scipy.stats as stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Local imports
from recursive_training.metrics.training_metrics import RecursiveTrainingMetrics
from recursive_training.metrics.metrics_store import get_metrics_store
from recursive_training.integration.cost_controller import get_cost_controller


class EnhancedRecursiveTrainingMetrics(RecursiveTrainingMetrics):
    """
    Advanced metrics tracking and analysis for recursive training.
    
    Extends the base RecursiveTrainingMetrics with:
    - Uncertainty quantification and confidence intervals
    - Statistical significance testing
    - Distribution and calibration analysis
    - Advanced convergence detection
    - Drift detection and correction
    - Multi-criteria performance evaluation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EnhancedRecursiveTrainingMetrics.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.logger = logging.getLogger("EnhancedRecursiveTrainingMetrics")
        
        # Initialize advanced tracking variables
        self.uncertainty_estimates = {}
        self.calibration_metrics = {}
        self.statistical_tests = {}
        self.drift_metrics = {}
        self.convergence_status = {
            "converged": False,
            "converged_at_iteration": None,
            "convergence_criteria": {},
            "stability_window": []
        }
        
        # Set advanced thresholds from config
        self.calibration_threshold = self.config.get("calibration_threshold", 0.1)
        self.statistical_significance = self.config.get("statistical_significance", 0.05)
        self.uncertainty_threshold = self.config.get("uncertainty_threshold", 0.2)
        self.stability_window_size = self.config.get("stability_window_size", 10)
        
        # Adaptive thresholds that change during training
        self.adaptive_thresholds = {
            "mse": {"initial": 0.1, "current": 0.1, "min": 0.001, "decay_rate": 0.95},
            "mae": {"initial": 0.2, "current": 0.2, "min": 0.01, "decay_rate": 0.95},
            "accuracy": {"initial": 0.7, "current": 0.7, "max": 0.99, "growth_rate": 1.02}
        }
        
        # Initialize offline evaluation datasets
        self.evaluation_datasets = {}
        
        # Cost controller
        self.cost_controller = get_cost_controller()
    
    def calculate_uncertainty(self, predictions: List[Union[int, float, Any]], 
                            method: str = "bootstrap", 
                            confidence: float = 0.95,
                            n_samples: int = 1000) -> Dict[str, Any]:
        """
        Calculate uncertainty estimates for predictions.
        
        Args:
            predictions: List of predicted values (int or float)
            method: Method for uncertainty estimation ('bootstrap', 'std', 'quartile')
            confidence: Confidence level for intervals (0.0-1.0)
            n_samples: Number of bootstrap samples (if applicable)
            
        Returns:
            Dictionary of uncertainty metrics
        """
        # Filter out non-numeric predictions for uncertainty calculation
        numeric_predictions = [p for p in predictions if isinstance(p, (int, float))]

        if len(numeric_predictions) < 2:
            return {"error": "Not enough numeric data points for uncertainty estimation"}
        
        result: Dict[str, Any] = {
            "mean": None,
            "std": None,
            "confidence_interval": None,
            "method": method
        }
        
        try:
            if NUMPY_AVAILABLE:
                predictions_array = np.array(numeric_predictions)
                
                # Calculate mean and standard deviation
                result["mean"] = float(np.mean(predictions_array))
                result["std"] = float(np.std(predictions_array))
                
                if method == "bootstrap" and len(numeric_predictions) >= 10:
                    if n_samples * len(numeric_predictions) > 1e7:
                        # Limit computation for cost control
                        n_samples = min(n_samples, int(1e7 / len(numeric_predictions)))
                        self.logger.info(f"Limiting bootstrap samples to {n_samples} for cost control")
                    
                    # Bootstrap sampling
                    bootstrap_means = []
                    rng = np.random.default_rng()
                    
                    for _ in range(n_samples):
                        sample = rng.choice(predictions_array, size=len(predictions_array), replace=True)
                        bootstrap_means.append(float(np.mean(sample)))
                    
                    # Calculate confidence interval
                    alpha = (1 - confidence) / 2
                    lower = float(np.quantile(bootstrap_means, alpha))
                    upper = float(np.quantile(bootstrap_means, 1 - alpha))
                    result["confidence_interval"] = (lower, upper)
                    
                elif method == "std" and SCIPY_AVAILABLE:
                    # Standard normal distribution-based interval
                    from scipy.stats import norm
                    z = norm.ppf(1 - (1 - confidence) / 2)
                    margin = z * result["std"] / math.sqrt(len(numeric_predictions))
                    result["confidence_interval"] = (result["mean"] - margin, result["mean"] + margin)
                    
                elif method == "quartile":
                    # Non-parametric quartile-based interval
                    lower = float(np.quantile(predictions_array, (1 - confidence) / 2))
                    upper = float(np.quantile(predictions_array, 1 - (1 - confidence) / 2))
                    result["confidence_interval"] = (lower, upper)
            else:
                # Fallback calculation without NumPy
                result["mean"] = statistics.mean(numeric_predictions)
                result["std"] = statistics.stdev(numeric_predictions) if len(numeric_predictions) > 1 else 0
                
                # Simple percentile-based confidence interval
                sorted_preds = sorted(numeric_predictions)
                lower_idx = int(len(sorted_preds) * (1 - confidence) / 2)
                upper_idx = int(len(sorted_preds) * (1 - (1 - confidence) / 2))
                lower = sorted_preds[max(0, lower_idx)]
                upper = sorted_preds[min(len(sorted_preds) - 1, upper_idx)]
                result["confidence_interval"] = (lower, upper)
                
        except Exception as e:
            self.logger.error(f"Error calculating uncertainty: {e}")
            return {"error": f"Failed to calculate uncertainty: {e}"}
        
        return result
    
    def calculate_calibration(self, true_values: List[Any], predicted_probs: List[List[float]], 
                            n_bins: int = 10) -> Dict[str, Any]:
        """
        Calculate calibration metrics for probabilistic predictions.
        
        Args:
            true_values: List of true class labels
            predicted_probs: List of predicted probability distributions
            n_bins: Number of bins for calibration curve
            
        Returns:
            Dictionary of calibration metrics
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not available for calibration metrics"}
        
        if len(true_values) != len(predicted_probs):
            return {"error": "Length mismatch between true values and predictions"}
        
        if not predicted_probs or not isinstance(predicted_probs[0], (list, tuple, np.ndarray if NUMPY_AVAILABLE else tuple)):
            return {"error": "predicted_probs must contain probability distributions"}
            
        try:
            # Convert to numpy arrays if available
            if NUMPY_AVAILABLE:
                y_true = np.array(true_values)
                y_prob = np.array(predicted_probs)
            else:
                y_true = true_values
                y_prob = predicted_probs

            # Handle different prediction formats
            if NUMPY_AVAILABLE and isinstance(y_prob, np.ndarray):
                if y_prob.ndim == 2 and y_prob.shape[1] == 1:
                    # Binary classification with single probability
                    y_prob = y_prob.flatten()
                    
                if y_prob.ndim == 1:
                    # Binary classification
                    prob_pos = y_prob
                else:
                    # Multiclass: take max probability as confidence
                    prob_pos = np.max(y_prob, axis=1)
            elif isinstance(y_prob, list) and y_prob and isinstance(y_prob[0], (int, float)):
                 # Fallback for binary classification without numpy
                 prob_pos = y_prob
            elif isinstance(y_prob, list) and y_prob and isinstance(y_prob[0], (list, tuple)):
                 # Fallback for multiclass without numpy
                 prob_pos = [max(p) for p in y_prob]
            else:
                 return {"error": "Unsupported predicted_probs format"}


            # Calculate calibration curve
            prob_true, prob_pred = sk_calibration.calibration_curve(
                y_true, prob_pos, n_bins=n_bins, strategy='uniform'
            )
            
            # Calculate expected calibration error
            ece = 0
            for i in range(len(prob_true)):
                ece += abs(prob_true[i] - prob_pred[i])
            ece /= len(prob_true)
            
            # Calculate Brier score
            if NUMPY_AVAILABLE and isinstance(y_prob, np.ndarray) and y_prob.ndim == 1:
                # Binary case with numpy
                brier_score = sk_metrics.brier_score_loss(y_true, prob_pos)
            elif NUMPY_AVAILABLE and isinstance(y_prob, np.ndarray) and y_prob.ndim > 1:
                # Multi-class with numpy: average Brier score across classes
                brier_score = 0
                for i in range(y_prob.shape[1]):
                    brier_score += sk_metrics.brier_score_loss(
                        y_true == i, y_prob[:, i]
                    )
                brier_score /= y_prob.shape[1]
            elif isinstance(y_prob, list) and y_prob and isinstance(y_prob[0], (int, float)):
                 # Fallback for binary classification without numpy
                 # Simple squared error for binary case
                 brier_score = sum([(y_true[i] - prob_pos[i])**2 for i in range(len(y_true))]) / len(y_true)
            elif isinstance(y_prob, list) and y_prob and isinstance(y_prob[0], (list, tuple)):
                 # Fallback for multiclass without numpy
                 # Simple average squared error across classes
                 brier_score = sum([sum([( (1 if y_true[i] == c else 0) - y_prob[i][c] )**2 for c in range(len(y_prob[i]))]) for i in range(len(y_true))]) / len(y_true) / len(y_prob[0])
            else:
                 brier_score = None # Cannot calculate Brier score


            return {
                "expected_calibration_error": float(ece),
                "brier_score": float(brier_score) if brier_score is not None else None,
                "reliability_diagram": {
                    "y_true": prob_true.tolist(),
                    "y_pred": prob_pred.tolist()
                },
                "is_well_calibrated": ece < self.calibration_threshold
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating calibration metrics: {e}")
            return {"error": f"Failed to calculate calibration metrics: {e}"}
    
    def statistical_significance_test(self, method_a_errors: List[float], 
                                     method_b_errors: List[float],
                                     test_type: str = "ttest") -> Dict[str, Any]:
        """
        Perform statistical significance test to compare two methods.
        
        Args:
            method_a_errors: List of errors from method A
            method_b_errors: List of errors from method B
            test_type: Type of test ('ttest', 'wilcoxon', 'sign', 'mannwhitney')
            
        Returns:
            Dictionary with test results
        """
        if not SCIPY_AVAILABLE:
            return {"error": "scipy not available for statistical tests"}
        
        if len(method_a_errors) < 5 or len(method_b_errors) < 5:
            return {
                "error": "Not enough data points for statistical testing",
                "method_a_count": len(method_a_errors),
                "method_b_count": len(method_b_errors)
            }
            
        try:
            results: Dict[str, Any] = {
                "test_type": test_type,
                "method_a_mean": statistics.mean(method_a_errors) if method_a_errors else None,
                "method_b_mean": statistics.mean(method_b_errors) if method_b_errors else None,
                "significant": False,
                "p_value": None
            }
            
            # Perform the selected statistical test
            if test_type == "ttest":
                # Paired t-test
                if len(method_a_errors) != len(method_b_errors):
                    # Use independent t-test if lengths don't match
                    stat, p_value = stats.ttest_ind(method_a_errors, method_b_errors, equal_var=False)
                else:
                    stat, p_value = stats.ttest_rel(method_a_errors, method_b_errors)
                    
            elif test_type == "wilcoxon" and len(method_a_errors) == len(method_b_errors):
                # Wilcoxon signed-rank test (non-parametric, paired)
                stat, p_value = stats.wilcoxon(method_a_errors, method_b_errors)
                
            elif test_type == "sign" and len(method_a_errors) == len(method_b_errors):
                # Sign test (non-parametric, paired)
                differences = [a - b for a, b in zip(method_a_errors, method_b_errors)]
                pos = sum(1 for d in differences if d > 0)
                neg = sum(1 for d in differences if d < 0)
                # Use binomtest instead of binom_test
                result = stats.binomtest(min(pos, neg), n=pos + neg, p=0.5)
                p_value = result.pvalue
                stat = None # binomtest does not return a stat in the same way
                
            elif test_type == "mannwhitney":
                # Mann-Whitney U test (non-parametric, independent)
                stat, p_value = stats.mannwhitneyu(method_a_errors, method_b_errors)
                
            else:
                return {"error": f"Unsupported test type: {test_type}"}
                
            results["p_value"] = float(p_value) if p_value is not None else None
            results["significant"] = p_value is not None and p_value < self.statistical_significance
            
            # Determine better method only if means are available
            if results["method_a_mean"] is not None and results["method_b_mean"] is not None:
                 results["better_method"] = "A" if results["method_a_mean"] < results["method_b_mean"] else "B"
            else:
                 results["better_method"] = None
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error performing statistical test: {e}")
            return {"error": f"Failed to perform statistical test: {e}"}
    
    def track_advanced_iteration(self, iteration: int, metrics: Dict[str, Any],
                                predictions: Optional[List[Union[int, float, str, bool]]] = None,
                                true_values: Optional[List[Any]] = None,
                                predicted_probs: Optional[List[List[float]]] = None,
                                model_name: str = "default",
                                rule_type: Optional[str] = None,
                                tags: Optional[List[str]] = None) -> str:
        """
        Track a training iteration with advanced metrics.
        
        Args:
            iteration: Training iteration number
            metrics: Dictionary of metric values
            predictions: Optional list of discrete predictions
            true_values: Optional list of true values
            predicted_probs: Optional list of predicted probability distributions
            model_name: Name of the model
            rule_type: Type of rule (symbolic, neural, hybrid)
            tags: Optional list of tags
            
        Returns:
            ID of the stored metrics record
        """
        # First, track with the base implementation
        metric_id = super().track_iteration(iteration, metrics, model_name, rule_type, tags)
        
        # Now add advanced metrics if we have predictions and true values
        advanced_metrics = {}
        
        if predictions is not None and true_values is not None:
            # Calculate classification metrics if applicable
            if all(isinstance(p, (int, str, bool)) for p in predictions) and SKLEARN_AVAILABLE:
                # Classification metrics
                try:
                    # Confusion matrix
                    cm = sk_metrics.confusion_matrix(true_values, predictions).tolist()
                    advanced_metrics["confusion_matrix"] = cm
                    
                    # Classification report
                    report = sk_metrics.classification_report(
                        true_values, predictions, output_dict=True
                    )
                    advanced_metrics["classification_report"] = report
                except Exception as e:
                    self.logger.warning(f"Error calculating classification metrics: {e}")
            
            # Calculate uncertainty for regression metrics
            if all(isinstance(p, (int, float)) for p in predictions) and NUMPY_AVAILABLE:
                uncertainty = self.calculate_uncertainty(predictions)
                if "error" not in uncertainty:
                    advanced_metrics["uncertainty"] = uncertainty
                    self.uncertainty_estimates[iteration] = uncertainty
            
            # Calculate calibration metrics if we have probabilistic predictions
            if predicted_probs and SKLEARN_AVAILABLE:
                calibration = self.calculate_calibration(true_values, predicted_probs)
                if "error" not in calibration:
                    advanced_metrics["calibration"] = calibration
                    self.calibration_metrics[iteration] = calibration
        
        # Update adaptive thresholds
        self._update_adaptive_thresholds(iteration, metrics)
        
        # Check for drift
        if iteration > 1:
            drift_metrics = self._check_for_drift(iteration, metrics)
            advanced_metrics["drift"] = drift_metrics
            self.drift_metrics[iteration] = drift_metrics
        
        # Check convergence with advanced criteria
        convergence_status = self._check_advanced_convergence(iteration, metrics)
        advanced_metrics["convergence"] = convergence_status
        self.convergence_status = convergence_status
        
        # Store advanced metrics
        if advanced_metrics:
            # Prepare advanced metrics data
            advanced_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metric_type": "advanced_metrics",
                "base_metric_id": metric_id,
                "iteration": iteration,
                "model": model_name,
                "advanced_metrics": advanced_metrics,
                "tags": (tags or []) + ["advanced"]
            }
            
            # Add rule type if provided
            if rule_type:
                advanced_data["rule_type"] = rule_type
                advanced_data["tags"].append(f"rule_type:{rule_type}")
            
            # Store in metrics store
            self.metrics_store.store_metric(advanced_data)
        
        return metric_id
    
    def _update_adaptive_thresholds(self, iteration: int, metrics: Dict[str, Any]) -> None:
        """
        Update adaptive thresholds based on current performance.
        
        Args:
            iteration: Training iteration number
            metrics: Dictionary of metric values
        """
        # Update error thresholds (decrease over time)
        for metric_name in ["mse", "mae", "rmse"]:
            if metric_name in metrics and metric_name in self.adaptive_thresholds:
                threshold = self.adaptive_thresholds[metric_name]
                
                # Apply decay, but don't go below minimum
                new_value = max(threshold["current"] * threshold["decay_rate"], 
                               threshold["min"])
                self.adaptive_thresholds[metric_name]["current"] = new_value
        
        # Update accuracy/f1 thresholds (increase over time)
        for metric_name in ["accuracy", "f1_score"]:
            if metric_name in metrics and metric_name in self.adaptive_thresholds:
                threshold = self.adaptive_thresholds[metric_name]
                
                # Apply growth, but don't exceed maximum
                new_value = min(threshold["current"] * threshold["growth_rate"], 
                               threshold["max"])
                self.adaptive_thresholds[metric_name]["current"] = new_value
    
    def _check_for_drift(self, iteration: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for drift in performance metrics.
        
        Args:
            iteration: Training iteration number
            metrics: Dictionary of metric values
            
        Returns:
            Dictionary with drift analysis
        """
        drift_results = {
            "detected": False,
            "metrics": {}
        }
        
        # Need at least 3 iterations for meaningful drift detection
        if iteration < 3 or len(self.iteration_history) < 3:
            return drift_results
        
        # Get metrics from last few iterations
        recent_iterations = sorted(
            [ih for ih in self.iteration_history if "iteration" in ih],
            key=lambda x: x["iteration"],
            reverse=True
        )[:5]  # Last 5 iterations
        
        if len(recent_iterations) < 3:
            return drift_results
        
        # Check key metrics for drift
        for metric_name in ["mse", "mae", "accuracy", "f1_score"]:
            if metric_name not in metrics:
                continue
                
            # Extract metric values from recent iterations
            values = []
            for it in recent_iterations:
                if "metrics" in it and metric_name in it["metrics"]:
                    values.append(it["metrics"][metric_name])
            
            if len(values) < 3:
                continue
                
            # Calculate trend
            trend = 0
            for i in range(len(values) - 1):
                if values[i] > values[i + 1]:  # Increasing (worse for error metrics)
                    trend += 1
                elif values[i] < values[i + 1]:  # Decreasing (worse for accuracy metrics)
                    trend -= 1
            
            # Determine if there's drift
            metric_drift = False
            direction = ""
            
            if metric_name in ["mse", "mae", "rmse"]:
                # For error metrics, an increasing trend is bad
                if trend > 0 and values[0] > values[-1] * 1.1:  # 10% increase
                    metric_drift = True
                    direction = "increasing"
            else:
                # For accuracy metrics, a decreasing trend is bad
                if trend < 0 and values[0] < values[-1] * 0.9:  # 10% decrease
                    metric_drift = True
                    direction = "decreasing"
            
            drift_results["metrics"][metric_name] = {
                "trend": trend,
                "drift_detected": metric_drift,
                "direction": direction,
                "values": values
            }
            
            if metric_drift:
                drift_results["detected"] = True
        
        return drift_results
    
    def _check_advanced_convergence(self, iteration: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for convergence using advanced criteria.
        
        Args:
            iteration: Training iteration number
            metrics: Dictionary of metric values
            
        Returns:
            Dictionary with convergence status
        """
        # Update convergence status
        convergence_status = self.convergence_status.copy()
        
        # Update stability window
        if "mse" in metrics:
            window = convergence_status.get("stability_window", [])
            window.append(metrics["mse"])
            
            # Keep only the last N values
            window = window[-self.stability_window_size:]
            convergence_status["stability_window"] = window
        
        # Skip if we don't have enough data
        if len(convergence_status.get("stability_window", [])) < self.stability_window_size:
            return convergence_status
        
        # Calculate convergence criteria
        criteria = {}
        
        # Criterion 1: Standard deviation of recent values below threshold
        window = convergence_status["stability_window"]
        if len(window) >= 3:
            std_dev = statistics.stdev(window)
            mean_val = statistics.mean(window)
            
            # Normalized standard deviation
            if mean_val != 0:
                normalized_std = std_dev / mean_val
                criteria["normalized_std"] = normalized_std
                criteria["std_converged"] = normalized_std < self.convergence_threshold
            
        # Criterion 2: No significant improvement in last N iterations
        if len(window) >= self.stability_window_size:
            first_half = window[:len(window)//2]
            second_half = window[len(window)//2:]
            
            first_mean = statistics.mean(first_half)
            second_mean = statistics.mean(second_half)
            
            # Calculate relative improvement
            if first_mean != 0:
                rel_improvement = (first_mean - second_mean) / first_mean
                criteria["relative_improvement"] = rel_improvement
                criteria["improvement_converged"] = rel_improvement < self.convergence_threshold
        
        # Criterion 3: Rate of change below threshold
        if len(window) >= 2:
            rates = [abs(window[i] - window[i-1]) / (abs(window[i-1]) if window[i-1] != 0 else 1.0) 
                    for i in range(1, len(window))]
            avg_rate = statistics.mean(rates)
            
            criteria["average_rate_of_change"] = avg_rate
            criteria["rate_converged"] = avg_rate < self.convergence_threshold
        
        # Update convergence criteria
        convergence_status["convergence_criteria"] = criteria
        
        # Check if we've converged based on all criteria
        all_converged = all([
            criteria.get("std_converged", False),
            criteria.get("improvement_converged", False),
            criteria.get("rate_converged", False)
        ])
        
        # Update convergence status
        if all_converged and not convergence_status.get("converged", False):
            convergence_status["converged"] = True
            convergence_status["converged_at_iteration"] = iteration
            self.logger.info(f"Training converged at iteration {iteration} based on advanced criteria")
        
        return convergence_status
    
    def evaluate_offline(self, model, dataset_name: str, dataset: Dict[str, Any],
                        metrics_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform offline evaluation on a held-out dataset.
        
        Args:
            model: Model to evaluate
            dataset_name: Name of the dataset
            dataset: Dictionary with 'inputs' and 'targets' keys
            metrics_list: List of metrics to calculate
            
        Returns:
            Dictionary with evaluation results
        """
        if "inputs" not in dataset or "targets" not in dataset:
            return {"error": "Dataset must contain 'inputs' and 'targets' keys"}
        
        if len(dataset["inputs"]) != len(dataset["targets"]):
            return {"error": "Number of inputs must match number of targets"}
        
        if metrics_list is None:
            metrics_list = ["mse", "mae", "rmse", "accuracy", "f1_score"]
        
        try:
            # Generate predictions
            inputs = dataset["inputs"]
            targets = dataset["targets"]
            
            # Track cost for prediction operation
            prediction_start_time = datetime.now()
            
            # Predict function should be implemented appropriately for the model
            predictions: List[Any] = []
            predicted_probs: List[List[float]] = []
            
            # This is a simplified example - in real implementation, 
            # we would have a more sophisticated prediction interface
            if hasattr(model, "predict"):
                predictions = model.predict(inputs)
            elif callable(model):
                predictions = [model(x) for x in inputs]
            else:
                return {"error": "Model must have a predict method or be callable"}
            
            # Also get probabilistic predictions if available
            if hasattr(model, "predict_proba"):
                predicted_probs = model.predict_proba(inputs)
            
            # Track cost for prediction
            prediction_duration = (datetime.now() - prediction_start_time).total_seconds()
            self.cost_controller.track_operation(
                operation_type="model_inference", 
                data_size=len(inputs),
                duration=prediction_duration
            )
            
            # Calculate metrics
            evaluation_results = {}
            
            # Error metrics for regression
            if "mse" in metrics_list and all(isinstance(t, (int, float)) for t in targets):
                # Ensure predictions are float for regression metrics
                float_predictions = [float(p) for p in predictions]
                evaluation_results["mse"] = self.calculate_mse(targets, float_predictions)
            
            if "mae" in metrics_list and all(isinstance(t, (int, float)) for t in targets):
                # Ensure predictions are float for regression metrics
                float_predictions = [float(p) for p in predictions]
                evaluation_results["mae"] = self.calculate_mae(targets, float_predictions)
            
            if "rmse" in metrics_list and all(isinstance(t, (int, float)) for t in targets):
                # Ensure predictions are float for regression metrics
                float_predictions = [float(p) for p in predictions]
                evaluation_results["rmse"] = self.calculate_rmse(targets, float_predictions)
            
            # Classification metrics
            if "accuracy" in metrics_list:
                evaluation_results["accuracy"] = self.calculate_accuracy(targets, predictions)
            
            if "f1_score" in metrics_list:
                evaluation_results["f1_score"] = self.calculate_f1_score(targets, predictions)
            
            # Advanced metrics
            if predicted_probs and SKLEARN_AVAILABLE:
                calibration = self.calculate_calibration(targets, predicted_probs)
                if "error" not in calibration:
                    evaluation_results["calibration"] = calibration
            
            if predictions is not None and NUMPY_AVAILABLE:
                # Ensure predictions are float for uncertainty calculation
                float_predictions = [float(p) for p in predictions if isinstance(p, (int, float))]
                if float_predictions:
                    uncertainty = self.calculate_uncertainty(float_predictions)
                    if "error" not in uncertainty:
                        evaluation_results["uncertainty"] = uncertainty
            
            # Store the evaluation
            timestamp = datetime.now(timezone.utc).isoformat()
            evaluation_data = {
                "timestamp": timestamp,
                "dataset": dataset_name,
                "dataset_size": len(inputs),
                "metric_type": "offline_evaluation",
                "metrics": evaluation_results,
                "tags": ["offline_evaluation", f"dataset:{dataset_name}"]
            }
            
            # Store in metrics store
            eval_id = self.metrics_store.store_metric(evaluation_data)
            
            # Add result to our evaluation datasets
            self.evaluation_datasets[dataset_name] = {
                "last_eval_id": eval_id,
                "last_eval_time": timestamp,
                "results": evaluation_results
            }
            
            return {
                "eval_id": eval_id,
                "results": evaluation_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in offline evaluation: {e}")
            return {"error": f"Failed to perform offline evaluation: {e}"}
    
    def get_advanced_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance summary with advanced metrics.
        
        Returns:
            Dictionary with advanced performance summary
        """
        # Get basic summary
        basic_summary = self.get_performance_summary()
        
        if "error" in basic_summary:
            return basic_summary
        
        # Add advanced metrics
        advanced_summary = basic_summary.copy()
        
        # Add calibration metrics if available
        if self.calibration_metrics:
            latest_calibration = max(self.calibration_metrics.items(), key=lambda x: x[0])[1]
            advanced_summary["calibration"] = latest_calibration
        
        # Add uncertainty metrics if available
        if self.uncertainty_estimates:
            latest_uncertainty = max(self.uncertainty_estimates.items(), key=lambda x: x[0])[1]
            advanced_summary["uncertainty"] = latest_uncertainty
        
        # Add drift metrics if available
        if self.drift_metrics:
            latest_drift = max(self.drift_metrics.items(), key=lambda x: x[0])[1]
            advanced_summary["drift"] = latest_drift
        
        # Add convergence status
        advanced_summary["convergence_status"] = self.convergence_status
        
        # Add adaptive thresholds
        advanced_summary["adaptive_thresholds"] = self.adaptive_thresholds
        
        # Add offline evaluation results if available
        if self.evaluation_datasets:
            advanced_summary["offline_evaluations"] = {
                name: data["results"] 
                for name, data in self.evaluation_datasets.items()
            }
        
        return advanced_summary
    
    def compare_models_advanced(self, model_names: List[str], 
                              metric_names: Optional[List[str]] = None,
                              statistical_test: str = "ttest") -> Dict[str, Any]:
        """
        Advanced comparison of multiple models with statistical testing.
        
        Args:
            model_names: List of model names to compare
            metric_names: List of metrics to compare (default: ["mse", "mae", "accuracy"])
            statistical_test: Statistical test to use
            
        Returns:
            Dictionary with comparison results
        """
        if metric_names is None:
            metric_names = ["mse", "mae", "accuracy"]
        
        # Get basic comparison for each metric
        comparisons = {}
        for metric_name in metric_names:
            comparisons[metric_name] = self.compare_models(model_names, metric_name)
        
        # Get detailed metrics for each model for statistical testing
        model_metrics = {}
        for model_name in model_names:
            # Query detailed metrics for this model
            metrics_records = self.metrics_store.query_metrics(
                models=[model_name],
                metric_types=["training_iteration"],
                limit=None  # Get all iterations
            )
            
            if not metrics_records:
                continue
                
            # Extract metrics for each iteration
            model_metrics[model_name] = {}
            for metric_name in metric_names:
                model_metrics[model_name][metric_name] = [
                    record["metrics"].get(metric_name)
                    for record in metrics_records
                    if "metrics" in record and metric_name in record["metrics"]
                ]
        
        # Perform statistical tests between each pair of models
        statistical_results = {}
        for metric_name in metric_names:
            statistical_results[metric_name] = {}
            
            for i, model_a in enumerate(model_names):
                if model_a not in model_metrics:
                    continue
                    
                for model_b in model_names[i+1:]:
                    if model_b not in model_metrics:
                        continue
                        
                    # Get metric values for both models
                    values_a = model_metrics[model_a][metric_name]
                    values_b = model_metrics[model_b][metric_name]
                    
                    if not values_a or not values_b:
                        continue
                    
                    # Perform statistical test
                    test_result = self.statistical_significance_test(
                        values_a, values_b, test_type=statistical_test
                    )
                    
                    comparison_key = f"{model_a}_vs_{model_b}"
                    statistical_results[metric_name][comparison_key] = test_result
        
        # Find the overall best model
        best_models = {}
        for metric_name in metric_names:
            if metric_name in comparisons and "best_model" in comparisons[metric_name]:
                best_models[metric_name] = comparisons[metric_name]["best_model"]
        
        # Count how many metrics each model is best at
        model_scores = {model: 0 for model in model_names}
        for metric, model in best_models.items():
            if model in model_scores:
                model_scores[model] += 1
        
        # Overall best model is the one best at most metrics
        overall_best = max(model_scores.items(), key=lambda x: x[1])[0] if model_scores else None
        
        return {
            "comparisons": comparisons,
            "statistical_tests": statistical_results,
            "best_models_by_metric": best_models,
            "model_scores": model_scores,
            "overall_best_model": overall_best
        }