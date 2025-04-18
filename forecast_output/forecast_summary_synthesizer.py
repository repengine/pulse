"""
Module: forecast_summary_synthesizer.py
Pulse Version: v0.015.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Synthesizes strategic summaries from forecast clusters or raw forecast sets.
Extracts symbolic drivers, ranks by confidence, and compresses into human-readable summary outputs.

Inputs:
- List[Dict]: Each dict is a forecast (must include 'confidence', 'symbolic_tag', optional 'drivers')

Outputs:
- Summarized JSONL per forecast
- Optional printout or interactive use

Used by:
- forecast_compressor.py
- Pulse CLI
- Strategos Digest
- PFPA Loggers

Log Output:
- logs/forecast_summary_log.jsonl
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime

SUMMARY_LOG_PATH = "logs/forecast_summary_log.jsonl"

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def summarize_forecasts(forecasts: List[Dict], method: str = "default", log_path: Optional[str] = None) -> List[Dict]:
    """
    Generate a human-readable summary of each forecast.
    Returns a list of summary dicts and writes them to log.
    """
    if not forecasts:
        return []

    path = log_path or SUMMARY_LOG_PATH
    ensure_log_dir(path)

    summaries = []
    for i, f in enumerate(forecasts):
        conf = f.get("confidence", 0.5)
        tag = f.get("symbolic_tag", "unlabeled")
        drivers = f.get("drivers", ["unknown"])
        scenario = {
            "summary": f"Scenario {i+1}: {tag} scenario driven by {', '.join(drivers)}.",
            "confidence": round(conf, 4),
            "symbolic_tag": tag,
            "drivers": drivers,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "version": "v0.015.0",
                "source": "pulse/forecast_output/forecast_summary_synthesizer.py"
            }
        }
        summaries.append(scenario)

        try:
            with open(path, "a") as f:
                f.write(json.dumps(scenario) + "\n")
        except Exception as e:
            print(f"[SummarySynthesizer] Logging error: {e}")

    return summaries

# Example usage
if __name__ == "__main__":
    sample_forecasts = [
        {"confidence": 0.78, "symbolic_tag": "Hope Rising", "drivers": ["AI policy", "VIX drop"]},
        {"confidence": 0.52, "symbolic_tag": "Fatigue Plateau", "drivers": ["media overload", "macro stability"]}
    ]
    summaries = summarize_forecasts(sample_forecasts)
    for s in summaries:
        print(s["summary"], "| Confidence:", s["confidence"])
