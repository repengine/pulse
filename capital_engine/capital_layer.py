"""
capital_layer.py

Unified Capital Simulation Layer
Combines symbolic-driven asset forks, portfolio state summarization,
and shortview foresight logic.

Author: Pulse v0.33
"""

from typing import Dict, Optional, List, Any
from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_capital
from core.variable_accessor import get_overlay
from symbolic_system.symbolic_utils import symbolic_fragility_index
from pulse.config.loader import Config  # Import the new Config class

# Initialize config
config = Config()

# === Parameters ===
TRUST_GROWTH_THRESHOLD = config.get("capital_engine.trust_growth_threshold", 0.6)
FATIGUE_DEFENSIVE_THRESHOLD = config.get(
    "capital_engine.fatigue_defensive_threshold", 0.5
)


# === Symbolic-to-Capital Fork Logic ===
def simulate_nvda_fork(state: WorldState) -> None:
    h = get_overlay(state, "hope") or 0.0
    d = get_overlay(state, "despair") or 0.0
    t = get_overlay(state, "trust") or 0.0
    f = get_overlay(state, "fatigue") or 0.0
    confidence_threshold = config.get("core.confidence_threshold", 0.5)
    trust_weight = config.get("core.trust_weight", 1.0)
    despair_weight = config.get("core.despair_weight", 1.0)
    default_fragility_threshold = config.get("core.default_fragility_threshold", 0.5)
    nvda_exposure_multiplier = config.get(
        "capital_engine.nvda_exposure_multiplier", 1000
    )

    delta = (h * confidence_threshold + t * trust_weight) - (
        d * despair_weight + f * default_fragility_threshold
    )
    adjust_capital(state, "nvda", round(delta * nvda_exposure_multiplier, 2))
    state.log_event(
        f"[FORK] NVDA symbolic-driven exposure delta: {round(delta * nvda_exposure_multiplier, 2):.2f}"
    )


def simulate_msft_fork(state: WorldState) -> None:
    t = get_overlay(state, "trust") or 0.0
    r = get_overlay(state, "rage") or 0.0
    f = get_overlay(state, "fatigue") or 0.0
    confidence_threshold = config.get("core.confidence_threshold", 0.5)
    msft_rage_weight = config.get("capital_engine.msft_rage_weight", 0.3)
    default_fragility_threshold = config.get("core.default_fragility_threshold", 0.5)
    msft_exposure_multiplier = config.get(
        "capital_engine.msft_exposure_multiplier", 800
    )

    delta = (t * confidence_threshold) - (
        r * msft_rage_weight + f * default_fragility_threshold
    )
    adjust_capital(state, "msft", round(delta * msft_exposure_multiplier, 2))
    state.log_event(
        f"[FORK] MSFT symbolic-driven exposure delta: {round(delta * msft_exposure_multiplier, 2):.2f}"
    )


def simulate_ibit_fork(state: WorldState) -> None:
    h = get_overlay(state, "hope") or 0.0
    d = get_overlay(state, "despair") or 0.0
    r = get_overlay(state, "rage") or 0.0
    confidence_threshold = config.get("core.confidence_threshold", 0.5)
    ibit_rage_weight = config.get("capital_engine.ibit_rage_weight", 0.2)
    ibit_exposure_multiplier = config.get(
        "capital_engine.ibit_exposure_multiplier", 1200
    )

    delta = (h * confidence_threshold) - (
        d * confidence_threshold + r * ibit_rage_weight
    )
    adjust_capital(state, "ibit", round(delta * ibit_exposure_multiplier, 2))
    state.log_event(
        f"[FORK] IBIT symbolic-driven exposure delta: {round(delta * ibit_exposure_multiplier, 2):.2f}"
    )


def simulate_spy_fork(state: WorldState) -> None:
    h = get_overlay(state, "hope") or 0.0
    d = get_overlay(state, "despair") or 0.0
    f = get_overlay(state, "fatigue") or 0.0
    t = get_overlay(state, "trust") or 0.0
    confidence_threshold = config.get("core.confidence_threshold", 0.5)
    spy_hope_despair_weight = config.get("capital_engine.spy_hope_despair_weight", 0.4)
    default_fragility_threshold = config.get("core.default_fragility_threshold", 0.5)
    spy_exposure_multiplier = config.get("capital_engine.spy_exposure_multiplier", 900)

    delta = (t * confidence_threshold + h * spy_hope_despair_weight) - (
        d * spy_hope_despair_weight + f * default_fragility_threshold
    )
    adjust_capital(state, "spy", round(delta * spy_exposure_multiplier, 2))
    state.log_event(
        f"[FORK] SPY symbolic-driven exposure delta: {round(delta * spy_exposure_multiplier, 2):.2f}"
    )


def run_capital_forks(state: WorldState, assets: Optional[List[str]] = None) -> None:
    if assets is None or "nvda" in assets:
        simulate_nvda_fork(state)
    if assets is None or "msft" in assets:
        simulate_msft_fork(state)
    if assets is None or "ibit" in assets:
        simulate_ibit_fork(state)
    if assets is None or "spy" in assets:
        simulate_spy_fork(state)


