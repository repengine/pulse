"""
PATCHED: forecast_compressor.py
Pulse Version: v0.21.2
Patch: Auto-calls forecast_summary_synthesizer after compressing clusters
"""

import json
import os
from typing import List, Dict, Optional

from forecast_output.forecast_summary_synthesizer import summarize_forecasts
from utils.log_utils import get_logger

logger = get_logger(__name__)

COMPRESSED_FORECAST_LOG = "logs/forecast_output_compressed.jsonl"

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def compress_forecasts(forecasts: List[Dict], method: str = "symbolic_average", log_path: Optional[str] = None) -> List[Dict]:
    if not forecasts or not isinstance(forecasts, list):
        raise ValueError("Input must be a non-empty list of forecast dicts.")

    path = log_path or COMPRESSED_FORECAST_LOG
    ensure_log_dir(path)

    clusters = {}
    for forecast in forecasts:
        tag = forecast.get("symbolic_tag", "unknown")
        clusters.setdefault(tag, []).append(forecast)

    compressed_output = []
    for tag, group in clusters.items():
        confidences = [f.get("confidence", 0.5) for f in group if isinstance(f.get("confidence"), (int, float))]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        summary = {
            "tag": tag,
            "count": len(group),
            "avg_confidence": round(avg_conf, 4),
            "examples": group[:2],
            "metadata": {
                "version": "v0.21.2",
                "compression_method": method,
                "source": "forecast_compressor.py"
            }
        }
        compressed_output.append(summary)
        try:
            with open(path, "a") as f:
                f.write(json.dumps(summary) + "\n")
        except Exception as e:
            logger.error(f"[ForecastCompressor] Error writing summary log: {e}")

    # NEW: Generate human-readable summaries automatically
    try:
        _ = summarize_forecasts(forecasts)
    except Exception as e:
        print(f"[ForecastCompressor] Summary synthesizer error: {e}")

    return compressed_output

# Example usage
if __name__ == "__main__":
    sample = [
        {"symbolic_tag": "hope", "confidence": 0.62, "drivers": ["NVDA earnings", "AI sentiment"]},
        {"symbolic_tag": "hope", "confidence": 0.68, "drivers": ["FED stance"]},
        {"symbolic_tag": "fatigue", "confidence": 0.43, "drivers": ["news overload"]}
    ]
    compress_forecasts(sample)
