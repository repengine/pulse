"""
RecursiveTrainingMetrics

Implements core metrics calculation for the recursive training system.
Responsible for tracking training progress, calculating error metrics,
and providing performance insights for model evaluation.
"""

import logging
import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Callable

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import sklearn.metrics as sk_metrics
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
        self.training_costs = {
            "api_calls": 0,
            "token_usage": 0,
            "total_cost": 0.0
        }
        
        # Track performance by rule type
        self.rule_performance = {
            "symbolic": {},
            "neural": {},
            "hybrid": {}
        }
    
    def _validate_data(self, true_values: List[Any], predicted_values: List[Any]) -> bool:
        """
        Validate input data for metrics calculation.
        
        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            
        Returns:
            Whether the data is valid
        """
        if len(true_values) != len(predicted_values):
            self.logger.error(f"Length mismatch: true values ({len(true_values)}) != predicted values ({len(predicted_values)})")
            return False
        
        if len(true_values) == 0:
            self.logger.error("Empty data provided for metrics calculation")
            return False
        
        return True
    
    def _safe_calculation(self, metric_func: Callable, 
                          true_values: List[Any], 
                          predicted_values: List[Any], 
                          default_value: Any = None) -> Any:
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
    
    def calculate_mse(self, true_values: List[float], predicted_values: List[float]) -> float:
        """
        Calculate Mean Squared Error.
        
        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            
        Returns:
            MSE value or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float('nan')
        
        if NUMPY_AVAILABLE:
            import numpy as np
            return self._safe_calculation(
                lambda x, y: np.mean(np.square(np.array(x) - np.array(y))),
                true_values, predicted_values, float('nan')
            )
        else:
            # Fallback calculation
            try:
                squared_errors = [(t - p) ** 2 for t, p in zip(true_values, predicted_values)]
                return sum(squared_errors) / len(squared_errors)
            except Exception as e:
                self.logger.error(f"Error calculating MSE: {e}")
                return float('nan')
    
    def calculate_mae(self, true_values: List[float], predicted_values: List[float]) -> float:
        """
        Calculate Mean Absolute Error.
        
        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            
        Returns:
            MAE value or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float('nan')
        
        if NUMPY_AVAILABLE:
            import numpy as np
            return self._safe_calculation(
                lambda x, y: np.mean(np.abs(np.array(x) - np.array(y))),
                true_values, predicted_values, float('nan')
            )
        else:
            # Fallback calculation
            try:
                absolute_errors = [abs(t - p) for t, p in zip(true_values, predicted_values)]
                return sum(absolute_errors) / len(absolute_errors)
            except Exception as e:
                self.logger.error(f"Error calculating MAE: {e}")
                return float('nan')
    
    def calculate_rmse(self, true_values: List[float], predicted_values: List[float]) -> float:
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
            return float('nan')
        
        try:
            return math.sqrt(mse)
        except Exception as e:
            self.logger.error(f"Error calculating RMSE: {e}")
            return float('nan')
    
    def calculate_accuracy(self, true_values: List[Any], predicted_values: List[Any]) -> float:
        """
        Calculate classification accuracy.
        
        Args:
            true_values: List of true/expected values
            predicted_values: List of predicted values
            
        Returns:
            Accuracy value or None on error
        """
        if not self._validate_data(true_values, predicted_values):
            return float('nan')
        
        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics
            return self._safe_calculation(
                sk_metrics.accuracy_score,
                true_values, predicted_values, float('nan')
            )
        else:
            # Fallback calculation
            try:
                correct = sum(1 for t, p in zip(true_values, predicted_values) if t == p)
                return correct / len(true_values)
            except Exception as e:
                self.logger.error(f"Error calculating accuracy: {e}")
                return float('nan')
    
    def calculate_f1_score(self, true_values: List[Any], predicted_values: List[Any],
                          average: str = 'weighted') -> float:
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
            return float('nan')
        
        if SKLEARN_AVAILABLE:
            import sklearn.metrics as sk_metrics
            # Handle each average type explicitly to satisfy type checking
            if average == 'micro':
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(x, y, average='micro'),
                    true_values, predicted_values, float('nan')
                )
            elif average == 'macro':
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(x, y, average='macro'),
                    true_values, predicted_values, float('nan')
                )
            elif average == 'samples':
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(x, y, average='samples'),
                    true_values, predicted_values, float('nan')
                )
            elif average == 'binary':
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(x, y, average='binary'),
                    true_values, predicted_values, float('nan')
                )
            else:
                # Default to weighted
                return self._safe_calculation(
                    lambda x, y: sk_metrics.f1_score(x, y, average='weighted'),
                    true_values, predicted_values, float('nan')
                )
        else:
            self.logger.warning("scikit-learn not available for F1 calculation")
            return float('nan')
    
    def track_iteration(self, iteration: int, metrics: Dict[str, Any], 
                       model_name: str = "default", 
                       rule_type: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> str:
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
            "tags": tags or []
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
                if metrics[key] > self.baseline_metrics[key] * (1 + self.alert_threshold):
                    self.logger.warning(
                        f"Metric {key} degraded: {metrics[key]:.4f} vs baseline {self.baseline_metrics[key]:.4f}"
                    )
        
        # Check for accuracy or f1 regression
        for key in ["accuracy", "f1_score"]:
            if key in metrics and key in self.baseline_metrics:
                # For these metrics, lower is worse
                if metrics[key] < self.baseline_metrics[key] * (1 - self.alert_threshold):
                    self.logger.warning(
                        f"Metric {key} degraded: {metrics[key]:.4f} vs baseline {self.baseline_metrics[key]:.4f}"
                    )
    
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
            "tags": ["baseline"]
        }
        
        self.metrics_store.store_metric(baseline_data)
    
    def track_cost(self, api_calls: int = 0, token_usage: int = 0, 
                  cost: float = 0.0) -> Dict[str, Any]:
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
            "tags": ["cost"]
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
        for record in sorted(self.iteration_history, key=lambda x: x["iteration"], reverse=True)[:self.early_stopping_patience]:
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
    
    def compare_models(self, model_names: List[str], 
                      metric_name: str = "mse") -> Dict[str, Any]:
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
                limit=1  # Get the most recent
            )
            
            if metrics and "metrics" in metrics[0] and metric_name in metrics[0]["metrics"]:
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
        
        return {
            "metric": metric_name,
            "values": comparison,
            "best_model": best_model
        }
    
    def evaluate_rule_performance(self, rule_type: str) -> Dict[str, Any]:
        """
        Evaluate performance of a specific rule type.
        
        Args:
            rule_type: Type of rule to evaluate (symbolic, neural, hybrid)
            
        Returns:
            Dictionary with performance evaluation
        """
        if rule_type not in self.rule_performance or not self.rule_performance[rule_type]:
            return {"error": f"No performance data available for rule type: {rule_type}"}
        
        # Get the most recent iteration for this rule type
        latest_iteration = max(self.rule_performance[rule_type].keys())
        latest_metrics = self.rule_performance[rule_type][latest_iteration]
        
        # Get historical performance for this rule type
        historical = []
        for iteration, metrics in sorted(self.rule_performance[rule_type].items()):
            if "mse" in metrics:
                historical.append({
                    "iteration": iteration,
                    "mse": metrics["mse"]
                })
        
        # Calculate improvement if possible
        improvement = {}
        if len(historical) > 1:
            first = historical[0]
            last = historical[-1]
            
            # For error metrics, negative percentages mean improvement
            for key in ["mse", "rmse", "mae"]:
                if key in first and key in last and first[key] != 0:
                    improvement[key] = (last[key] - first[key]) / first[key] * 100
            
            # For accuracy metrics, positive percentages mean improvement
            for key in ["accuracy", "f1_score"]:
                if key in first and key in last and first[key] != 0:
                    improvement[key] = (last[key] - first[key]) / first[key] * 100
        
        return {
            "rule_type": rule_type,
            "latest_iteration": latest_iteration,
            "latest_metrics": latest_metrics,
            "historical": historical,
            "improvement": improvement
        }
    
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
                "shutdown": self.metrics_store.cost_thresholds["shutdown_threshold"]
            }
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
                if key in first_metrics and key in latest_metrics and first_metrics[key] != 0:
                    improvement[key] = (latest_metrics[key] - first_metrics[key]) / first_metrics[key] * 100
            
            # For accuracy metrics, positive percentages mean improvement
            for key in ["accuracy", "f1_score"]:
                if key in first_metrics and key in latest_metrics and first_metrics[key] != 0:
                    improvement[key] = (latest_metrics[key] - first_metrics[key]) / first_metrics[key] * 100
        
        # Get rule type performance
        rule_performance = {}
        for rule_type in self.rule_performance:
            if self.rule_performance[rule_type]:
                rule_performance[rule_type] = self.evaluate_rule_performance(rule_type)
        
        return {
            "total_iterations": len(self.iteration_history),
            "latest_iteration": latest_iteration["iteration"],
            "latest_metrics": latest_iteration.get("metrics", {}),
            "improvement": improvement,
            "convergence": self.check_convergence(),
            "rule_performance": rule_performance,
            "cost": self.get_cost_summary()
        }