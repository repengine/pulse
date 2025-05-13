"""
Pytest fixtures for the recursive_training/rules module.

This module contains fixtures used by multiple test files in the rules module,
providing common setup and teardown functionality.
"""

import pytest
import os
import shutil
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

# Create SimpleNamespace objects to allow attribute access on config objects
# This addresses the 'dict' object has no attribute errors

@pytest.fixture
def mock_config():
    """
    Fixture for mock configuration as a SimpleNamespace for attribute access.
    
    Returns a SimpleNamespace object that can be accessed using attribute notation
    while still having dictionary-like contents.
    """
    return SimpleNamespace(
        rules_path="./test_rules",
        max_rule_backups=3,
        validate_rules=True,
        track_rule_usage=True,
        backup_rules=True,
        daily_cost_threshold_usd=10.0,
        max_rule_iterations=5,
        improvement_threshold=0.05,
        default_generation_method="gpt_symbolic_loop",
        default_evaluation_scope="comprehensive",
        min_acceptable_score=0.7,
        enable_cost_control=True,
        enable_dict_compatibility=True,
        prefer_object_representation=True,
        metrics_tracking=True,
        cost_track_enabled=True,
        registered_rule_types=["discount", "shipping"]
    )

@pytest.fixture
def mock_cost_controller():
    """Fixture for mock cost controller."""
    cost_controller = MagicMock()
    cost_controller.can_make_api_call.return_value = True
    cost_controller.track_cost.return_value = None
    return cost_controller

@pytest.fixture
def mock_metrics_store():
    """Fixture for mock metrics store."""
    metrics_store = MagicMock()
    metrics_store.store_metric.return_value = None
    return metrics_store

@pytest.fixture
def config_setup(mock_config):
    """
    Fixture to create a properly structured config object.
    
    Returns a MagicMock with the proper structure for config objects,
    specifically setting the hybrid_rules, cost_control and other config
    categories to use the same mock_config object.
    """
    config_obj = MagicMock()
    config_obj.hybrid_rules = mock_config
    config_obj.cost_control = mock_config
    return config_obj