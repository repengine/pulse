from core.pulse_learning_log import log_variable_weight_change

def adjust_rules_from_learning(learning_profile):
    """
    Adjust rule weights based on learning profile.
    Upgrades/downgrades trust for arcs/tags with consistent poor/good performance.
    """
    arc_perf = learning_profile.get("arc_performance", {})
    tag_perf = learning_profile.get("tag_performance", {})
    # Example: adjust trust for arcs
    for arc, stats in arc_perf.items():
        win_rate = stats.get("rate", 0)
        old_weight = stats.get("weight", 1.0)
        if win_rate < 0.3:
            new_weight = max(0.0, old_weight - 0.1)
            log_variable_weight_change(arc, old_weight, new_weight)
            # TODO: persist new_weight to rule/arc registry
        elif win_rate > 0.8:
            new_weight = min(1.0, old_weight + 0.1)
            log_variable_weight_change(arc, old_weight, new_weight)
            # TODO: persist new_weight to rule/arc registry
    # Example: adjust trust for tags
    for tag, stats in tag_perf.items():
        win_rate = stats.get("rate", 0)
        old_weight = stats.get("weight", 1.0)
        if win_rate < 0.3:
            new_weight = max(0.0, old_weight - 0.1)
            log_variable_weight_change(tag, old_weight, new_weight)
            # TODO: persist new_weight to tag registry
        elif win_rate > 0.8:
            new_weight = min(1.0, old_weight + 0.1)
            log_variable_weight_change(tag, old_weight, new_weight)
            # TODO: persist new_weight to tag registry
