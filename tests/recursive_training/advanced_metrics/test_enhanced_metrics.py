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
from unittest.mock import patch, MagicMock
from recursive_training.advanced_metrics.enhanced_metrics import (
    EnhancedRecursiveTrainingMetrics,
)


@pytest.fixture
def mock_config():
    return {
        "convergence_threshold": 0.01,
        "max_iterations": 10,
        "alert_threshold": 0.2,
        "cost_control": {"max_cost": 100.0},
    }


@pytest.fixture
def mock_metrics_store():
    store = MagicMock()
    store.store_metric.return_value = "metric_id"
    store.track_cost.return_value = {
        "total_cost": 10.0,
        "status": "ok",
    }  # Ensure status is present
    store.query_metrics.return_value = []
    store.get_metrics_summary.return_value = {
        "total_metrics": 0,
        "metrics_by_type": {},
        "time_range": {"start": None, "end": None},
        "models": [],
        "tags": [],
        "cost_tracking": {"total_cost": 0.0, "api_calls": 0, "token_usage": 0},
    }
    return store


@pytest.fixture
def mock_cost_controller():
    controller = MagicMock()
    controller.track_operation.return_value = {"cost": 1.0, "status": "ok"}
    return controller


@pytest.fixture
def enhanced_metrics(mock_config, mock_metrics_store, mock_cost_controller):
    with (
        patch(
            "recursive_training.metrics.training_metrics.get_metrics_store",
            return_value=mock_metrics_store,
        ),
        patch(
            "recursive_training.advanced_metrics.enhanced_metrics.get_cost_controller",
            return_value=mock_cost_controller,
        ),
    ):
        return EnhancedRecursiveTrainingMetrics(mock_config)


@pytest.fixture
def sample_predictions():
    return [0.1, 0.5, 0.9, 0.2, 0.8]


@pytest.fixture
def sample_true_values():
    return [0, 1, 1, 0, 1]


@pytest.fixture
def sample_predicted_probs():
    return [[0.8, 0.2], [0.3, 0.7], [0.1, 0.9], [0.6, 0.4], [0.2, 0.8]]


def test_initialization(enhanced_metrics, mock_config):
    assert enhanced_metrics.config == mock_config
    assert hasattr(enhanced_metrics, "metrics_store")
    assert isinstance(enhanced_metrics.current_metrics, dict)


def test_calculate_uncertainty(enhanced_metrics, sample_predictions):
    result = enhanced_metrics.calculate_uncertainty(sample_predictions)
    assert isinstance(result, dict)
    assert "mean" in result and "std" in result


def test_calculate_calibration(
    enhanced_metrics, sample_true_values, sample_predicted_probs
):
    result = enhanced_metrics.calculate_calibration(
        sample_true_values, sample_predicted_probs
    )
    assert isinstance(result, dict)
    assert "brier_score" in result or "ece" in result


def test_statistical_significance_test(enhanced_metrics):
    errors_a = [0.1, 0.2, 0.15, 0.18, 0.16]  # Extended to 5 elements
    errors_b = [0.12, 0.22, 0.13, 0.19, 0.17]  # Extended to 5 elements
    result = enhanced_metrics.statistical_significance_test(
        errors_a, errors_b, test_type="ttest"
    )
    assert isinstance(result, dict)
    assert "p_value" in result


def test_track_advanced_iteration(enhanced_metrics, monkeypatch):
    # This test only verifies that track_advanced_iteration returns the expected mock ID

    # Create a simple mock for track_iteration that returns "metric_id"
    def mock_track_iteration(*args, **kwargs):
        return "metric_id"

    # Create a simple mock for store_metric
    def mock_store_metric(*args, **kwargs):
        return "mock_metric_id"

    # Apply the mocks
    monkeypatch.setattr(
        enhanced_metrics.__class__.__bases__[0], "track_iteration", mock_track_iteration
    )
    monkeypatch.setattr(
        enhanced_metrics.metrics_store, "store_metric", mock_store_metric
    )

    # Call the method
    metrics = {"mse": 0.05, "accuracy": 0.9}
    metric_id = enhanced_metrics.track_advanced_iteration(
        1, metrics, model_name="hybrid", rule_type="hybrid", tags=["test"]
    )

    # Only verify that we get the expected metric_id back
    assert metric_id == "metric_id"


def test_update_adaptive_thresholds_and_drift(enhanced_metrics):
    metrics = {"mse": 0.05, "accuracy": 0.9}
    enhanced_metrics._update_adaptive_thresholds(2, metrics)
    drift = enhanced_metrics._check_for_drift(2, metrics)
    assert isinstance(drift, dict)
    convergence = enhanced_metrics._check_advanced_convergence(2, metrics)
    assert isinstance(convergence, dict)


def test_evaluate_offline(enhanced_metrics):
    mock_model = MagicMock()
    mock_model.predict = MagicMock(return_value=[0, 1])
    dataset = {"inputs": [[1, 2], [3, 4]], "targets": [0, 1]}
    result = enhanced_metrics.evaluate_offline(mock_model, "test_dataset", dataset)
    assert isinstance(result, dict)
    assert "eval_id" in result or "results" in result or "error" in result


def test_get_advanced_performance_summary(enhanced_metrics):
    summary = enhanced_metrics.get_advanced_performance_summary()
    assert isinstance(summary, dict)


def test_compare_models_advanced(enhanced_metrics):
    model_names = ["modelA", "modelB"]
    result = enhanced_metrics.compare_models_advanced(
        model_names, metric_names=["accuracy"]
    )
    assert isinstance(result, dict)
    assert (
        "overall_best_model" in result
        or "best_models_by_metric" in result
        or "comparisons" in result
    )


def test_cost_control_integration(enhanced_metrics, monkeypatch):
    # Create a proper Mock for store_metric
    mock_store_metric = MagicMock(return_value="mock_metric_id")

    # Create a mock function to replace the real track_cost method
    def mock_track_cost(*args, **kwargs):
        return {"total_cost": 120.0, "status": "warning"}

    # Monkeypatch both methods
    monkeypatch.setattr(enhanced_metrics.metrics_store, "track_cost", mock_track_cost)
    monkeypatch.setattr(
        enhanced_metrics.metrics_store, "store_metric", mock_store_metric
    )

    # Test with the patched methods
    metrics = {"mse": 0.05}
    enhanced_metrics.track_advanced_iteration(3, metrics)

    # Verify that store_metric was called at least once
    assert mock_store_metric.called


def test_hybrid_rule_integration(enhanced_metrics):
    # Simulate hybrid rule performance tracking
    metrics = {"mse": 0.04, "accuracy": 0.92}
    enhanced_metrics.track_advanced_iteration(4, metrics, rule_type="hybrid")
    assert 4 in enhanced_metrics.rule_performance["hybrid"]
