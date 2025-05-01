"""
Visualization tools for advanced metrics in recursive training.

Provides plotting utilities and dashboards for model performance,
uncertainty, drift, and convergence diagnostics.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

def plot_metrics_dashboard(metrics_history: List[Dict[str, Any]], show: bool = True):
    """
    Plots a dashboard of key advanced metrics over training iterations.

    Args:
        metrics_history: List of metrics dictionaries (one per iteration).
        show: Whether to display the plot immediately.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib is not available. Cannot plot metrics dashboard.")
        return

    if not metrics_history:
        print("No metrics history provided.")
        return

    iterations = [m.get("iteration", i) for i, m in enumerate(metrics_history)]
    mse = [m.get("metrics", {}).get("mse") for m in metrics_history]
    accuracy = [m.get("metrics", {}).get("accuracy") for m in metrics_history]
    uncertainty = [m.get("advanced_metrics", {}).get("uncertainty", {}).get("mean") for m in metrics_history]
    drift = [m.get("advanced_metrics", {}).get("drift", {}).get("detected") for m in metrics_history]
    convergence = [m.get("advanced_metrics", {}).get("convergence", {}).get("converged") for m in metrics_history]

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Recursive Training Advanced Metrics Dashboard")

    # MSE
    axs[0, 0].plot(iterations, mse, label="MSE", color="tab:blue")
    axs[0, 0].set_title("Mean Squared Error")
    axs[0, 0].set_xlabel("Iteration")
    axs[0, 0].set_ylabel("MSE")
    axs[0, 0].grid(True)

    # Accuracy
    axs[0, 1].plot(iterations, accuracy, label="Accuracy", color="tab:green")
    axs[0, 1].set_title("Accuracy")
    axs[0, 1].set_xlabel("Iteration")
    axs[0, 1].set_ylabel("Accuracy")
    axs[0, 1].grid(True)

    # Uncertainty
    axs[1, 0].plot(iterations, uncertainty, label="Uncertainty (mean)", color="tab:orange")
    axs[1, 0].set_title("Uncertainty (mean)")
    axs[1, 0].set_xlabel("Iteration")
    axs[1, 0].set_ylabel("Uncertainty")
    axs[1, 0].grid(True)

    # Drift and Convergence
    axs[1, 1].plot(iterations, drift, label="Drift Detected", color="tab:red", linestyle="--")
    axs[1, 1].plot(iterations, convergence, label="Converged", color="tab:purple", linestyle=":")
    axs[1, 1].set_title("Drift & Convergence")
    axs[1, 1].set_xlabel("Iteration")
    axs[1, 1].set_yticks([0, 1])
    axs[1, 1].set_yticklabels(["False", "True"])
    axs[1, 1].legend()
    axs[1, 1].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if show:
        plt.show()

def plot_reliability_diagram(calibration_metrics: Dict[str, Any], show: bool = True):
    """
    Plots a reliability diagram for model calibration.

    Args:
        calibration_metrics: Dictionary with 'reliability_diagram' key.
        show: Whether to display the plot immediately.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib is not available. Cannot plot reliability diagram.")
        return

    diagram = calibration_metrics.get("reliability_diagram")
    if not diagram:
        print("No reliability diagram data found.")
        return

    y_true = diagram.get("y_true")
    y_pred = diagram.get("y_pred")
    if not y_true or not y_pred:
        print("Reliability diagram missing y_true or y_pred.")
        return

    plt.figure(figsize=(6, 6))
    plt.plot(y_pred, y_true, marker="o", label="Model")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly Calibrated")
    plt.xlabel("Predicted Probability")
    plt.ylabel("True Probability")
    plt.title("Reliability Diagram")
    plt.legend()
    plt.grid(True)
    if show:
        plt.show()