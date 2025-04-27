"""
Iris Trust Engine

Handles signal trust scoring:
- Recency scoring
- Anomaly detection (Isolation Forest + Z-Score)
- Signal Trust Index (STI) calculation

Author: Pulse Development Team
Date: 2025-04-27
"""

import numpy as np
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest
from typing import List, Optional

class IrisTrustScorer:
    def __init__(self):
        """
        Initialize the Iris Trust Engine.
        """
        self.zscore_window: List[float] = []
        self.anomaly_model = IsolationForest(contamination=0.1, random_state=42)

    def score_recency(self, timestamp: datetime) -> float:
        """
        Score how fresh a signal is.

        Args:
            timestamp (datetime): Signal timestamp.

        Returns:
            float: Recency score (0.0 = stale, 1.0 = fresh).
        """
        now = datetime.now(timezone.utc)
        delta_seconds = (now - timestamp).total_seconds()
        max_age = 7 * 24 * 3600  # 7 days
        return max(0.0, min(1.0, 1.0 - delta_seconds / max_age))

    def detect_anomaly_isolation(self, value: float) -> bool:
        """
        Detect anomalies using Isolation Forest on recent window.

        Args:
            value (float): New signal value.

        Returns:
            bool: True if anomalous.
        """
        try:
            window = np.array(self.zscore_window[-100:] + [value]).reshape(-1, 1)
            self.anomaly_model.fit(window)
            prediction = self.anomaly_model.predict([[value]])
            return prediction[0] == -1
        except Exception:
            return False  # Fail safe: no anomaly

    def detect_anomaly_zscore(self, value: float) -> bool:
        """
        Detect anomalies using z-score threshold.

        Args:
            value (float): New signal value.

        Returns:
            bool: True if anomalous.
        """
        self.zscore_window.append(value)
        if len(self.zscore_window) < 10:
            return False
        if len(self.zscore_window) > 50:
            self.zscore_window = self.zscore_window[-50:]

        mean = np.mean(self.zscore_window)
        std = np.std(self.zscore_window) + 1e-6  # Avoid division by zero
        z = (value - mean) / std
        return bool(abs(z) > 3.0)

    def compute_signal_trust_index(self, recency_score: float, anomaly_flag: bool) -> float:
        """
        Compute the Signal Trust Index (STI).

        Args:
            recency_score (float): Freshness score.
            anomaly_flag (bool): Whether the signal is anomalous.

        Returns:
            float: STI (0.0 to 1.0 scale).
        """
        base = 0.6
        recency_boost = 0.3 * recency_score
        anomaly_penalty = -0.2 if anomaly_flag else 0.0
        sti = base + recency_boost + anomaly_penalty
        return round(max(0.0, min(1.0, sti)), 3)
