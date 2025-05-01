"""
Tests for EnhancedRecursiveTrainingMetrics

Covers:
- Uncertainty quantification
- Calibration and statistical significance
- Advanced iteration tracking
- Drift/convergence detection
- Offline evaluation and model comparison
- Cost control and hybrid rule integration
"""

import pytest
import math
from unittest.mock import patch, MagicMock
from recursive_training.advanced_metrics.enhanced_metrics import EnhancedRecursiveTrainingMetrics

@pytest.fixture
def mock_config():
    return {
        "convergence_threshold": 0.01,
        "max_iterations": 10,
        "alert_threshold": 0.2,
        "cost_control": {"max_cost": 100.0}
    }

@pytest.fixture
def mock_metrics_store():
    store = MagicMock()
    store.store_metric.return_value = "metric_id"
    store.track_cost.return_value = {"total_cost": 10.0}
    store.query_metrics.return_value = []
    return store

@pytest.fixture
def enhanced_metrics(mock_config, mock_metrics_store):
    with patch("recursive_training.advanced_metrics.enhanced_metrics.get_metrics_store", return_value=mock_metrics_store):
        return EnhancedRecursiveTrainingMetrics(mock_config)

@pytest.fixture
def sample_predictions():
    return [0.1, 0.5, 0.9, 0.2, 0.8]

@pytest.fixture
def sample_true_values():
    return [0, 1, 1, 0, 1]

@pytest.fixture
def sample_predicted_probs():
    return [
        [0.8, 0.2],
        [0.3, 0.7],
        [0.1, 0.9],
        [0.6, 0.4],
        [0.2, 0.8]
    ]

def test_initialization(enhanced_metrics, mock_config):
    assert enhanced_metrics.config == mock_config
    assert hasattr(enhanced_metrics, "metrics_store")
    assert isinstance(enhanced_metrics.current_metrics, dict)

def test_calculate_uncertainty(enhanced_metrics, sample_predictions):
    result = enhanced_metrics.calculate_uncertainty(sample_predictions)
    assert isinstance(result, dict)
    assert "mean" in result and "std" in result

def test_calculate_calibration(enhanced_metrics, sample_true_values, sample_predicted_probs):
    result = enhanced_metrics.calculate_calibration(sample_true_values, sample_predicted_probs)
    assert isinstance(result, dict)
    assert "brier_score" in result or "ece" in result

def test_statistical_significance_test(enhanced_metrics):
    errors_a = [0.1, 0.2, 0.15, 0.18]
    errors_b = [0.12, 0.22, 0.13, 0.19]
    result = enhanced_metrics.statistical_significance_test(errors_a, errors_b, test_type="t-test")
    assert isinstance(result, dict)
    assert "p_value" in result

def test_track_advanced_iteration(enhanced_metrics):
    metrics = {"mse": 0.05, "accuracy": 0.9}
    metric_id = enhanced_metrics.track_advanced_iteration(1, metrics, model_name="hybrid", rule_type="hybrid", tags=["test"])
    assert metric_id == "metric_id"
    enhanced_metrics.metrics_store.store_metric.assert_called_once()
    stored = enhanced_metrics.metrics_store.store_metric.call_args[0][0]
    assert stored["iteration"] == 1
    assert stored["metrics"] == metrics
    assert "rule_type:hybrid" in stored["tags"]

def test_update_adaptive_thresholds_and_drift(enhanced_metrics):
    metrics = {"mse": 0.05, "accuracy": 0.9}
    enhanced_metrics._update_adaptive_thresholds(2, metrics)
    drift = enhanced_metrics._check_for_drift(2, metrics)
    assert isinstance(drift, dict)
    convergence = enhanced_metrics._check_advanced_convergence(2, metrics)
    assert isinstance(convergence, dict)

def test_evaluate_offline(enhanced_metrics):
    mock_model = MagicMock()
    dataset = {"X": [[1,2],[3,4]], "y": [0,1]}
    result = enhanced_metrics.evaluate_offline(mock_model, "test_dataset", dataset)
    assert isinstance(result, dict)
    assert "evaluation" in result or "metrics" in result

def test_get_advanced_performance_summary(enhanced_metrics):
    summary = enhanced_metrics.get_advanced_performance_summary()
    assert isinstance(summary, dict)

def test_compare_models_advanced(enhanced_metrics):
    model_names = ["modelA", "modelB"]
    result = enhanced_metrics.compare_models_advanced(model_names, metric_name="accuracy")
    assert isinstance(result, dict)
    assert "best_model" in result

def test_cost_control_integration(enhanced_metrics):
    # Simulate cost tracking and check enforcement
    enhanced_metrics.metrics_store.track_cost.return_value = {"total_cost": 120.0}
    metrics = {"mse": 0.05}
    enhanced_metrics.track_advanced_iteration(3, metrics)
    # Should still call store_metric, but cost control logic may trigger
    enhanced_metrics.metrics_store.store_metric.assert_called()

def test_hybrid_rule_integration(enhanced_metrics):
    # Simulate hybrid rule performance tracking
    metrics = {"mse": 0.04, "accuracy": 0.92}
    enhanced_metrics.track_advanced_iteration(4, metrics, rule_type="hybrid")
    assert 4 in enhanced_metrics.rule_performance["hybrid"]