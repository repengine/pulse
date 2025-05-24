# pulse/tools/pulse_forecast_evaluator.py
"""
Module: pulse_forecast_evaluator.py
Purpose: Evaluate Pulse forecast trace accuracy against real-world event trace.

Compares:
- Variable trajectories (forecast vs real)
- Symbolic tag sequence alignment
- Retrodiction-style overlay divergence

Outputs a CLI-readable and optionally exportable accuracy summary.
Author: Pulse AI Engine
Version: v0.5.2
"""

import argparse
import json
import os
from typing import List, Dict


def load_trace(path: str) -> List[Dict]:
    """
    Load a .jsonl trace file from disk.

    Parameters:
        path (str): path to .jsonl file

    Returns:
        List of parsed forecast or real trace steps (as dicts)
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing trace file: {path}")
        with open(path, "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load trace from {path}: {e}")
        return []


def mse_forecast_vs_real(
    real: List[Dict], forecast: List[Dict], key: str, mode: str = "variables"
) -> float:
    """
    Compute mean squared error between variable/overlay values over time.

    Parameters:
        real (List[Dict]): list of true historical state entries
        forecast (List[Dict]): list of Pulse forecast entries
        key (str): the variable or overlay to compare
        mode (str): "variables" or "overlays"

    Returns:
        float: mean squared error (MSE) across aligned steps
    """
    values = []
    for i in range(min(len(real), len(forecast))):
        r_val = real[i].get(mode, {}).get(key)
        f_val = forecast[i].get(mode, {}).get(key)
        if isinstance(r_val, (int, float)) and isinstance(f_val, (int, float)):
            values.append((r_val - f_val) ** 2)
    print(f"🔍 MSE samples used: {len(values)}")
    return round(sum(values) / len(values), 4) if values else -1.0


def tag_alignment_score(real: List[Dict], forecast: List[Dict]) -> float:
    """
    Return percentage of stepwise tag alignment between real and forecast traces.

    Parameters:
        real (List[Dict]): list of true history entries with symbolic tags
        forecast (List[Dict]): list of forecast entries with symbolic tags

    Returns:
        float: percentage match of tags (0–100)
    """
    matches = 0
    mismatches = []
    total = min(len(real), len(forecast))
    for i in range(total):
        rt = real[i].get("symbolic_tag")
        ft = forecast[i].get("symbolic_tag")
        if rt == ft:
            matches += 1
        else:
            mismatches.append((i, rt, ft))
    print(f"🔍 Tag alignment: {matches}/{total} matched")
    return round((matches / total) * 100, 2) if total else 0.0


def evaluate_forecast(
    real_path: str, forecast_path: str, variable: str = "hope", mode: str = "overlays"
) -> Dict:
    """
    Perform overall comparison and score forecast accuracy.

    Returns:
        Dict: summary with MSE and tag match rate
    """
    real = load_trace(real_path)
    forecast = load_trace(forecast_path)
    return {
        "mse_variable": mse_forecast_vs_real(real, forecast, key=variable, mode=mode),
        "tag_alignment_percent": tag_alignment_score(real, forecast),
        "steps_compared": min(len(real), len(forecast)),
    }


def main():
    parser = argparse.ArgumentParser(description="Pulse Forecast Evaluator")
    parser.add_argument(
        "--real", required=True, help="Path to real world trace (.jsonl)"
    )
    parser.add_argument(
        "--forecast", required=True, help="Path to Pulse forecast trace (.jsonl)"
    )
    parser.add_argument(
        "--var",
        type=str,
        default="hope",
        help="Variable/overlay to compare (default: hope)",
    )
    parser.add_argument(
        "--mode",
        choices=["variables", "overlays"],
        default="overlays",
        help="Data mode",
    )
    parser.add_argument(
        "--export", type=str, help="Optional: path to save results (JSON)"
    )
    args = parser.parse_args()

    result = evaluate_forecast(
        args.real, args.forecast, variable=args.var, mode=args.mode
    )

    print("\n📊 Forecast Evaluation Summary:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    if args.export:
        with open(args.export, "w") as f:
            json.dump(result, f, indent=2)
        print(f"📤 Exported summary to {args.export}")


if __name__ == "__main__":
    main()
