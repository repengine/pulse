"""
overlay_bridge.py

Provides compatibility and transition functions between the existing overlay system
and the new Symbolic Pillar / Gravity Fabric architecture.

This bridge enables gradual migration from overlays to pillars while maintaining
backward compatibility with existing code.

Author: Pulse v3.5
"""

import logging
from typing import Dict, Optional

from simulation_engine.worldstate import WorldState
import symbolic_system.symbolic_utils as legacy_utils
from symbolic_system.gravity.integration import (
    get_pillar_system,
    get_gravity_fabric,
    is_gravity_enabled,
    adapt_overlays_to_pillars,
)

logger = logging.getLogger(__name__)


def get_pillar_snapshot(state: Optional[WorldState] = None) -> Dict[str, float]:
    """
    Returns a dictionary of all symbolic pillar values.

    Similar to legacy get_overlay_snapshot() but uses pillar system.

    Parameters
    ----------
    state : WorldState, optional
        If provided, will sync pillars from state overlays first

    Returns
    -------
    Dict[str, float]
        Dictionary of pillar names to intensity values
    """
    pillar_system = get_pillar_system()

    # If state is provided, sync pillars from overlays first
    if state is not None:
        adapt_overlays_to_pillars(state)

    return pillar_system.as_dict()


def normalize_pillar_vector(pillars: Dict[str, float]) -> Dict[str, float]:
    """
    Normalizes pillar values into a unit vector for comparison/scoring.

    Analog to legacy normalize_overlay_vector() but for pillars.

    Parameters
    ----------
    pillars : Dict[str, float]
        Dictionary of pillar values

    Returns
    -------
    Dict[str, float]
        Normalized pillar values
    """
    total = sum(pillars.values())
    if total == 0:
        return {k: 0.0 for k in pillars}
    return {k: v / total for k, v in pillars.items()}


def pillar_tension_score(pillars: Optional[Dict[str, float]] = None) -> float:
    """
    Calculates a tension score based on internal contradictions between pillars.

    Similar to legacy symbolic_tension_score() but uses pillar system if no
    pillars dictionary is provided.

    Parameters
    ----------
    pillars : Dict[str, float], optional
        Dictionary of pillar values. If None, uses current pillar system.

    Returns
    -------
    float
        Tension score (0.0-1.0)
    """
    if pillars is None:
        pillar_system = get_pillar_system()
        pillars = pillar_system.as_dict()

    return pillar_system.symbolic_tension_score()


def pillar_fragility_index(state: Optional[WorldState] = None) -> float:
    """
    Returns a symbolic fragility index based on pillar system.

    Enhanced version of legacy symbolic_fragility_index() that also
    incorporates gravity residuals.

    Parameters
    ----------
    state : WorldState, optional
        If provided, will sync pillars from state overlays first

    Returns
    -------
    float
        Fragility index (0.0-1.0+)
    """
    # Get current pillar values
    pillar_system = get_pillar_system()
    if state is not None:
        adapt_overlays_to_pillars(state)

    pillars = pillar_system.as_dict()

    # Calculate base fragility from pillar tension
    tension = pillar_system.symbolic_tension_score()
    fragility = tension

    # Amplify fragility if Trust is low while Despair or Rage are high
    if pillars.get("trust", 0.5) < 0.3:
        fragility += pillars.get("despair", 0) * 0.5
        fragility += pillars.get("rage", 0) * 0.4

    # If gravity system is enabled, factor in gravity metrics
    if is_gravity_enabled():
        fabric = get_gravity_fabric()
        engine = fabric.gravity_engine

        # High RMS weight suggests over-reliance on gravity corrections
        rms_weight = engine.rms_weight()
        if rms_weight > 0.5:
            fragility += (rms_weight - 0.5) * 0.6

        # Recent large residuals suggest instability
        if fabric.residual_history:
            for var, points in fabric.residual_history.items():
                if not points:
                    continue

                # Get most recent point
                latest = points[-1]

                # Large recent residuals increase fragility
                if abs(latest.residual) > 1.0:
                    normalized_residual = min(abs(latest.residual / 10.0), 1.0)
                    fragility += normalized_residual * 0.3

    return round(min(fragility, 1.0), 3)


