"""
rule_audit_viewer.py

Displays symbolic and variable deltas caused by rules from a saved forecast file.

Author: Pulse v0.20
"""

import json
import argparse
from utils.log_utils import get_logger
from core.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

logger = get_logger(__name__)


def show_audit_from_forecast(forecast_path):
    with open(forecast_path, "r") as f:
        data = json.load(f)

    print(f"📄 Forecast ID: {data.get('forecast_id')}")
    metadata = data.get("metadata", {})
    print(
        f"Confidence: {metadata.get('confidence')} | Fragility: {metadata.get('fragility')}"
    )
    audit_log = metadata.get("rule_audit", [])

    print("\n🔍 Rule Audit Trail:")
    for entry in audit_log:
        print(f"• {entry['rule_id']} (tags: {entry['symbolic_tags']})")
        for var, delta in entry.get("variables_changed", {}).items():
            print(f"   Δ {var}: {delta['from']} → {delta['to']}")
        for ov, delta in entry.get("overlays_changed", {}).items():
            print(f"   Δ [overlay] {ov}: {delta['from']} → {delta['to']}")
        print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "forecast_file", help="Path to forecast JSON file with rule audit"
    )
    args = parser.parse_args()
    show_audit_from_forecast(args.forecast_file)
