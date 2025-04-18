"""
forecast_summary_synthesizer.py

Generates strategic summaries from compressed forecast batches.
Summarizes symbolic trajectory, drivers, confidence, and fragility.
"""

from typing import List, Dict
from core.forecast_tags import FORECAST_TAGS

def synthesize_forecast_summary(compressed_forecasts: List[Dict]) -> Dict:
    """
    Synthesizes a high-level summary from a list of compressed forecast outputs.

    Args:
        compressed_forecasts (List[Dict]): A list of compressed forecast outputs.

    Returns:
        Dict: A dictionary summary including dominant trajectory, drivers, and metrics.
    """

    if not compressed_forecasts:
        return {
            "summary": "No forecasts to summarize.",
            "top_trajectory": None,
            "top_driver": None,
            "average_confidence": 0.0,
            "fragility_level": "Unknown"
        }

    # Count symbolic trajectory occurrences
    trajectory_counts = {}
    driver_counts = {}
    confidences = []

    for forecast in compressed_forecasts:
        traj = forecast.get(FORECAST_TAGS["SYMBOLIC_TRAJECTORY"], "unknown")
        trajectory_counts[traj] = trajectory_counts.get(traj, 0) + 1

        driver = forecast.get(FORECAST_TAGS["TOP_DRIVER"], "unknown")
        driver_counts[driver] = driver_counts.get(driver, 0) + 1

        conf = forecast.get(FORECAST_TAGS["CONFIDENCE"], 0.0)
        confidences.append(conf)

    top_trajectory = max(trajectory_counts, key=trajectory_counts.get)
    top_driver = max(driver_counts, key=driver_counts.get)
    avg_conf = sum(confidences) / len(confidences)

    # Determine fragility
    fragility_level = "Low"
    if avg_conf < 0.5:
        fragility_level = "High"
    elif avg_conf < 0.75:
        fragility_level = "Moderate"

    return {
        "summary": f"Most forecasts follow the {top_trajectory} path with {top_driver} as top driver.",
        "top_trajectory": top_trajectory,
        "top_driver": top_driver,
        "average_confidence": round(avg_conf, 3),
        "fragility_level": fragility_level
    }