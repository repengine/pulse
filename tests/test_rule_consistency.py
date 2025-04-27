"""
Test suite for rule matching and registry consistency across Pulse modules.
"""
import pytest
from simulation_engine.rules import rule_matching_utils, reverse_rule_mapper, reverse_rule_engine
from simulation_engine.rules.rule_registry import RuleRegistry

@pytest.fixture
def sample_delta():
    return {"hope": 0.1, "despair": -0.05}

@pytest.fixture
def sample_rule():
    return {"rule_id": "R999_TEST", "effects": {"hope": 0.1, "despair": -0.05}}

def test_matching_consistency(sample_delta):
    """Ensure all matching modules return the same rule for a given delta."""
    utils_matches = rule_matching_utils.match_rule_by_delta(sample_delta)
    mapper_matches = reverse_rule_mapper.match_rule_by_delta(sample_delta)
    engine_matches = reverse_rule_engine.match_rule_by_delta(sample_delta)
    # Only compare rule_ids, ignore scores
    utils_ids = [m[0] for m in utils_matches]
    mapper_ids = [m[0] for m in mapper_matches]
    engine_ids = [m[0] for m in engine_matches]
    assert utils_ids == mapper_ids == engine_ids

def test_registry_visibility(sample_rule):
    """Test that a new rule is visible in all modules after addition."""
    reg = RuleRegistry()
    reg.load_all_rules()
    reg.rules.append(sample_rule)
    # Should be visible in matching utils
    all_fps = rule_matching_utils.get_all_rule_fingerprints()
    assert any(r.get("rule_id") == sample_rule["rule_id"] for r in all_fps)
    # Should be visible in reverse_rule_mapper
    mapper_fps = reverse_rule_mapper.get_all_rule_fingerprints()
    assert any(r.get("rule_id") == sample_rule["rule_id"] for r in mapper_fps)
    # Should be visible in reverse_rule_engine
    engine_fps = reverse_rule_engine.get_all_rule_fingerprints()
    assert any(r.get("rule_id") == sample_rule["rule_id"] for r in engine_fps)
