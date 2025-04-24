"""
Consolidated simulation engine and rule management module.
"""

from simulation_engine.causal_rules import apply_causal_rules
from simulation_engine.rules.static_rules import build_static_rules
from simulation_engine.rule_engine import run_rules
from simulation_engine.rule_mutation_engine import propose_rule_mutations, apply_rule_mutations
from simulation_engine.rules.pulse_rule_expander import expand_rules_from_regret
from simulation_engine.rules.pulse_rule_explainer import explain_forecast, match_forecast_to_rules
from simulation_engine.rules.reverse_rule_engine import run_reverse_rules
from simulation_engine.rules.reverse_rule_mapper import map_reverse_rule_matches
from simulation_engine.rules.rule_coherence_checker import check_rule_coherence
from simulation_engine.rules.rule_fingerprint_expander import expand_rule_fingerprints
from simulation_engine.rules.rule_autoevolver import auto_evolve_rules
from simulation_engine.utils.pulse_variable_forecaster import simulate_forward, plot_forecast, save_forecast_data
from learning.learning import LearningEngine
from core.pulse_learning_log import log_learning_event

__all__ = [
    "apply_causal_rules",
    "build_static_rules",
    "run_rules",
    "propose_rule_mutations",
    "apply_rule_mutations",
    "expand_rules_from_regret",
    "explain_forecast",
    "match_forecast_to_rules",
    "run_reverse_rules",
    "map_reverse_rule_matches",
    "check_rule_coherence",
    "expand_rule_fingerprints",
    "auto_evolve_rules",
    "simulate_forward",
    "plot_forecast",
    "save_forecast_data",
    "LearningEngine",
    "log_learning_event",
]