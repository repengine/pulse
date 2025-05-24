"""
Tests for HybridRuleAdapter

This module contains unit tests for the HybridRuleAdapter class,
focusing on conversions between dictionary and object rule representations.
"""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from typing import List

from recursive_training.rules.hybrid_adapter import (
    HybridRuleAdapter,
    Rule,
    RuleCondition,
    RuleAction,
    RuleMetadata,
    ConversionError,
    get_hybrid_adapter,
)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    # Use SimpleNamespace for attribute access
    from types import SimpleNamespace

    return SimpleNamespace(
        enable_dict_compatibility=True,
        prefer_object_representation=True,
        cost_track_enabled=True,
        registered_rule_types=["discount", "shipping"],
    )


@pytest.fixture
def mock_cost_controller():
    """Fixture for mock cost controller."""
    cost_controller = MagicMock()
    cost_controller.track_cost.return_value = None
    return cost_controller


@pytest.fixture
def sample_rule_dict():
    """Sample rule in dictionary format."""
    return {
        "id": "test_rule_1",
        "type": "discount",
        "conditions": [
            {
                "type": "comparison",
                "parameters": {"variable": "price", "operator": ">", "value": 100},
                "description": "Price greater than 100",
            },
            {
                "type": "category",
                "parameters": {
                    "variable": "category",
                    "operator": "==",
                    "value": "electronics",
                },
                "description": "Category is electronics",
            },
        ],
        "actions": [
            {
                "type": "set_value",
                "parameters": {"variable": "discount", "value": 0.1},
                "description": "Set 10% discount",
            }
        ],
        "priority": 1,
        "description": "10% discount on electronics over $100",
        "metadata": {
            "created_at": "2025-04-30T12:00:00",
            "updated_at": "2025-04-30T12:00:00",
            "version": 1,
            "status": "active",
            "generator": "UnitTest",
            "tags": ["test", "discount", "electronics"],
        },
    }


@pytest.fixture
def hybrid_adapter(mock_config, mock_cost_controller):
    """Fixture for hybrid adapter with mocked dependencies."""
    with patch(
        "recursive_training.rules.hybrid_adapter.get_cost_controller"
    ) as mock_get_cost_controller:
        with patch(
            "recursive_training.rules.hybrid_adapter.get_config"
        ) as mock_get_config:
            # Setup mocks
            mock_get_cost_controller.return_value = mock_cost_controller

            config_obj = MagicMock()
            config_obj.hybrid_rules = mock_config
            mock_get_config.return_value = config_obj

            # Reset singleton for testing
            HybridRuleAdapter._instance = None

            # Create adapter
            adapter = HybridRuleAdapter(mock_config)

            yield adapter


@dataclass
class _TestCondition(RuleCondition):
    """Test custom condition class."""

    threshold: float = 0.0
    additional_param: str = ""


@dataclass
class _TestAction(RuleAction):
    """Test custom action class."""

    duration: int = 0
    additional_param: str = ""


@dataclass
class DiscountRule(Rule):
    """Test custom rule class for discounts."""

    discount_type: str = "percentage"
    applies_to: List[str] = field(default_factory=list)


