"""
asset_forks.py

Defines symbolic-capital fork logic for key tracked assets (e.g., NVDA, MSFT, IBIT, SPY).
Links symbolic overlay state to directional adjustments in capital exposure or expected asset behavior.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_capital
from typing import List
from core.variable_accessor import get_overlay
from core.pulse_config import MODULES_ENABLED

def simulate_nvda_fork(state: WorldState):
    h = get_overlay(state, "hope")
    d = get_overlay(state, "despair")
    t = get_overlay(state, "trust")
    f = get_overlay(state, "fatigue")
    delta = (h * 0.7 + t * 0.4) - (d * 0.5 + f * 0.3)
    net_exposure = round(delta * 1000, 2)
    adjust_capital(state, "nvda", net_exposure)
    state.log_event(f"[FORK] NVDA symbolic-driven exposure delta: {net_exposure:.2f}")

def simulate_msft_fork(state: WorldState):
    t = get_overlay(state, "trust")
    r = get_overlay(state, "rage")
    f = get_overlay(state, "fatigue")
    delta = (t * 0.6) - (r * 0.3 + f * 0.2)
    net_exposure = round(delta * 800, 2)
    adjust_capital(state, "msft", net_exposure)
    state.log_event(f"[FORK] MSFT symbolic-driven exposure delta: {net_exposure:.2f}")

def simulate_ibit_fork(state: WorldState):
    h = get_overlay(state, "hope")
    d = get_overlay(state, "despair")
    r = get_overlay(state, "rage")
    delta = (h * 0.6) - (d * 0.6 + r * 0.2)
    net_exposure = round(delta * 1200, 2)
    adjust_capital(state, "ibit", net_exposure)
    state.log_event(f"[FORK] IBIT symbolic-driven exposure delta: {net_exposure:.2f}")

def simulate_spy_fork(state: WorldState):
    h = get_overlay(state, "hope")
    d = get_overlay(state, "despair")
    f = get_overlay(state, "fatigue")
    t = get_overlay(state, "trust")
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
