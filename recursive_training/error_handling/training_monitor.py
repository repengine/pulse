"""
RecursiveTrainingMonitor

Monitors training for errors, anomalies, and threshold violations.
Provides real-time alerts and integrates with error handling and recovery.
"""

import logging
from typing import Any, Dict, Optional, Callable


class RecursiveTrainingMonitor:
    """
    Monitors recursive training runs for errors, metric anomalies, and alert thresholds.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("RecursiveTrainingMonitor")
        self.alert_thresholds = self.config.get(
            "alert_thresholds", {"mse": 1.0, "uncertainty": 0.5, "drift": True}
        )
        self.alert_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.last_alert = None

    def set_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Sets a callback to be invoked when an alert is triggered.

        Args:
            callback: Function to call with (alert_type, context).
        """
        self.alert_callback = callback

    def monitor_metrics(
        self, metrics: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ):
        """
        Checks metrics for threshold violations and triggers alerts if needed.

        Args:
            metrics: Dictionary of current metrics.
            context: Optional context dictionary.
        """
        alerts = []

        # Check MSE threshold
        mse = metrics.get("mse")
        if mse is not None and mse > self.alert_thresholds.get("mse", float("inf")):
            alerts.append(("mse_threshold", {"mse": mse}))

        # Check uncertainty threshold
        uncertainty = metrics.get("uncertainty", {}).get("mean")
        if uncertainty is not None and uncertainty > self.alert_thresholds.get(
            "uncertainty", float("inf")
        ):
            alerts.append(("uncertainty_threshold", {"uncertainty": uncertainty}))

        # Check drift detection
        drift = metrics.get("drift", {}).get("detected")
        if drift and self.alert_thresholds.get("drift", False):
            alerts.append(("drift_detected", {"drift": drift}))

        for alert_type, alert_context in alerts:
            self.trigger_alert(alert_type, alert_context, context)

    def trigger_alert(
        self,
        alert_type: str,
        alert_context: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Triggers an alert and calls the alert callback if set.

        Args:
            alert_type: Type of alert (e.g., "mse_threshold").
            alert_context: Context for the alert.
            context: Additional context.
        """
        msg = f"ALERT [{alert_type}]: {alert_context}"
        if context:
            msg += f" | Context: {context}"
        self.logger.warning(msg)
        self.last_alert = (alert_type, alert_context, context)
        if self.alert_callback:
            self.alert_callback(alert_type, alert_context)
