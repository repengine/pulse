"""
asset_forks.py

Defines symbolic-capital fork logic for key tracked assets (e.g., NVDA, MSFT, IBIT, SPY).
Links symbolic overlay state to directional adjustments in capital exposure or expected asset behavior.

Author: Pulse v3.5
"""

from worldstate import WorldState
from state_mutation import adjust_capital
from typing import List


def simulate_nvda_fork(state: WorldState):
    h, d, t, f = (
        state.overlays.hope,
        state.overlays.despair,
        state.overlays.trust,
        state.overlays.fatigue,
    )
    delta = (h * 0.7 + t * 0.4) - (d * 0.5 + f * 0.3)
    net_exposure = round(delta * 1000, 2)
    adjust_capital(state, "nvda", net_exposure)
    state.log_event(f"[FORK] NVDA symbolic-driven exposure delta: {net_exposure:.2f}")


def simulate_msft_fork(state: WorldState):
    t, r, f = (
        state.overlays.trust,
        state.overlays.rage,
        state.overlays.fatigue,
    )
    delta = (t * 0.6) - (r * 0.3 + f * 0.2)
    net_exposure = round(delta * 800, 2)
    adjust_capital(state, "msft", net_exposure)
    state.log_event(f"[FORK] MSFT symbolic-driven exposure delta: {net_exposure:.2f}")


def simulate_ibit_fork(state: WorldState):
    h, d, r = (
        state.overlays.hope,
        state.overlays.despair,
        state.overlays.rage,
    )
    delta = (h * 0.6) - (d * 0.6 + r * 0.2)
    net_exposure = round(delta * 1200, 2)
    adjust_capital(state, "ibit", net_exposure)
    state.log_event(f"[FORK] IBIT symbolic-driven exposure delta: {net_exposure:.2f}")


def simulate_spy_fork(state: WorldState):
    h, d, f, t = (
        state.overlays.hope,
        state.overlays.despair,
        state.overlays.fatigue,
        state.overlays.trust,
    )
    delta = (t * 0.5 + h * 0.4) - (d * 0.4 + f * 0.2)
    net_exposure = round(delta * 900, 2)
    adjust_capital(state, "spy", net_exposure)
    state.log_event(f"[FORK] SPY symbolic-driven exposure delta: {net_exposure:.2f}")


def run_capital_forks(state: WorldState, assets: List[str] = None):
    if assets is None or "nvda" in assets:
        simulate_nvda_fork(state)
    if assets is None or "msft" in assets:
        simulate_msft_fork(state)
    if assets is None or "ibit" in assets:
        simulate_ibit_fork(state)
    if assets is None or "spy" in assets:
        simulate_spy_fork(state)
