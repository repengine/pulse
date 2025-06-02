"""
pulse_forecast_test_suite.py

Validates saved forecast files for:
- Presence of required metadata (confidence, fragility, symbolic driver)
- Structural integrity
- Output report written to /forecast_output/tests/forecast_audit_summary.json

Author: Pulse v0.10
"""

import os
import json
import argparse
from datetime import datetime
from utils.log_utils import get_logger
from engine.path_registry import PATHS

logger = get_logger(__name__)

FORECAST_DIR = PATHS["FORECAST_HISTORY"]
SUMMARY_FILE = PATHS["BATCH_FORECAST_SUMMARY"]
OUTPUT_DIR = PATHS["FORECAST_TEST_OUTPUT"]


def validate_forecast(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            meta = data.get("metadata", {})
            confidence = meta.get("confidence")
            fragility = meta.get("fragility")
            symbolic = meta.get("symbolic_driver")

            return {
                "file": os.path.basename(file_path),
                "valid": (
                    confidence is not None
                    and fragility is not None
                    and symbolic not in (None, "None", "")
                ),
                "confidence": confidence,
                "fragility": fragility,
                "symbolic_driver": symbolic,
            }
    except Exception as e:
        return {"file": os.path.basename(file_path), "valid": False, "error": str(e)}


def run_forecast_validation(log_dir=FORECAST_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    forecasts = [
        f
        for f in os.listdir(log_dir)
        if f.endswith(".json") and not f.startswith("test")
    ]
    results = []

    for file in forecasts:
        result = validate_forecast(os.path.join(log_dir, file))
        if not result.get("valid"):
            logger.warning(
                f"Invalid forecast: {
                    result.get('file')} | Error: {
                    result.get(
                        'error',
                        'Unknown')}")
        results.append(result)

    summary = {
        "run_timestamp": datetime.now().isoformat(),
        "total_checked": len(results),
        "valid_forecasts": sum(1 for r in results if r["valid"]),
        "invalid_forecasts": sum(1 for r in results if not r["valid"]),
        "results": results,
    }

    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(
        f"✅ Forecast audit complete: {
            summary['valid_forecasts']} valid / {
            summary['total_checked']} total")
    print(f"📝 Summary written to {SUMMARY_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Forecast Audit Suite")
    parser.add_argument(
        "--log_dir",
        type=str,
        default="forecast_output",
        help="Path to directory of forecast logs",
    )
    args = parser.parse_args()
    run_forecast_validation(log_dir=args.log_dir)
