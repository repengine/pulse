"""
PulseAdapter

Adapter for integrating the Recursive Training System with Pulse's core components.
Provides bidirectional communication between the systems, handles data format
conversions, and ensures proper interaction with Pulse's architecture.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

# Try to import Pulse components with graceful fallbacks
try:
    from core.pulse_config import PulseConfig
    PULSE_CONFIG_AVAILABLE = True
except ImportError:
    PULSE_CONFIG_AVAILABLE = False
    class PulseConfig:
        """Minimal PulseConfig implementation for fallback."""
        def __init__(self):
            pass
        def get(self, key, default=None):
            return default

try:
    from core.event_system import PulseEventSystem
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    class PulseEventSystem:
        """Minimal PulseEventSystem implementation for fallback."""
        @classmethod
        def emit(cls, event_type, data=None):
            pass
        @classmethod
        def subscribe(cls, event_type, callback):
            pass

try:
    from symbolic_system.symbolic_executor import SymbolicExecutor
    SYMBOLIC_EXECUTOR_AVAILABLE = True
except ImportError:
    SYMBOLIC_EXECUTOR_AVAILABLE = False
    class SymbolicExecutor:
        """Minimal SymbolicExecutor implementation for fallback."""
        def __init__(self):
            pass
        def execute_rule(self, rule):
            return {"status": "error", "message": "SymbolicExecutor not available"}

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
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'PulseAdapter':
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
        self.event_counts = {
            "sent": 0,
            "received": 0,
            "errors": 0
        }
        
        self.logger.info(f"PulseAdapter initialized (version {self.version})")
        
    def _init_pulse_config(self):
        """Initialize connection to Pulse's configuration system."""
        try:
            if PULSE_CONFIG_AVAILABLE:
                self.pulse_config = PulseConfig()
                
                # Get integration-specific configuration
                integration_config = self.pulse_config.get("recursive_training", {})
                
                # Merge with local config (local takes precedence)
                for key, value in integration_config.items():
                    if key not in self.config:
                        self.config[key] = value
                        
                self.logger.info("Connected to Pulse configuration system")
                self.pulse_connected = True
            else:
                self.pulse_config = PulseConfig()  # Fallback
                self.logger.warning("Pulse configuration system not available, using fallback")
        except Exception as e:
            self.logger.error(f"Error connecting to Pulse configuration: {e}")
            self.pulse_config = PulseConfig()  # Fallback
    
    def _init_event_system(self):
        """Initialize connection to Pulse's event system."""
        try:
            if EVENT_SYSTEM_AVAILABLE:
                self.event_system = PulseEventSystem
                self.logger.info("Connected to Pulse event system")
                
                # Register event handlers
                self._register_event_handlers()
            else:
                self.event_system = PulseEventSystem  # Fallback
                self.logger.warning("Pulse event system not available, using fallback")
        except Exception as e:
            self.logger.error(f"Error connecting to Pulse event system: {e}")
            self.event_system = PulseEventSystem  # Fallback
    
    def _init_symbolic_system(self):
        """Initialize connection to Pulse's symbolic system."""
        try:
            if SYMBOLIC_EXECUTOR_AVAILABLE:
                self.symbolic_executor = SymbolicExecutor()
                self.logger.info("Connected to Pulse symbolic executor")
            else:
                self.symbolic_executor = SymbolicExecutor()  # Fallback
                self.logger.warning("Pulse symbolic executor not available, using fallback")
        except Exception as e:
            self.logger.error(f"Error connecting to Pulse symbolic executor: {e}")
            self.symbolic_executor = SymbolicExecutor()  # Fallback
    
    def _register_event_handlers(self):
        """Register handlers for Pulse events."""
        if self.event_handlers_registered:
            return
            
        try:
            # Register for training-related events
            self.event_system.subscribe("pulse.model.trained", self._handle_model_trained_event)
            self.event_system.subscribe("pulse.rule.updated", self._handle_rule_updated_event)
            self.event_system.subscribe("pulse.metrics.request", self._handle_metrics_request_event)
            
            self.event_handlers_registered = True
            self.logger.info("Event handlers registered with Pulse event system")
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {e}")
    
    def _handle_model_trained_event(self, data):
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
                tags=["pulse_model", f"model:{model_name}"]
            )
            
            self.logger.info(f"Processed model training event for {model_name}")
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error handling model trained event: {e}")
    
    def _handle_rule_updated_event(self, data):
        """
        Handle Pulse rule updated event.
        
        Args:
            data: Event data from Pulse
        """
        try:
            self.event_counts["received"] += 1
            
            # Extract rule details
            rule_id = data.get("rule_id", "unknown")
            rule_type = data.get("rule_type", "unknown")
            rule_data = data.get("rule_data", {})
            
            # Process the rule update in our system
            # This is a simplified implementation
            result = {
                "rule_id": rule_id,
                "processed": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Send result back to Pulse
            self._emit_event("recursive_training.rule.processed", result)
            
            self.logger.info(f"Processed rule update event for {rule_id}")
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error handling rule updated event: {e}")
    
    def _handle_metrics_request_event(self, data):
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
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._emit_event("recursive_training.metrics.response", response)
            
            self.logger.info(f"Processed metrics request {request_id}")
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error handling metrics request event: {e}")
    
    def _emit_event(self, event_type, data):
        """
        Emit an event to Pulse's event system.
        
        Args:
            event_type: Type of event to emit
            data: Event data
        """
        try:
            self.event_system.emit(event_type, data)
            self.event_counts["sent"] += 1
            return True
        except Exception as e:
            self.event_counts["errors"] += 1
            self.logger.error(f"Error emitting event {event_type}: {e}")
            return False
    
    def execute_rule(self, rule_data):
        """
        Execute a rule using Pulse's symbolic executor.
        
        Args:
            rule_data: Rule definition
            
        Returns:
            Execution result
        """
        try:
            if not SYMBOLIC_EXECUTOR_AVAILABLE:
                return {"status": "error", "message": "Symbolic executor not available"}
            
            result = self.symbolic_executor.execute_rule(rule_data)
            
            # Track execution in metrics
            timestamp = datetime.now(timezone.utc).isoformat()
            self.metrics_store.store_metric({
                "timestamp": timestamp,
                "metric_type": "rule_execution",
                "rule_id": rule_data.get("id", "unknown"),
                "execution_status": result.get("status", "unknown"),
                "tags": ["rule_execution"]
            })
            
            return result
        except Exception as e:
            self.logger.error(f"Error executing rule: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_connection_status(self):
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
            "integration_timestamp": self.integration_timestamp
        }
    
    def convert_pulse_data_format(self, data, target_format):
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
                "version": self.version
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