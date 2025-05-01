"""
Tests for RecursiveRuleEvaluator

This module contains unit tests for the RecursiveRuleEvaluator class,
focusing on rule evaluation, quality assessment, and comparison functions.
"""

import pytest
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

from recursive_training.rules.rule_evaluator import (
    RecursiveRuleEvaluator,
    EvaluationScope,
    EvaluationStatus,
    get_rule_evaluator
)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "daily_cost_threshold_usd": 10.0,
        "min_acceptable_score": 0.7,
        "default_evaluation_scope": "comprehensive",
        "enable_cost_control": True,
        "metrics_tracking": True
    }


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
    """Sample context for rule evaluation."""
    return {
        "domain": "ecommerce",
        "variables": ["price", "category", "quantity", "customer_type"],
        "historical_data": [
            {"price": 120, "category": "electronics", "quantity": 1, "customer_type": "regular", "discount": 0.0},
            {"price": 200, "category": "electronics", "quantity": 2, "customer_type": "premium", "discount": 0.1},
            {"price": 50, "category": "books", "quantity": 5, "customer_type": "regular", "discount": 0.05}
        ]
    }


@pytest.fixture
def sample_valid_rule():
    """Sample valid rule for testing."""
    return {
        "id": "test_rule_1",
        "type": "discount",
        "conditions": [
            {"variable": "price", "operator": ">", "value": 100},
            {"variable": "category", "operator": "==", "value": "electronics"},
            {"variable": "customer_type", "operator": "==", "value": "premium"}
        ],
        "actions": [
            {"variable": "discount", "value": 0.1}
        ],
        "priority": 1,
        "description": "10% discount on electronics over $100 for premium customers"
    }


@pytest.fixture
def sample_invalid_rule():
    """Sample invalid rule for testing."""
    return {
        "id": "test_rule_2",
        "type": "discount",
        # Missing conditions field
        "actions": [
            {"variable": "discount", "value": 0.05}
        ]
    }


@pytest.fixture
def sample_rules_for_comparison():
    """Sample rules for comparison testing."""
    return [
        {
            "id": "rule_1",
            "type": "discount",
            "conditions": [
                {"variable": "price", "operator": ">", "value": 100}
            ],
            "actions": [
                {"variable": "discount", "value": 0.1}
            ],
            "priority": 1,
            "description": "Basic rule"
        },
        {
            "id": "rule_2",
            "type": "discount",
            "conditions": [
                {"variable": "price", "operator": ">", "value": 100},
                {"variable": "category", "operator": "==", "value": "electronics"}
            ],
            "actions": [
                {"variable": "discount", "value": 0.1}
            ],
            "priority": 1,
            "description": "More specific rule"
        },
        {
            "id": "rule_3",
            "type": "discount",
            "conditions": [
                {"variable": "price", "operator": ">", "value": 150},
                {"variable": "category", "operator": "==", "value": "electronics"},
                {"variable": "customer_type", "operator": "==", "value": "premium"}
            ],
            "actions": [
                {"variable": "discount", "value": 0.15}
            ],
            "priority": 2,
            "description": "Most specific rule"
        }
    ]


@pytest.fixture
def rule_evaluator(mock_config, mock_cost_controller, mock_metrics_store):
    """Fixture for rule evaluator with mocked dependencies."""
    with patch('recursive_training.rules.rule_evaluator.get_cost_controller') as mock_get_cost_controller:
        with patch('recursive_training.rules.rule_evaluator.get_metrics_store') as mock_get_metrics_store:
            with patch('recursive_training.rules.rule_evaluator.get_config') as mock_get_config:
                # Setup mocks
                mock_get_cost_controller.return_value = mock_cost_controller
                mock_get_metrics_store.return_value = mock_metrics_store
                
                config_obj = MagicMock()
                config_obj.hybrid_rules = mock_config
                config_obj.cost_control = mock_config
                mock_get_config.return_value = config_obj
                
                # Reset singleton for testing
                RecursiveRuleEvaluator._instance = None
                
                # Create evaluator
                evaluator = RecursiveRuleEvaluator(mock_config)
                
                # Set up test datasets
                evaluator.test_datasets = {
                    "syntax": [],
                    "logic": [
                        {"price": 120, "category": "electronics"},
                        {"price": 80, "category": "books"}
                    ],
                    "coverage": [
                        {"price": 120, "category": "electronics", "customer_type": "premium"},
                        {"price": 120, "category": "electronics", "customer_type": "regular"},
                        {"price": 50, "category": "books", "customer_type": "premium"}
                    ],
                    "performance": []
                }
                
                yield evaluator


