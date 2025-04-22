# forecast_memory/forecast_memory_promoter.py

"""
Forecast Memory Promoter

Selects certified, trust-approved, and fork-winning forecasts
for final memory retention.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import List, Dict

MEMORY_PATH = "memory/core_forecast_memory.jsonl"

logger = logging.getLogger("forecast_memory_promoter")
logging.basicConfig(level=logging.INFO)

def select_promotable_forecasts(forecasts) -> List[Dict]:
    """
    Select forecasts with full trust alignment.

    Criteria:
    - certified: True
    - license_status: ✅ Approved
    - trust_label: 🟢 Trusted
    - fork_winner: True (optional)

    Returns:
        List[Dict]
    """
    # Accept ForecastMemory or list
    if hasattr(forecasts, "_memory"):
        forecasts = forecasts._memory

    selected = []
    for fc in forecasts:
        if (
            fc.get("certified") is True and
            fc.get("license_status") == "✅ Approved" and
            fc.get("trust_label") == "🟢 Trusted" and
            not fc.get("symbolic_fragmented") and
            fc.get("alignment_score", 0) >= 75
        ):
            if fc.get("fork_winner") or fc.get("confidence", 0) > 0.85:
                selected.append(fc)
    return selected


def export_promoted(forecasts: List[Dict], path: str = MEMORY_PATH):
    """Save selected forecasts to memory file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            for fc in forecasts:
                f.write(json.dumps(fc, ensure_ascii=False) + "\n")
        logger.info(f"✅ Promoted {len(forecasts)} forecasts to memory: {path}")
    except Exception as e:
        logger.error(f"❌ Memory promotion failed: {e}")


def _test_forecast_memory_promoter():
    dummy = [
        {"certified": True, "license_status": "✅ Approved", "trust_label": "🟢 Trusted", "symbolic_fragmented": False, "alignment_score": 80, "fork_winner": True, "confidence": 0.9},
        {"certified": False, "license_status": "✅ Approved", "trust_label": "🟢 Trusted", "symbolic_fragmented": False, "alignment_score": 80, "fork_winner": True, "confidence": 0.9},
    ]
    selected = select_promotable_forecasts(dummy)
    assert len(selected) == 1
    logger.info("✅ Forecast memory promoter test passed.")


if __name__ == "__main__":
    _test_forecast_memory_promoter()
