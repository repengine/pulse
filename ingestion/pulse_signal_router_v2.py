"""
pulse_signal_router_v2.py (corrected)

Module Purpose:
- Ingest, tag, and route external signals into IRIS Core subsystems.
- Maintain signal metadata (timestamp, source, type).
- Interface with IrisSymbolism, IrisTrust, and IrisArchive modules.
- Enable modular future expansions (signal clustering, enrichment, prioritization).

Author: Pulse-IRIS Development Team
Version: 0.427A (Corrected)
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Corrected imports for actual IRIS Core
try:
    from ingestion.iris_symbolism import IrisSymbolismTagger
    from ingestion.iris_trust import IrisTrustScorer
    from ingestion.iris_archive import IrisArchive
except ImportError:
    from iris_symbolism import IrisSymbolismTagger
    from iris_trust import IrisTrustScorer
    from iris_archive import IrisArchive


class PulseSignalRouter:
    def __init__(
        self,
        symbolism_engine: IrisSymbolismTagger,
        trust_engine: IrisTrustScorer,
        archive_engine: IrisArchive,
    ) -> None:
        """
        Initialize the Pulse Signal Router with IRIS Core subsystem references.

        Args:
            symbolism_engine (IrisSymbolismTagger): Symbolic overlay manager.
            trust_engine (IrisTrustScorer): Trust scorer and monitor.
            archive_engine (IrisArchive): Signal archiver.
        """
        self.symbolism_engine = symbolism_engine
        self.trust_engine = trust_engine
        self.archive_engine = archive_engine

    def route_signal(self, signal: Dict[str, Any]) -> None:
        """
        Route an incoming signal to appropriate IRIS modules.

        Args:
            signal (Dict[str, Any]): Incoming signal with required fields:
                - 'type': symbolic, trust, etc.
                - 'payload': actual signal data
                - 'source': origin identifier (e.g., 'scraper_google_trends')
                - 'timestamp' (optional): fallback to now if missing

        Raises:
            ValueError: If required fields are missing.
        """
        required_keys = ["type", "payload", "source"]
        if not all(key in signal for key in required_keys):
            raise ValueError(
                f"Incoming signal missing required fields: {required_keys}"
            )

        signal_metadata = {
            "timestamp": signal.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            ),
            "source": signal["source"],
            "type": signal["type"],
        }

        signal_type = signal["type"].lower()
        signal_record = {**signal, **signal_metadata}

        if signal_type == "symbolic":
            # Use IrisSymbolismTagger to infer tag
            tag = self.symbolism_engine.infer_symbolic_tag(str(signal["payload"]))
            signal_record["symbolic_tag"] = tag
            self.archive_engine.append_signal(signal_record)
        elif signal_type == "trust":
            # Use IrisTrustScorer to compute trust metrics
            payload = signal["payload"]
            value = payload.get("value", 0.0)
            timestamp = signal.get("timestamp", datetime.now(timezone.utc).isoformat())
            try:
                ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
            recency_score = self.trust_engine.score_recency(ts)
            anomaly_flag = self.trust_engine.detect_anomaly_isolation(value)
            sti = self.trust_engine.compute_signal_trust_index(
                recency_score, anomaly_flag
            )
            signal_record["recency_score"] = recency_score
            signal_record["anomaly_flag"] = anomaly_flag
            signal_record["sti"] = sti
            self.archive_engine.append_signal(signal_record)
        else:
            self.archive_engine.append_signal(signal_record)
            print(
                f"[PulseSignalRouter] Unhandled signal type: {signal_type}. Archived only."
            )

    def batch_route(self, signals: list) -> None:
        """
        Process a batch of incoming signals.

        Args:
            signals (list): List of signal dicts.
        """
        for signal in signals:
            try:
                self.route_signal(signal)
            except Exception as e:
                print(f"[PulseSignalRouter] Error processing signal: {e}")


# Usage Example
if __name__ == "__main__":
    symbolism = IrisSymbolismTagger()
    trust = IrisTrustScorer()
    archive = IrisArchive()

    router = PulseSignalRouter(symbolism, trust, archive)

    incoming_signal = {
        "type": "symbolic",
        "payload": "hope resurgence",
        "source": "scraper_google_trends",
    }

    router.route_signal(incoming_signal)
