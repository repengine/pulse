""" 
causal_rules.py

Unified causal rule engine for Pulse v0.4.
Handles symbolic → symbolic, variable → symbolic, and variable → capital
transformations with symbolic tagging added for traceability.

Author: Pulse v0.10
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_overlay, update_numeric_variable, adjust_capital


def apply_causal_rules(state: WorldState):
    """
    Executes causal rules and mutates overlays and capital. Includes symbolic tagging.
    """

    v = state.variables  # shorthand

    if state.overlays.hope > 0.7 and state.overlays.fatigue < 0.3:
        adjust_overlay(state, "trust", +0.02)
        update_numeric_variable(state, "hope_surge_count", +1, max_val=100)
        state.log_event("SYMBOLIC: hope → trust (tag: optimism)")

    if state.overlays.despair > 0.6:
        adjust_overlay(state, "fatigue", +0.015)
        state.log_event("SYMBOLIC: despair → fatigue")

    if state.overlays.despair > 0.5:
        adjust_overlay(state, "hope", -0.01)
        state.log_event("SYMBOLIC: despair suppresses hope")

    if state.overlays.trust > 0.6:
        adjust_capital(state, "nvda", +500)
        state.log_event("CAPITAL: trust boosts NVDA")

    if state.overlays.fatigue > 0.75:
        adjust_capital(state, "ibit", -250)
        state.log_event("CAPITAL: fatigue suppresses IBIT")

    if v.inflation_index > 0.05:
        adjust_overlay(state, "despair", +0.01)
        adjust_overlay(state, "hope", -0.01)
        state.log_event("VARIABLE: inflation raises despair")

    if v.geopolitical_stability < 0.4:
        adjust_overlay(state, "rage", +0.02)
        adjust_overlay(state, "trust", -0.01)
        state.log_event("VARIABLE: instability triggers rage")

    if v.media_sentiment_score > 0.6:
        adjust_overlay(state, "hope", +0.015)
        adjust_overlay(state, "fatigue", -0.01)
        state.log_event("VARIABLE: sentiment boosts hope")

    if v.ai_policy_risk > 0.7:
        adjust_overlay(state, "fatigue", +0.01)
        adjust_overlay(state, "despair", +0.01)
        state.log_event("VARIABLE: ai risk raises fatigue + despair")

    if v.market_volatility_index > 0.5:
        adjust_overlay(state, "fatigue", +0.01)

    if v.public_trust_level < 0.4:
        adjust_overlay(state, "despair", +0.01)
        adjust_overlay(state, "trust", -0.01)

    if v.fed_funds_rate > 0.05:
        adjust_capital(state, "msft", -200)
        adjust_capital(state, "spy", -300)
        state.log_event("CAPITAL: fed rate hit MSFT and SPY")

    if v.crypto_instability > 0.5:
        adjust_capital(state, "ibit", -400)

    if v.energy_price_index > 0.7:
        adjust_capital(state, "nvda", -250)
        adjust_overlay(state, "fatigue", +0.01)