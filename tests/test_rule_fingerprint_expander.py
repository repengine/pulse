from simulation_engine.rules.rule_fingerprint_expander import suggest_fingerprints


def test_suggest_fingerprints_trust_weighted():
    forecasts = [
        {"trace_id": "t1", "confidence": 0.9, "effects": {"a": 1}},
        {"trace_id": "t2", "confidence": 0.5, "effects": {"a": 2}},
    ]
    suggestions = suggest_fingerprints(forecasts, min_conf=0.7)
    assert any(s["trace_id"] == "t1" for s in suggestions)
    assert all(s["weight"] >= 0.7 for s in suggestions)
