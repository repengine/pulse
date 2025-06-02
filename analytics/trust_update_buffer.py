"""
TrustUpdateBuffer

An efficient buffer for collecting and batching trust updates before
sending them to the OptimizedBayesianTrustTracker. This reduces lock
contention and improves performance during high-throughput training.
"""

import logging
import threading
import time
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

from analytics.optimized_trust_tracker import optimized_bayesian_trust_tracker

logger = logging.getLogger(__name__)


class TrustUpdateBuffer:
    """
    Efficiently buffers trust updates before sending them to the
    OptimizedBayesianTrustTracker in optimized batches.

    Features:
    - Collects updates in memory with efficient NumPy structures
    - Provides thread-safe access for concurrent updates
    - Automatically flushes when thresholds are reached
    - Supports manual flush for critical updates
    - Configurable buffer sizes and flush triggers
    """

    _instance = None

    @classmethod
    def get_instance(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> "TrustUpdateBuffer":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = TrustUpdateBuffer(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the TrustUpdateBuffer."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.max_buffer_size = self.config.get("trust_buffer_size", 1000)
        self.flush_threshold = self.config.get("trust_flush_threshold", 100)
        self.auto_flush_interval = self.config.get("trust_auto_flush_interval_sec", 5.0)

        # Buffer data structures
        self._buffer_lock = threading.RLock()
        self._buffer = defaultdict(list)  # key -> [(success, weight), ...]
        self._buffer_size = 0
        self._last_flush_time = time.time()

        # Statistics
        self.stats = {
            "updates_buffered": 0,
            "updates_flushed": 0,
            "flush_operations": 0,
            "auto_flushes": 0,
            "manual_flushes": 0,
        }

        # Get the trust tracker
        self.trust_tracker = optimized_bayesian_trust_tracker

    def add_update(self, key: str, success: bool, weight: float = 1.0) -> bool:
        """
        Add a trust update to the buffer.

        Args:
            key: The rule or variable identifier
            success: Whether the prediction was successful
            weight: Weight of the observation (default=1.0)

        Returns:
            True if buffer was automatically flushed
        """
        flushed = False

        with self._buffer_lock:
            # Add update to buffer
            self._buffer[key].append((success, weight))
            self._buffer_size += 1
            self.stats["updates_buffered"] += 1

            # Check if we need to flush
            current_time = time.time()
            time_to_flush = (
                current_time - self._last_flush_time
            ) >= self.auto_flush_interval
            size_to_flush = self._buffer_size >= self.flush_threshold

            if time_to_flush or size_to_flush:
                self._flush_internal()
                flushed = True

                if time_to_flush:
                    self.stats["auto_flushes"] += 1

        return flushed

    def add_updates_batch(self, updates: List[Tuple[str, bool, float]]) -> bool:
        """
        Add multiple trust updates at once.

        Args:
            updates: List of (key, success, weight) tuples

        Returns:
            True if buffer was automatically flushed
        """
        if not updates:
            return False

        flushed = False

        with self._buffer_lock:
            # Add all updates to buffer
            for key, success, weight in updates:
                self._buffer[key].append((success, weight))

            self._buffer_size += len(updates)
            self.stats["updates_buffered"] += len(updates)

            # Check if we need to flush
            current_time = time.time()
            time_to_flush = (
                current_time - self._last_flush_time
            ) >= self.auto_flush_interval
            size_to_flush = self._buffer_size >= self.flush_threshold

            if time_to_flush or size_to_flush:
                self._flush_internal()
                flushed = True

                if time_to_flush:
                    self.stats["auto_flushes"] += 1

        return flushed

    def flush(self) -> int:
        """
        Manually flush the buffer.

        Returns:
            Number of updates flushed
        """
        with self._buffer_lock:
            updates_flushed = self._flush_internal()
            self.stats["manual_flushes"] += 1

        return updates_flushed

    def _flush_internal(self) -> int:
        """
        Internal method to flush the buffer.

        Returns:
            Number of updates flushed
        """
        if self._buffer_size == 0:
            return 0

        # Transform buffer into optimized batch updates
        optimized_updates = []

        for key, updates in self._buffer.items():
            # Aggregate updates by success value
            success_count = 0
            success_weight = 0.0
            failure_count = 0
            failure_weight = 0.0

            for success, weight in updates:
                if success:
                    success_count += 1
                    success_weight += weight
                else:
                    failure_count += 1
                    failure_weight += weight

            # Add aggregated updates
            if success_count > 0:
                optimized_updates.append((key, True, success_weight))

            if failure_count > 0:
                optimized_updates.append((key, False, failure_weight))

        # Send optimized batch to trust tracker
        if optimized_updates:
            self.trust_tracker.batch_update(optimized_updates)

        # Update statistics
        updates_flushed = self._buffer_size
        self.stats["updates_flushed"] += updates_flushed
        self.stats["flush_operations"] += 1

        # Reset buffer
        self._buffer.clear()
        self._buffer_size = 0
        self._last_flush_time = time.time()

        return updates_flushed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about buffer usage.

        Returns:
            Dictionary of statistics
        """
        with self._buffer_lock:
            stats = self.stats.copy()
            stats["current_buffer_size"] = self._buffer_size
            stats["unique_keys"] = len(self._buffer)

            # Calculate derived statistics
            if stats["flush_operations"] > 0:
                stats["avg_updates_per_flush"] = (
                    stats["updates_flushed"] / stats["flush_operations"]
                )
            else:
                stats["avg_updates_per_flush"] = 0

            stats["buffer_utilization"] = min(
                100.0, (self._buffer_size / self.max_buffer_size) * 100.0
            )

            return stats


# Create vectorized operations for NumPy batch processing
def create_aggregated_updates(
    updates: List[Tuple[str, bool, float]],
) -> List[Tuple[str, bool, float]]:
    """
    Aggregate a list of updates by key and success value, combining weights.

    Args:
        updates: List of (key, success, weight) tuples

    Returns:
        Aggregated list of updates
    """
    if not updates:
        return []

    # Group updates by key and success value
    aggregated = defaultdict(float)

    for key, success, weight in updates:
        # Create a compound key for the aggregation
        compound_key = (key, success)
        aggregated[compound_key] += weight

    # Convert back to list of tuples
    return [(key, success, weight) for (key, success), weight in aggregated.items()]


# Convenient singleton accessor
def get_trust_update_buffer(
    config: Optional[Dict[str, Any]] = None,
) -> TrustUpdateBuffer:
    """
    Get the singleton instance of TrustUpdateBuffer.

    Args:
        config: Optional configuration dictionary

    Returns:
        TrustUpdateBuffer instance
    """
    return TrustUpdateBuffer.get_instance(config)
