TRUST_WEIGHT = 0.4
DESPAIR_WEIGHT = 0.5

"""
asset_forks.py

Defines symbolic-capital fork logic for key tracked assets (e.g., NVDA, MSFT, IBIT, SPY).
Links symbolic overlay state to directional adjustments in capital exposure or expected asset behavior.

Author: Pulse v3.5

Each asset fork function computes a net exposure delta based on symbolic overlays and config weights.
If overlays are missing, defaults to 0.0. All events are logged to the simulation state.
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_capital
from typing import List, Optional
from core.variable_accessor import get_overlay
from core.pulse_config import MODULES_ENABLED, CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD, TRUST_WEIGHT, DESPAIR_WEIGHT


def simulate_nvda_fork(state: WorldState) -> None:
    """
    Adjust NVDA capital exposure based on symbolic overlays.
    Formula: (hope * CONFIDENCE_THRESHOLD + trust * TRUST_WEIGHT)
             - (despair * DESPAIR_WEIGHT + fatigue * DEFAULT_FRAGILITY_THRESHOLD)
    """
    h = get_overlay(state, "hope") or 0.0
    d = get_overlay(state, "despair") or 0.0
    t = get_overlay(state, "trust") or 0.0
    f = get_overlay(state, "fatigue") or 0.0
    delta = (h * CONFIDENCE_THRESHOLD + t * TRUST_WEIGHT) - (d * DESPAIR_WEIGHT + f * DEFAULT_FRAGILITY_THRESHOLD)
    net_exposure = round(delta * 1000, 2)
    adjust_capital(state, "nvda", net_exposure)
    state.log_event(f"[FORK] NVDA symbolic-driven exposure delta: {net_exposure:.2f}")


def simulate_msft_fork(state: WorldState) -> None:
    """
    Adjust MSFT capital exposure based on symbolic overlays.
    Formula: (trust * CONFIDENCE_THRESHOLD) - (rage * 0.3 + fatigue * DEFAULT_FRAGILITY_THRESHOLD)
    """
    t = get_overlay(state, "trust") or 0.0
    r = get_overlay(state, "rage") or 0.0
    f = get_overlay(state, "fatigue") or 0.0
    delta = (t * CONFIDENCE_THRESHOLD) - (r * 0.3 + f * DEFAULT_FRAGILITY_THRESHOLD)
    net_exposure = round(delta * 800, 2)
    adjust_capital(state, "msft", net_exposure)
    state.log_event(f"[FORK] MSFT symbolic-driven exposure delta: {net_exposure:.2f}")


def simulate_ibit_fork(state: WorldState) -> None:
    """
    Adjust IBIT capital exposure based on symbolic overlays.
    Formula: (hope * CONFIDENCE_THRESHOLD) - (despair * CONFIDENCE_THRESHOLD + rage * 0.2)
    """
    h = get_overlay(state, "hope") or 0.0
    d = get_overlay(state, "despair") or 0.0
    r = get_overlay(state, "rage") or 0.0
    delta = (h * CONFIDENCE_THRESHOLD) - (d * CONFIDENCE_THRESHOLD + r * 0.2)
    net_exposure = round(delta * 1200, 2)
    adjust_capital(state, "ibit", net_exposure)
    state.log_event(f"[FORK] IBIT symbolic-driven exposure delta: {net_exposure:.2f}")


def simulate_spy_fork(state: WorldState) -> None:
    """
    Adjust SPY capital exposure based on symbolic overlays.
    Formula: (trust * CONFIDENCE_THRESHOLD + hope * 0.4)
             - (despair * 0.4 + fatigue * DEFAULT_FRAGILITY_THRESHOLD)
    """
    h = get_overlay(state, "hope") or 0.0
    d = get_overlay(state, "despair") or 0.0
    f = get_overlay(state, "fatigue") or 0.0
    t = get_overlay(state, "trust") or 0.0
    delta = (t * CONFIDENCE_THRESHOLD + h * 0.4) - (d * 0.4 + f * DEFAULT_FRAGILITY_THRESHOLD)
    net_exposure = round(delta * 900, 2)
    adjust_capital(state, "spy", net_exposure)
    state.log_event(f"[FORK] SPY symbolic-driven exposure delta: {net_exposure:.2f}")


def run_capital_forks(state: WorldState, assets: Optional[List[str]] = None) -> None:
    """
    Run all or selected asset fork simulations for the given state.
    Args:
        state (WorldState): The simulation state.
        assets (Optional[List[str]]): List of asset names to run forks for (default: all).
    """
    if assets is None or "nvda" in assets:
        simulate_nvda_fork(state)
    if assets is None or "msft" in assets:
        simulate_msft_fork(state)
    if assets is None or "ibit" in assets:
        simulate_ibit_fork(state)
    if assets is None or "spy" in assets:
        simulate_spy_fork(state)