class TestRuleEvaluatorInitialization:
    """Tests for rule evaluator initialization."""
    
    def test_singleton_pattern(self, mock_config):
        """Test that the evaluator uses singleton pattern."""
        # Reset singleton for test
        RecursiveRuleEvaluator._instance = None
        
        with patch('recursive_training.rules.rule_evaluator.get_config') as mock_get_config:
            config_obj = MagicMock()
            config_obj.hybrid_rules = mock_config
            config_obj.cost_control = mock_config
            mock_get_config.return_value = config_obj
            
            # Get two instances
            instance1 = get_rule_evaluator()
            instance2 = get_rule_evaluator()
            
            # Verify they are the same object
            assert instance1 is instance2
    
    def test_initialization_with_config(self, mock_config):
        """Test initialization with custom config."""
        with patch('recursive_training.rules.rule_evaluator.get_cost_controller'):
            with patch('recursive_training.rules.rule_evaluator.get_metrics_store'):
                with patch('recursive_training.rules.rule_evaluator.get_config'):
                    # Reset singleton for test
                    RecursiveRuleEvaluator._instance = None
                    
                    # Create with custom config
                    evaluator = RecursiveRuleEvaluator(mock_config)
                    
                    # Verify configuration was applied
                    assert evaluator.min_acceptable_score == mock_config["min_acceptable_score"]
                    assert evaluator.default_scope == EvaluationScope.COMPREHENSIVE
                    assert evaluator.evaluation_status == EvaluationStatus.NOT_STARTED


