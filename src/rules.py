"""
Consolidated rule utility module.
"""

from simulation_engine.rules.static_rules import build_static_rules
from simulation_engine.rules.pulse_rule_expander import expand_rules_from_regret
from simulation_engine.rules.pulse_rule_explainer import explain_forecast, match_forecast_to_rules, explain_forecast_batch
from simulation_engine.rules.reverse_rule_engine import run_reverse_rules
from simulation_engine.rules.reverse_rule_mapper import map_reverse_rule_matches
from simulation_engine.rules.rule_coherence_checker import check_rule_coherence
from simulation_engine.rules.rule_fingerprint_expander import expand_rule_fingerprints
from simulation_engine.rules.rule_autoevolver import auto_evolve_rules
from simulation_engine.rules.rule_audit_layer import audit_rule

__all__ = [
    "build_static_rules",
    "expand_rules_from_regret",
    "explain_forecast",
    "match_forecast_to_rules",
    "explain_forecast_batch",
    "run_reverse_rules",
    "map_reverse_rule_matches",
    "check_rule_coherence",
    "expand_rule_fingerprints",
    "auto_evolve_rules",
    "audit_rule",
]