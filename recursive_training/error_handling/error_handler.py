"""
RecursiveTrainingErrorHandler

Comprehensive error handler for the Recursive AI Training system.
Handles exceptions, logs errors, triggers alerts, and coordinates recovery.
"""

import logging
from typing import Any, Dict, Optional


class RecursiveTrainingErrorHandler:
    """
    Centralized error handler for recursive training.
    Provides structured error logging, alerting, and escalation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("RecursiveTrainingErrorHandler")
        self.alert_threshold = self.config.get("alert_threshold", "critical")
        self.recovery_enabled = self.config.get("recovery_enabled", True)
        self.error_count = 0
        self.last_error = None

    def handle_exception(
        self, exc: Exception, context: Optional[Dict[str, Any]] = None
    ):
        """
        Handles an exception, logs it, and triggers alerts or recovery if needed.

        Args:
            exc: The exception instance.
            context: Optional context dictionary with additional info.
        """
        self.error_count += 1
        self.last_error = exc
        error_msg = f"Exception occurred: {exc}"
        if context:
            error_msg += f" | Context: {context}"
        self.logger.error(error_msg)

        # Trigger alert if severity is high
        if self.should_alert(exc):
            self.trigger_alert(exc, context)

        # Attempt recovery if enabled
        if self.recovery_enabled:
            recovery_success = self.attempt_recovery(exc, context)
            self.logger.info(
                f"Recovery attempt {'succeeded' if recovery_success else 'failed'}"
            )

    def should_alert(self, exc: Exception) -> bool:
        """
        Determines if an alert should be triggered for the given exception.

        Args:
            exc: The exception instance.

        Returns:
            True if alert should be triggered, False otherwise.
        """
        # Example: escalate on critical errors
        return self.alert_threshold == "critical" or isinstance(exc, RuntimeError)

    def trigger_alert(self, exc: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Triggers an alert (e.g., log, email, or external system).

        Args:
            exc: The exception instance.
            context: Optional context dictionary.
        """
        alert_msg = f"ALERT: {exc}"
        if context:
            alert_msg += f" | Context: {context}"
        self.logger.warning(alert_msg)
        # Extend: send email, push notification, or integrate with monitoring system

    def attempt_recovery(
        self, exc: Exception, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Attempts to recover from the error if possible.

        Args:
            exc: The exception instance.
            context: Optional context dictionary.

        Returns:
            True if recovery was successful, False otherwise.
        """
        self.logger.info(f"Attempting recovery for error: {exc}")
        # Extend: call recovery strategies, rollback, or restart components

        # For now, implement a simple recovery strategy:
        # Assume recovery is possible for ValueError but not for other exceptions
        return not isinstance(exc, (RuntimeError, SystemError))

    def get_error_status(self) -> Dict[str, Any]:
        """
        Returns the current error status.

        Returns:
            Dictionary with error count and last error.
        """
        return {
            "error_count": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None,
        }
