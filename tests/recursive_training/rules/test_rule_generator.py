"""
Tests for RecursiveRuleGenerator

This module contains unit tests for the RecursiveRuleGenerator class,
focusing on rule generation, GPT-Symbolic feedback loop, and cost control.
"""

import pytest
from unittest.mock import patch, MagicMock

from recursive_training.rules.rule_generator import (
    RecursiveRuleGenerator,
    RuleGenerationMethod,
    RuleGenerationStatus,
    get_rule_generator,
)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    # Use SimpleNamespace for attribute access
    from types import SimpleNamespace

    return SimpleNamespace(
        daily_cost_threshold_usd=10.0,
        max_rule_iterations=5,
        improvement_threshold=0.05,
        default_generation_method="gpt_symbolic_loop",
        enable_cost_control=True,
        metrics_tracking=True,
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
def sample_context():
    """Sample context for rule generation."""
    return {
        "domain": "ecommerce",
        "variables": ["price", "category", "quantity", "customer_type"],
        "target_behavior": "discount_calculation",
        "example_scenarios": [
            {
                "price": 120,
                "category": "electronics",
                "quantity": 1,
                "customer_type": "regular",
                "expected_discount": 0.0,
            },
            {
                "price": 200,
                "category": "electronics",
                "quantity": 2,
                "customer_type": "premium",
                "expected_discount": 0.1,
            },
            {
                "price": 50,
                "category": "books",
                "quantity": 5,
                "customer_type": "regular",
                "expected_discount": 0.05,
            },
        ],
    }


@pytest.fixture
def rule_generator(mock_config, mock_cost_controller, mock_metrics_store):
    """Fixture for rule generator with mocked dependencies."""
    with patch(
        "recursive_training.rules.rule_generator.get_cost_controller"
    ) as mock_get_cost_controller:
        with patch(
            "recursive_training.rules.rule_generator.get_metrics_store"
        ) as mock_get_metrics_store:
            with patch(
                "recursive_training.rules.rule_generator.get_config"
            ) as mock_get_config:
                # Setup mocks
                mock_get_cost_controller.return_value = mock_cost_controller
                mock_get_metrics_store.return_value = mock_metrics_store

                config_obj = MagicMock()
                config_obj.hybrid_rules = mock_config
                config_obj.cost_control = mock_config
                mock_get_config.return_value = config_obj

                # Reset singleton for testing
                RecursiveRuleGenerator._instance = None

                # Create generator
                generator = RecursiveRuleGenerator(mock_config)

                # Mock internal methods for testing
                generator._generate_with_gpt = MagicMock(
                    return_value={
                        "id": "test_rule_1",
                        "type": "discount",
                        "conditions": [
                            {"variable": "price", "operator": ">", "value": 100},
                            {
                                "variable": "category",
                                "operator": "==",
                                "value": "electronics",
                            },
                        ],
                        "actions": [{"variable": "discount", "value": 0.1}],
                        "priority": 1,
                        "description": "10% discount on electronics over $100",
                    }
                )

                generator._generate_with_symbolic = MagicMock(
                    return_value={
                        "id": "test_rule_2",
                        "type": "discount",
                        "conditions": [
                            {"variable": "quantity", "operator": ">", "value": 3}
                        ],
                        "actions": [{"variable": "shipping", "value": "free"}],
                        "priority": 2,
                        "description": "5% discount for bulk purchases",
                    }
                )

                generator._evaluate_rule_quality = MagicMock(
                    return_value=(
                        0.8,  # quality score
                        {
                            "overall_quality": 0.8,
                            "issues": [],
                            "improvement_suggestions": [
                                "Consider adding customer type conditions"
                            ],
                        },
                    )
                )

                generator._refine_rule = MagicMock(
                    side_effect=lambda rule, feedback: {
                        **rule,
                        "conditions": rule["conditions"]
                        + [
                            {
                                "variable": "customer_type",
                                "operator": "==",
                                "value": "premium",
                            }
                        ],
                        "description": f"Refined: {rule['description']}",
                    }
                )

                yield generator


class TestRuleGeneratorInitialization:
    """Tests for rule generator initialization."""

    def test_singleton_pattern(self, mock_config):
        """Test that the generator uses singleton pattern."""
        # Reset singleton for test
        RecursiveRuleGenerator._instance = None

        with patch(
            "recursive_training.rules.rule_generator.get_config"
        ) as mock_get_config:
            config_obj = MagicMock()
            config_obj.hybrid_rules = mock_config
            config_obj.cost_control = mock_config
            mock_get_config.return_value = config_obj

            # Get two instances
            instance1 = get_rule_generator()
            instance2 = get_rule_generator()

            # Verify they are the same object
            assert instance1 is instance2

    def test_initialization_with_config(self, mock_config):
        """Test initialization with custom config."""
        with patch("recursive_training.rules.rule_generator.get_cost_controller"):
            with patch("recursive_training.rules.rule_generator.get_metrics_store"):
                with patch("recursive_training.rules.rule_generator.get_config"):
                    # Reset singleton for test
                    RecursiveRuleGenerator._instance = None

                    # Create with custom config
                    generator = RecursiveRuleGenerator(mock_config)

                    # Verify configuration was applied
                    assert generator.max_iterations == mock_config.max_rule_iterations
                    assert (
                        generator.improvement_threshold
                        == mock_config.improvement_threshold
                    )
                    assert (
                        generator.generation_status == RuleGenerationStatus.NOT_STARTED
                    )


class TestRuleGeneration:
    """Tests for rule generation functionality."""

    def test_generate_rule_gpt_only(self, rule_generator, sample_context):
        """Test generating a rule using GPT-only method."""
        # Call generate_rule with GPT_ONLY method
        rule = rule_generator.generate_rule(
            context=sample_context,
            rule_type="discount",
            method=RuleGenerationMethod.GPT_ONLY,
        )

        # Verify the correct internal method was called
        rule_generator._generate_with_gpt.assert_called_once()
        rule_generator._generate_with_symbolic.assert_not_called()

        # Verify result structure
        assert "id" in rule
        assert "type" in rule
        assert "conditions" in rule
        assert "actions" in rule
        assert "metadata" in rule

        # Verify metadata
        assert rule["metadata"]["generator"] == "RecursiveRuleGenerator"
        assert rule["metadata"]["method"] == RuleGenerationMethod.GPT_ONLY.value
        assert rule["metadata"]["rule_type"] == "discount"

    def test_generate_rule_symbolic_only(self, rule_generator, sample_context):
        """Test generating a rule using Symbolic-only method."""
        # Call generate_rule with SYMBOLIC_ONLY method
        rule = rule_generator.generate_rule(
            context=sample_context,
            rule_type="discount",
            method=RuleGenerationMethod.SYMBOLIC_ONLY,
        )

        # Verify the correct internal method was called
        rule_generator._generate_with_symbolic.assert_called_once()
        rule_generator._generate_with_gpt.assert_not_called()

        # Verify result
        assert rule["type"] == "discount"
        assert len(rule["conditions"]) > 0
        assert len(rule["actions"]) > 0

    def test_generate_rule_gpt_symbolic_loop(self, rule_generator, sample_context):
        """Test generating a rule using GPT-Symbolic feedback loop."""
        # Call generate_rule with GPT_SYMBOLIC_LOOP method
        rule = rule_generator.generate_rule(
            context=sample_context,
            rule_type="discount",
            method=RuleGenerationMethod.GPT_SYMBOLIC_LOOP,
            max_iterations=3,
        )

        # Verify both methods were called in sequence
        rule_generator._generate_with_gpt.assert_called_once()
        rule_generator._evaluate_rule_quality.assert_called()

        # Verify result includes feedback-based refinements
        assert "Refined" in rule["description"]
        assert "customer_type" in str(rule["conditions"])

        # Verify metrics were tracked
        assert rule_generator.metrics["total_rules_generated"] > 0
        assert rule_generator.metrics["successful_rules"] > 0

    def test_cost_control_limits(
        self, rule_generator, sample_context, mock_cost_controller
    ):
        """Test cost control limits prevent rule generation."""
        # Make cost controller reject the request
        mock_cost_controller.can_make_api_call.return_value = False

        # Call generate_rule
        result = rule_generator.generate_rule(
            context=sample_context, rule_type="discount"
        )

        # Verify generation was canceled
        assert "error" in result
        assert rule_generator.generation_status == RuleGenerationStatus.CANCELED

    def test_error_handling(self, rule_generator, sample_context):
        """Test error handling during rule generation."""
        # Make _generate_with_gpt raise an exception
        rule_generator._generate_with_gpt.side_effect = Exception("Simulated error")

        # Call generate_rule
        result = rule_generator.generate_rule(
            context=sample_context, rule_type="discount"
        )

        # Verify error was handled
        assert "error" in result
        assert "Simulated error" in result["error"]
        assert rule_generator.generation_status == RuleGenerationStatus.FAILED
        assert rule_generator.metrics["failed_attempts"] > 0


class TestRuleRefinement:
    """Tests for rule refinement functionality."""

    def test_rule_improvement_threshold(self, rule_generator, sample_context):
        """Test rule generation stops when improvement is below threshold."""
        # Make quality evaluation return diminishing scores
        quality_scores = [0.8, 0.82, 0.83]  # Third improvement is below threshold
        feedback = {
            "overall_quality": 0.0,
            "issues": [],
            "improvement_suggestions": ["Add more conditions"],
        }

        rule_generator._evaluate_rule_quality.side_effect = [
            (score, {**feedback, "overall_quality": score}) for score in quality_scores
        ]

        # Call generate_rule
        _rule = rule_generator.generate_rule(
            context=sample_context,
            rule_type="discount",
            method=RuleGenerationMethod.GPT_SYMBOLIC_LOOP,
            max_iterations=5,  # More than we'll use
        )

        # Verify only the expected number of iterations occurred
        assert rule_generator._evaluate_rule_quality.call_count == 3

    def test_max_iterations_limit(self, rule_generator, sample_context):
        """Test rule generation stops at max iterations."""
        # Make quality evaluation always return good scores to force max iterations
        rule_generator._evaluate_rule_quality.return_value = (
            0.9,
            {
                "overall_quality": 0.9,
                "issues": [],
                "improvement_suggestions": ["Add more conditions"],
            },
        )

        # Call generate_rule with low max_iterations
        _rule = rule_generator.generate_rule(
            context=sample_context,
            rule_type="discount",
            method=RuleGenerationMethod.GPT_SYMBOLIC_LOOP,
            max_iterations=2,
        )

        # Verify only the specified number of iterations occurred
        assert rule_generator._evaluate_rule_quality.call_count <= 2


class TestStatusReporting:
    """Tests for status reporting functionality."""

    def test_get_generation_status(self, rule_generator, sample_context):
        """Test getting the generation status."""
        # Generate a rule
        _rule = rule_generator.generate_rule(
            context=sample_context, rule_type="discount"
        )

        # Get status
        status = rule_generator.get_generation_status()

        # Verify status
        assert status["status"] == RuleGenerationStatus.COMPLETED.value
        assert "metrics" in status
        assert status["metrics"]["total_rules_generated"] > 0

    def test_status_updates_during_generation(self, rule_generator, sample_context):
        """Test status is properly updated during generation phases."""
        # Replace generate_rule with a version that checks status
        original_generate = rule_generator.generate_rule
        status_checks = []

        def generate_with_checks(*args, **kwargs):
            # Record initial status
            status_checks.append(rule_generator.generation_status)

            # Call original
            result = original_generate(*args, **kwargs)

            # Record final status
            status_checks.append(rule_generator.generation_status)
            return result

        rule_generator.generate_rule = generate_with_checks

        # Generate a rule
        _rule = rule_generator.generate_rule(
            context=sample_context, rule_type="discount"
        )

        # Verify status transitions
        assert status_checks[0] == RuleGenerationStatus.NOT_STARTED
        assert status_checks[1] == RuleGenerationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main()
