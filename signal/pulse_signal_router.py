"""
pulse_signal_router.py

Routes incoming symbolic, narrative, or signal-driven events into
appropriate changes in Pulse's worldstate.

Each signal string maps to:
- variable updates
- symbolic overlay adjustments
- optional capital fork nudges

This allows external narratives (e.g., "ai_panic", "fed_cut") to drive
real simulations through symbolic causality.

Author: Pulse v0.4
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_overlay, adjust_capital
from simulation_engine.variables.worldstate_variables import WorldstateVariables


def route_signal(state: WorldState, signal: str):
    """
    Applies signal-based changes to worldstate.
    Parameters:
        state (WorldState): the simulation state to modify
        signal (str): a named event or trigger (e.g., "ai_panic", "fed_cut")
    """
    sig = signal.lower()

    # === AI Panic: increases fatigue + despair, reduces AI optimism
    if sig in ("ai_panic", "openai_collapse", "ai_regulation_spike"):
        adjust_overlay(state, "despair", +0.02)
        adjust_overlay(state, "fatigue", +0.01)
        state.variables.ai_policy_risk = min(1.0, state.variables.ai_policy_risk + 0.2)

    # === Federal Rate Cut: boost markets, increase hope
    elif sig == "fed_cut":
        state.variables.fed_funds_rate = max(0.0, state.variables.fed_funds_rate - 0.25)
        adjust_overlay(state, "hope", +0.015)
        adjust_capital(state, "spy", +400)
        adjust_capital(state, "msft", +200)

    # === Crypto crash: symbolic panic + IBIT drain
    elif sig == "crypto_rumor" or sig == "bitcoin_flash_crash":
        state.variables.crypto_instability = min(1.0, state.variables.crypto_instability + 0.3)
        adjust_overlay(state, "despair", +0.02)
        adjust_capital(state, "ibit", -500)

    # === Sentiment Surge (e.g., good news)
    elif sig == "media_hope_surge":
        adjust_overlay(state, "hope", +0.03)
        state.variables.media_sentiment_score = min(1.0, state.variables.media_sentiment_score + 0.2)

    # === Energy Spike → Fatigue and NVDA drop
    elif sig == "energy_crisis":
        state.variables.energy_price_index = min(1.0, state.variables.energy_price_index + 0.3)
        adjust_overlay(state, "fatigue", +0.02)
        adjust_capital(state, "nvda", -350)

    # === Institutional Scandal → Trust collapses
    elif sig == "gov_trust_break" or sig == "election_crisis":
        adjust_overlay(state, "trust", -0.03)
        adjust_overlay(state, "despair", +0.015)
        state.variables.public_trust_level = max(0.0, state.variables.public_trust_level - 0.3)

    else:
        print(f"⚠️ Unknown signal: {signal}")