class TestHybridAdapterInitialization:
    """Tests for hybrid adapter initialization."""

    def test_singleton_pattern(self, mock_config):
        """Test that the adapter uses singleton pattern."""
        # Reset singleton for test
        HybridRuleAdapter._instance = None

        with patch(
            "recursive_training.rules.hybrid_adapter.get_config"
        ) as mock_get_config:
            config_obj = MagicMock()
            config_obj.hybrid_rules = mock_config
            mock_get_config.return_value = config_obj

            # Get two instances
            instance1 = get_hybrid_adapter()
            instance2 = get_hybrid_adapter()

            # Verify they are the same object
            assert instance1 is instance2

    def test_initialization_with_config(self, mock_config):
        """Test initialization with custom config."""
        with patch("recursive_training.rules.hybrid_adapter.get_cost_controller"):
            with patch("recursive_training.rules.hybrid_adapter.get_config"):
                # Reset singleton for test
                HybridRuleAdapter._instance = None

                # Create with custom config
                adapter = HybridRuleAdapter(mock_config)

                # Verify configuration was applied
                assert (
                    adapter.enable_dict_compatibility
                    == mock_config.enable_dict_compatibility
                )
                assert (
                    adapter.prefer_object_representation
                    == mock_config.prefer_object_representation
                )

    def test_class_registration(self, hybrid_adapter):
        """Test registering custom rule classes."""
        # Register a custom rule class
        hybrid_adapter.register_rule_class("discount", DiscountRule)

        # Verify registration
        assert "discount" in hybrid_adapter.rule_classes
        assert hybrid_adapter.rule_classes["discount"] == DiscountRule

        # Register a custom condition class
        hybrid_adapter.register_condition_class("test_condition", _TestCondition)

        # Verify registration
        assert "test_condition" in hybrid_adapter.condition_classes
        assert hybrid_adapter.condition_classes["test_condition"] == _TestCondition

        # Register a custom action class
        hybrid_adapter.register_action_class("test_action", _TestAction)

        # Verify registration
        assert "test_action" in hybrid_adapter.action_classes
        assert hybrid_adapter.action_classes["test_action"] == _TestAction

    def test_register_non_dataclass(self, hybrid_adapter):
        """Test error when registering a non-dataclass."""

        # Try to register a regular class
        class RegularClass:
            pass

        with pytest.raises(ValueError, match="must be a dataclass"):
            hybrid_adapter.register_rule_class("invalid", RegularClass)

        with pytest.raises(ValueError, match="must be a dataclass"):
            hybrid_adapter.register_condition_class("invalid", RegularClass)

        with pytest.raises(ValueError, match="must be a dataclass"):
            hybrid_adapter.register_action_class("invalid", RegularClass)


class TestDictToObjectConversion:
    """Tests for converting from dictionary to object representation."""

    def test_basic_conversion(self, hybrid_adapter, sample_rule_dict):
        """Test basic conversion from dictionary to object."""
        # Convert rule
        rule_obj = hybrid_adapter.to_object(sample_rule_dict)

        # Verify result is a Rule object
        assert isinstance(rule_obj, Rule)

        # Verify basic properties
        assert rule_obj.id == sample_rule_dict["id"]
        assert rule_obj.type == sample_rule_dict["type"]
        assert rule_obj.priority == sample_rule_dict["priority"]
        assert rule_obj.description == sample_rule_dict["description"]

        # Verify conditions
        assert len(rule_obj.conditions) == len(sample_rule_dict["conditions"])
        for i, condition in enumerate(rule_obj.conditions):
            assert isinstance(condition, RuleCondition)
            assert condition.type == sample_rule_dict["conditions"][i]["type"]
            assert (
                condition.parameters == sample_rule_dict["conditions"][i]["parameters"]
            )
            assert (
                condition.description
                == sample_rule_dict["conditions"][i]["description"]
            )

        # Verify actions
        assert len(rule_obj.actions) == len(sample_rule_dict["actions"])
        for i, action in enumerate(rule_obj.actions):
            assert isinstance(action, RuleAction)
            assert action.type == sample_rule_dict["actions"][i]["type"]
            assert action.parameters == sample_rule_dict["actions"][i]["parameters"]
            assert action.description == sample_rule_dict["actions"][i]["description"]

        # Verify metadata
        assert isinstance(rule_obj.metadata, RuleMetadata)
        assert (
            rule_obj.metadata.created_at == sample_rule_dict["metadata"]["created_at"]
        )
        assert rule_obj.metadata.version == sample_rule_dict["metadata"]["version"]
        assert rule_obj.metadata.status == sample_rule_dict["metadata"]["status"]
        assert rule_obj.metadata.tags == sample_rule_dict["metadata"]["tags"]

    def test_custom_rule_class_conversion(self, hybrid_adapter, sample_rule_dict):
        """Test conversion to a custom rule class."""
        # Register a custom rule class
        hybrid_adapter.register_rule_class("discount", DiscountRule)

        # Add custom fields to the dict
        discount_rule_dict = sample_rule_dict.copy()
        discount_rule_dict["discount_type"] = "percentage"
        discount_rule_dict["applies_to"] = ["electronics", "computers"]

        # Convert rule
        rule_obj = hybrid_adapter.to_object(discount_rule_dict)

        # Verify result is a DiscountRule object
        assert isinstance(rule_obj, DiscountRule)

        # Verify custom properties
        assert rule_obj.discount_type == "percentage"
        assert rule_obj.applies_to == ["electronics", "computers"]

    def test_custom_condition_action_conversion(self, hybrid_adapter, sample_rule_dict):
        """Test conversion with custom condition and action classes."""
        # Register custom classes
        hybrid_adapter.register_condition_class("comparison", _TestCondition)
        hybrid_adapter.register_action_class("set_value", _TestAction)

        # Add custom fields to the dict
        rule_dict = sample_rule_dict.copy()
        rule_dict["conditions"][0]["threshold"] = 50.0
        rule_dict["conditions"][0]["additional_param"] = "test_param"
        rule_dict["actions"][0]["duration"] = 30
        rule_dict["actions"][0]["additional_param"] = "test_action_param"

        # Convert rule
        rule_obj = hybrid_adapter.to_object(rule_dict)

        # Verify condition is converted to _TestCondition
        assert isinstance(rule_obj.conditions[0], _TestCondition)
        assert rule_obj.conditions[0].threshold == 50.0
        assert rule_obj.conditions[0].additional_param == "test_param"

        # Verify action is converted to _TestAction
        assert isinstance(rule_obj.actions[0], _TestAction)
        assert rule_obj.actions[0].duration == 30
        assert rule_obj.actions[0].additional_param == "test_action_param"

    def test_error_handling(self, hybrid_adapter):
        """Test error handling during conversion."""
        # Invalid rule missing required fields
        invalid_rule = {
            "id": "missing_fields_rule"
            # Missing other required fields
        }

        with pytest.raises(ConversionError):
            hybrid_adapter.to_object(invalid_rule)

        # Invalid nested structure
        invalid_nested = {
            "id": "invalid_nested",
            "type": "discount",
            "conditions": "not_a_list",  # Should be a list
            "actions": [],
        }

        with pytest.raises(ConversionError):
            hybrid_adapter.to_object(invalid_nested)


