"""
portfolio_state.py

Provides analytics and strategic labeling for current capital exposures in WorldState.
Supports total exposure calculation, percentage breakdowns, and symbolic alignment tags.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from typing import Dict


def summarize_exposure(state: WorldState) -> Dict[str, float]:
    """
    Returns the raw capital exposure values from WorldState.
    """
    return state.capital.as_dict()


def total_exposure(state: WorldState) -> float:
    """
    Computes total deployed capital (excluding cash).
    """
    cap = state.capital
    return round(cap.nvda + cap.msft + cap.ibit + cap.spy, 2)


def exposure_percentages(state: WorldState) -> Dict[str, float]:
    """
    Returns asset exposure as % of total deployed capital.
    Cash is excluded.

    Returns:
        Dict[str, float]: mapping of asset name → % of deployed capital
    """
    cap = state.capital
    total = total_exposure(state)

    if total == 0:
        return {k: 0.0 for k in cap.as_dict() if k != "cash"}

    return {
        k: round(getattr(cap, k) / total, 4)
        for k in cap.as_dict() if k != "cash"
    }


def portfolio_alignment_tags(state: WorldState) -> Dict[str, str]:
    """
    Tags the current portfolio with symbolic alignment bias.
    Example: 'growth-aligned', 'defensive', or 'neutral'.

    Returns:
        Dict[str, str]: tag labels keyed by concept
    """
    tags = {}
    overlays = state.overlays
    trust = overlays.trust
    fatigue = overlays.fatigue

    if trust > 0.6:
        tags["bias"] = "growth-aligned"
    elif fatigue > 0.5:
        tags["bias"] = "defensive"
    else:
        tags["bias"] = "neutral"

    return tags
