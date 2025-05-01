"""
Tests for RecursiveTrainingMetrics

This module contains unit tests for the RecursiveTrainingMetrics class,
focusing on metrics calculation, error tracking, and performance evaluation.
"""

import pytest
import json
import math
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone

from recursive_training.metrics.training_metrics import RecursiveTrainingMetrics


@pytest.fixture
def mock_metrics_store():
    """Fixture for mock metrics store."""
    mock_store = MagicMock()
    mock_store.store_metric.return_value = "test_metric_id"
    mock_store.track_cost.return_value = {
        "total_cost": 5.0, 
        "api_calls": 50, 
        "token_usage": 5000,
        "status": "ok"
    }
    mock_store.query_metrics.return_value = []
    return mock_store


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "convergence_threshold": 0.005,
        "max_iterations": 50,
        "early_stopping_patience": 3,
        "alert_threshold": 0.2
    }


@pytest.fixture
def sample_metrics():
    """Fixture for sample metrics dictionary."""
    return {
        "mse": 0.05,
        "mae": 0.02,
        "rmse": 0.22,
        "accuracy": 0.95,
        "f1_score": 0.94
    }


@pytest.fixture
def training_metrics(mock_config, mock_metrics_store):
    """Fixture for training metrics with mocked dependencies."""
    with patch('recursive_training.metrics.training_metrics.get_metrics_store', return_value=mock_metrics_store):
        metrics = RecursiveTrainingMetrics(mock_config)
        return metrics


@pytest.fixture
def sample_true_values():
    """Fixture for sample true values."""
    return [1.0, 2.0, 3.0, 4.0, 5.0]


@pytest.fixture
def sample_predicted_values():
    """Fixture for sample predicted values."""
    return [1.2, 1.9, 3.1, 3.8, 5.2]


