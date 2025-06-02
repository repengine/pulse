"""
OptimizedBayesianTrustTracker

An optimized version of the Bayesian trust tracker with batch operations,
efficient data structures, and caching for improved performance during
retrodiction training.
"""

import threading
import json
import os
import time
import numpy as np
from collections import defaultdict
from typing import Dict, Tuple, List, Any, Union
import math
from functools import lru_cache


class OptimizedBayesianTrustTracker:
    """
    Optimized tracker for Bayesian trust/confidence using batch operations
    and efficient data structures. Maintains thread safety for concurrent updates.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.stats: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (1.0, 1.0)
        )  # (alpha, beta) priors
        self.last_update: Dict[str, float] = defaultdict(
            float
        )  # Track last update time

        # Use numpy arrays for timestamps instead of lists of tuples for better
        # memory efficiency
        self.timestamps: Dict[str, Dict[str, np.ndarray]] = defaultdict(
            lambda: {
                "times": np.array([], dtype=np.float64),
                "values": np.array([], dtype=np.float64),
            }
        )

        # Add cache for frequently accessed trust values
        self._trust_cache: Dict[str, float] = {}
        self._cache_valid: Dict[str, bool] = defaultdict(bool)

        # Add batch operation support
        self._pending_updates: List[Tuple[str, bool, float]] = []
        self.batch_size = 50  # Process updates in batches of 50

        # Statistics for performance monitoring
        self.stats_enabled = False
        self.performance_stats = {
            "batch_operations": 0.0,
            "cache_hits": 0.0,
            "cache_misses": 0.0,
            "single_updates": 0.0,
            "batch_updates": 0.0,
        }

    def update(self, key: str, success: bool, weight: float = 1.0):
        """
        Update the Beta distribution for a rule/variable.
        This implementation adds to a pending batch to be processed efficiently.

        Args:
            key (str): Rule or variable identifier.
            success (bool): Outcome (True=success, False=failure).
            weight (float): Weight of the observation (default=1.0).
        """
        # For single updates, just perform directly for responsive feedback
        self._perform_update(key, success, weight)
        if self.stats_enabled:
            self.performance_stats["single_updates"] += 1

    def _perform_update(self, key: str, success: bool, weight: float):
        """Internal method to actually perform the update."""
        with self.lock:
            alpha, beta = self.stats[key]
            if success:
                alpha += weight
            else:
                beta += weight

            self.stats[key] = (alpha, beta)
            current_time = time.time()
            self.last_update[key] = current_time

            # Append to timestamps using numpy's efficient append
            ts_dict = self.timestamps[key]
            ts_dict["times"] = np.append(ts_dict["times"], current_time)
            ts_dict["values"] = np.append(ts_dict["values"], alpha / (alpha + beta))

            # Invalidate cache
            self._cache_valid[key] = False

    def batch_update(
        self, results: List[Union[Tuple[str, bool], Tuple[str, bool, float]]]
    ) -> None:
        """
        Efficiently update trust for multiple keys in a batch operation.

        Args:
            results: List of tuples (key, success, weight) to update.
                    Weight is optional and defaults to 1.0 if not provided.
        """
        if not results:
            return

        with self.lock:
            # Process all updates in a single lock acquisition
            for update in results:
                # Check tuple length and unpack accordingly
                if len(update) == 2:
                    # Two-element tuple case
                    key_val: str = update[0]
                    success_val: bool = update[1]
                    weight_val: float = 1.0
                else:
                    # Three-element tuple case
                    key_val: str = update[0]
                    success_val: bool = update[1]
                    weight_val: float = float(update[2])  # Ensure it's a float

                alpha, beta = self.stats[key_val]
                if success_val:
                    alpha += weight_val
                else:
                    beta += weight_val

                self.stats[key_val] = (alpha, beta)
                current_time = time.time()
                self.last_update[key_val] = current_time

                # Invalidate cache
                self._cache_valid[key_val] = False

                # Update timestamps more efficiently in batch
                ts_dict = self.timestamps[key_val]
                if len(ts_dict["times"]) == 0:
                    # Initialize arrays
                    ts_dict["times"] = np.array([current_time])
                    ts_dict["values"] = np.array([alpha / (alpha + beta)])
                else:
                    # Append to existing arrays
                    ts_dict["times"] = np.append(ts_dict["times"], current_time)
                    ts_dict["values"] = np.append(
                        ts_dict["values"], alpha / (alpha + beta)
                    )

            if self.stats_enabled:
                self.performance_stats["batch_operations"] += 1.0
                self.performance_stats["batch_updates"] += float(len(results))

    def add_pending_update(self, key: str, success: bool, weight: float = 1.0):
        """
        Add an update to the pending batch without immediately processing it.
        Useful for high-throughput scenarios during training.

        Args:
            key (str): Rule or variable identifier.
            success (bool): Outcome (True=success, False=failure).
            weight (float): Weight of the observation (default=1.0).
        """
        with self.lock:
            self._pending_updates.append((key, success, weight))
            if len(self._pending_updates) >= self.batch_size:
                self._process_pending_updates()

    def _process_pending_updates(self):
        """Process all pending updates in an efficient batch."""
        with self.lock:
            if not self._pending_updates:
                return

            # Group by key for more efficient processing
            updates_by_key = defaultdict(list)
            for key, success, weight in self._pending_updates:
                updates_by_key[key].append((success, weight))

            # Process each key's updates in batch
            for key, key_updates in updates_by_key.items():
                alpha, beta = self.stats[key]

                # Calculate total alpha and beta increments
                alpha_increment = sum(
                    weight for success, weight in key_updates if success
                )
                beta_increment = sum(
                    weight for success, weight in key_updates if not success
                )

                # Update in one operation
                alpha += alpha_increment
                beta += beta_increment
                self.stats[key] = (alpha, beta)

                # Update timestamp with latest time only
                current_time = time.time()
                self.last_update[key] = current_time

                # Add final trust value to timestamps
                trust = alpha / (alpha + beta)
                ts_dict = self.timestamps[key]
                ts_dict["times"] = np.append(ts_dict["times"], current_time)
                ts_dict["values"] = np.append(ts_dict["values"], trust)

                # Invalidate cache
                self._cache_valid[key] = False

            # Clear pending updates
            self._pending_updates = []

    def apply_decay(self, key: str, decay_factor: float = 0.99, min_count: int = 5):
        """
        Apply time decay to reduce certainty of old observations.
        Optimized implementation with cache invalidation.

        Args:
            key: Key to apply decay to
            decay_factor: How much to preserve (0.99 = 99% preserved)
            min_count: Minimum count to maintain after decay
        """
        with self.lock:
            if key in self.stats:
                alpha, beta = self.stats[key]
                if alpha + beta > min_count:
                    alpha = max(1.0, alpha * decay_factor)
                    beta = max(1.0, beta * decay_factor)
                    self.stats[key] = (alpha, beta)
                    self._cache_valid[key] = False

    def apply_global_decay(self, decay_factor: float = 0.99, min_count: int = 5):
        """
        Apply decay to all tracked entities in batch.
        Optimized with single lock acquisition for all entities.
        """
        with self.lock:
            # Process all keys in one lock
            keys_to_update = list(self.stats.keys())
            for key in keys_to_update:
                alpha, beta = self.stats[key]
                if alpha + beta > min_count:
                    alpha = max(1.0, alpha * decay_factor)
                    beta = max(1.0, beta * decay_factor)
                    self.stats[key] = (alpha, beta)
                    self._cache_valid[key] = False

    @lru_cache(maxsize=1024)
    def get_trust(self, key: str) -> float:
        """
        Returns the mean trust/confidence for a rule/variable.
        Uses caching for frequently accessed values.
        """
        # Check cache first
        if self._cache_valid.get(key, False) and key in self._trust_cache:
            if self.stats_enabled:
                self.performance_stats["cache_hits"] += 1
            return self._trust_cache[key]

        # Cache miss
        if self.stats_enabled:
            self.performance_stats["cache_misses"] += 1

        alpha, beta = self.stats.get(key, (1.0, 1.0))
        trust = alpha / (alpha + beta)

        # Update cache
        self._trust_cache[key] = trust
        self._cache_valid[key] = True

        return trust

    def get_trust_batch(self, keys: List[str]) -> Dict[str, float]:
        """
        Efficiently get trust values for multiple keys at once.

        Args:
            keys: List of keys to get trust for

        Returns:
            Dictionary mapping keys to trust values
        """
        results = {}
        with self.lock:
            for key in keys:
                # Check cache first
                if self._cache_valid.get(key, False) and key in self._trust_cache:
                    results[key] = self._trust_cache[key]
                    if self.stats_enabled:
                        self.performance_stats["cache_hits"] += 1
                else:
                    # Cache miss
                    if self.stats_enabled:
                        self.performance_stats["cache_misses"] += 1

                    alpha, beta = self.stats.get(key, (1.0, 1.0))
                    trust = alpha / (alpha + beta)

                    # Update cache
                    self._trust_cache[key] = trust
                    self._cache_valid[key] = True
                    results[key] = trust

        return results

    def get_confidence_interval(self, key: str, z: float = 1.96) -> Tuple[float, float]:
        """
        Returns a confidence interval for the trust estimate.
        Optimized to minimize square root calculations.

        Args:
            z (float): Z-score for confidence level (default 1.96 for 95%).
        """
        alpha, beta = self.stats.get(key, (1.0, 1.0))
        n = alpha + beta
        p = alpha / n
        se = (p * (1 - p) / n) ** 0.5
        return max(0.0, p - z * se), min(1.0, p + z * se)

    def get_confidence_interval_batch(
        self, keys: List[str], z: float = 1.96
    ) -> Dict[str, Tuple[float, float]]:
        """
        Get confidence intervals for multiple keys efficiently.

        Args:
            keys: List of keys to get intervals for
            z: Z-score for confidence level

        Returns:
            Dictionary mapping keys to confidence interval tuples
        """
        results = {}
        with self.lock:
            for key in keys:
                alpha, beta = self.stats.get(key, (1.0, 1.0))
                n = alpha + beta
                p = alpha / n
                se = (p * (1 - p) / n) ** 0.5
                results[key] = (max(0.0, p - z * se), min(1.0, p + z * se))

        return results

    def get_stats(self, key: str) -> Tuple[float, float]:
        """Get raw alpha/beta values."""
        return self.stats.get(key, (1.0, 1.0))

    def get_sample_size(self, key: str) -> int:
        """Get total number of observations."""
        alpha, beta = self.stats.get(key, (1.0, 1.0))
        return int(alpha + beta - 2)  # Subtract prior

    def get_confidence_strength(self, key: str) -> float:
        """
        Returns how confident we are in the trust estimate (0-1).
        Higher values mean more data points and narrower confidence intervals.
        """
        alpha, beta = self.stats.get(key, (1.0, 1.0))
        n = alpha + beta - 2  # Subtract prior
        return 1 / (1 + math.exp(-0.1 * (n - 10)))

    def get_time_since_update(self, key: str) -> float:
        """Get time in seconds since last update."""
        if key not in self.last_update:
            return float("inf")
        return time.time() - self.last_update[key]

    def export_to_file(self, filepath: str):
        """Export tracker state to a JSON file."""
        with self.lock:
            # Process any pending updates first
            if self._pending_updates:
                self._process_pending_updates()

            # Convert numpy arrays to lists for JSON serialization
            timestamps_json = {}
            for key, ts_dict in self.timestamps.items():
                timestamps_json[key] = {
                    "times": ts_dict["times"].tolist(),
                    "values": ts_dict["values"].tolist(),
                }

            data = {
                "stats": {k: list(v) for k, v in self.stats.items()},
                "last_update": dict(self.last_update),
                "timestamps": timestamps_json,
                "export_time": time.time(),
            }

            # Use a temporary file to avoid corruption if interrupted
            temp_filepath = filepath + ".tmp"
            with open(temp_filepath, "w") as f:
                json.dump(data, f)

            # Atomically replace the original file
            os.replace(temp_filepath, filepath)

    def import_from_file(self, filepath: str) -> bool:
        """Import tracker state from a JSON file."""
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            with self.lock:
                # Clear existing state
                self.stats = defaultdict(lambda: (1.0, 1.0))
                self.last_update = defaultdict(float)
                self.timestamps = defaultdict(
                    lambda: {
                        "times": np.array([], dtype=np.float64),
                        "values": np.array([], dtype=np.float64),
                    }
                )
                self._trust_cache = {}
                self._cache_valid = defaultdict(bool)

                # Import stats
                for k, v in data.get("stats", {}).items():
                    self.stats[k] = tuple(v)

                # Import last update times
                for k, v in data.get("last_update", {}).items():
                    self.last_update[k] = v

                # Import timestamps (convert lists to numpy arrays)
                for k, ts_data in data.get("timestamps", {}).items():
                    if (
                        isinstance(ts_data, dict)
                        and "times" in ts_data
                        and "values" in ts_data
                    ):
                        self.timestamps[k] = {
                            "times": np.array(ts_data["times"], dtype=np.float64),
                            "values": np.array(ts_data["values"], dtype=np.float64),
                        }
                    else:
                        # Handle older format (list of tuples)
                        times = []
                        values = []
                        for item in ts_data:
                            if isinstance(item, list) and len(item) == 2:
                                times.append(item[0])
                                values.append(item[1])

                        self.timestamps[k] = {
                            "times": np.array(times, dtype=np.float64),
                            "values": np.array(values, dtype=np.float64),
                        }

                # All cache entries are invalid after import
                self._cache_valid = defaultdict(bool)

            return True

        except Exception as e:
            print(f"Error importing trust data: {e}")
            return False

    def enable_performance_stats(self, enabled: bool = True):
        """
        Enable or disable collection of performance statistics.

        Args:
            enabled: Whether to enable statistics collection
        """
        self.stats_enabled = enabled
        if enabled:
            # Reset stats when enabling
            self.performance_stats = {
                "batch_operations": 0.0,
                "cache_hits": 0.0,
                "cache_misses": 0.0,
                "single_updates": 0.0,
                "batch_updates": 0.0,
            }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        with self.lock:
            stats = self.performance_stats.copy()

            # Add derived metrics
            if stats["cache_hits"] + stats["cache_misses"] > 0:
                stats["cache_hit_ratio"] = float(stats["cache_hits"]) / float(
                    stats["cache_hits"] + stats["cache_misses"]
                )
            else:
                # No type annotation issues when explicitly typed as float
                stats["cache_hit_ratio"] = 0.0

            return stats

    def reset_performance_stats(self):
        """Reset performance statistics."""
        with self.lock:
            self.performance_stats = {
                "batch_operations": 0.0,
                "cache_hits": 0.0,
                "cache_misses": 0.0,
                "single_updates": 0.0,
                "batch_updates": 0.0,
            }

    def purge_old_timestamps(self, max_history: int = 100):
        """
        Purge old timestamp entries to save memory.
        Keeps only the most recent max_history entries.

        Args:
            max_history: Maximum number of timestamp entries to keep
        """
        with self.lock:
            for key in self.timestamps:
                ts_dict = self.timestamps[key]
                if len(ts_dict["times"]) > max_history:
                    # Keep only the most recent entries
                    ts_dict["times"] = ts_dict["times"][-max_history:]
                    ts_dict["values"] = ts_dict["values"][-max_history:]


# Optimized singleton instance for global use
optimized_bayesian_trust_tracker = OptimizedBayesianTrustTracker()
