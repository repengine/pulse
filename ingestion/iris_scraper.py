"""
Iris Scraper (Signal Collector)

Main orchestration for:
- Running registered ingestion plugins
- Applying trust scoring (recency, anomaly, STI)
- Symbolic tagging (hope, despair, rage, fatigue, neutral)
- Exporting trusted signals to JSONL

Author: Pulse Development Team
Date: 2025-04-27
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ingestion.iris_trust import IrisTrustScorer
from ingestion.iris_symbolism import IrisSymbolismTagger
from ingestion.iris_plugins import IrisPluginManager
from ingestion.iris_archive import IrisArchive

logger = logging.getLogger(__name__)

SIGNAL_LOG_DIR = "data/iris_signals"
SIGNAL_LOG_FILE = os.path.join(SIGNAL_LOG_DIR, "signals_latest.jsonl")


class IrisScraper:
    def __init__(self):
        """
        Initialize the Iris Scraper (Signal Collector).
        """
        self.trust_engine = IrisTrustScorer()
        self.symbolism_engine = IrisSymbolismTagger()
        self.plugin_manager = IrisPluginManager()
        self.signal_log = []
        self.archive = IrisArchive()
        os.makedirs(SIGNAL_LOG_DIR, exist_ok=True)

    def ingest_signal(
        self, name: str, value: float, source: str, timestamp: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Ingest a single signal, apply trust and symbolism.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        recency_score = self.trust_engine.score_recency(timestamp)
        anomaly_flag = self.trust_engine.detect_anomaly_zscore(value)
        symbolic_tag = self.symbolism_engine.infer_symbolic_tag(name)
        sti = self.trust_engine.compute_signal_trust_index(recency_score, anomaly_flag)

        signal_record = {
            "name": name,
            "value": value,
            "source": source,
            "timestamp": timestamp.isoformat(),
            "symbolic_tag": symbolic_tag,
            "recency_score": round(recency_score, 3),
            "anomaly_flag": anomaly_flag,
            "sti": sti,
        }

        self.signal_log.append(signal_record)
        self.archive.append_signal(signal_record)  # <-- NEW line
        return signal_record

    def batch_ingest_from_plugins(self) -> None:
        """
        Ingest signals from all registered plugins.
        """
        plugin_signals = self.plugin_manager.run_plugins()
        for sig in plugin_signals:
            try:
                name = sig.get("name")
                value = sig.get("value")
                if name is None or value is None:
                    logger.error(
                        "[IrisScraper] Signal missing required 'name' or 'value': %s",
                        sig,
                    )
                    continue
                self.ingest_signal(
                    name=name,
                    value=value,
                    source=sig.get("source", "plugin"),
                    timestamp=sig.get("timestamp"),
                )
            except Exception as e:
                logger.error("[IrisScraper] Failed to ingest plugin signal: %s", e)

    def export_signal_log(self) -> str:
        """
        Export collected signals to disk.

        Returns:
            str: Path to saved signal file.
        """
        with open(SIGNAL_LOG_FILE, "w", encoding="utf-8") as f:
            for record in self.signal_log:
                f.write(json.dumps(record) + "\n")
        logger.info("[IrisScraper] Signal log exported to %s", SIGNAL_LOG_FILE)
        return SIGNAL_LOG_FILE

    def reset_signal_log(self) -> None:
        """
        Clear the internal signal memory.
        """
        self.signal_log = []


# Example CLI usage (for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    iris = IrisScraper()

    # Dummy plugin for testing
    def dummy_plugin():
        return [
            {"name": "trust_rebound", "value": 0.8, "source": "mock_plugin"},
            {"name": "despair_spike", "value": 0.3, "source": "mock_plugin"},
        ]

    iris = IrisScraper()
    iris.plugin_manager.autoload()  # <- new line
    iris.batch_ingest_from_plugins()
