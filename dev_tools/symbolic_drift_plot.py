from typing import List, Dict
from trust_system.trust_engine import compute_symbolic_attention_score
import logging

logger = logging.getLogger("symbolic_drift_plot")


def flag_high_attention_forecasts(
    forecasts: List[Dict], arc_drift: Dict[str, int], threshold: float = 0.7
) -> List[Dict]:
    """
    Adds attention flags to forecasts based on symbolic drift volatility.

    Args:
        forecasts (List[Dict]): List of forecast dicts. Each must have 'arc_label'.
        arc_drift (Dict[str, int]): Drift delta by arc_label.
        threshold (float): Flag if score exceeds this.

    Returns:
        List[Dict]: Updated forecasts with 'attention_score' and 'attention_flag'.
    """
    if not isinstance(forecasts, list):
        logger.warning("Input 'forecasts' is not a list.")
        return []
    if not isinstance(arc_drift, dict):
        logger.warning("Input 'arc_drift' is not a dict.")
        return forecasts

    for fc in forecasts:
        try:
            score = compute_symbolic_attention_score(fc, arc_drift)
            fc["attention_score"] = score
            fc["attention_flag"] = (
                "🚨 High Attention" if score >= threshold else "✅ Stable"
            )
        except Exception as e:
            logger.warning(
                f"Failed to compute attention for forecast: {fc}. Error: {e}"
            )
            fc["attention_score"] = None
            fc["attention_flag"] = "⚠️ Error"
    return forecasts


if __name__ == "__main__":
    # Example/test usage
    test_forecasts = [
        {"arc_label": "Hope Surge"},
        {"arc_label": "Collapse Risk"},
        {"arc_label": "Unknown"},
    ]
    test_arc_drift = {"Hope Surge": 8, "Collapse Risk": 2}
    flagged = flag_high_attention_forecasts(test_forecasts, test_arc_drift)
    for f in flagged:
        print(f)
