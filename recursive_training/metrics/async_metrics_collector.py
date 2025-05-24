"""
AsyncMetricsCollector

A non-blocking metrics collection system that uses an internal queue and
background worker to process metrics without blocking the main training process.
"""

import logging
import queue
import threading
import time
from typing import Dict, Any, Optional, List, Callable
import uuid
from datetime import datetime, timezone
import traceback

from recursive_training.metrics.metrics_store import get_metrics_store

logger = logging.getLogger(__name__)


class AsyncMetricsCollector:
    """
    Asynchronous metrics collection system that uses a background thread
    to process metrics without blocking the main training process.

    Features:
    - Non-blocking metrics submission
    - Background worker for processing metrics
    - Batch processing for improved efficiency
    - Graceful shutdown
    - Configurable flush intervals
    - Error handling with retry logic
    """

    _instance = None

    @classmethod
    def get_instance(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> "AsyncMetricsCollector":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = AsyncMetricsCollector(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the AsyncMetricsCollector."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Queue for metrics
        self.metrics_queue = queue.Queue()

        # Configuration options
        self.batch_size = self.config.get("metrics_batch_size", 50)
        self.flush_interval = self.config.get("metrics_flush_interval_sec", 5.0)
        self.max_retries = self.config.get("metrics_max_retries", 3)
        self.retry_delay = self.config.get("metrics_retry_delay_sec", 1.0)

        # Status flags
        self.running = False
        self.worker_thread = None
        self.error_callbacks = []

        # Statistics
        self.stats = {
            "metrics_submitted": 0,
            "metrics_processed": 0,
            "metrics_failed": 0,
            "batches_processed": 0,
            "processing_time": 0.0,
            "last_flush_time": time.time(),
        }

        # Get metrics store
        self.metrics_store = get_metrics_store()

        # Start worker thread
        self.start()

    def start(self):
        """Start the background worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(
                target=self._worker_loop, name="AsyncMetricsCollector", daemon=True
            )
            self.worker_thread.start()
            self.logger.info("AsyncMetricsCollector worker thread started")

    def stop(self, wait_for_completion: bool = True, timeout: float = 10.0):
        """
        Stop the background worker thread.

        Args:
            wait_for_completion: If True, wait for all pending metrics to be processed
            timeout: Maximum time to wait for completion (seconds)
        """
        if self.running:
            self.logger.info("Stopping AsyncMetricsCollector worker thread")
            self.running = False

            if wait_for_completion and self.worker_thread is not None:
                wait_start = time.time()
                while not self.metrics_queue.empty():
                    if time.time() - wait_start > timeout:
                        self.logger.warning(
                            f"Timeout waiting for metrics queue to empty. {self.metrics_queue.qsize()} items remaining."
                        )
                        break
                    time.sleep(0.1)

                self.worker_thread.join(timeout=timeout)
                if self.worker_thread.is_alive():
                    self.logger.warning(
                        "AsyncMetricsCollector worker thread did not terminate within timeout"
                    )
                else:
                    self.logger.info(
                        "AsyncMetricsCollector worker thread stopped successfully"
                    )

    def submit_metric(self, metric_data: Dict[str, Any]) -> str:
        """
        Submit a metric for asynchronous processing.

        Args:
            metric_data: Metric data to submit

        Returns:
            Unique ID for the submitted metric
        """
        # Ensure timestamp is present
        if "timestamp" not in metric_data:
            metric_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Generate ID if not provided
        metric_id = metric_data.get("id")
        if metric_id is None:
            metric_id = str(uuid.uuid4())
            metric_data["id"] = metric_id

        # Add to queue
        self.metrics_queue.put(metric_data)
        self.stats["metrics_submitted"] += 1

        return metric_id

    def _worker_loop(self):
        """Background worker thread main loop."""
        while self.running or not self.metrics_queue.empty():
            try:
                # Process metrics in batches
                metrics_batch = []
                _batch_start_time = time.time()

                # Try to collect a batch of metrics
                while len(metrics_batch) < self.batch_size:
                    try:
                        # Don't block forever if we're shutting down
                        timeout = 0.1 if self.running else 0.0
                        metric = self.metrics_queue.get(block=True, timeout=timeout)
                        metrics_batch.append(metric)
                    except queue.Empty:
                        break

                # Process the batch
                if metrics_batch:
                    self._process_metrics_batch(metrics_batch)
                    self.stats["batches_processed"] += 1

                # Check if we need to flush based on time
                current_time = time.time()
                if current_time - self.stats["last_flush_time"] >= self.flush_interval:
                    # In a real implementation, this might do additional flushing
                    # or sync operations with persistent storage
                    self.stats["last_flush_time"] = current_time

                # Sleep a tiny bit to avoid consuming too much CPU
                # when queue is empty but we're still running
                if self.running and not metrics_batch:
                    time.sleep(0.01)

            except Exception as e:
                self.logger.error(f"Error in metrics worker thread: {e}")
                traceback.print_exc()

                # Notify error callbacks
                for callback in self.error_callbacks:
                    try:
                        callback(e)
                    except Exception as callback_error:
                        self.logger.error(
                            f"Error in metrics error callback: {callback_error}"
                        )

    def _process_metrics_batch(self, metrics_batch: List[Dict[str, Any]]):
        """
        Process a batch of metrics.

        Args:
            metrics_batch: List of metric data dictionaries to process
        """
        start_time = time.time()

        # Track metrics that need retry
        _retry_metrics = []

        for metric in metrics_batch:
            success = False
            retries = 0

            while not success and retries <= self.max_retries:
                try:
                    # Store the metric
                    self.metrics_store.store_metric(metric)
                    success = True
                    self.stats["metrics_processed"] += 1

                except Exception as e:
                    retries += 1
                    if retries <= self.max_retries:
                        self.logger.warning(
                            f"Failed to process metric {metric.get('id')}, retrying ({retries}/{self.max_retries}): {e}"
                        )
                        time.sleep(self.retry_delay)
                    else:
                        self.logger.error(
                            f"Failed to process metric {metric.get('id')} after {self.max_retries} retries: {e}"
                        )
                        self.stats["metrics_failed"] += 1

                        # Notify error callbacks
                        for callback in self.error_callbacks:
                            try:
                                callback(e)
                            except Exception as callback_error:
                                self.logger.error(
                                    f"Error in metrics error callback: {callback_error}"
                                )

                        # In a more robust implementation, these could be
                        # saved to a "dead letter queue" for later analysis

            # Signal task completion to queue
            self.metrics_queue.task_done()

        # Update processing time statistics
        processing_time = time.time() - start_time
        self.stats["processing_time"] += processing_time

    def register_error_callback(self, callback: Callable[[Exception], None]):
        """
        Register a callback for error handling.

        Args:
            callback: Function to call when an error occurs
        """
        self.error_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about metrics processing.

        Returns:
            Dictionary of statistics
        """
        stats = self.stats.copy()
        stats["queue_size"] = self.metrics_queue.qsize()

        # Calculate derived metrics
        if stats["metrics_submitted"] > 0:
            stats["success_rate"] = (
                stats["metrics_processed"] / stats["metrics_submitted"]
            ) * 100.0
        else:
            stats["success_rate"] = 100.0

        if stats["batches_processed"] > 0:
            stats["avg_batch_time"] = (
                stats["processing_time"] / stats["batches_processed"]
            )
        else:
            stats["avg_batch_time"] = 0.0

        return stats


# Convenient singleton accessor
def get_async_metrics_collector(
    config: Optional[Dict[str, Any]] = None,
) -> AsyncMetricsCollector:
    """
    Get the singleton instance of AsyncMetricsCollector.

    Args:
        config: Optional configuration dictionary

    Returns:
        AsyncMetricsCollector instance
    """
    return AsyncMetricsCollector.get_instance(config)
