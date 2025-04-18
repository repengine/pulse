"""
Module: forecast_confidence_gate.py
Pulse Version: v0.018.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Filters forecasts based on minimum trustworthiness thresholds.
Used to determine whether a foresight scenario is safe for display or action.

Inputs:
- List[Dict] forecasts or single forecast
- Confidence threshold (default 0.6)
- Optional fragility override

Outputs:
- List[Dict] of forecasts marked: "✅ Actionable", "⚠️ Risky", "❌ Rejected"

Log Output:
- logs/forecast_confidence_filter_log.jsonl
"""

import json
import os
from typing import List, Dict, Union
from datetime import datetime

CONFIDENCE_LOG_PATH = "logs/forecast_confidence_filter_log.jsonl"

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def filter_by_confidence(
    forecasts: Union[List[Dict], Dict],
    min_confidence: float = 0.6,
    max_fragility: float = 0.7
) -> List[Dict]:
    """
    Tags each forecast with confidence status based on trust threshold.
    """
    ensure_log_dir(CONFIDENCE_LOG_PATH)
    if isinstance(forecasts, dict):
        forecasts = [forecasts]

    output = []
    for f in forecasts:
        conf = f.get("confidence", 0.0)
        frag = f.get("fragility", 0.5)
        if conf >= min_confidence and frag < max_fragility:
            f["confidence_status"] = "✅ Actionable"
        elif conf >= 0.4:
            f["confidence_status"] = "⚠️ Risky"
        else:
            f["confidence_status"] = "❌ Rejected"

        try:
            with open(CONFIDENCE_LOG_PATH, "a") as log:
                log.write(json.dumps({
                    "trace_id": f.get("trace_id", "unknown"),
                    "confidence": conf,
                    "fragility": frag,
                    "status": f["confidence_status"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source": "forecast_confidence_gate.py",
                        "version": "v0.018.0"
                    }
                }) + "\n")
        except Exception as e:
            print(f"[ConfidenceGate] Log error: {e}")

        output.append(f)

    return output

# === Example usage
if __name__ == "__main__":
    test_batch = [
        {"trace_id": "fc001", "confidence": 0.78, "fragility": 0.3},
        {"trace_id": "fc002", "confidence": 0.53, "fragility": 0.6},
        {"trace_id": "fc003", "confidence": 0.39, "fragility": 0.2}
    ]
    tagged = filter_by_confidence(test_batch)
    for t in tagged:
        print(f"{t['trace_id']}: {t['confidence_status']}")
