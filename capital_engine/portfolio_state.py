"""
portfolio_state.py

Provides analytics and strategic labeling for current capital exposures in WorldState.
Supports total exposure calculation, percentage breakdowns, and symbolic alignment tags.

Author: Pulse v3.5

Thresholds for alignment tags are parameterized for flexibility.
Handles missing capital/overlay attributes gracefully.
"""

from simulation_engine.worldstate import WorldState
from typing import Dict, Optional

# Parameterized thresholds for alignment tags
TRUST_GROWTH_THRESHOLD = 0.6
FATIGUE_DEFENSIVE_THRESHOLD = 0.5


def summarize_exposure(state: WorldState) -> Dict[str, float]:
    """
    Returns the raw capital exposure values from WorldState.
    Handles missing capital attributes gracefully.
    """
    try:
        return state.capital.as_dict()
    except AttributeError:
        return {}


def total_exposure(state: WorldState) -> float:
    """
    Computes total deployed capital (excluding cash).
    Handles missing capital attributes gracefully.
    """
    cap = getattr(state, 'capital', None)
    if not cap:
        return 0.0
    # Only sum known assets
    total = sum(getattr(cap, k, 0.0) for k in ["nvda", "msft", "ibit", "spy"])
    return round(total, 2)


def exposure_percentages(state: WorldState) -> Dict[str, float]:
    """
    Returns asset exposure as % of total deployed capital.
    Cash is excluded. Handles division by zero and missing attributes.

    Returns:
        Dict[str, float]: mapping of asset name → % of deployed capital
    """
    cap = getattr(state, 'capital', None)
    if not cap:
        return {}
    total = total_exposure(state)
    try:
        asset_dict = cap.as_dict()
    except AttributeError:
        return {}
    if total == 0:
        return {k: 0.0 for k in asset_dict if k != "cash"}
    return {
        k: round(getattr(cap, k, 0.0) / total, 4)
        for k in asset_dict if k != "cash"
    }


def portfolio_alignment_tags(
    state: WorldState,
    trust_growth_threshold: float = TRUST_GROWTH_THRESHOLD,
    fatigue_defensive_threshold: float = FATIGUE_DEFENSIVE_THRESHOLD
) -> Dict[str, str]:
    """
    Tags the current portfolio with symbolic alignment bias.
    Example: 'growth-aligned', 'defensive', or 'neutral'.
    Thresholds are parameterized for flexibility.

    Returns:
        Dict[str, str]: tag labels keyed by concept
    """
    tags = {}
    overlays = getattr(state, 'overlays', None)
    trust = getattr(overlays, 'trust', 0.5) if overlays else 0.5
    fatigue = getattr(overlays, 'fatigue', 0.5) if overlays else 0.5

    # Inline comments for logic clarity
    if trust > trust_growth_threshold:
        tags["bias"] = "growth-aligned"
    elif fatigue > fatigue_defensive_threshold:
        tags["bias"] = "defensive"
    else:
        tags["bias"] = "neutral"

    return tags
