from core.pulse_learning_log import log_variable_weight_change
from simulation_engine.rules.rule_registry import RuleRegistry
from core.variable_registry import registry as variable_registry


def adjust_rules_from_learning(learning_profile):
    """
    Adjust rule weights based on learning profile.
    Upgrades/downgrades trust for arcs/tags with consistent poor/good performance.
    """
    arc_perf = learning_profile.get("arc_performance", {})
    tag_perf = learning_profile.get("tag_performance", {})

    # Initialize registry instances
    rule_registry = RuleRegistry()
    rule_registry.load_all_rules()

    # Example: adjust trust for arcs
    for arc, stats in arc_perf.items():
        win_rate = stats.get("rate", 0)
        old_weight = stats.get("weight", 1.0)
        if win_rate < 0.3:
            new_weight = max(0.0, old_weight - 0.1)
            log_variable_weight_change(arc, old_weight, new_weight)
            # Persist new_weight to rule/arc registry
            rule_registry.update_trust_score(arc, -0.1)
        elif win_rate > 0.8:
            new_weight = min(1.0, old_weight + 0.1)
            log_variable_weight_change(arc, old_weight, new_weight)
            # Persist new_weight to rule/arc registry
            rule_registry.update_trust_score(arc, 0.1)

    # Example: adjust trust for tags
    for tag, stats in tag_perf.items():
        win_rate = stats.get("rate", 0)
        old_weight = stats.get("weight", 1.0)
        if win_rate < 0.3:
            new_weight = max(0.0, old_weight - 0.1)
            log_variable_weight_change(tag, old_weight, new_weight)
            # Persist new_weight to tag registry
            # Store tag weight in variable registry with special tag prefix
            tag_var_name = f"tag_weight_{tag}"
            variable_registry.register_variable(
                tag_var_name,
                {
                    "type": "trust_weight",
                    "description": f"Trust weight for tag: {tag}",
                    "default": new_weight,
                    "range": [0.0, 1.0],
                    "tags": ["trust_weight", "symbolic_tag", tag],
                },
            )
            # Also update any rules with this tag
            for rule in rule_registry.get_rules_by_symbolic_tag(tag):
                rule_id = rule.get("rule_id") or rule.get("id")
                if rule_id:
                    rule_registry.update_trust_score(
                        rule_id, -0.05
                    )  # Smaller effect for tag-based updates
        elif win_rate > 0.8:
            new_weight = min(1.0, old_weight + 0.1)
            log_variable_weight_change(tag, old_weight, new_weight)
            # Persist new_weight to tag registry
            # Store tag weight in variable registry with special tag prefix
            tag_var_name = f"tag_weight_{tag}"
            variable_registry.register_variable(
                tag_var_name,
                {
                    "type": "trust_weight",
                    "description": f"Trust weight for tag: {tag}",
                    "default": new_weight,
                    "range": [0.0, 1.0],
                    "tags": ["trust_weight", "symbolic_tag", tag],
                },
            )
            # Also update any rules with this tag
            for rule in rule_registry.get_rules_by_symbolic_tag(tag):
                rule_id = rule.get("rule_id") or rule.get("id")
                if rule_id:
                    rule_registry.update_trust_score(
                        rule_id, 0.05
                    )  # Smaller effect for tag-based updates