class TestRecursiveTrainingMetrics:
    """Tests for the RecursiveTrainingMetrics class."""

    def test_initialization(self, mock_config, mock_metrics_store):
        """Test correct initialization of the training metrics."""
        with patch('recursive_training.metrics.training_metrics.get_metrics_store', return_value=mock_metrics_store):
            metrics = RecursiveTrainingMetrics(mock_config)
            
            assert metrics.logger is not None
            assert metrics.config == mock_config
            assert metrics.metrics_store == mock_metrics_store
            assert metrics.convergence_threshold == mock_config["convergence_threshold"]
            assert metrics.max_iterations == mock_config["max_iterations"]
            assert metrics.early_stopping_patience == mock_config["early_stopping_patience"]
            assert metrics.alert_threshold == mock_config["alert_threshold"]
            assert isinstance(metrics.current_metrics, dict)
            assert isinstance(metrics.baseline_metrics, dict)
            assert isinstance(metrics.iteration_history, list)
            assert isinstance(metrics.training_costs, dict)
            assert "api_calls" in metrics.training_costs
            assert "token_usage" in metrics.training_costs
            assert "total_cost" in metrics.training_costs
            assert isinstance(metrics.rule_performance, dict)
            assert "symbolic" in metrics.rule_performance
            assert "neural" in metrics.rule_performance
            assert "hybrid" in metrics.rule_performance

    def test_validate_data(self, training_metrics):
        """Test data validation for metrics calculation."""
        # Valid data
        assert training_metrics._validate_data([1, 2, 3], [4, 5, 6]) is True
        
        # Invalid: length mismatch
        assert training_metrics._validate_data([1, 2, 3], [4, 5]) is False
        
        # Invalid: empty data
        assert training_metrics._validate_data([], []) is False

    def test_safe_calculation(self, training_metrics):
        """Test safe calculation with error handling."""
        # Test normal function
        def good_func(x, y):
            return sum(x) / len(x) - sum(y) / len(y)
        
        result = training_metrics._safe_calculation(good_func, [1, 2, 3], [4, 5, 6], "error")
        assert result == -3.0
        
        # Test function that raises exception
        def bad_func(x, y):
            raise ValueError("Test error")
        
        result = training_metrics._safe_calculation(bad_func, [1, 2, 3], [4, 5, 6], "error")
        assert result == "error"

    def test_calculate_mse(self, training_metrics, sample_true_values, sample_predicted_values):
        """Test MSE calculation."""
        # Normal calculation
        mse = training_metrics.calculate_mse(sample_true_values, sample_predicted_values)
        expected_mse = sum((t - p) ** 2 for t, p in zip(sample_true_values, sample_predicted_values)) / 5
        assert mse == pytest.approx(expected_mse)
        
        # Invalid data
        mse_invalid = training_metrics.calculate_mse([], [1, 2, 3])
        assert math.isnan(mse_invalid)

    def test_calculate_mae(self, training_metrics, sample_true_values, sample_predicted_values):
        """Test MAE calculation."""
        # Normal calculation
        mae = training_metrics.calculate_mae(sample_true_values, sample_predicted_values)
        expected_mae = sum(abs(t - p) for t, p in zip(sample_true_values, sample_predicted_values)) / 5
        assert mae == pytest.approx(expected_mae)
        
        # Invalid data
        mae_invalid = training_metrics.calculate_mae([1, 2], [1, 2, 3])
        assert math.isnan(mae_invalid)

    def test_calculate_rmse(self, training_metrics, sample_true_values, sample_predicted_values):
        """Test RMSE calculation."""
        # Normal calculation
        rmse = training_metrics.calculate_rmse(sample_true_values, sample_predicted_values)
        mse = sum((t - p) ** 2 for t, p in zip(sample_true_values, sample_predicted_values)) / 5
        expected_rmse = math.sqrt(mse)
        assert rmse == pytest.approx(expected_rmse)
        
        # Invalid data
        rmse_invalid = training_metrics.calculate_rmse([], [1, 2, 3])
        assert math.isnan(rmse_invalid)

    def test_calculate_accuracy(self, training_metrics):
        """Test accuracy calculation."""
        # Test with classification data
        true_values = [0, 1, 0, 1, 1]
        predicted_values = [0, 1, 1, 1, 0]
        # 3/5 correct predictions
        accuracy = training_metrics.calculate_accuracy(true_values, predicted_values)
        assert accuracy == 0.6
        
        # Invalid data
        accuracy_invalid = training_metrics.calculate_accuracy([0, 1], [0, 1, 1])
        assert math.isnan(accuracy_invalid)

    def test_calculate_f1_score(self, training_metrics):
        """Test F1 score calculation."""
        # Test with mock sklearn
        with patch('recursive_training.metrics.training_metrics.SKLEARN_AVAILABLE', True):
            with patch('recursive_training.metrics.training_metrics.sk_metrics') as mock_sk_metrics:
                mock_sk_metrics.f1_score.return_value = 0.75
                
                true_values = [0, 1, 0, 1, 1]
                predicted_values = [0, 1, 1, 1, 0]
                
                # Test with different average methods
                f1 = training_metrics.calculate_f1_score(true_values, predicted_values, average='weighted')
                assert f1 == 0.75
                mock_sk_metrics.f1_score.assert_called_with(true_values, predicted_values, average='weighted')
                
                f1_micro = training_metrics.calculate_f1_score(true_values, predicted_values, average='micro')
                assert f1_micro == 0.75
                mock_sk_metrics.f1_score.assert_called_with(true_values, predicted_values, average='micro')
        
        # Test without sklearn
        with patch('recursive_training.metrics.training_metrics.SKLEARN_AVAILABLE', False):
            f1 = training_metrics.calculate_f1_score([0, 1], [0, 1])
            assert math.isnan(f1)

    def test_track_iteration(self, training_metrics, sample_metrics):
        """Test tracking a training iteration."""
        # Test tracking with default values
        metric_id = training_metrics.track_iteration(
            iteration=1,
            metrics=sample_metrics
        )
        
        # Verify metrics were stored
        training_metrics.metrics_store.store_metric.assert_called_once()
        stored_data = training_metrics.metrics_store.store_metric.call_args[0][0]
        assert stored_data["metric_type"] == "training_iteration"
        assert stored_data["iteration"] == 1
        assert stored_data["metrics"] == sample_metrics
        
        # Verify current metrics were updated
        assert training_metrics.current_metrics == sample_metrics
        
        # Verify iteration was added to history
        assert len(training_metrics.iteration_history) == 1
        assert training_metrics.iteration_history[0]["iteration"] == 1
        
        # Verify returned metric ID
        assert metric_id == "test_metric_id"
        
        # Test with rule type and custom model
        training_metrics.metrics_store.store_metric.reset_mock()
        training_metrics.track_iteration(
            iteration=2,
            metrics=sample_metrics,
            model_name="custom_model",
            rule_type="symbolic",
            tags=["test_tag"]
        )
        
        # Verify rule type was tracked
        stored_data = training_metrics.metrics_store.store_metric.call_args[0][0]
        assert stored_data["model"] == "custom_model"
        assert stored_data["rule_type"] == "symbolic"
        assert "rule_type:symbolic" in stored_data["tags"]
        assert "test_tag" in stored_data["tags"]
        
        # Verify rule performance was tracked
        assert 2 in training_metrics.rule_performance["symbolic"]
        assert training_metrics.rule_performance["symbolic"][2] == sample_metrics

    def test_check_metrics_alerts(self, training_metrics):
        """Test metrics alerts checking."""
        # Setup baseline and current metrics
        training_metrics.baseline_metrics = {
            "mse": 0.1,
            "rmse": 0.3,
            "mae": 0.05,
            "accuracy": 0.9,
            "f1_score": 0.85
        }
        
        # Test no degradation (better metrics)
        current_metrics = {
            "mse": 0.08,  # Lower is better
            "accuracy": 0.95  # Higher is better
        }
        
        # This should not log any warnings
        with patch.object(training_metrics.logger, 'warning') as mock_warning:
            training_metrics._check_metrics_alerts(current_metrics)
            mock_warning.assert_not_called()
        
        # Test significant degradation
        degraded_metrics = {
            "mse": 0.15,  # 50% worse, above threshold
            "accuracy": 0.7  # 22% worse, above threshold
        }
        
        # This should log warnings
        with patch.object(training_metrics.logger, 'warning') as mock_warning:
            training_metrics._check_metrics_alerts(degraded_metrics)
            assert mock_warning.call_count == 2  # One for each degraded metric

    def test_set_baseline(self, training_metrics, sample_metrics):
        """Test setting baseline metrics."""
        # Set baseline
        training_metrics.set_baseline(sample_metrics)
        
        # Verify baseline was set
        assert training_metrics.baseline_metrics == sample_metrics
        
        # Verify metrics were stored
        training_metrics.metrics_store.store_metric.assert_called_once()
        stored_data = training_metrics.metrics_store.store_metric.call_args[0][0]
        assert stored_data["metric_type"] == "baseline"
        assert stored_data["metrics"] == sample_metrics
        assert "baseline" in stored_data["tags"]

    def test_track_cost(self, training_metrics):
        """Test cost tracking."""
        # Test direct cost tracking
        result = training_metrics.track_cost(api_calls=10, token_usage=1000, cost=1.5)
        
        # Verify local tracking was updated
        assert training_metrics.training_costs["api_calls"] == 10
        assert training_metrics.training_costs["token_usage"] == 1000
        assert training_metrics.training_costs["total_cost"] == 1.5
        
        # Verify metrics were stored
        training_metrics.metrics_store.store_metric.assert_called_once()
        stored_data = training_metrics.metrics_store.store_metric.call_args[0][0]
        assert stored_data["metric_type"] == "cost"
        assert stored_data["api_calls"] == 10
        assert stored_data["token_usage"] == 1000
        assert stored_data["cost"] == 1.5
        
        # Verify metrics_store.track_cost was called
        training_metrics.metrics_store.track_cost.assert_called_once_with(1.5, 10, 1000)
        
        # Verify result was returned from metrics_store.track_cost
        assert result == training_metrics.metrics_store.track_cost.return_value
        
        # Test cost estimation from tokens
        training_metrics.metrics_store.store_metric.reset_mock()
        training_metrics.metrics_store.track_cost.reset_mock()
        
        training_metrics.track_cost(token_usage=1000)
        
        # Verify cost was estimated
        assert training_metrics.training_costs["total_cost"] > 1.5  # Should have increased

    def test_check_convergence(self, training_metrics):
        """Test convergence checking."""
        # Test with insufficient data
        assert training_metrics.check_convergence() is False
        
        # Setup history with converging metrics
        training_metrics.iteration_history = [
            {"iteration": 3, "metrics": {"mse": 0.050}},
            {"iteration": 2, "metrics": {"mse": 0.052}},
            {"iteration": 1, "metrics": {"mse": 0.055}}
        ]
        
        # Should converge with default tolerance
        assert training_metrics.check_convergence() is True
        
        # Should not converge with stricter tolerance
        assert training_metrics.check_convergence(tolerance=0.001) is False
        
        # Test with non-converging metrics
        training_metrics.iteration_history = [
            {"iteration": 3, "metrics": {"mse": 0.050}},
            {"iteration": 2, "metrics": {"mse": 0.070}},
            {"iteration": 1, "metrics": {"mse": 0.055}}
        ]
        
        assert training_metrics.check_convergence() is False

    def test_compare_models(self, training_metrics):
        """Test comparing multiple models."""
        # Setup mock query results
        training_metrics.metrics_store.query_metrics.side_effect = [
            [{"metrics": {"mse": 0.05}}],  # model1
            [{"metrics": {"mse": 0.02}}],  # model2
            []  # model3 (no metrics)
        ]
        
        # Compare models
        result = training_metrics.compare_models(
            model_names=["model1", "model2", "model3"],
            metric_name="mse"
        )
        
        # Verify query calls
        assert training_metrics.metrics_store.query_metrics.call_count == 3
        
        # Verify result structure
        assert result["metric"] == "mse"
        assert "model1" in result["values"]
        assert "model2" in result["values"]
        assert "model3" in result["values"]
        assert result["values"]["model1"] == 0.05
        assert result["values"]["model2"] == 0.02
        assert result["values"]["model3"] is None
        
        # Verify best model (for MSE, lower is better)
        assert result["best_model"] == "model2"
        
        # Test with accuracy metric (higher is better)
        training_metrics.metrics_store.query_metrics.reset_mock()
        training_metrics.metrics_store.query_metrics.side_effect = [
            [{"metrics": {"accuracy": 0.9}}],  # model1
            [{"metrics": {"accuracy": 0.85}}]  # model2
        ]
        
        result = training_metrics.compare_models(
            model_names=["model1", "model2"],
            metric_name="accuracy"
        )
        
        # Verify best model (for accuracy, higher is better)
        assert result["best_model"] == "model1"

    def test_evaluate_rule_performance(self, training_metrics, sample_metrics):
        """Test evaluating rule performance."""
        # Setup rule performance data
        training_metrics.rule_performance["symbolic"] = {
            1: {"mse": 0.1, "accuracy": 0.8},
            2: {"mse": 0.08, "accuracy": 0.85},
            3: {"mse": 0.05, "accuracy": 0.9}
        }
        
        # Evaluate symbolic rules
        result = training_metrics.evaluate_rule_performance("symbolic")
        
        # Verify result structure
        assert result["rule_type"] == "symbolic"
        assert result["latest_iteration"] == 3
        assert result["latest_metrics"] == {"mse": 0.05, "accuracy": 0.9}
        assert len(result["historical"]) == 3
        
        # Verify improvement calculation
        assert "mse" in result["improvement"]
        assert "accuracy" in result["improvement"]
        assert result["improvement"]["mse"] < 0  # MSE decreased (improved)
        assert result["improvement"]["accuracy"] > 0  # Accuracy increased (improved)
        
        # Test with non-existent rule type
        result = training_metrics.evaluate_rule_performance("nonexistent")
        assert "error" in result

    def test_get_cost_summary(self, training_metrics):
        """Test getting cost summary."""
        # Setup training costs
        training_metrics.training_costs = {
            "api_calls": 100,
            "token_usage": 10000,
            "total_cost": 5.0
        }
        
        # Setup cost thresholds in metrics store
        training_metrics.metrics_store.cost_thresholds = {
            "warning_threshold": 10.0,
            "critical_threshold": 50.0,
            "shutdown_threshold": 100.0
        }
        
        # Get cost summary
        summary = training_metrics.get_cost_summary()
        
        # Verify summary structure
        assert summary["api_calls"] == 100
        assert summary["token_usage"] == 10000
        assert summary["estimated_cost_usd"] == 5.0
        assert "warning" in summary["cost_thresholds"]
        assert "critical" in summary["cost_thresholds"]
        assert "shutdown" in summary["cost_thresholds"]

    def test_get_performance_summary(self, training_metrics):
        """Test getting performance summary."""
        # Setup iteration history
        training_metrics.iteration_history = [
            {
                "iteration": 1,
                "metrics": {"mse": 0.1, "accuracy": 0.8}
            },
            {
                "iteration": 2,
                "metrics": {"mse": 0.05, "accuracy": 0.9}
            }
        ]
        
        # Setup rule performance
        training_metrics.rule_performance["symbolic"] = {
            1: {"mse": 0.1},
            2: {"mse": 0.05}
        }
        
        # Mock evaluate_rule_performance
        training_metrics.evaluate_rule_performance = MagicMock(return_value={"summary": "data"})
        
        # Mock check_convergence
        training_metrics.check_convergence = MagicMock(return_value=True)
        
        # Mock get_cost_summary
        training_metrics.get_cost_summary = MagicMock(return_value={"cost": "data"})
        
        # Get performance summary
        summary = training_metrics.get_performance_summary()
        
        # Verify summary structure
        assert summary["total_iterations"] == 2
        assert summary["latest_iteration"] == 2
        assert summary["latest_metrics"] == {"mse": 0.05, "accuracy": 0.9}
        assert "improvement" in summary
        assert summary["improvement"]["mse"] == -50.0  # 50% reduction in MSE
        assert summary["improvement"]["accuracy"] == 12.5  # 12.5% increase in accuracy
        assert summary["convergence"] is True
        assert "symbolic" in summary["rule_performance"]
        assert summary["rule_performance"]["symbolic"] == {"summary": "data"}
        assert summary["cost"] == {"cost": "data"}


if __name__ == "__main__":
    pytest.main()