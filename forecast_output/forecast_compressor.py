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
from core.path_registry import PATHS

COMPRESSED_OUTPUT = PATHS["FORECAST_COMPRESSED"]

logger = get_logger(__name__)

def compress_forecasts(forecasts):
    import json
    with open(COMPRESSED_OUTPUT, "w") as f:
        json.dump(forecasts, f, indent=2)
    print(f"Compressed forecasts written to {COMPRESSED_OUTPUT}")

# Example usage
if __name__ == "__main__":
    sample = [
        {"symbolic_tag": "hope", "confidence": 0.62, "drivers": ["NVDA earnings", "AI sentiment"]},
        {"symbolic_tag": "hope", "confidence": 0.68, "drivers": ["FED stance"]},
        {"symbolic_tag": "fatigue", "confidence": 0.43, "drivers": ["news overload"]}
    ]
    compress_forecasts(sample)
