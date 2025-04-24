""" 
causal_rules.py

Unified causal rule engine for Pulse v0.4.
Handles symbolic → symbolic, variable → symbolic, and variable → capital
transformations with symbolic tagging added for traceability.

Author: Pulse v0.32
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_overlay, update_numeric_variable, adjust_capital
from core.variable_accessor import get_variable, get_overlay
from core.pulse_config import CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD
from core.pulse_learning_log import log_bayesian_trust_metrics
from core.bayesian_trust_tracker import bayesian_trust_tracker
import logging

logger = logging.getLogger("causal_rules")

# Rule definitions with IDs and metadata
RULES = {
    "R001_HopeTrust": {
        "description": "Hope builds trust when fatigue is low",
        "category": "symbolic",
        "importance": 0.8
    },
    "R002_DespairFatigue": {
        "description": "Despair induces fatigue",
        "category": "symbolic",
        "importance": 0.7
    },
    "R003_DespairHope": {
        "description": "Despair suppresses hope",
        "category": "symbolic",
        "importance": 0.7
    },
    "R004_TrustCapital": {
        "description": "Trust boosts NVDA capital",
        "category": "capital",
        "importance": 0.9
    },
    "R005_FatigueCapital": {
        "description": "Fatigue suppresses IBIT capital",
        "category": "capital",
        "importance": 0.6
    },
    "R006_InflationEffect": {
        "description": "Inflation raises despair, lowers hope",
        "category": "variable",
        "importance": 0.8
    },
    "R007_StabilityEffect": {
        "description": "Geopolitical instability triggers rage, lowers trust",
        "category": "variable",
        "importance": 0.7
    },
    "R008_SentimentEffect": {
        "description": "Positive media sentiment boosts hope, reduces fatigue",
        "category": "variable",
        "importance": 0.7
    },
    "R009_AiRiskEffect": {
        "description": "AI policy risk increases fatigue and despair",
        "category": "variable",
        "importance": 0.6
    },
    "R010_VolatilityEffect": {
        "description": "Market volatility increases fatigue",
        "category": "variable",
        "importance": 0.5
    },
    "R011_PublicTrustEffect": {
        "description": "Low public trust increases despair, lowers trust",
        "category": "variable",
        "importance": 0.6
    },
    "R012_FedRateEffect": {
        "description": "Fed rate hike suppresses MSFT and SPY capital",
        "category": "capital",
        "importance": 0.8
    },
    "R013_CryptoEffect": {
        "description": "Crypto instability suppresses IBIT capital",
        "category": "capital",
        "importance": 0.7
    },
    "R014_EnergyEffect": {
        "description": "High energy prices suppress NVDA and increase fatigue",
        "category": "mixed",
        "importance": 0.6
    },
    "R015_EnergySpike": {
        "description": "Hope builds trust based on trust score",
        "category": "symbolic",
        "importance": 0.7
    }
}

def apply_rule(state: WorldState, rule_id: str, condition_func, effect_func) -> bool:
    """
    Apply a rule with tracking and trust modulation.
    
    Args:
        state: WorldState object
        rule_id: Rule identifier
        condition_func: Function that determines if rule should trigger
        effect_func: Function that applies rule effects
        
    Returns:
        bool: Whether rule was triggered
    """
    if rule_id not in RULES:
        logger.warning(f"Unknown rule ID: {rule_id}")
        return False
    
    # Check if rule should trigger
    if not condition_func(state):
        state.log_event(f"Rule checked but not triggered: {rule_id}")
        return False
    
    # Get trust score for this rule
    trust = bayesian_trust_tracker.get_trust(rule_id)
    importance = RULES[rule_id]["importance"]
    
    # Modulate effect by rule trust and importance
    modulation = trust * importance
    
    # Apply effects with modulation
    try:
        effect_func(state, modulation)
        state.log_event(f"Rule triggered: {rule_id} (trust={trust:.2f}, mod={modulation:.2f})")
        
        # Log for Bayesian update
        log_bayesian_trust_metrics(rule_id, kind="rule")
        
        # Success!
        return True
    except Exception as e:
        logger.error(f"Error applying rule {rule_id}: {e}")
        return False

def apply_causal_rules(state: WorldState):
    """
    Executes causal rules and mutates overlays and capital. Includes symbolic tagging.
    """
    # Track rule activations for reporting
    activated_rules = []
    
    # Remove all programmatically generated (AUTO_RULE) and placeholder rules. Only keep real, interpretable rules.
    # The following are real, interpretable rules based on actual relationships:
    # R001_HopeTrust
    if apply_rule(
        state, 
        "R001_HopeTrust",
        lambda s: get_overlay(s, "hope") > CONFIDENCE_THRESHOLD and get_overlay(s, "fatigue") < DEFAULT_FRAGILITY_THRESHOLD,
        lambda s, mod: (
            adjust_overlay(s, "trust", +0.02 * mod),
            update_numeric_variable(s, "hope_surge_count", +1, max_val=100),
            s.log_event(f"SYMBOLIC: hope → trust (tag: optimism) [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R001_HopeTrust")
    # R002_DespairFatigue
    if apply_rule(
        state,
        "R002_DespairFatigue",
        lambda s: get_overlay(s, "despair") > 0.6,
        lambda s, mod: (
            adjust_overlay(s, "fatigue", +0.015 * mod),
            s.log_event(f"SYMBOLIC: despair → fatigue [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R002_DespairFatigue")
    # R003_DespairHope
    if apply_rule(
        state,
        "R003_DespairHope",
        lambda s: get_overlay(s, "despair") > 0.5,
        lambda s, mod: (
            adjust_overlay(s, "hope", -0.01 * mod),
            s.log_event(f"SYMBOLIC: despair suppresses hope [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R003_DespairHope")
    # R004_TrustCapital
    if apply_rule(
        state,
        "R004_TrustCapital",
        lambda s: get_overlay(s, "trust") > 0.6,
        lambda s, mod: (
            adjust_capital(s, "nvda", +500 * mod),
            s.log_event(f"CAPITAL: trust boosts NVDA [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R004_TrustCapital")
    # R005_FatigueCapital
    if apply_rule(
        state,
        "R005_FatigueCapital",
        lambda s: get_overlay(s, "fatigue") > DEFAULT_FRAGILITY_THRESHOLD,
        lambda s, mod: (
            adjust_capital(s, "ibit", -250 * mod),
            s.log_event(f"CAPITAL: fatigue suppresses IBIT [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R005_FatigueCapital")
    # R006_InflationEffect
    if apply_rule(
        state,
        "R006_InflationEffect",
        lambda s: get_variable(s, "inflation_index") > 0.05,
        lambda s, mod: (
            adjust_overlay(s, "despair", +0.01 * mod),
            adjust_overlay(s, "hope", -0.01 * mod),
            s.log_event(f"VARIABLE: inflation raises despair [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R006_InflationEffect")
    # R007_StabilityEffect
    if apply_rule(
        state,
        "R007_StabilityEffect",
        lambda s: get_variable(s, "geopolitical_stability") < 0.5,
        lambda s, mod: (
            adjust_overlay(s, "rage", +0.01 * mod),
            adjust_overlay(s, "trust", -0.01 * mod),
            s.log_event(f"VARIABLE: instability triggers rage, lowers trust [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R007_StabilityEffect")
    # R008_SentimentEffect
    if apply_rule(
        state,
        "R008_SentimentEffect",
        lambda s: get_variable(s, "media_sentiment_score") > 0.6,
        lambda s, mod: (
            adjust_overlay(s, "hope", +0.01 * mod),
            adjust_overlay(s, "fatigue", -0.01 * mod),
            s.log_event(f"VARIABLE: positive media sentiment boosts hope, reduces fatigue [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R008_SentimentEffect")
    # R009_AiRiskEffect
    if apply_rule(
        state,
        "R009_AiRiskEffect",
        lambda s: get_variable(s, "ai_policy_risk") > 0.5,
        lambda s, mod: (
            adjust_overlay(s, "fatigue", +0.01 * mod),
            adjust_overlay(s, "despair", +0.01 * mod),
            s.log_event(f"VARIABLE: AI policy risk increases fatigue and despair [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R009_AiRiskEffect")
    # R010_VolatilityEffect
    if apply_rule(
        state,
        "R010_VolatilityEffect",
        lambda s: get_variable(s, "market_volatility_index") > 0.5,
        lambda s, mod: (
            adjust_overlay(s, "fatigue", +0.01 * mod),
            s.log_event(f"VARIABLE: market volatility increases fatigue [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R010_VolatilityEffect")
    # R011_PublicTrustEffect
    if apply_rule(
        state,
        "R011_PublicTrustEffect",
        lambda s: get_variable(s, "public_trust_level") < 0.4,
        lambda s, mod: (
            adjust_overlay(s, "despair", +0.01 * mod),
            adjust_overlay(s, "trust", -0.01 * mod),
            s.log_event(f"VARIABLE: low public trust increases despair, lowers trust [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R011_PublicTrustEffect")
    # R012_FedRateEffect
    if apply_rule(
        state,
        "R012_FedRateEffect",
        lambda s: get_variable(s, "fed_funds_rate") > 0.07,
        lambda s, mod: (
            adjust_capital(s, "msft", -200 * mod),
            adjust_capital(s, "spy", -200 * mod),
            s.log_event(f"CAPITAL: fed rate hike suppresses MSFT and SPY [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R012_FedRateEffect")
    # R013_CryptoEffect
    if apply_rule(
        state,
        "R013_CryptoEffect",
        lambda s: get_variable(s, "crypto_instability") > 0.5,
        lambda s, mod: (
            adjust_capital(s, "ibit", -200 * mod),
            s.log_event(f"CAPITAL: crypto instability suppresses IBIT [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R013_CryptoEffect")
    # R014_EnergyEffect
    if apply_rule(
        state,
        "R014_EnergyEffect",
        lambda s: get_variable(s, "energy_price_index") > 1.0,
        lambda s, mod: (
            adjust_capital(s, "nvda", -200 * mod),
            adjust_overlay(s, "fatigue", +0.01 * mod),
            s.log_event(f"MIXED: high energy prices suppress NVDA, increase fatigue [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R014_EnergyEffect")
    # R015_EnergySpike
    if apply_rule(
        state,
        "R015_EnergySpike",
        lambda s: get_variable(s, "energy_price_index") > 1.5,
        lambda s, mod: (
            adjust_overlay(s, "trust", +0.01 * mod),
            s.log_event(f"SYMBOLIC: hope builds trust based on trust score [mod={mod:.2f}]")
        )
    ):
        activated_rules.append("R015_EnergySpike")
    return activated_rules

def generate_rule_statistics() -> dict:
    """
    Generate statistics about rule effectiveness.
    
    Returns:
        dict: Statistics about each rule
    """
    stats = {}
    for rule_id in RULES:
        trust = bayesian_trust_tracker.get_trust(rule_id)
        confidence = bayesian_trust_tracker.get_confidence_strength(rule_id)
        sample_size = bayesian_trust_tracker.get_sample_size(rule_id)
        ci = bayesian_trust_tracker.get_confidence_interval(rule_id)
        
        stats[rule_id] = {
            "description": RULES[rule_id]["description"],
            "category": RULES[rule_id]["category"],
            "importance": RULES[rule_id]["importance"],
            "trust": trust,
            "confidence": confidence,
            "sample_size": sample_size,
            "confidence_interval": ci
        }
    
    return stats