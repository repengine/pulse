"""
Retrodiction Trigger module for connecting regime change events to retrodiction model re-evaluation.
Provides mechanisms to trigger "retrodiction snapshots" based on detected regime changes.
"""

import logging
import os
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import queue

from recursive_training.regime_sensor.regime_detector import (
    RegimeType,
    RegimeChangeEvent,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TriggerCause(Enum):
    """Types of triggers that can cause a retrodiction snapshot."""

    REGIME_CHANGE = "regime_change"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    ERROR_THRESHOLD = "error_threshold"
    CONFIDENCE_DROP = "confidence_drop"
    NEW_DATA = "new_data"
    ANOMALY = "anomaly"


class TriggerPriority(Enum):
    """Priority levels for retrodiction triggers."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class RetrodictionSnapshot:
    """
    Represents a snapshot of state for retrodiction model evaluation.
    Contains information about the trigger cause, timing, and data.
    """

    def __init__(
        self,
        snapshot_id: str,
        timestamp: datetime,
        cause: TriggerCause,
        priority: TriggerPriority,
        regime_change: Optional[RegimeChangeEvent] = None,
        variables: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a retrodiction snapshot.

        Args:
            snapshot_id: Unique identifier for this snapshot
            timestamp: When the snapshot was created
            cause: What caused this snapshot to be triggered
            priority: Priority level for processing this snapshot
            regime_change: The regime change event that triggered this snapshot (if applicable)
            variables: List of variables to include in retrodiction
            time_range: Time range to consider for retrodiction (start, end)
            metadata: Additional metadata about the snapshot
        """
        self.snapshot_id = snapshot_id
        self.timestamp = timestamp
        self.cause = cause
        self.priority = priority
        self.regime_change = regime_change
        self.variables = variables or []
        self.time_range = time_range
        self.metadata = metadata or {}
        self.processed = False
        self.processing_start: Optional[datetime] = None
        self.processing_end: Optional[datetime] = None
        self.results = {}

    def __str__(self):
        return (
            f"RetrodictionSnapshot({self.snapshot_id}, {self.cause.value}, "
            f"priority={self.priority.name}, processed={self.processed})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        result = {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "cause": self.cause.value,
            "priority": self.priority.value,
            "variables": self.variables,
            "metadata": self.metadata,
            "processed": self.processed,
            "processing_start": self.processing_start.isoformat()
            if self.processing_start
            else None,
            "processing_end": self.processing_end.isoformat()
            if self.processing_end
            else None,
            "results": self.results,
        }

        if self.regime_change:
            result["regime_change_id"] = self.regime_change.regime_change_id

        if self.time_range:
            result["time_range_start"] = self.time_range[0].isoformat()
            result["time_range_end"] = self.time_range[1].isoformat()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrodictionSnapshot":
        """Create a snapshot from a dictionary."""
        # Convert cause value to enum
        cause_value = data.get("cause", TriggerCause.MANUAL.value)
        cause = TriggerCause(cause_value)

        # Convert priority value to enum
        priority_value = data.get("priority", TriggerPriority.MEDIUM.value)
        priority = TriggerPriority(priority_value)

        # Parse timestamp
        timestamp_str = data.get("timestamp", datetime.now().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            logger.warning(
                f"Invalid timestamp format: {timestamp_str}, using current time"
            )
            timestamp = datetime.now()

        # Parse time range if present
        time_range = None
        if "time_range_start" in data and "time_range_end" in data:
            try:
                start = datetime.fromisoformat(
                    data["time_range_start"].replace("Z", "+00:00")
                )
                end = datetime.fromisoformat(
                    data["time_range_end"].replace("Z", "+00:00")
                )
                time_range = (start, end)
            except ValueError:
                logger.warning("Invalid time range format, ignoring")

        # Create snapshot
        snapshot = cls(
            snapshot_id=data.get("snapshot_id", ""),
            timestamp=timestamp,
            cause=cause,
            priority=priority,
            variables=data.get("variables", []),
            time_range=time_range,
            metadata=data.get("metadata", {}),
        )

        # Set additional fields
        snapshot.processed = data.get("processed", False)

        if "processing_start" in data and data["processing_start"]:
            try:
                snapshot.processing_start = datetime.fromisoformat(
                    data["processing_start"].replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning("Invalid processing_start format, ignoring")

        if "processing_end" in data and data["processing_end"]:
            try:
                snapshot.processing_end = datetime.fromisoformat(
                    data["processing_end"].replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning("Invalid processing_end format, ignoring")

        snapshot.results = data.get("results", {})

        return snapshot


class RetrodictionTrigger:
    """
    Manages the triggering of retrodiction snapshots based on various events.
    Connects regime changes to retrodiction evaluation and handles scheduling.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the retrodiction trigger manager.

        Args:
            config: Configuration parameters for trigger behavior
        """
        self.config = config or {}
        self.snapshot_queue = queue.PriorityQueue()  # Priority queue for snapshots
        self.snapshot_history = []
        self.handlers = []
        self.running = False
        self.processing_thread = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        # Load configuration
        self.auto_trigger_enabled = self.config.get("auto_trigger_enabled", True)
        self.default_time_window = self.config.get("default_time_window_days", 365)
        self.default_variables = self.config.get("default_variables", [])
        self.schedule_interval = self.config.get("schedule_interval_hours", 24)
        self.last_scheduled = None

        # Storage config
        self.storage_enabled = self.config.get("storage_enabled", True)
        self.storage_path = self.config.get(
            "storage_path", "data/retrodiction_snapshots"
        )

        # Initialize storage directory if enabled
        if self.storage_enabled:
            os.makedirs(self.storage_path, exist_ok=True)

        logger.info("RetrodictionTrigger initialized")

    def register_handler(self, handler: Callable[[RetrodictionSnapshot], None]):
        """
        Register a handler to be called when a snapshot is ready for processing.

        Args:
            handler: Function to call with the retrodiction snapshot
        """
        with self.lock:
            self.handlers.append(handler)

    def handle_regime_change(self, regime_change: RegimeChangeEvent):
        """
        Handle a regime change event by creating a retrodiction snapshot.

        Args:
            regime_change: The regime change event that occurred
        """
        if not self.auto_trigger_enabled:
            logger.info(
                f"Auto-triggering disabled, ignoring regime change: {regime_change}"
            )
            return

        logger.info(f"Handling regime change: {regime_change}")

        # Determine priority based on confidence and regime type
        priority = TriggerPriority.MEDIUM

        # Higher priority for more significant regime changes
        if regime_change.confidence > 0.8:
            priority = TriggerPriority.HIGH

        # Certain regime types are more critical
        if regime_change.new_regime in [
            RegimeType.VOLATILITY_SHOCK,
            RegimeType.GEOPOLITICAL_CRISIS,
        ]:
            priority = TriggerPriority.CRITICAL

        # Create time range based on default window
        end_time = datetime.now()
        start_time = end_time.replace(
            year=end_time.year - 1
            if self.default_time_window >= 365
            else end_time.year,
            day=1,
            month=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        # Create snapshot
        snapshot_id = f"snapshot_{len(self.snapshot_history) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        snapshot = RetrodictionSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(),
            cause=TriggerCause.REGIME_CHANGE,
            priority=priority,
            regime_change=regime_change,
            variables=self.default_variables.copy(),
            time_range=(start_time, end_time),
            metadata={
                "trigger_timestamp": datetime.now().isoformat(),
                "regime_type": regime_change.new_regime.value,
                "confidence": regime_change.confidence,
            },
        )

        # Queue the snapshot
        self._enqueue_snapshot(snapshot)

        # Mark regime change as having triggered retrodiction
        regime_change.retrodiction_triggered = True

    def trigger_manual_snapshot(
        self,
        variables: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        priority: TriggerPriority = TriggerPriority.HIGH,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RetrodictionSnapshot:
        """
        Manually trigger a retrodiction snapshot.

        Args:
            variables: List of variables to include
            time_range: Time range to consider
            priority: Priority level
            metadata: Additional metadata

        Returns:
            The created RetrodictionSnapshot
        """
        logger.info("Manually triggering retrodiction snapshot")

        # Use default time range if not provided
        if time_range is None:
            end_time = datetime.now()
            start_time = end_time.replace(
                year=end_time.year - 1
                if self.default_time_window >= 365
                else end_time.year,
                day=1,
                month=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            time_range = (start_time, end_time)

        # Create snapshot
        snapshot_id = f"manual_{len(self.snapshot_history) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        snapshot = RetrodictionSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(),
            cause=TriggerCause.MANUAL,
            priority=priority,
            variables=variables or self.default_variables.copy(),
            time_range=time_range,
            metadata=metadata or {"manual_trigger": True},
        )

        # Queue the snapshot
        self._enqueue_snapshot(snapshot)

        return snapshot

    def _enqueue_snapshot(self, snapshot: RetrodictionSnapshot):
        """
        Add a snapshot to the processing queue.

        Args:
            snapshot: The snapshot to queue
        """
        with self.lock:
            # Add to priority queue with priority as the first element of the tuple
            # Use negative priority value to make higher priority snapshots processed first
            self.snapshot_queue.put((-snapshot.priority.value, time.time(), snapshot))
            logger.debug(f"Enqueued snapshot: {snapshot}")

            # Add to history
            self.snapshot_history.append(snapshot)

            # Store if enabled
            if self.storage_enabled:
                self._store_snapshot(snapshot)

    def _store_snapshot(self, snapshot: RetrodictionSnapshot):
        """
        Store a snapshot to disk.

        Args:
            snapshot: Snapshot to store
        """
        try:
            # Create filename
            filename = f"{snapshot.snapshot_id}.json"
            file_path = os.path.join(self.storage_path, filename)

            # Store as JSON
            with open(file_path, "w") as f:
                json.dump(snapshot.to_dict(), f, indent=2)

            logger.debug(f"Stored snapshot to {file_path}")
        except Exception as e:
            logger.error(f"Error storing snapshot: {e}")

    def _process_snapshot(self, snapshot: RetrodictionSnapshot):
        """
        Process a single snapshot by calling appropriate handlers.

        Args:
            snapshot: Snapshot to process
        """
        try:
            # Update processing time
            snapshot.processing_start = datetime.now()

            # Call all registered handlers
            for handler in self.handlers:
                try:
                    handler(snapshot)
                except Exception as e:
                    logger.error(f"Error in snapshot handler: {e}")

            # Update processing status
            snapshot.processed = True
            snapshot.processing_end = datetime.now()

            # Update stored snapshot
            if self.storage_enabled:
                self._store_snapshot(snapshot)

            logger.info(f"Processed snapshot: {snapshot}")
        except Exception as e:
            logger.error(f"Error processing snapshot: {e}")

    def _snapshot_processor_loop(self):
        """Background thread for processing snapshots from the queue."""
        logger.info("Snapshot processor thread started")

        while not self.stop_event.is_set():
            try:
                # Check if it's time for a scheduled snapshot
                self._check_scheduled_snapshot()

                # Get a snapshot from the queue with timeout to allow checking stop_event
                try:
                    _, _, snapshot = self.snapshot_queue.get(timeout=1.0)
                    self._process_snapshot(snapshot)
                    self.snapshot_queue.task_done()
                except queue.Empty:
                    continue  # No snapshots in queue, try again
            except Exception as e:
                logger.error(f"Error in snapshot processor loop: {e}")
                time.sleep(1)  # Avoid tight loop in case of recurring errors

        logger.info("Snapshot processor thread stopped")

    def _check_scheduled_snapshot(self):
        """Check if it's time to create a scheduled snapshot."""
        # Skip if auto-trigger is disabled
        if not self.auto_trigger_enabled:
            return

        now = datetime.now()

        # If never run, or if schedule_interval hours have passed
        if (
            self.last_scheduled is None
            or (now - self.last_scheduled).total_seconds()
            >= self.schedule_interval * 3600
        ):
            logger.info("Creating scheduled retrodiction snapshot")

            # Create a scheduled snapshot
            self.last_scheduled = now

            # Use default time range
            end_time = now
            start_time = end_time.replace(
                year=end_time.year - 1
                if self.default_time_window >= 365
                else end_time.year,
                day=1,
                month=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            # Create snapshot
            snapshot_id = f"scheduled_{len(self.snapshot_history) + 1}_{now.strftime('%Y%m%d%H%M%S')}"
            snapshot = RetrodictionSnapshot(
                snapshot_id=snapshot_id,
                timestamp=now,
                cause=TriggerCause.SCHEDULED,
                priority=TriggerPriority.LOW,
                variables=self.default_variables.copy(),
                time_range=(start_time, end_time),
                metadata={"scheduled": True, "interval_hours": self.schedule_interval},
            )

            # Queue the snapshot
            self._enqueue_snapshot(snapshot)

    def start(self):
        """Start the snapshot processing thread."""
        with self.lock:
            if not self.running:
                self.stop_event.clear()
                self.processing_thread = threading.Thread(
                    target=self._snapshot_processor_loop
                )
                self.processing_thread.daemon = True
                self.processing_thread.start()
                self.running = True
                logger.info("RetrodictionTrigger started")

    def stop(self):
        """Stop the snapshot processing thread."""
        with self.lock:
            if self.running:
                self.stop_event.set()
                if self.processing_thread:
                    self.processing_thread.join(timeout=5.0)
                self.running = False
                logger.info("RetrodictionTrigger stopped")

    def get_snapshot_history(self) -> List[RetrodictionSnapshot]:
        """Get the history of snapshots."""
        return self.snapshot_history.copy()

    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[RetrodictionSnapshot]:
        """
        Retrieve a snapshot by its ID.

        Args:
            snapshot_id: ID of the snapshot to retrieve

        Returns:
            Snapshot if found, None otherwise
        """
        for snapshot in self.snapshot_history:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None


# Example implementation of a retrodiction handler
class RetrodictionRunner:
    """
    Handles the actual running of retrodiction models based on snapshots.
    This is a simple implementation - a real system would connect to more sophisticated
    model training and evaluation systems.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the retrodiction runner.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.results_path = self.config.get("results_path", "data/retrodiction_results")
        os.makedirs(self.results_path, exist_ok=True)
        logger.info("RetrodictionRunner initialized")

    def process_snapshot(self, snapshot: RetrodictionSnapshot):
        """
        Process a retrodiction snapshot by running models and storing results.

        Args:
            snapshot: The snapshot to process
        """
        logger.info(f"Running retrodiction for snapshot: {snapshot}")

        # In a real implementation, this would:
        # 1. Load the appropriate data based on snapshot.variables and snapshot.time_range
        # 2. Configure retrodiction models
        # 3. Run the models and evaluate performance
        # 4. Store results

        # Simulate processing time
        time.sleep(1)

        # Simulate some results
        results = {
            "success": True,
            "processing_time_seconds": 1.0,
            "variables_processed": len(snapshot.variables),
            "model_metrics": {"accuracy": 0.85, "mae": 0.12, "rmse": 0.18},
            "timestamp": datetime.now().isoformat(),
        }

        # Update snapshot with results
        snapshot.results = results

        # Store results
        self._store_results(snapshot)

        logger.info(f"Completed retrodiction for snapshot: {snapshot}")

    def _store_results(self, snapshot: RetrodictionSnapshot):
        """
        Store retrodiction results.

        Args:
            snapshot: Snapshot with results to store
        """
        try:
            # Create filename
            filename = f"result_{snapshot.snapshot_id}.json"
            file_path = os.path.join(self.results_path, filename)

            # Store as JSON
            with open(file_path, "w") as f:
                json.dump(
                    {"snapshot": snapshot.to_dict(), "results": snapshot.results},
                    f,
                    indent=2,
                )

            logger.debug(f"Stored retrodiction results to {file_path}")
        except Exception as e:
            logger.error(f"Error storing retrodiction results: {e}")


# Example usage
if __name__ == "__main__":
    # Create a retrodiction trigger
    trigger = RetrodictionTrigger(
        {
            "auto_trigger_enabled": True,
            "default_time_window_days": 365,
            "default_variables": ["spx_close", "us_10y_yield", "vix"],
        }
    )

    # Create a retrodiction runner
    runner = RetrodictionRunner()

    # Register the runner as a handler for snapshots
    trigger.register_handler(runner.process_snapshot)

    # Start the trigger
    trigger.start()

    # Create a test regime change to trigger a snapshot
    from recursive_training.regime_sensor.regime_detector import RegimeChangeEvent

    regime_change = RegimeChangeEvent(
        regime_change_id="test_change_1",
        timestamp=datetime.now(),
        old_regime=RegimeType.EXPANSION,
        new_regime=RegimeType.VOLATILITY_SHOCK,
        confidence=0.85,
        supporting_evidence=[],
        market_indicators={"vix": 35, "price_change": -0.05},
    )

    # Handle the regime change
    trigger.handle_regime_change(regime_change)

    # Also create a manual snapshot
    manual_snapshot = trigger.trigger_manual_snapshot(
        variables=["spx_close", "us_10y_yield", "us_3m_yield", "vix"],
        priority=TriggerPriority.HIGH,
        metadata={"test": True, "custom": "value"},
    )

    # Allow time for processing
    time.sleep(5)

    # Stop the trigger
    trigger.stop()

    # Print results
    for snapshot in trigger.get_snapshot_history():
        print(f"Snapshot: {snapshot}")
        print(f"  Processed: {snapshot.processed}")
        print(f"  Results: {snapshot.results}")