class TestRuleEvaluation:
    """Tests for rule evaluation functionality."""
    
    def test_evaluate_rule_syntax_only(self, rule_evaluator, sample_valid_rule, sample_context):
        """Test evaluating rule syntax only."""
        # Patch internal evaluation methods for controlled testing
        with patch.object(rule_evaluator, '_evaluate_syntax') as mock_syntax:
            # Setup mock return value
            mock_syntax.return_value = {
                "score": 0.9,
                "passed": True,
                "issues": [],
                "recommendations": [],
                "evaluation_cost": 0.0005
            }
            
            # Evaluate rule with SYNTAX scope
            result = rule_evaluator.evaluate_rule(
                rule=sample_valid_rule,
                context=sample_context,
                scope=EvaluationScope.SYNTAX
            )
            
            # Verify evaluation was performed
            mock_syntax.assert_called_once_with(sample_valid_rule)
            
            # Verify result structure
            assert result["rule_id"] == sample_valid_rule["id"]
            assert "overall_score" in result
            assert "details" in result
            assert "syntax" in result["details"]
            assert result["passed"] == True
    
    def test_evaluate_rule_comprehensive(self, rule_evaluator, sample_valid_rule, sample_context):
        """Test evaluating rule with comprehensive scope."""
        # Patch internal evaluation methods for controlled testing
        with patch.object(rule_evaluator, '_evaluate_syntax') as mock_syntax, \
             patch.object(rule_evaluator, '_evaluate_logic') as mock_logic, \
             patch.object(rule_evaluator, '_evaluate_coverage') as mock_coverage, \
             patch.object(rule_evaluator, '_evaluate_performance') as mock_performance:
            
            # Setup mock return values
            mock_syntax.return_value = {
                "score": 0.9,
                "passed": True,
                "issues": [],
                "recommendations": [],
                "evaluation_cost": 0.0005
            }
            
            mock_logic.return_value = {
                "score": 0.85,
                "passed": True,
                "issues": [],
                "recommendations": [{
                    "description": "Consider more specific conditions",
                    "importance": 1
                }],
                "evaluation_cost": 0.001
            }
            
            mock_coverage.return_value = {
                "score": 0.75,
                "passed": True,
                "issues": [{
                    "type": "limited_coverage",
                    "description": "Missing some customer types",
                    "severity": 1
                }],
                "recommendations": [],
                "evaluation_cost": 0.002
            }
            
            mock_performance.return_value = {
                "score": 0.95,
                "passed": True,
                "issues": [],
                "recommendations": [],
                "evaluation_cost": 0.0005
            }
            
            # Evaluate rule with COMPREHENSIVE scope
            result = rule_evaluator.evaluate_rule(
                rule=sample_valid_rule,
                context=sample_context,
                scope=EvaluationScope.COMPREHENSIVE
            )
            
            # Verify all evaluations were performed
            mock_syntax.assert_called_once()
            mock_logic.assert_called_once()
            mock_coverage.assert_called_once()
            mock_performance.assert_called_once()
            
            # Verify result contains all evaluations
            assert "syntax" in result["details"]
            assert "logic" in result["details"]
            assert "coverage" in result["details"]
            assert "performance" in result["details"]
            
            # Verify weighted score calculation
            expected_score = (
                (0.9 * 0.3) +  # syntax 30% weight
                (0.85 * 0.4) +  # logic 40% weight
                (0.75 * 0.2) +  # coverage 20% weight
                (0.95 * 0.1)    # performance 10% weight
            )
            assert result["overall_score"] == pytest.approx(expected_score, 0.01)
    
    def test_syntax_evaluation_failure(self, rule_evaluator, sample_invalid_rule, sample_context):
        """Test behavior when syntax evaluation fails."""
        # Use the real _evaluate_syntax method
        with patch.object(rule_evaluator, '_update_metrics'):
            # Evaluate invalid rule
            result = rule_evaluator.evaluate_rule(
                rule=sample_invalid_rule,
                context=sample_context,
                scope=EvaluationScope.COMPREHENSIVE
            )
            
            # Verify early return when syntax fails
            assert result["passed"] == False
            assert result["overall_score"] < rule_evaluator.min_acceptable_score
            assert len(result["issues"]) > 0
            assert "logic" not in result["details"]
            assert "coverage" not in result["details"]
            assert "performance" not in result["details"]
    
    def test_cost_limit_enforcement(self, rule_evaluator, sample_valid_rule, sample_context):
        """Test cost limits prevent full evaluation."""
        # Patch internal evaluation methods for controlled testing
        with patch.object(rule_evaluator, '_evaluate_syntax') as mock_syntax, \
             patch.object(rule_evaluator, '_evaluate_logic') as mock_logic, \
             patch.object(rule_evaluator, '_evaluate_coverage') as mock_coverage, \
             patch.object(rule_evaluator, '_evaluate_performance') as mock_performance:
            
            # Setup mock return values with high costs
            mock_syntax.return_value = {
                "score": 0.9,
                "passed": True,
                "issues": [],
                "recommendations": [],
                "evaluation_cost": 0.01  # High cost
            }
            
            mock_logic.return_value = {
                "score": 0.85,
                "passed": True,
                "issues": [],
                "recommendations": [],
                "evaluation_cost": 0.02  # Even higher cost
            }
            
            # Set a very low cost limit
            result = rule_evaluator.evaluate_rule(
                rule=sample_valid_rule,
                context=sample_context,
                scope=EvaluationScope.COMPREHENSIVE,
                cost_limit=0.015  # Only enough for syntax evaluation
            )
            
            # Verify syntax evaluation was performed but others were skipped due to cost
            mock_syntax.assert_called_once()
            mock_logic.assert_called_once()
            mock_coverage.assert_not_called()
            mock_performance.assert_not_called()
            
            # Verify result only contains syntax details
            assert "syntax" in result["details"]
            assert "logic" in result["details"]
            assert "coverage" not in result["details"]
            assert "performance" not in result["details"]
    
    def test_error_handling(self, rule_evaluator, sample_valid_rule, sample_context):
        """Test error handling during evaluation."""
        # Make _evaluate_syntax raise an exception
        with patch.object(rule_evaluator, '_evaluate_syntax', side_effect=Exception("Simulated error")):
            # Evaluate rule
            result = rule_evaluator.evaluate_rule(
                rule=sample_valid_rule,
                context=sample_context
            )
            
            # Verify error was handled
            assert "error" in result
            assert "Simulated error" in result["error"]
            assert result["passed"] == False
            assert rule_evaluator.evaluation_status == EvaluationStatus.FAILED


