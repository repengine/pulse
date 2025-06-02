"""
test_rule_adjustment.py

Tests for the trust system rule adjustment functionality, specifically the persistence
of weight changes to rule/arc registry and tag registry.
"""

import unittest
import os
import sys
from unittest.mock import patch

# Add parent directory to path to allow imports from trust_system
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from trust_system.rule_adjustment import adjust_rules_from_learning


class TestRuleAdjustment(unittest.TestCase):
    def setUp(self):
        # Create mock learning profile
        self.learning_profile = {
            "arc_performance": {
                "R001_EnergySpike": {
                    "rate": 0.2,  # Below threshold, should decrease weight
                    "weight": 0.7,
                },
                "R002_TrustRebound": {
                    "rate": 0.9,  # Above threshold, should increase weight
                    "weight": 0.6,
                },
            },
            "tag_performance": {
                "hope": {
                    "rate": 0.2,  # Below threshold, should decrease weight
                    "weight": 0.8,
                },
                "stability": {
                    "rate": 0.9,  # Above threshold, should increase weight
                    "weight": 0.5,
                },
            },
        }

    @patch("rules.rule_registry.RuleRegistry.update_trust_score")
    @patch("engine.variable_registry.VariableRegistry.register_variable")
    @patch(
        "trust_system.rule_adjustment.log_variable_weight_change"
    )  # Corrected patch target
    def test_adjust_rules_from_learning(
        self, mock_log, mock_register_variable, mock_update_trust_score
    ):
        # Mock the rule_registry's get_rules_by_symbolic_tag method
        with patch(
            "rules.rule_registry.RuleRegistry.get_rules_by_symbolic_tag"
        ) as mock_get_rules:
            # Set up mock rule data
            mock_get_rules.return_value = [
                {"rule_id": "R003", "symbolic_tags": ["hope"]},
                {"rule_id": "R004", "symbolic_tags": ["stability"]},
            ]

            # Call the function under test
            adjust_rules_from_learning(self.learning_profile)

            # Verify arc weight updates
            mock_update_trust_score.assert_any_call("R001_EnergySpike", -0.1)
            mock_update_trust_score.assert_any_call("R002_TrustRebound", 0.1)

            # Verify tag weight updates
            # For 'tag_weight_hope'
            hope_call_found = False
            for call_args in mock_register_variable.call_args_list:
                args, kwargs = call_args
                if args[0] == "tag_weight_hope":
                    hope_call_found = True
                    config_arg = args[1]
                    self.assertEqual(config_arg["type"], "trust_weight")
                    self.assertEqual(
                        config_arg["description"], "Trust weight for tag: hope"
                    )
                    self.assertAlmostEqual(config_arg["default"], 0.7, places=7)
                    self.assertEqual(config_arg["range"], [0.0, 1.0])
                    self.assertEqual(
                        config_arg["tags"], ["trust_weight", "symbolic_tag", "hope"]
                    )
                    break
            self.assertTrue(
                hope_call_found,
                "Call for 'tag_weight_hope' not found or did not match.",
            )

            # Similarly for 'tag_weight_stability'
            stability_call_found = False
            expected_stability_default = 0.6  # Based on self.learning_profile
            for call_args in mock_register_variable.call_args_list:
                args, kwargs = call_args
                if args[0] == "tag_weight_stability":
                    stability_call_found = True
                    config_arg = args[1]
                    self.assertEqual(config_arg["type"], "trust_weight")
                    self.assertEqual(
                        config_arg["description"], "Trust weight for tag: stability"
                    )
                    self.assertAlmostEqual(
                        config_arg["default"], expected_stability_default, places=7
                    )
                    self.assertEqual(config_arg["range"], [0.0, 1.0])
                    self.assertEqual(
                        config_arg["tags"],
                        ["trust_weight", "symbolic_tag", "stability"],
                    )
                    break
            self.assertTrue(
                stability_call_found,
                "Call for 'tag_weight_stability' not found or did not match.",
            )

            # Verify rules with tags got updated
            mock_update_trust_score.assert_any_call(
                "R003", -0.05
            )  # hope tag has poor performance
            mock_update_trust_score.assert_any_call(
                "R004", 0.05
            )  # stability tag has good performance

            # Verify logging happened
            self.assertEqual(mock_log.call_count, 4)  # 2 arcs + 2 tags


if __name__ == "__main__":
    unittest.main()
