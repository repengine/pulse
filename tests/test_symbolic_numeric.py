"""
test_symbolic_numeric.py

Tests for the bidirectional transforms between numeric indicators and symbolic states.
Validates the integration between statistical data and symbolic overlays.
"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import patch

# Add parent directory to path to import Pulse modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.worldstate import WorldState
from symbolic_system.numeric_transforms import get_numeric_transformer


class TestSymbolicNumericIntegration(unittest.TestCase):
    """Tests for the symbolic-numeric integration"""

    def setUp(self):
        """Set up test environment"""
        self.transformer = get_numeric_transformer()
        self.state = WorldState()

        # Set some specific overlay values for testing
        self.state.overlays.hope = 0.7
        self.state.overlays.despair = 0.3
        self.state.overlays.trust = 0.6

    def test_numeric_to_symbolic(self):
        """Test converting numeric indicators to symbolic overlays"""
        # Test volatility index -> fear transformation
        overlay_name, value, confidence = self.transformer.numeric_to_symbolic(
            "volatility_index", 30
        )
        self.assertEqual(overlay_name, "fear")
        self.assertGreater(value, 0.5)  # Should be higher than neutral
        self.assertGreater(confidence, 0.7)  # Should have good confidence

        # Test positive momentum -> hope transformation
        overlay_name, value, confidence = self.transformer.numeric_to_symbolic(
            "price_momentum", 5
        )
        self.assertEqual(overlay_name, "hope")
        self.assertGreater(value, 0.5)

        # Test negative momentum -> despair transformation
        overlay_name, value, confidence = self.transformer.numeric_to_symbolic(
            "price_momentum", -5
        )
        self.assertEqual(overlay_name, "despair")
        self.assertGreater(value, 0.5)

    def test_symbolic_to_numeric(self):
        """Test converting symbolic overlays to numeric impacts"""
        # Test hope -> numeric impacts
        impacts = self.transformer.symbolic_to_numeric("hope", 0.8)
        self.assertIn("price_momentum", impacts)
        self.assertGreater(impacts["price_momentum"], 0)  # Positive momentum
        self.assertIn("volatility_index", impacts)
        self.assertLess(impacts["volatility_index"], 10)  # Lower volatility

        # Test despair -> numeric impacts
        impacts = self.transformer.symbolic_to_numeric("despair", 0.8)
        self.assertIn("price_momentum", impacts)
        self.assertLess(impacts["price_momentum"], 0)  # Negative momentum
        self.assertIn("volatility_index", impacts)
        self.assertGreater(impacts["volatility_index"], 10)  # Higher volatility

    def test_apply_numeric_to_state(self):
        """Test applying numeric indicators to a world state"""
        # Create indicators
        indicators = {
            "volatility_index": 35,  # High volatility
            "price_momentum": 8,  # Strong positive momentum
            "rsi": 75,  # Overbought condition
        }

        # Save original values
        original_hope = self.state.overlays.hope

        # Apply to state
        transformations = self.transformer.apply_numeric_to_state(
            self.state, indicators
        )

        # Should have applied transformations
        self.assertGreater(len(transformations), 0)

        # Check for the expected effect of price_momentum on hope
        self.assertGreater(self.state.overlays.hope, original_hope)

        # Check if "fear" was created as a dynamic overlay due to high volatility
        self.assertTrue(
            hasattr(self.state.overlays, "fear")
            or "fear" in self.state.overlays._dynamic_overlays
        )

    def test_adaptive_thresholds(self):
        """Test updating adaptive thresholds with historical data"""
        # Create sample historical data
        historical_data = {
            "volatility_index": [10, 12, 15, 18, 25, 30, 20, 17, 14, 13],
            "price_momentum": [-5, -3, 0, 2, 5, 4, 3, -1, -2, -4],
        }

        # Update thresholds
        self.transformer.update_adaptive_thresholds(historical_data)

        # Check that thresholds were created
        self.assertIn("volatility_index_high", self.transformer.adaptive_thresholds)
        self.assertIn("volatility_index_low", self.transformer.adaptive_thresholds)

        # High threshold should be around 80th percentile
        self.assertAlmostEqual(
            self.transformer.adaptive_thresholds["volatility_index_high"],
            np.percentile([10, 12, 15, 18, 25, 30, 20, 17, 14, 13], 80),
            delta=0.1,
        )

    def test_dynamic_overlay_creation(self):
        """Test that new overlays can be dynamically created"""
        # Before applying numeric values, the "confidence" overlay shouldn't exist
        self.assertFalse(self.state.overlays.has_overlay("confidence"))

        # Apply a low volatility indicator that should create "confidence" overlay
        indicators = {"volatility_index": 10}  # Very low volatility

        # Apply with high confidence to ensure creation
        with patch.object(self.transformer, "numeric_to_symbolic") as mock_transform:
            mock_transform.return_value = ("confidence", 0.8, 0.9)  # high confidence
            self.transformer.apply_numeric_to_state(self.state, indicators)

        # Now the confidence overlay should exist
        self.assertTrue(self.state.overlays.has_overlay("confidence"))

        # And it should have a value close to 0.8
        confidence_value = getattr(
            self.state.overlays,
            "confidence",
            self.state.overlays._dynamic_overlays.get("confidence", 0),
        )
        self.assertGreater(confidence_value, 0.7)

    def test_confidence_scoring(self):
        """Test confidence scoring for transformations"""
        # Record some transformations
        self.transformer._record_transformation(
            "volatility_index", 30, "fear", 0.7, 0.8
        )
        self.transformer._record_transformation(
            "volatility_index", 25, "fear", 0.6, 0.7
        )

        # Get confidence for fear
        confidence = self.transformer.get_confidence("fear")

        # Should have non-zero confidence
        self.assertGreater(confidence, 0)

    def test_hierarchical_overlay_response(self):
        """Test that hierarchical overlays respond appropriately"""
        # Add a secondary overlay as child of hope
        self.state.overlays.add_overlay(
            name="optimism",
            value=0.5,
            category="secondary",
            parent="hope",
            description="Child of hope",
        )

        # Apply momentum that affects hope
        indicators = {"price_momentum": 7}  # Strong positive momentum
        self.transformer.apply_numeric_to_state(self.state, indicators)

        # Now check if optimism was affected indirectly
        # TODO: Implement this indirect effect in the numeric transformer


if __name__ == "__main__":
    unittest.main()
