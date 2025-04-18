""" 
causal_rules.py

Unified causal rule engine for Pulse v0.4.
Handles symbolic → symbolic, variable → symbolic, and variable → capital
transformations with symbolic tagging added for traceability.

Author: Pulse v0.10
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_overlay, update_numeric_variable, adjust_capital
from core.variable_accessor import get_variable, get_overlay
from core.pulse_config import CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD
from core.module_registry import MODULE_REGISTRY


def apply_causal_rules(state: WorldState):
    """
    Executes causal rules and mutates overlays and capital. Includes symbolic tagging.
    """
    if not MODULE_REGISTRY.get("rule_engine", {}).get("enabled", True):
        return

    v = state.variables  # shorthand

    # Use accessors and config constants
    if get_overlay(state, "hope") > CONFIDENCE_THRESHOLD and get_overlay(state, "fatigue") < DEFAULT_FRAGILITY_THRESHOLD:
        adjust_overlay(state, "trust", +0.02)
        update_numeric_variable(state, "hope_surge_count", +1, max_val=100)
        state.log_event("SYMBOLIC: hope → trust (tag: optimism)")

    if get_overlay(state, "despair") > 0.6:
        adjust_overlay(state, "fatigue", +0.015)
        state.log_event("SYMBOLIC: despair → fatigue")

    if get_overlay(state, "despair") > 0.5:
        adjust_overlay(state, "hope", -0.01)
        state.log_event("SYMBOLIC: despair suppresses hope")

    if get_overlay(state, "trust") > 0.6:
        adjust_capital(state, "nvda", +500)
        state.log_event("CAPITAL: trust boosts NVDA")

    if get_overlay(state, "fatigue") > DEFAULT_FRAGILITY_THRESHOLD:
        adjust_capital(state, "ibit", -250)
        state.log_event("CAPITAL: fatigue suppresses IBIT")

    if get_variable(state, "inflation_index") > 0.05:
        adjust_overlay(state, "despair", +0.01)
        adjust_overlay(state, "hope", -0.01)
        state.log_event("VARIABLE: inflation raises despair")

    if get_variable(state, "geopolitical_stability") < 0.4:
        adjust_overlay(state, "rage", +0.02)
        adjust_overlay(state, "trust", -0.01)
        state.log_event("VARIABLE: instability triggers rage")

    if get_variable(state, "media_sentiment_score") > 0.6:
        adjust_overlay(state, "hope", +0.015)
        adjust_overlay(state, "fatigue", -0.01)
        state.log_event("VARIABLE: sentiment boosts hope")

    if get_variable(state, "ai_policy_risk") > 0.7:
        adjust_overlay(state, "fatigue", +0.01)
        adjust_overlay(state, "despair", +0.01)
        state.log_event("VARIABLE: ai risk raises fatigue + despair")

    if get_variable(state, "market_volatility_index") > 0.5:
        adjust_overlay(state, "fatigue", +0.01)

    if get_variable(state, "public_trust_level") < 0.4:
        adjust_overlay(state, "despair", +0.01)
        adjust_overlay(state, "trust", -0.01)

    if get_variable(state, "fed_funds_rate") > 0.05:
        adjust_capital(state, "msft", -200)
        adjust_capital(state, "spy", -300)
        state.log_event("CAPITAL: fed rate hit MSFT and SPY")

    if get_variable(state, "crypto_instability") > 0.5:
        adjust_capital(state, "ibit", -400)

    if get_variable(state, "energy_price_index") > 0.7:
        adjust_capital(state, "nvda", -250)
        adjust_overlay(state, "fatigue", +0.01)