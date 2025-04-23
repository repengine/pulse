"""
scraper.py

Pulse Signal Intake Shell (Gated + PulseGrow-Enabled + Exportable)

This module collects external signals via plugins, scores and symbolically tags them,
and passes them through signal_gating. It also exports the full signal log
in a format compatible with output_data_reader.py.

Author: Pulse v0.308
"""

import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

try:
    from transformers import pipeline
    zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception:
    zero_shot = None

try:
    from learning.pulsegrow import PulseGrow
    pulse_grow = PulseGrow()
except Exception:
    pulse_grow = None

try:
    from learning.signal_gating import gate_signals
except Exception:
    gate_signals = None

logger = logging.getLogger(__name__)

SYMBOLIC_CATEGORIES = ["hope", "despair", "rage", "fatigue"]
SIGNAL_LOG_DIR = "data/signal_logs"
SIGNAL_LOG_FILE = os.path.join(SIGNAL_LOG_DIR, "signals_latest.json")

class SignalScraper:
    def __init__(self):
        self.signal_log = []
        self.plugins: List[Callable[[], List[Dict[str, float]]]] = []
        self.anomaly_model = IsolationForest(contamination=0.1, random_state=42)
        self.zscore_window = []

    def ingest_signal(self, name: str, value: float, source: str, timestamp: Optional[datetime] = None) -> Optional[Dict[str, float]]:
        if timestamp is None:
            timestamp = datetime.utcnow()

        recency_score = self._score_recency(timestamp)
        anomaly_flag = self._detect_anomaly_zscore(value)
        symbolic = self._infer_symbolic(name)

        log_entry = {
            "name": name,
            "value": value,
            "source": source,
            "timestamp": timestamp.isoformat(),
            "symbolic": symbolic,
            "recency_score": round(recency_score, 3),
            "anomaly": anomaly_flag,
            "sti": round(0.6 + 0.3 * recency_score - (0.2 if anomaly_flag else 0.0), 3)
        }

        if gate_signals:
            accepted, suppressed, escalated = gate_signals([log_entry])
            if accepted:
                self.signal_log.extend(accepted)
                return accepted[0]
            elif suppressed:
                logger.info("[Scraper] Signal suppressed by gate: %s", name)
                return None
            elif escalated:
                self.signal_log.extend(escalated)
                return escalated[0]
        else:
            self.signal_log.append(log_entry)

        if pulse_grow:
            try:
                pulse_grow.register_variable(name, metadata={
                    "source": source,
                    "inferred_symbolic": symbolic,
                    "initial_recency": recency_score
                })
            except Exception as e:
                logger.warning("[Scraper] PulseGrow registration failed for %s: %s", name, e)

        return log_entry

    def _score_recency(self, timestamp: datetime) -> float:
        age = (datetime.utcnow() - timestamp).total_seconds()
        tau = 86400.0
        return float(np.exp(-age / tau))

    def _detect_anomaly_zscore(self, value: float) -> bool:
        self.zscore_window.append(value)
        if len(self.zscore_window) < 10:
            return False
        if len(self.zscore_window) > 50:
            self.zscore_window = self.zscore_window[-50:]
        z = (value - np.mean(self.zscore_window)) / (np.std(self.zscore_window) + 1e-6)
        return abs(z) > 3.0

    def _infer_symbolic(self, name: str) -> Optional[str]:
        if zero_shot:
            try:
                result = zero_shot(name, SYMBOLIC_CATEGORIES)
                return result["labels"][0] if result["scores"][0] > 0.5 else None
            except Exception as e:
                logger.warning("[Scraper] Symbolic inference failed: %s", e)
        return None

    def export_log(self) -> pd.DataFrame:
        return pd.DataFrame(self.signal_log)

    def export_to_disk(self):
        os.makedirs(SIGNAL_LOG_DIR, exist_ok=True)
        try:
            with open(SIGNAL_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.signal_log, f, indent=2)
            logger.info("[Scraper] Signal log exported to %s", SIGNAL_LOG_FILE)
        except Exception as e:
            logger.error("[Scraper] Failed to write signal log: %s", e)

    def register_plugin(self, plugin_fn: Callable[[], List[Dict[str, float]]]):
        self.plugins.append(plugin_fn)
        logger.info("[Scraper] Plugin registered: %s", plugin_fn.__name__)

    def run_plugins(self):
        for plugin in self.plugins:
            try:
                results = plugin()
                for entry in results:
                    self.ingest_signal(
                        name=entry["name"],
                        value=entry["value"],
                        source=entry.get("source", "plugin"),
                        timestamp=entry.get("timestamp")
                    )
            except Exception as e:
                logger.error("[Scraper] Plugin %s failed: %s", plugin.__name__, e)

        self.export_to_disk()

def get_latest_signal_map() -> dict:
    """
    Return the most recent value for each signal as {var_name: value}.
    """
    latest = {}
    for entry in reversed(SignalScraper().signal_log):
        name = entry.get("name")
        value = entry.get("value")
        if name and name not in latest:
            latest[name] = value
    return latest