# === Portfolio State Summary ===
def summarize_exposure(state: WorldState) -> Dict[str, float]:
    try:
        return state.capital.as_dict()
    except AttributeError:
        return {}


def total_exposure(state: WorldState) -> float:
    cap = getattr(state, "capital", None)
    if not cap:
        return 0.0
    total = sum(getattr(cap, k, 0.0) for k in ["nvda", "msft", "ibit", "spy"])
    return round(total, 2)


def exposure_percentages(state: WorldState) -> Dict[str, float]:
    cap = getattr(state, "capital", None)
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
        k: round(getattr(cap, k, 0.0) / total, 4) for k in asset_dict if k != "cash"
    }


def portfolio_alignment_tags(state: WorldState) -> Dict[str, str]:
    tags = {}
    overlays = getattr(state, "overlays", None)
    trust = getattr(overlays, "trust", 0.5) if overlays else 0.5
    fatigue = getattr(overlays, "fatigue", 0.5) if overlays else 0.5
    trust_growth_threshold = config.get("capital_engine.trust_growth_threshold", 0.6)
    fatigue_defensive_threshold = config.get(
        "capital_engine.fatigue_defensive_threshold", 0.5
    )

    if trust > trust_growth_threshold:
        tags["bias"] = "growth-aligned"
    elif fatigue > fatigue_defensive_threshold:
        tags["bias"] = "defensive"
    else:
        tags["bias"] = "neutral"
    return tags


# === Short-Term Symbolic Forecast Layer ===
def run_shortview_forecast(
    state: WorldState, asset_subset: Optional[List[str]] = None, duration_days: int = 2
) -> Dict[str, Any]:
    """
    Runs a short-term symbolic forecast for the given state and asset subset.

    Args:
        state (WorldState): The simulation world state.
        asset_subset (List[str], optional): List of asset symbols to forecast. Defaults to None (all).
        duration_days (int, optional): Duration of the forecast in days. Must be between 1 and 7. Defaults to 2.

    Returns:
        Dict[str, Any]: Dictionary containing forecast results, including symbolic fragility, capital deltas, symbolic changes, alignment tags, and confidence.
    Raises:
        ValueError: If duration_days is outside the allowed range.
    """
    min_duration = config.get("capital_engine.shortview_min_duration_days", 1)
    max_duration = config.get("capital_engine.shortview_max_duration_days", 7)
    if (
        not isinstance(duration_days, int)
        or duration_days < min_duration
        or duration_days > max_duration
    ):
        raise ValueError(
            f"ShortView duration must be between {min_duration} and {max_duration} days."
        )

    # Take a snapshot of the initial state
    try:
        start_snapshot = state.snapshot()
    except Exception as e:
        # Optionally log or handle snapshot errors
        raise RuntimeError(f"Failed to take start snapshot: {e}")

    # Run capital forks for the specified assets
    run_capital_forks(state, assets=asset_subset)

    # Take a snapshot of the state after simulation
    try:
        end_snapshot = state.snapshot()
    except Exception as e:
        raise RuntimeError(f"Failed to take end snapshot: {e}")

    # Calculate symbolic overlay changes
    symbolic_change = {}
    start_overlays = start_snapshot.get("overlays", {})
    end_overlays = end_snapshot.get("overlays", {})
    for overlay in start_overlays:
        symbolic_change[overlay] = round(
            end_overlays.get(overlay, 0.0) - start_overlays.get(overlay, 0.0), 3
        )

    # Calculate capital deltas
    end_cap = end_snapshot.get("capital", {})
    start_cap = start_snapshot.get("capital", {})
    capital_delta = {k: end_cap.get(k, 0.0) - start_cap.get(k, 0.0) for k in end_cap}

    # Compose the forecast result
    try:
        fragility = symbolic_fragility_index(state)
    except Exception:
        fragility = None  # fallback if symbolic_fragility_index fails

    try:
        alignment = portfolio_alignment_tags(state)
    except Exception:
        alignment = {}

    forecast = {
        "duration_days": duration_days,
        "symbolic_fragility": fragility,
        "start_capital": start_cap,
        "end_capital": end_cap,
        "capital_delta": capital_delta,
        "symbolic_change": symbolic_change,
        "portfolio_alignment": alignment,
        "confidence": None,  # Placeholder for future confidence calculation
    }

    # Log the forecast event, handle logging errors gracefully
    try:
        state.log_event(
            f"[SHORTVIEW] Forecast run for {duration_days} days. Fragility: {forecast['symbolic_fragility']:.3f}"
            if forecast["symbolic_fragility"] is not None
            else "[SHORTVIEW] Forecast run (fragility unavailable)."
        )
    except Exception:
        pass  # Logging should not break the forecast

    # Minimal runtime assertion for output structure (for testing/debugging)
    assert (
        isinstance(forecast, dict)
        and "duration_days" in forecast
        and "capital_delta" in forecast
    ), "Forecast output structure invalid"

    return forecast
