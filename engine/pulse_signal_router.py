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

import logging
from typing import Callable, Dict

from engine.worldstate import WorldState
from engine.state_mutation import adjust_overlay, adjust_capital


def _ai_panic(state):
    adjust_overlay(state, "despair", +0.02)
    adjust_overlay(state, "fatigue", +0.01)
    try:
        state.variables.ai_policy_risk = min(1.0, state.variables.ai_policy_risk + 0.2)
    except AttributeError:
        logging.error("State missing ai_policy_risk attribute.")


def _fed_cut(state):
    try:
        state.variables.fed_funds_rate = max(0.0, state.variables.fed_funds_rate - 0.25)
    except AttributeError:
        logging.error("State missing fed_funds_rate attribute.")
    adjust_overlay(state, "hope", +0.015)
    adjust_capital(state, "spy", +400)
    adjust_capital(state, "msft", +200)


def _crypto_crash(state):
    try:
        state.variables.crypto_instability = min(
            1.0, state.variables.crypto_instability + 0.3
        )
    except AttributeError:
        logging.error("State missing crypto_instability attribute.")
    adjust_overlay(state, "despair", +0.02)
    adjust_capital(state, "ibit", -500)


def _media_hope_surge(state):
    adjust_overlay(state, "hope", +0.03)
    try:
        state.variables.media_sentiment_score = min(
            1.0, state.variables.media_sentiment_score + 0.2
        )
    except AttributeError:
        logging.error("State missing media_sentiment_score attribute.")


def _energy_crisis(state):
    try:
        state.variables.energy_price_index = min(
            1.0, state.variables.energy_price_index + 0.3
        )
    except AttributeError:
        logging.error("State missing energy_price_index attribute.")
    adjust_overlay(state, "fatigue", +0.02)
    adjust_capital(state, "nvda", -350)


def _gov_trust_break(state):
    adjust_overlay(state, "trust", -0.03)
    adjust_overlay(state, "despair", +0.015)
    try:
        state.variables.public_trust_level = max(
            0.0, state.variables.public_trust_level - 0.3
        )
    except AttributeError:
        logging.error("State missing public_trust_level attribute.")


_signal_handlers: Dict[str, Callable] = {
    "ai_panic": _ai_panic,
    "openai_collapse": _ai_panic,
    "ai_regulation_spike": _ai_panic,
    "fed_cut": _fed_cut,
    "crypto_rumor": _crypto_crash,
    "bitcoin_flash_crash": _crypto_crash,
    "media_hope_surge": _media_hope_surge,
    "energy_crisis": _energy_crisis,
    "gov_trust_break": _gov_trust_break,
    "election_crisis": _gov_trust_break,
}


def route_signal(state: WorldState, signal: str) -> bool:
    """
    Applies signal-based changes to worldstate.
    Parameters:
        state (WorldState): the simulation state to modify
        signal (str): a named event or trigger (e.g., "ai_panic", "fed_cut")
    Returns:
        bool: True if signal was handled, False if unknown
    """
    if not isinstance(signal, str):
        logging.error("Signal must be a string.")
        return False
    sig = signal.lower()
    handler = _signal_handlers.get(sig)
    if handler:
        try:
            handler(state)
            logging.info(f"Signal '{signal}' applied.")
            return True
        except Exception as e:
            logging.exception(f"Error applying signal '{signal}': {e}")
            return False
    else:
        logging.warning(f"Unknown signal: {signal}")
        return False


def _test_route_signal():
    # Use the actual WorldState class for type correctness
    from engine.worldstate import WorldState

    s = WorldState()
    # Set required variables for testing
    s.variables.ai_policy_risk = 0.0
    s.variables.fed_funds_rate = 1.0
    s.variables.crypto_instability = 0.0
    s.variables.media_sentiment_score = 0.0
    s.variables.energy_price_index = 0.0
    s.variables.public_trust_level = 1.0
    assert route_signal(s, "ai_panic")
    assert route_signal(s, "fed_cut")
    assert not route_signal(s, "unknown_signal")
    print("✅ route_signal test passed.")