def compute_pillar_drift_penalty(forecast: dict) -> float:
    """
    Returns a penalty (0–1) for symbolic pillar instability.

    Enhanced version of legacy compute_symbolic_drift_penalty() that
    incorporates pillar growth rates and gravity corrections.

    Parameters
    ----------
    forecast : dict
        Forecast dictionary with metadata

    Returns
    -------
    float
        Drift penalty (0.0-1.0)
    """
    penalty = 0.0

    # Include original overlay penalties
    if forecast.get("symbolic_fragmented"):
        penalty += 0.2
    if forecast.get("arc_volatility_score", 0) > 0.7:
        penalty += 0.1

    # Check for rapid pillar changes
    pillar_system = get_pillar_system()
    for name, pillar in pillar_system.pillars.items():
        growth_rate = pillar.get_growth_rate()
        if abs(growth_rate) > 0.1:  # Significant growth/decline
            penalty += min(abs(growth_rate) * 2, 0.3)

    # Check gravity system for large corrections
    if is_gravity_enabled():
        fabric = get_gravity_fabric()
        _engine = fabric.gravity_engine

        # Large gravity corrections suggest instability
        for var, points in fabric.residual_history.items():
            if not points or len(points) < 2:
                continue

            # Get most recent points
            p1, p2 = points[-2], points[-1]

            # Significant change in correction magnitude
            if (
                abs(p2.corrected - p2.predicted)
                > abs(p1.corrected - p1.predicted) * 1.5
            ):
                penalty += 0.15

    return min(penalty, 1.0)


def legacy_to_pillar_system(overlays: Dict[str, float]) -> None:
    """
    Convert legacy overlay values to pillar system.

    Parameters
    ----------
    overlays : Dict[str, float]
        Dictionary of overlay values
    """
    pillar_system = get_pillar_system()

    # Reset all pillars first
    for name in pillar_system.pillars:
        pillar_system.adjust_pillar(name, -pillar_system.get_pillar_value(name))

    # Set pillar values from overlays
    for name, value in overlays.items():
        if name in pillar_system.pillars:
            pillar_system.adjust_pillar(name, value)


def pillar_to_legacy_overlays() -> Dict[str, float]:
    """
    Convert current pillar system to legacy overlay values.

    Returns
    -------
    Dict[str, float]
        Dictionary of overlay values
    """
    pillar_system = get_pillar_system()
    return pillar_system.as_dict()


def get_unified_tension_score(state: WorldState) -> float:
    """
    Unified tension score that works with both systems.

    Uses pillar system if gravity is enabled, otherwise falls back
    to legacy overlay system.

    Parameters
    ----------
    state : WorldState
        Current world state

    Returns
    -------
    float
        Tension score (0.0-1.0)
    """
    if is_gravity_enabled():
        adapt_overlays_to_pillars(state)
        return pillar_tension_score()
    else:
        overlays = legacy_utils.get_overlay_snapshot(state)
        return legacy_utils.symbolic_tension_score(overlays)


def get_unified_fragility_index(state: WorldState) -> float:
    """
    Unified fragility index that works with both systems.

    Uses pillar system if gravity is enabled, otherwise falls back
    to legacy overlay system.

    Parameters
    ----------
    state : WorldState
        Current world state

    Returns
    -------
    float
        Fragility index (0.0-1.0+)
    """
    if is_gravity_enabled():
        return pillar_fragility_index(state)
    else:
        return legacy_utils.symbolic_fragility_index(state)


def update_forecast_with_pillar_data(forecast: dict) -> dict:
    """
    Updates a forecast dictionary with pillar-related metadata.

    Enhances existing forecast metadata with additional information from
    the pillar and gravity systems.

    Parameters
    ----------
    forecast : dict
        Forecast dictionary with metadata

    Returns
    -------
    dict
        Updated forecast dictionary
    """
    # Keep existing forecast intact
    updated = forecast.copy()

    # Only add pillar data if gravity system is enabled
    if not is_gravity_enabled():
        return updated

    # Get pillar system data
    pillar_system = get_pillar_system()
    fabric = get_gravity_fabric()

    # Add pillar values
    updated["pillar_values"] = pillar_system.as_dict()

    # Add dominant pillars
    updated["dominant_pillars"] = pillar_system.get_dominant_pillars()

    # Add gravity metrics
    updated["gravity_metrics"] = {
        "rms_weight": fabric.gravity_engine.rms_weight(),
        "top_contributors": [
            {"name": n, "weight": w}
            for n, w in fabric.gravity_engine.get_top_contributors(n=3)
        ],
    }

    # Add pillar tension score
    updated["pillar_tension_score"] = pillar_system.symbolic_tension_score()

    # Add pillar contributions to gravity
    updated["pillar_contributions"] = fabric.get_pillar_contributions()

    # Add per-variable improvement metrics
    updated["variable_improvements"] = {}
    for var in fabric.residual_history:
        mae_orig, mae_corr = fabric.get_mean_absolute_error(var)
        if mae_orig > 0:
            pct_improvement = fabric.get_improvement_percentage(var)
            updated["variable_improvements"][var] = {
                "original_mae": mae_orig,
                "corrected_mae": mae_corr,
                "percentage_improvement": pct_improvement,
            }

    return updated
