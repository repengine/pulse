"""
test_rule_adjustment.py

Tests for the trust system rule adjustment functionality, specifically the persistence
of weight changes to rule/arc registry and tag registry.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports from trust_system
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trust_system.rule_adjustment import adjust_rules_from_learning
from simulation_engine.rules.rule_registry import RuleRegistry
from core.variable_registry import registry as variable_registry


class TestRuleAdjustment(unittest.TestCase):
    def setUp(self):
        # Create mock learning profile
        self.learning_profile = {
            "arc_performance": {
                "R001_EnergySpike": {
                    "rate": 0.2,  # Below threshold, should decrease weight
                    "weight": 0.7
                },
                "R002_TrustRebound": {
                    "rate": 0.9,  # Above threshold, should increase weight
                    "weight": 0.6
                }
            },
            "tag_performance": {
                "hope": {
                    "rate": 0.2,  # Below threshold, should decrease weight
                    "weight": 0.8
                },
                "stability": {
                    "rate": 0.9,  # Above threshold, should increase weight
                    "weight": 0.5
                }
            }
        }

    @patch('simulation_engine.rules.rule_registry.RuleRegistry.update_trust_score')
    @patch('core.variable_registry.registry.register_variable')
    @patch('core.pulse_learning_log.log_variable_weight_change')
    def test_adjust_rules_from_learning(self, mock_log, mock_register_variable, mock_update_trust_score):
        # Mock the rule_registry's get_rules_by_symbolic_tag method
        with patch('simulation_engine.rules.rule_registry.RuleRegistry.get_rules_by_symbolic_tag') as mock_get_rules:
            # Set up mock rule data
            mock_get_rules.return_value = [
                {"rule_id": "R003", "symbolic_tags": ["hope"]},
                {"rule_id": "R004", "symbolic_tags": ["stability"]}
            ]
            
            # Call the function under test
            adjust_rules_from_learning(self.learning_profile)
            
            # Verify arc weight updates
            mock_update_trust_score.assert_any_call("R001_EnergySpike", -0.1)
            mock_update_trust_score.assert_any_call("R002_TrustRebound", 0.1)
            
            # Verify tag weight updates
            mock_register_variable.assert_any_call(
                "tag_weight_hope",
                {
                    "type": "trust_weight", 
                    "description": "Trust weight for tag: hope",
                    "default": 0.7,  # 0.8 - 0.1
                    "range": [0.0, 1.0],
                    "tags": ["trust_weight", "symbolic_tag", "hope"]
                }
            )
            mock_register_variable.assert_any_call(
                "tag_weight_stability",
                {
                    "type": "trust_weight", 
                    "description": "Trust weight for tag: stability",
                    "default": 0.6,  # 0.5 + 0.1
                    "range": [0.0, 1.0],
                    "tags": ["trust_weight", "symbolic_tag", "stability"]
                }
            )
            
            # Verify rules with tags got updated
            mock_update_trust_score.assert_any_call("R003", -0.05)  # hope tag has poor performance
            mock_update_trust_score.assert_any_call("R004", 0.05)   # stability tag has good performance
            
            # Verify logging happened
            self.assertEqual(mock_log.call_count, 4)  # 2 arcs + 2 tags


if __name__ == "__main__":
    unittest.main()