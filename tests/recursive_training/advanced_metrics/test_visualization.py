"""
Tests for Advanced Metrics Visualization Tools

Covers:
- plot_metrics_dashboard
- plot_reliability_diagram
- Visualization formatting and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from recursive_training.advanced_metrics.visualization import (
    plot_metrics_dashboard,
    plot_reliability_diagram,
)


@pytest.fixture
def metrics_history():
    return [
        {
            "iteration": 1,
            "metrics": {"mse": 0.1, "accuracy": 0.8},
            "advanced_metrics": {
                "uncertainty": {"mean": 0.5},
                "drift": {"detected": False},
                "convergence": {"converged": True},
            },
        },
        {
            "iteration": 2,
            "metrics": {"mse": 0.05, "accuracy": 0.9},
            "advanced_metrics": {
                "uncertainty": {"mean": 0.4},
                "drift": {"detected": True},
                "convergence": {"converged": False},
            },
        },
    ]


@pytest.fixture
def calibration_metrics():
    return {
        "brier_score": 0.12,
        "ece": 0.08,
        "reliability_diagram": {
            "y_true": [0.0, 0.2, 0.5, 0.7, 1.0],
            "y_pred": [0.1, 0.3, 0.4, 0.8, 0.9],
        },
        "bins": [
            0.1,
            0.2,
            0.3,
        ],  # Kept for other potential tests, not used by plot_reliability_diagram
        "probs": [0.15, 0.25, 0.35],  # Kept for other potential tests
    }


def test_plot_metrics_dashboard(metrics_history):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        # Configure mock_plt.subplots to return a tuple of (fig, axs)
        mock_fig = MagicMock()
        # Create a 2x2 array-like structure for axs
        # Each element needs to be a mock that can handle attribute access and method calls
        # (e.g., .plot(), .set_title(), .set_xlabel(), .set_ylabel(), .grid(), .legend(), .set_yticks(), .set_yticklabels())
        mock_ax_00 = MagicMock(name="axs[0,0]")
        # Configure all methods called on axs[0,0]
        mock_ax_00.plot = MagicMock()
        mock_ax_00.set_title = MagicMock()
        mock_ax_00.set_xlabel = MagicMock()
        mock_ax_00.set_ylabel = MagicMock()
        mock_ax_00.grid = MagicMock()

        mock_ax_01 = MagicMock(name="axs[0,1]")
        # Configure all methods called on axs[0,1]
        mock_ax_01.plot = MagicMock()
        mock_ax_01.set_title = MagicMock()
        mock_ax_01.set_xlabel = MagicMock()
        mock_ax_01.set_ylabel = MagicMock()
        mock_ax_01.grid = MagicMock()

        mock_ax_10 = MagicMock(name="axs[1,0]")
        # Configure all methods called on axs[1,0]
        mock_ax_10.plot = MagicMock()
        mock_ax_10.set_title = MagicMock()
        mock_ax_10.set_xlabel = MagicMock()
        mock_ax_10.set_ylabel = MagicMock()
        mock_ax_10.grid = MagicMock()

        mock_ax_11 = MagicMock(name="axs[1,1]")
        # Configure all methods called on axs[1,1]
        mock_ax_11.plot = MagicMock()
        mock_ax_11.set_title = MagicMock()
        mock_ax_11.set_xlabel = MagicMock()
        mock_ax_11.set_ylabel = MagicMock()
        mock_ax_11.grid = MagicMock()
        mock_ax_11.legend = MagicMock()
        mock_ax_11.set_yticks = MagicMock()
        mock_ax_11.set_yticklabels = MagicMock()

        mock_axs_array = np.empty((2, 2), dtype=object)
        mock_axs_array[0, 0] = mock_ax_00
        mock_axs_array[0, 1] = mock_ax_01
        mock_axs_array[1, 0] = mock_ax_10
        mock_axs_array[1, 1] = mock_ax_11
        mock_plt.subplots.return_value = (mock_fig, mock_axs_array)

        plot_metrics_dashboard(metrics_history, show=True)
        assert mock_plt.show.called
        mock_plt.subplots.assert_called_once_with(2, 2, figsize=(12, 8))


def test_plot_metrics_dashboard_no_show(metrics_history):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        # Configure mock_plt.subplots to return a tuple of (fig, axs)
        mock_fig = MagicMock()
        # Create a 2x2 array-like structure for axs
        mock_ax_00 = MagicMock(name="axs[0,0]")
        # Configure all methods called on axs[0,0]
        mock_ax_00.plot = MagicMock()
        mock_ax_00.set_title = MagicMock()
        mock_ax_00.set_xlabel = MagicMock()
        mock_ax_00.set_ylabel = MagicMock()
        mock_ax_00.grid = MagicMock()

        mock_ax_01 = MagicMock(name="axs[0,1]")
        # Configure all methods called on axs[0,1]
        mock_ax_01.plot = MagicMock()
        mock_ax_01.set_title = MagicMock()
        mock_ax_01.set_xlabel = MagicMock()
        mock_ax_01.set_ylabel = MagicMock()
        mock_ax_01.grid = MagicMock()

        mock_ax_10 = MagicMock(name="axs[1,0]")
        # Configure all methods called on axs[1,0]
        mock_ax_10.plot = MagicMock()
        mock_ax_10.set_title = MagicMock()
        mock_ax_10.set_xlabel = MagicMock()
        mock_ax_10.set_ylabel = MagicMock()
        mock_ax_10.grid = MagicMock()

        mock_ax_11 = MagicMock(name="axs[1,1]")
        # Configure all methods called on axs[1,1]
        mock_ax_11.plot = MagicMock()
        mock_ax_11.set_title = MagicMock()
        mock_ax_11.set_xlabel = MagicMock()
        mock_ax_11.set_ylabel = MagicMock()
        mock_ax_11.grid = MagicMock()
        mock_ax_11.legend = MagicMock()
        mock_ax_11.set_yticks = MagicMock()
        mock_ax_11.set_yticklabels = MagicMock()

        mock_axs_array = np.empty((2, 2), dtype=object)
        mock_axs_array[0, 0] = mock_ax_00
        mock_axs_array[0, 1] = mock_ax_01
        mock_axs_array[1, 0] = mock_ax_10
        mock_axs_array[1, 1] = mock_ax_11
        mock_plt.subplots.return_value = (mock_fig, mock_axs_array)

        plot_metrics_dashboard(metrics_history, show=False)
        assert not mock_plt.show.called
        mock_plt.subplots.assert_called_once_with(2, 2, figsize=(12, 8))


def test_plot_reliability_diagram(calibration_metrics):
    with (
        patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt,
        patch(
            "recursive_training.advanced_metrics.visualization.MATPLOTLIB_AVAILABLE",
            True,
        ),
    ):
        mock_fig = MagicMock()
        # plot_reliability_diagram uses plt.figure(), not subplots, so no need to mock subplots here.
        # However, it does call plt.show()
        mock_plt.figure.return_value = mock_fig

        plot_reliability_diagram(calibration_metrics, show=True)
        assert mock_plt.show.called
        mock_plt.figure.assert_called_once_with(figsize=(6, 6))


def test_plot_reliability_diagram_no_show(calibration_metrics):
    with patch("recursive_training.advanced_metrics.visualization.plt") as mock_plt:
        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig

        plot_reliability_diagram(calibration_metrics, show=False)
        assert not mock_plt.show.called
        mock_plt.figure.assert_called_once_with(figsize=(6, 6))


def test_plot_metrics_dashboard_handles_empty(metrics_history):
    with patch("recursive_training.advanced_metrics.visualization.plt"):
        # Should not raise error on empty input
        plot_metrics_dashboard([], show=False)


def test_plot_reliability_diagram_handles_empty():
    with patch("recursive_training.advanced_metrics.visualization.plt"):
        # Should not raise error on empty input
        plot_reliability_diagram({}, show=False)