class TestObjectToDictConversion:
    """Tests for converting from object to dictionary representation."""

    def test_basic_conversion(self, hybrid_adapter, sample_rule_dict):
        """Test basic conversion from object to dictionary."""
        # First convert dict to object
        rule_obj = hybrid_adapter.to_object(sample_rule_dict)

        # Then convert back to dict
        result_dict = hybrid_adapter.to_dict(rule_obj)

        # Verify result is a dictionary
        assert isinstance(result_dict, dict)

        # Verify basic properties
        assert result_dict["id"] == sample_rule_dict["id"]
        assert result_dict["type"] == sample_rule_dict["type"]
        assert result_dict["priority"] == sample_rule_dict["priority"]
        assert result_dict["description"] == sample_rule_dict["description"]

        # Verify conditions
        assert len(result_dict["conditions"]) == len(sample_rule_dict["conditions"])
        for i, condition in enumerate(result_dict["conditions"]):
            assert condition["type"] == sample_rule_dict["conditions"][i]["type"]
            assert (
                condition["parameters"]
                == sample_rule_dict["conditions"][i]["parameters"]
            )
            assert (
                condition["description"]
                == sample_rule_dict["conditions"][i]["description"]
            )

        # Verify actions
        assert len(result_dict["actions"]) == len(sample_rule_dict["actions"])
        for i, action in enumerate(result_dict["actions"]):
            assert action["type"] == sample_rule_dict["actions"][i]["type"]
            assert action["parameters"] == sample_rule_dict["actions"][i]["parameters"]
            assert (
                action["description"] == sample_rule_dict["actions"][i]["description"]
            )

        # Verify metadata
        assert (
            result_dict["metadata"]["created_at"]
            == sample_rule_dict["metadata"]["created_at"]
        )
        assert (
            result_dict["metadata"]["version"]
            == sample_rule_dict["metadata"]["version"]
        )
        assert (
            result_dict["metadata"]["status"] == sample_rule_dict["metadata"]["status"]
        )
        assert result_dict["metadata"]["tags"] == sample_rule_dict["metadata"]["tags"]

    def test_custom_class_conversion(self, hybrid_adapter):
        """Test conversion of custom class objects to dictionaries."""
        # Create custom rule object
        custom_rule = DiscountRule(
            id="custom_rule",
            type="discount",
            conditions=[
                _TestCondition(
                    type="test_condition",
                    parameters={"variable": "price", "operator": ">", "value": 100},
                    threshold=75.0,
                    additional_param="test",
                )
            ],
            actions=[
                _TestAction(
                    type="test_action",
                    parameters={"variable": "discount", "value": 0.2},
                    duration=60,
                    additional_param="action_test",
                )
            ],
            discount_type="fixed",
            applies_to=["books", "electronics"],
        )

        # Convert to dictionary
        result_dict = hybrid_adapter.to_dict(custom_rule)

        # Verify result contains custom fields
        assert result_dict["discount_type"] == "fixed"
        assert result_dict["applies_to"] == ["books", "electronics"]
        assert result_dict["conditions"][0]["threshold"] == 75.0
        assert result_dict["conditions"][0]["additional_param"] == "test"
        assert result_dict["actions"][0]["duration"] == 60
        assert result_dict["actions"][0]["additional_param"] == "action_test"

    def test_error_handling(self, hybrid_adapter):
        """Test error handling during object to dict conversion."""

        # Try to convert a non-dataclass
        class RegularClass:
            def __init__(self):
                self.some_field = "value"

        with pytest.raises(ConversionError):
            hybrid_adapter.to_dict(RegularClass())


