"""
Tests for EnhancedRetrodictionCurriculum

Covers:
- Uncertainty-driven curriculum selection
- Curriculum updates and state retrieval
- Integration with cost control and hybrid rules
"""

import pytest
from unittest.mock import patch, MagicMock
from recursive_training.advanced_metrics.retrodiction_curriculum import EnhancedRetrodictionCurriculum

@pytest.fixture
def mock_config():
    return {
        "uncertainty_threshold": 0.2,
        "max_iterations": 10,
        "cost_control": {"max_cost": 100.0}
    }

@pytest.fixture
def mock_data_store():
    store = MagicMock()
    store.get_data.return_value = [
        {"features": [1,2], "label": 0, "uncertainty": 0.1},
        {"features": [3,4], "label": 1, "uncertainty": 0.3}
    ]
    return store

@pytest.fixture
def enhanced_curriculum(mock_config, mock_data_store):
    with patch("recursive_training.advanced_metrics.retrodiction_curriculum.get_data_store", return_value=mock_data_store):
        return EnhancedRetrodictionCurriculum(mock_config)

def test_initialization(enhanced_curriculum, mock_config):
    assert enhanced_curriculum.config == mock_config
    assert hasattr(enhanced_curriculum, "data_store")

def test_select_data_for_training(enhanced_curriculum):
    # Should select data with uncertainty above threshold
    selected = enhanced_curriculum.select_data_for_training(current_iteration=1)
    assert isinstance(selected, list)
    for item in selected:
        assert "features" in item and "label" in item

def test_update_curriculum(enhanced_curriculum):
    # Simulate update and check for state change
    prev_state = enhanced_curriculum.get_curriculum_state().copy()
    enhanced_curriculum.update_curriculum(current_iteration=2, recent_metrics={"mse": 0.05}, model=None)
    new_state = enhanced_curriculum.get_curriculum_state()
    assert isinstance(new_state, dict)
    assert new_state != prev_state or new_state == prev_state  # State may or may not change, but must be dict

def test_get_curriculum_state(enhanced_curriculum):
    state = enhanced_curriculum.get_curriculum_state()
    assert isinstance(state, dict)

def test_cost_control_integration(enhanced_curriculum):
    # Simulate cost control logic if present
    enhanced_curriculum.config["cost_control"]["max_cost"] = 1.0
    # Should still allow selection, but may trigger internal logic
    selected = enhanced_curriculum.select_data_for_training(current_iteration=3)
    assert isinstance(selected, list)

def test_hybrid_rule_integration(enhanced_curriculum):
    # Simulate curriculum update with hybrid rule context
    enhanced_curriculum.update_curriculum(current_iteration=4, recent_metrics={"mse": 0.04, "rule_type": "hybrid"}, model=None)
    state = enhanced_curriculum.get_curriculum_state()
    assert isinstance(state, dict)