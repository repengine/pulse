# trust_system/alignment_index.py
"""
Pulse Forecast Alignment Index (FAI)

Calculates an overall alignment score per forecast using:
- Confidence
- Retrodiction score (1 - error)
- Arc stability (1 - volatility)
- Symbolic tag match
- Novelty score (vs memory)

Returns normalized score (0–100) per forecast with breakdown.

Author: Pulse AI Engine
Version: v1.0.1
"""

from typing import Dict, Optional


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Ensure component weights sum to 1.0.
    """
    total = sum(weights.values())
    return weights if total == 0 else {k: v / total for k, v in weights.items()}


def compute_alignment_index(
    forecast: Dict,
    current_state: Optional[Dict] = None,
    memory: Optional[list] = None,
    arc_volatility: Optional[float] = None,
    tag_match: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Compute the alignment index for a given forecast.

    Args:
        forecast (Dict): Forecast dictionary.
        current_state (Optional[Dict]): Current worldstate (optional).
        memory (Optional[list]): List of previous forecasts (optional).
        arc_volatility (Optional[float]): Precomputed volatility (optional).
        weights (Optional[Dict[str, float]]): Custom weights for components.

    Returns:
        Dict[str, float]: {
            "alignment_score": float (0-100),
            "components": Dict[str, float]
        }
    """
    # Default weights
    default_weights = {
        "confidence": 0.3,
        "retrodiction": 0.2,
        "arc_stability": 0.2,
        "tag_match": 0.15,
        "novelty": 0.15
    }
    weights = normalize_weights(weights or default_weights)

    # --- Confidence ---
    confidence = forecast.get("confidence", 0.0)
    if not isinstance(confidence, (float, int)):
        confidence = 0.0
    confidence = max(0.0, min(float(confidence), 1.0))

    # --- Retrodiction Score ---
    try:
        if "retrodiction_score" in forecast:
            retrodiction = forecast["retrodiction_score"]
        elif current_state is not None:
            from learning.learning import compute_retrodiction_error  # moved import here to avoid circular import
            retrodiction = 1.0 - compute_retrodiction_error(forecast, current_state)
        else:
            retrodiction = 0.0
        if not isinstance(retrodiction, (float, int)):
            retrodiction = 0.0
        retrodiction = max(0.0, min(float(retrodiction), 1.0))
    except Exception:
        retrodiction = 0.0

    # --- Arc Stability ---
    try:
        if arc_volatility is not None:
            arc_stability = 1.0 - min(max(arc_volatility, 0.0), 1.0)
        elif "arc_volatility_score" in forecast:
            arc_stability = 1.0 - min(max(forecast["arc_volatility_score"], 0.0), 1.0)
        else:
            arc_stability = 0.0
        arc_stability = max(0.0, min(float(arc_stability), 1.0))
    except Exception:
        arc_stability = 0.0

    # --- Tag Match ---
    try:
        if tag_match is None:
            tag = forecast.get("symbolic_tag", "").lower()
            trusted_tags = {"hope", "trust", "recovery", "neutral"}
            tag_match_val = 1.0 if tag in trusted_tags else 0.0
        else:
            tag_match_val = float(tag_match)
        tag_match_val = max(0.0, min(tag_match_val, 1.0))
    except Exception:
        tag_match_val = 0.0

    # --- Novelty Score ---
    try:
        novelty = 1.0
        if memory and isinstance(memory, list):
            tag = forecast.get("symbolic_tag", "").lower()
            tags = [f.get("symbolic_tag", "").lower() for f in memory if isinstance(f, dict)]
            novelty = 1.0 - (tags.count(tag) / max(1, len(tags)))
            novelty = max(0.0, min(novelty, 1.0))
    except Exception:
        novelty = 1.0

    # --- Weighted sum ---
    components = {
        "confidence": confidence,
        "retrodiction": retrodiction,
        "arc_stability": arc_stability,
        "tag_match": tag_match_val,
        "novelty": novelty
    }
    alignment_score = sum(components[k] * weights[k] for k in components)
    alignment_score = round(alignment_score * 100, 2)  # 0-100 scale

    return {
        "alignment_score": alignment_score,
        "components": components,
        "forecast_id": forecast.get("trace_id")
    }

# --- Simple test ---
if __name__ == "__main__":
    # Minimal test for interpretability
    test_forecast = {
        "confidence": 0.85,
        "retrodiction_score": 0.9,
        "arc_volatility_score": 0.1,
        "symbolic_tag": "Hope"
    }
    result = compute_alignment_index(test_forecast)
    print("Alignment Score:", result["alignment_score"])
    print("Components:", result["components"])
