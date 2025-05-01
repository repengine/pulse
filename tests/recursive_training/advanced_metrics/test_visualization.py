"""
Tests for Advanced Metrics Visualization Tools

Covers:
- plot_metrics_dashboard
- plot_reliability_diagram
- Visualization formatting and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from recursive_training.advanced_metrics.visualization import (
    plot_metrics_dashboard,
    plot_reliability_diagram
)

@pytest.fixture
def metrics_history():
    return [
        {"iteration": 1, "mse": 0.1, "accuracy": 0.8},
        {"iteration": 2, "mse": 0.05, "accuracy": 0.9}
    ]

@pytest.fixture
def calibration_metrics():
    return {
        "brier_score": 0.12,
        "ece": 0.08,
        "bins": [0.1, 0.2, 0.3],
        "probs": [0.15, 0.25, 0.35]
    }

def test_plot_metrics_dashboard(metrics_history):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        plot_metrics_dashboard(metrics_history, show=True)
        assert mock_plt.show.called

def test_plot_metrics_dashboard_no_show(metrics_history):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        plot_metrics_dashboard(metrics_history, show=False)
        assert not mock_plt.show.called

def test_plot_reliability_diagram(calibration_metrics):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        plot_reliability_diagram(calibration_metrics, show=True)
        assert mock_plt.show.called

def test_plot_reliability_diagram_no_show(calibration_metrics):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        plot_reliability_diagram(calibration_metrics, show=False)
        assert not mock_plt.show.called

def test_plot_metrics_dashboard_handles_empty(metrics_history):
    with patch("recursive_training.advanced_metrics.visualization.plt"):
        # Should not raise error on empty input
        plot_metrics_dashboard([], show=False)

def test_plot_reliability_diagram_handles_empty():
    with patch("recursive_training.advanced_metrics.visualization.plt"):
        # Should not raise error on empty input
        plot_reliability_diagram({}, show=False)