class TestAdaptionAndValidation:
    """Tests for rule adaptation and validation functionality."""

    def test_adapt_rule_to_preferred(self, hybrid_adapter, sample_rule_dict):
        """Test adapting rules to preferred representation."""
        # Set preference to object
        hybrid_adapter.prefer_object_representation = True

        # Adapt dict rule
        result = hybrid_adapter.adapt_rule(sample_rule_dict)

        # Verify result is an object
        assert isinstance(result, Rule)

        # Set preference to dict
        hybrid_adapter.prefer_object_representation = False

        # Adapt object rule
        rule_obj = hybrid_adapter.to_object(sample_rule_dict)
        result = hybrid_adapter.adapt_rule(rule_obj)

        # Verify result is a dict
        assert isinstance(result, dict)

    def test_validate_valid_rule(self, hybrid_adapter, sample_rule_dict):
        """Test validating a valid rule in both formats."""
        # Validate dict rule
        assert hybrid_adapter.validate_rule(sample_rule_dict) is True

        # Validate object rule
        rule_obj = hybrid_adapter.to_object(sample_rule_dict)
        assert hybrid_adapter.validate_rule(rule_obj) is True

    def test_validate_invalid_rule(self, hybrid_adapter):
        """Test validating an invalid rule."""
        # Invalid dict rule
        invalid_dict = {
            "id": "invalid_rule",
            # Missing required fields
        }
        assert hybrid_adapter.validate_rule(invalid_dict) is False

        # Invalid object (not a dataclass)
        class NotDataclass:
            pass

        assert hybrid_adapter.validate_rule(NotDataclass()) is False


class TestCostTracking:
    """Tests for cost tracking functionality."""

    def test_track_conversion_cost(
        self, hybrid_adapter, sample_rule_dict, mock_cost_controller
    ):
        """Test that conversion operations track costs."""
        # Convert dict to object
        hybrid_adapter.to_object(sample_rule_dict)

        # Verify cost was tracked
        assert mock_cost_controller.track_cost.called

        # Reset mock
        mock_cost_controller.track_cost.reset_mock()

        # Convert object to dict
        rule_obj = hybrid_adapter.to_object(sample_rule_dict)
        hybrid_adapter.to_dict(rule_obj)

        # Verify cost was tracked again
        assert mock_cost_controller.track_cost.called


if __name__ == "__main__":
    pytest.main()
