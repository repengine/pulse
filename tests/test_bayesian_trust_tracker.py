from analytics.bayesian_trust_tracker import bayesian_trust_tracker


def test_bayesian_updates():
    rule_id = "rule_X"
    var_id = "var_Y"
    # Simulate outcomes
    outcomes = [True, True, False, True, False, False, True, True, True, False]
    for outcome in outcomes:
        bayesian_trust_tracker.update(rule_id, outcome)
        bayesian_trust_tracker.update(var_id, not outcome)
    rule_trust = bayesian_trust_tracker.get_trust(rule_id)
    rule_ci = bayesian_trust_tracker.get_confidence_interval(rule_id)
    var_trust = bayesian_trust_tracker.get_trust(var_id)
    var_ci = bayesian_trust_tracker.get_confidence_interval(var_id)
    print(
        f"Rule {rule_id}: Trust={
            rule_trust:.3f}, 95% CI=({
            rule_ci[0]:.3f}, {
                rule_ci[1]:.3f})")
    print(
        f"Variable {var_id}: Trust={
            var_trust:.3f}, 95% CI=({
            var_ci[0]:.3f}, {
                var_ci[1]:.3f})")
    assert 0 <= rule_trust <= 1
    assert 0 <= var_trust <= 1


if __name__ == "__main__":
    test_bayesian_updates()
