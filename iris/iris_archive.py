"""
Iris Signal Archive

Append-only storage for incoming signals.
Supports long-term historical memory, symbolic volatility tracking, and trust retrospection.

Author: Pulse Development Team
Date: 2025-04-27
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

ARCHIVE_DIR = "data/iris_archive"
ARCHIVE_FILE = os.path.join(ARCHIVE_DIR, "signals_archive.jsonl")

class IrisArchive:
    def __init__(self):
        """
        Initialize the Iris Archive.
        """
        os.makedirs(ARCHIVE_DIR, exist_ok=True)

    def append_signal(self, signal_record: Dict[str, Any]) -> None:
        """
        Append a single signal to the archive.

        Args:
            signal_record (Dict): Full processed signal (with STI, symbolic tag, timestamp, etc).
        """
        try:
            with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(signal_record) + "\n")
            logger.info("[IrisArchive] Appended signal to archive: %s", signal_record.get("name", "unknown"))
        except Exception as e:
            logger.error("[IrisArchive] Failed to append signal: %s", e)

    def load_archive(self) -> list:
        """
        Load full historical signal archive (memory intensive for very large archives).

        Returns:
            List[Dict]: All signals stored historically.
        """
        signals = []
        try:
            if os.path.exists(ARCHIVE_FILE):
                with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                    signals.extend([json.loads(line) for line in f])
        except Exception as e:
            logger.error("[IrisArchive] Failed to load archive: %s", e)
        return signals

    def count_signals(self) -> int:
        """
        Count how many signals are stored.

        Returns:
            int: Total signal count.
        """
        try:
            if not os.path.exists(ARCHIVE_FILE):
                return 0
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

# Example CLI usage (for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    archive = IrisArchive()

    # Dummy append
    test_signal = {
        "name": "hope_resurgence",
        "value": 0.85,
        "source": "mock_plugin",
        "timestamp": "2025-04-27T00:00:00Z",
        "symbolic_tag": "hope",
        "recency_score": 0.99,
        "anomaly_flag": False,
        "sti": 0.93
    }
    archive.append_signal(test_signal)
    total = archive.count_signals()
    print(f"✅ Total signals archived: {total}")