class TestRuleComparison:
    """Tests for rule comparison functionality."""
    
    def test_compare_rules(self, rule_evaluator, sample_rules_for_comparison, sample_context):
        """Test comparing multiple rules."""
        # Patch evaluate_rule to return different scores for different rules
        with patch.object(rule_evaluator, 'evaluate_rule') as mock_evaluate:
            # Setup mock to return different scores based on rule ID
            def evaluate_side_effect(rule, context, scope=None, cost_limit=None):
                score = 0.7
                if rule["id"] == "rule_2":
                    score = 0.8
                elif rule["id"] == "rule_3":
                    score = 0.9
                
                return {
                    "rule_id": rule["id"],
                    "evaluation_id": "test_eval",
                    "scope": str(scope.value) if scope else "comprehensive",
                    "overall_score": score,
                    "passed": True,
                    "details": {},
                    "issues": [],
                    "recommendations": []
                }
            
            mock_evaluate.side_effect = evaluate_side_effect
            
            # Compare rules
            result = rule_evaluator.compare_rules(
                rules=sample_rules_for_comparison,
                context=sample_context,
                scope=EvaluationScope.COMPREHENSIVE
            )
            
            # Verify each rule was evaluated
            assert mock_evaluate.call_count == len(sample_rules_for_comparison)
            
            # Verify comparison result structure
            assert "best_rule_id" in result
            assert "best_score" in result
            assert "evaluations" in result
            assert "improvements" in result
            
            # Verify rule_3 is identified as best
            assert result["best_rule_id"] == "rule_3"
            assert result["best_score"] == 0.9
            
            # Verify improvements calculation
            assert len(result["improvements"]) == 2  # Improvements from rule_1 and rule_2 to rule_3
            assert any(imp["from_rule"] == "rule_1" and imp["improvement"] == 0.2 for imp in result["improvements"])
            assert any(imp["from_rule"] == "rule_2" and imp["improvement"] == 0.1 for imp in result["improvements"])
    
    def test_compare_empty_rules(self, rule_evaluator, sample_context):
        """Test comparing an empty rules list."""
        result = rule_evaluator.compare_rules(
            rules=[],
            context=sample_context
        )
        
        # Verify error is returned
        assert "error" in result


class TestStatusReporting:
    """Tests for status reporting functionality."""
    
    def test_get_evaluation_status(self, rule_evaluator, sample_valid_rule, sample_context):
        """Test getting the evaluation status."""
        # Evaluate a rule
        with patch.object(rule_evaluator, '_evaluate_syntax') as mock_syntax:
            mock_syntax.return_value = {
                "score": 0.9,
                "passed": True,
                "issues": [],
                "recommendations": [],
                "evaluation_cost": 0.0005
            }
            
            rule_evaluator.evaluate_rule(
                rule=sample_valid_rule,
                context=sample_context,
                scope=EvaluationScope.SYNTAX
            )
            
            # Get status
            status = rule_evaluator.get_evaluation_status()
            
            # Verify status
            assert status["status"] == EvaluationStatus.COMPLETED.value
            assert "metrics" in status
            assert status["metrics"]["total_evaluations"] > 0
    
    def test_unknown_evaluation_id(self, rule_evaluator):
        """Test getting status for unknown evaluation ID."""
        status = rule_evaluator.get_evaluation_status("nonexistent_id")
        
        # Verify error is returned
        assert status["status"] == "unknown"
        assert "error" in status


if __name__ == "__main__":
    pytest.main()