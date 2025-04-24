"""
bayesian_trust_tracker.py

Tracks Bayesian trust/confidence for rules and variables using a Beta distribution.

Author: Pulse v0.32
"""

import threading
import json
import os
import time
from collections import defaultdict
from typing import Dict, Tuple, List, Any, Optional
import math

class BayesianTrustTracker:
    """
    Tracks successes and failures for each rule/variable and computes trust/confidence.
    Thread-safe for concurrent updates.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.stats: Dict[str, Tuple[int, int]] = defaultdict(lambda: (1, 1))  # (alpha, beta) priors
        self.last_update: Dict[str, float] = defaultdict(float)  # Track last update time
        self.timestamps: Dict[str, List[float]] = defaultdict(list)  # Track confidence over time

    def update(self, key: str, success: bool, weight: float = 1.0):
        """
        Update the Beta distribution for a rule/variable.
        Args:
            key (str): Rule or variable identifier.
            success (bool): Outcome (True=success, False=failure).
            weight (float): Weight of the observation (default=1.0).
        """
        with self.lock:
            alpha, beta = self.stats[key]
            if success:
                alpha += weight
            else:
                beta += weight
            self.stats[key] = (alpha, beta)
            current_time = time.time()
            self.last_update[key] = current_time
            self.timestamps[key].append((current_time, self.get_trust(key)))

    def batch_update(self, updates: Dict[str, List[Tuple[bool, float]]]):
        """
        Apply multiple updates at once.
        Args:
            updates: Dictionary mapping keys to lists of (success, weight) tuples.
        """
        with self.lock:
            for key, results in updates.items():
                alpha, beta = self.stats[key]
                for success, weight in results:
                    if success:
                        alpha += weight
                    else:
                        beta += weight
                self.stats[key] = (alpha, beta)
                current_time = time.time()
                self.last_update[key] = current_time
                self.timestamps[key].append((current_time, self.get_trust(key)))

    def apply_decay(self, key: str, decay_factor: float = 0.99, min_count: int = 5):
        """
        Apply time decay to reduce certainty of old observations.
        Args:
            key: Key to apply decay to
            decay_factor: How much to preserve (0.99 = 99% preserved)
            min_count: Minimum count to maintain after decay
        """
        with self.lock:
            if key in self.stats:
                alpha, beta = self.stats[key]
                if alpha + beta > min_count:
                    alpha = max(1, alpha * decay_factor)
                    beta = max(1, beta * decay_factor)
                    self.stats[key] = (alpha, beta)

    def apply_global_decay(self, decay_factor: float = 0.99, min_count: int = 5):
        """Apply decay to all tracked entities."""
        with self.lock:
            for key in list(self.stats.keys()):
                self.apply_decay(key, decay_factor, min_count)

    def get_trust(self, key: str) -> float:
        """
        Returns the mean trust/confidence for a rule/variable.
        """
        alpha, beta = self.stats.get(key, (1, 1))
        return alpha / (alpha + beta)

    def get_confidence_interval(self, key: str, z: float = 1.96) -> Tuple[float, float]:
        """
        Returns a confidence interval for the trust estimate.
        Args:
            z (float): Z-score for confidence level (default 1.96 for 95%).
        """
        alpha, beta = self.stats.get(key, (1, 1))
        n = alpha + beta
        p = alpha / n
        se = (p * (1 - p) / n) ** 0.5
        return max(0, p - z * se), min(1, p + z * se)

    def get_stats(self, key: str) -> Tuple[int, int]:
        """Get raw alpha/beta values."""
        return self.stats.get(key, (1, 1))

    def get_sample_size(self, key: str) -> int:
        """Get total number of observations."""
        alpha, beta = self.stats.get(key, (1, 1))
        return alpha + beta - 2  # Subtract prior

    def get_confidence_strength(self, key: str) -> float:
        """
        Returns how confident we are in the trust estimate (0-1).
        Higher values mean more data points and narrower confidence intervals.
        """
        alpha, beta = self.stats.get(key, (1, 1))
        n = alpha + beta - 2  # Subtract prior
        # Sigmoid function that grows with n
        return 1 / (1 + math.exp(-0.1 * (n - 10)))

    def get_time_since_update(self, key: str) -> float:
        """Get time in seconds since last update."""
        if key not in self.last_update:
            return float('inf')
        return time.time() - self.last_update[key]

    def export_to_file(self, filepath: str):
        """Export tracker state to a JSON file."""
        with self.lock:
            data = {
                "stats": {k: list(v) for k, v in self.stats.items()},
                "last_update": dict(self.last_update),
                "timestamps": dict(self.timestamps),
                "export_time": time.time()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f)

    def import_from_file(self, filepath: str) -> bool:
        """Import tracker state from a JSON file."""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            with self.lock:
                self.stats = defaultdict(lambda: (1, 1))
                for k, v in data.get("stats", {}).items():
                    self.stats[k] = tuple(v)
                self.last_update = defaultdict(float)
                for k, v in data.get("last_update", {}).items():
                    self.last_update[k] = v
                self.timestamps = defaultdict(list)
                for k, v in data.get("timestamps", {}).items():
                    self.timestamps[k] = v
            return True
        except Exception as e:
            print(f"Error importing trust data: {e}")
            return False

    def generate_report(self, min_sample_size: int = 5) -> Dict[str, Any]:
        """
        Generate a statistical report on tracked entities.
        Args:
            min_sample_size: Minimum samples to include in report
        """
        report = {
            "high_trust": [],
            "low_trust": [],
            "high_confidence": [],
            "low_confidence": [],
            "recently_updated": [],
            "stale": [],
            "summary": {}
        }
        
        with self.lock:
            # Generate lists
            for key, (alpha, beta) in self.stats.items():
                if alpha + beta - 2 < min_sample_size:
                    continue
                    
                trust = self.get_trust(key)
                confidence = self.get_confidence_strength(key)
                ci = self.get_confidence_interval(key)
                last_update = self.get_time_since_update(key)
                
                entry = {
                    "key": key,
                    "trust": trust,
                    "confidence": confidence,
                    "ci": ci,
                    "sample_size": alpha + beta - 2,
                    "last_update": last_update
                }
                
                if trust > 0.8:
                    report["high_trust"].append(entry)
                if trust < 0.2:
                    report["low_trust"].append(entry)
                if confidence > 0.8:
                    report["high_confidence"].append(entry)
                if confidence < 0.2:
                    report["low_confidence"].append(entry)
                if last_update < 3600:  # 1 hour
                    report["recently_updated"].append(entry)
                if last_update > 86400:  # 1 day
                    report["stale"].append(entry)
                    
            # Generate summary
            report["summary"] = {
                "total_entities": len(self.stats),
                "active_entities": sum(1 for k, v in self.stats.items() if v[0] + v[1] - 2 >= min_sample_size),
                "avg_trust": sum(self.get_trust(k) for k in self.stats) / max(1, len(self.stats)),
                "avg_confidence": sum(self.get_confidence_strength(k) for k in self.stats) / max(1, len(self.stats)),
            }
            
        return report

# Singleton instance
bayesian_trust_tracker = BayesianTrustTracker()
