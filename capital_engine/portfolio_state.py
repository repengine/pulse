"""
portfolio_state.py

Provides derived metrics and diagnostics for the capital exposure system.
This includes exposure summaries, symbolic alignment analysis, and risk scoring stubs.
Supports future strategic rebalancing and confidence calibration.

Author: Pulse v3.5
"""

from worldstate import WorldState
from typing import Dict


def summarize_exposure(state: WorldState) -> Dict[str, float]:
    """
    Returns the current capital exposure as a dict of asset: value.
    """
    return state.capital.as_dict()


def total_exposure(state: WorldState) -> float:
    """
    Computes the total deployed capital across all assets (excluding cash).
    """
    cap = state.capital
    return round(
        cap.nvda + cap.msft + cap.ibit + cap.spy,
        2
    )


def exposure_percentages(state: WorldState) -> Dict[str, float]:
    """
    Returns the percentage breakdown of current portfolio (not including cash).
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
    Returns symbolic alignment labels for current exposure.
    Placeholder logic for future strategic classifiers.
    """
    tags = {}
    overlays = state.overlays
    trust, fatigue = overlays.trust, overlays.fatigue

    if trust > 0.6:
        tags["bias"] = "growth-aligned"
    elif fatigue > 0.5:
        tags["bias"] = "defensive"
    else:
        tags["bias"] = "neutral"

    return tags
