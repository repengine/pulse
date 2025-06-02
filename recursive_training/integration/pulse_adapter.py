"""
PulseAdapter

Adapter for integrating the Recursive Training System with Pulse's core components.
Provides bidirectional communication between the systems, handles data format
conversions, and ensures proper interaction with Pulse's architecture.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Try to import Pulse components with graceful fallbacks
from engine.pulse_config import PulseConfig


from engine.event_bus import event_bus, EventBus  # Import the instance and class

# SymbolicExecutor class is not defined in symbolic_system.symbolic_executor,
# that module provides functions. So, we remove this import.
# from symbolic_system.symbolic_executor import SymbolicExecutor


# Import from recursive training
from recursive_training.metrics.metrics_store import get_metrics_store
from recursive_training.metrics.training_metrics import RecursiveTrainingMetrics


class PulseAdapter:
    """
    Adapter for Pulse components integration.

    This class provides methods for:
    - Connecting to Pulse's event system
    - Converting between data formats
    - Routing metrics to Pulse's monitoring systems
    - Integrating with Pulse's symbolic rule executor
    - Handling Pulse's configuration system
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> "PulseAdapter":
        """
        Get or create the singleton instance of PulseAdapter.

        Args:
            config: Optional configuration dictionary

        Returns:
            PulseAdapter instance
        """
        if cls._instance is None:
            cls._instance = PulseAdapter(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PulseAdapter.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("PulseAdapter")
        self.config = config or {}

        # Initialize Pulse components
        self.pulse_config: Optional[PulseConfig] = None
        self.event_system: Optional[EventBus] = None
        self.symbolic_executor: Optional[Any] = (
            None  # Placeholder for actual symbolic executor type
        )

        self._init_pulse_config()
        self._init_event_system()
        self._init_symbolic_system()

        # Initialize metrics system
        self.metrics_store = get_metrics_store()
        self.training_metrics = RecursiveTrainingMetrics()

        # Track connection status
        self.pulse_connected = False
        self.event_handlers_registered = False

        # Initialize metadata
        self.version = "1.0.0"
        self.integration_timestamp = datetime.now(timezone.utc).isoformat()
        self.event_counts = {"sent": 0, "received": 0, "errors": 0}

        self.logger.info(f"PulseAdapter initialized (version {self.version})")

    def _init_pulse_config(self) -> None:
        """Initialize connection to Pulse's configuration system."""
        try:
            self.pulse_config = PulseConfig()
            integration_config = self.pulse_config.recursive_training

            # Merge with local config (local takes precedence)
            if isinstance(integration_config, dict):
                for key, value in integration_config.items():
                    if key not in self.config:
                        self.config[key] = value
            elif integration_config is not None:  # Handle if not a dict but not None
                self.logger.warning(
                    f"recursive_training config is not a dict: {integration_config}"
                )

            self.logger.info(
                "Initialized PulseConfig and merged recursive_training settings"
            )
            self.pulse_connected = True
        except Exception as e:
            self.logger.error(
                f"Error initializing PulseConfig or merging settings: {e}"
            )
            self.pulse_config = None
            self.pulse_connected = False

    def _init_event_system(self) -> None:
        """Initialize connection to Pulse's event system."""
        try:
            # Attempt to assign the imported event_bus instance
            self.event_system = event_bus
            if self.event_system:
                self.logger.info(
                    "Successfully assigned event_bus to self.event_system."
                )
                # Now that event_system is confirmed to be assigned, register handlers
                self._register_event_handlers()
            else:
                # This case implies 'event_bus' itself was None or evaluated to False
                self.logger.error(
                    "Failed to initialize event system: imported 'event_bus' is None or evaluates to False."
                )
                self.event_system = None  # Ensure it's None
        except ImportError:
            self.logger.error(
                "ImportError: Failed to import 'event_bus' from 'engine.event_bus'. Event system not available."
            )
            self.event_system = None
        except Exception as e:
            # Catch any other unexpected errors during assignment or the call to
            # _register_event_handlers
            self.logger.error(
                f"An unexpected error occurred during event system initialization: {e}"
            )
            self.event_system = None

    def _init_symbolic_system(self) -> None:
        """Initialize connection to Pulse's symbolic system."""
        try:
            # SymbolicExecutor class is not available as previously designed.
            # The module symbolic_system.symbolic_executor provides functions.
            # Setting to None as there's no direct class instance to create.
            self.symbolic_executor = None
            self.logger.info(
                "SymbolicExecutor class not found; symbolic execution via adapter method will be limited."
            )
        except Exception as e:  # Should not happen if we are just setting to None
            self.logger.error(f"Error during _init_symbolic_system: {e}")
            self.symbolic_executor = None

    def _register_event_handlers(self) -> None:
        """Register handlers for Pulse events."""
        if self.event_handlers_registered:
            self.logger.debug("Event handlers already registered.")
            return

        if not self.event_system:
            self.logger.warning(
                "Cannot register event handlers: self.event_system is not initialized (None)."
            )
            return

        try:
            # Register for training-related events
            self.logger.debug("Attempting to subscribe to Pulse events.")
            self.event_system.subscribe(
                "pulse.model.trained", self._handle_model_trained_event
            )
            self.event_system.subscribe(
                "pulse.rule.updated", self._handle_rule_updated_event
            )
            self.event_system.subscribe(
                "pulse.metrics.request", self._handle_metrics_request_event
            )

            self.event_handlers_registered = True
            self.logger.info(
                "Successfully registered event handlers with Pulse event system."
            )
        except AttributeError as ae:
            self.logger.error(
                f"AttributeError while registering event handlers: Does 'event_system' have 'subscribe'? Error: {ae}")
            # Potentially self.event_system became None between check and use, or
            # event_bus is malformed.
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred while registering event handlers: {e}"
            )
            # Do not set self.event_handlers_registered = False here, as it might lead to re-registration attempts.
            # The fact it's not True indicates failure.

    def _handle_model_trained_event(self, data: Dict[str, Any]) -> None:
        """
        Handle Pulse model trained event.

        Args:
            data: Event data from Pulse
        """
        try:
            self.event_counts["received"] += 1

            # Extract metrics from Pulse model training
            model_name = data.get("model_name", "unknown")
            metrics = data.get("metrics", {})
            iteration = data.get("iteration", 0)

            # Track in our metrics system
            self.training_metrics.track_iteration(
                iteration=iteration,
                metrics=metrics,
                model_name=model_name,
                tags=["pulse_model", f"model:{model_name}"],
            )

            self.logger.info(f"Processed model training event for {model_name}")
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error handling model trained event: {e}")

    def _handle_rule_updated_event(self, data: Dict[str, Any]) -> None:
        """
        Handle Pulse rule updated event.

        Args:
            data: Event data from Pulse
        """
        try:
            self.event_counts["received"] += 1

            # Extract rule details
            rule_id = data.get("rule_id", "unknown")
            _rule_type = data.get("rule_type", "unknown")
            _rule_data = data.get("rule_data", {})

            # Process the rule update in our system
            # This is a simplified implementation
            result = {
                "rule_id": rule_id,
                "processed": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Send result back to Pulse
            self._emit_event("recursive_training.rule.processed", result)

            self.logger.info(f"Processed rule update event for {rule_id}")
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error handling rule updated event: {e}")

    def _handle_metrics_request_event(self, data: Dict[str, Any]) -> None:
        """
        Handle Pulse metrics request event.

        Args:
            data: Event data from Pulse
        """
        try:
            self.event_counts["received"] += 1

            # Extract request details
            request_id = data.get("request_id", "unknown")
            metric_types = data.get("metric_types", [])

            # Get metrics from our system
            metrics = {}

            if "performance" in metric_types or not metric_types:
                metrics["performance"] = self.training_metrics.get_performance_summary()

            if "cost" in metric_types or not metric_types:
                metrics["cost"] = self.training_metrics.get_cost_summary()

            # Send metrics back to Pulse
            response = {
                "request_id": request_id,
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self._emit_event("recursive_training.metrics.response", response)

            self.logger.info(f"Processed metrics request {request_id}")
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error handling metrics request event: {e}")

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Emit an event to Pulse's event system.

        Args:
            event_type: Type of event to emit
            data: Event data
        """
        try:
            if self.event_system:
                self.event_system.publish(event_type, data)  # Changed emit to publish
            else:
                self.logger.error(
                    f"Event system not available, cannot publish event {event_type}"
                )
            self.event_counts["sent"] += 1
            return True
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error emitting event {event_type}: {e}")
            return False

    def execute_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a rule using Pulse's symbolic executor.

        Args:
            rule_data: Rule definition

        Returns:
            Execution result
        """
        try:
            # The SymbolicExecutor class as previously used is not available.
            # The symbolic_system.symbolic_executor module contains functions.
            # This method needs to be re-evaluated or call specific functions from that module if applicable.
            # For now, returning an error as the direct class method call is not
            # possible.
            self.logger.warning(
                "SymbolicExecutor class interface is not available. "
                "Rule execution via PulseAdapter.execute_rule is not supported in its current form.")
            return {
                "status": "error",
                "message": "Symbolic execution via adapter's execute_rule method is not currently available.",
            }

        except Exception as e:
            self.logger.error(f"Error executing rule: {e}")
            return {"status": "error", "message": str(e)}

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status with Pulse.

        Returns:
            Dictionary of connection status information
        """
        return {
            "pulse_connected": self.pulse_connected,
            "event_handlers_registered": self.event_handlers_registered,
            "events_sent": self.event_counts["sent"],
            "events_received": self.event_counts["received"],
            "event_errors": self.event_counts["errors"],
            "version": self.version,
            "integration_timestamp": self.integration_timestamp,
        }

    def convert_pulse_data_format(self, data: Any, target_format: str) -> Any:
        """
        Convert data between Pulse and Recursive Training formats.

        Args:
            data: Data to convert
            target_format: Target format name

        Returns:
            Converted data
        """
        # This is a simplified implementation
        # In a real system, this would handle various format conversions
        if target_format == "pulse_metrics":
            # Convert our metrics format to Pulse format
            return {
                "source": "recursive_training",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": data,
                "version": self.version,
            }
        elif target_format == "recursive_training":
            # Convert Pulse format to our format
            if "data" in data:
                return data["data"]
            return data
        else:
            self.logger.warning(f"Unknown target format: {target_format}")
            return data


def get_pulse_adapter(config: Optional[Dict[str, Any]] = None) -> PulseAdapter:
    """
    Get the singleton instance of PulseAdapter.

    Args:
        config: Optional configuration dictionary

    Returns:
        PulseAdapter instance
    """
    return PulseAdapter.get_instance(config)
