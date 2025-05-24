from simulation_engine.rules.reverse_rule_engine import fuzzy_match_rule_by_delta


def test_fuzzy_match_exact():
    delta = {"a": 1.0}
    fingerprints = [{"rule_id": "r1", "effects": {"a": 1.0}}]
    matches = fuzzy_match_rule_by_delta(delta, fingerprints, tol=0.01)
    assert matches and matches[0][0] == "r1"


def test_fuzzy_match_within_tol():
    delta = {"a": 1.0}
    fingerprints = [{"rule_id": "r2", "effects": {"a": 1.02}}]
    matches = fuzzy_match_rule_by_delta(delta, fingerprints, tol=0.05)
    assert matches and matches[0][0] == "r2"


def test_fuzzy_match_none():
    delta = {"a": 1.0}
    fingerprints = [{"rule_id": "r3", "effects": {"a": 2.0}}]
    matches = fuzzy_match_rule_by_delta(delta, fingerprints, tol=0.01)
    assert not matches
