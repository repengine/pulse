"""
numeric_transforms.py

Bidirectional transformations between numeric indicators and symbolic states.
This module bridges the gap between statistical data and symbolic overlays.

Key features:
- Convert statistical indicators to symbolic overlay values
- Map symbolic overlay states back to expected numeric impacts
- Track confidence scores for transformations
- Implement adaptive thresholds based on historical data
"""

import logging
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from engine.worldstate import WorldState

from symbolic_system.optimization import cached_symbolic
from symbolic_system.config import get_symbolic_config

logger = logging.getLogger(__name__)


class SymbolicNumericTransformer:
    """
    Bidirectional transformer between numeric indicators and symbolic states.

    This class handles:
    - Conversion from statistical indicators to symbolic overlay values
    - Mapping from symbolic states to expected numeric impacts
    - Confidence scoring for transformations
    - Adaptive threshold adjustment based on historical data
    """

    def __init__(self):
        """Initialize the transformer with default mappings"""
        self.confidence_scores = {}  # Store confidence in each transformation
        self.historical_stats = {}  # Store historical statistics for indicators
        self.adaptive_thresholds = {}  # Dynamic thresholds based on historical data
        self.transformation_history = []  # Store recent transformations for learning

        # Load adaptive thresholds from file if available
        self.threshold_file = os.path.join(
            os.path.dirname(__file__), "..", "config", "adaptive_thresholds.json"
        )
        self._load_thresholds()

    def _load_thresholds(self):
        """Load adaptive thresholds from file if available"""
        if os.path.exists(self.threshold_file):
            try:
                with open(self.threshold_file, "r") as f:
                    data = json.load(f)
                    self.adaptive_thresholds = data.get("thresholds", {})
                    self.historical_stats = data.get("statistics", {})
                    logger.info(
                        f"Loaded adaptive thresholds from {self.threshold_file}"
                    )
            except Exception as e:
                logger.error(f"Error loading adaptive thresholds: {e}")

    def _save_thresholds(self):
        """Save adaptive thresholds to file"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.threshold_file), exist_ok=True)

            data = {
                "thresholds": self.adaptive_thresholds,
                "statistics": self.historical_stats,
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.threshold_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved adaptive thresholds to {self.threshold_file}")
        except Exception as e:
            logger.error(f"Error saving adaptive thresholds: {e}")

    @cached_symbolic(ttl_seconds=300)
    def numeric_to_symbolic(
        self,
        indicator_name: str,
        value: float,
        historical_context: Optional[Dict[str, List[float]]] = None,
    ) -> Tuple[str, float, float]:
        """
        Transform a numeric indicator to a symbolic overlay value.

        Args:
            indicator_name: Name of the indicator
            value: Current value of the indicator
            historical_context: Optional historical values for context

        Returns:
            Tuple of (overlay_name, overlay_value, confidence)
        """
        # Get variable-specific mapping from configuration
        config = get_symbolic_config()
        variable_mapping = config.get_variable_mapping(indicator_name)

        # Use configured mapping if available
        if variable_mapping:
            if "high_impact" in variable_mapping and "threshold" in variable_mapping:
                if value > variable_mapping["threshold"]:
                    # Extract the primary overlay with highest impact
                    impact_overlays = variable_mapping["high_impact"]
                    if impact_overlays:
                        primary_overlay = impact_overlays[0]
                        # Scale value between threshold and 2*threshold to 0.5-1.0
                        overlay_value = 0.5 + min(
                            0.5,
                            (value - variable_mapping["threshold"])
                            / variable_mapping["threshold"]
                            * 0.5,
                        )
                        return primary_overlay, overlay_value, 0.8

        # Default mappings for common indicators if no specific mapping exists
        if indicator_name == "volatility_index" or indicator_name == "vix":
            # High volatility maps to fear/uncertainty
            thresh_high = self.adaptive_thresholds.get(f"{indicator_name}_high", 25)
            thresh_low = self.adaptive_thresholds.get(f"{indicator_name}_low", 15)

            if value > thresh_high:
                # High volatility -> high fear
                fear_value = min(0.5 + (value - thresh_high) / 20, 1.0)
                return "fear", fear_value, 0.8
            elif value < thresh_low:
                # Low volatility -> high confidence
                confidence_value = min(0.5 + (thresh_low - value) / 10, 1.0)
                return "confidence", confidence_value, 0.7

        elif indicator_name == "price_momentum" or "momentum" in indicator_name:
            # Positive momentum maps to hope, negative to despair
            if value > 0:
                hope_value = min(0.5 + value / 10, 1.0)
                return "hope", hope_value, 0.75
            else:
                despair_value = min(0.5 + abs(value) / 10, 1.0)
                return "despair", despair_value, 0.75

        elif "strength" in indicator_name or "rsi" in indicator_name.lower():
            # RSI and similar strength indicators
            if value > 70:
                # Overbought -> potential for despair (reversal)
                return "fatigue", min(0.5 + (value - 70) / 30, 1.0), 0.6
            elif value < 30:
                # Oversold -> potential for hope (reversal)
                return "hope", min(0.5 + (30 - value) / 30, 1.0), 0.6

        elif "trend" in indicator_name:
            # Trend strength indicators
            if value > 0.7:
                # Strong trend -> confidence
                return "trust", min(0.5 + value / 2, 1.0), 0.7
            elif value < 0.3:
                # Weak trend -> uncertainty
                return "fatigue", min(0.5 + (0.3 - value) / 0.3, 1.0), 0.6

        # Add the transformation to history for learning
        self._record_transformation(indicator_name, value, "neutral", 0.5, 0.3)

        # Default case - neutral influence
        return "neutral", 0.5, 0.3

    @cached_symbolic(ttl_seconds=300)
    def symbolic_to_numeric(self, overlay_name: str, value: float) -> Dict[str, float]:
        """
        Transform a symbolic overlay to expected impacts on numeric indicators.

        Args:
            overlay_name: Name of the symbolic overlay
            value: Current value of the overlay

        Returns:
            Dictionary of {indicator_name: expected_impact}
        """
        # Get configuration for potential custom mappings
        _config = get_symbolic_config()

        # Normalize value from 0-1 scale to -1 to 1 scale for impacts
        normalized_impact = value * 2 - 1

        # Core overlay mappings
        if overlay_name == "hope":
            return {
                "price_momentum": normalized_impact
                * 0.5,  # Positive hope -> positive momentum
                "trading_volume": value * 0.3
                + 0.2,  # More hope -> slightly higher volume
                "buy_pressure": value * 0.4 + 0.1,  # More hope -> more buying
                "volatility_index": (1 - value) * 10,  # More hope -> lower volatility
            }
        elif overlay_name == "despair":
            return {
                "price_momentum": -normalized_impact
                * 0.5,  # More despair -> negative momentum
                "trading_volume": value
                * 0.5,  # More despair -> can increase volume (panic)
                "sell_pressure": value * 0.4 + 0.1,  # More despair -> more selling
                "volatility_index": value * 15,  # More despair -> higher volatility
            }
        elif overlay_name == "rage":
            return {
                "trading_volume": value * 0.7 + 0.2,  # Rage -> high volume
                "volatility_index": value * 20,  # Rage -> high volatility
                "price_gap_frequency": value * 0.4,  # Rage -> more price gaps
            }
        elif overlay_name == "fatigue":
            return {
                "trading_volume": (1 - value) * 0.5,  # Fatigue -> lower volume
                "price_momentum_abs": (1 - value) * 0.3,  # Fatigue -> less momentum
                "volatility_index": (1 - value) * 5,  # Fatigue -> lower volatility
            }
        elif overlay_name == "trust":
            return {
                "trend_following": value * 0.5,  # Trust -> more trend following
                "volatility_index": (1 - value) * 8,  # Trust -> lower volatility
                "price_momentum_stability": value
                * 0.4,  # Trust -> more stable momentum
            }

        # For other overlays, check if they have a parent and inherit from it
        if overlay_name in ["hope", "despair", "rage", "fatigue", "trust"]:
            return {}

        # For unknown overlays, return empty impacts
        return {}

    def update_adaptive_thresholds(self, historical_data: Dict[str, List[float]]):
        """
        Update adaptive thresholds based on historical data distributions.

        Args:
            historical_data: Dictionary mapping indicator names to time series
        """
        updated = False

        for indicator_name, values in historical_data.items():
            if len(values) < 10:  # Need sufficient history
                continue

            # Store statistical summaries
            values_array = np.array(values)
            self.historical_stats[indicator_name] = {
                "mean": float(np.mean(values_array)),
                "std": float(np.std(values_array)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array)),
                "median": float(np.median(values_array)),
                "count": len(values),
                "last_updated": datetime.now().isoformat(),
            }

            # Update thresholds based on percentiles
            self.adaptive_thresholds[f"{indicator_name}_high"] = float(
                np.percentile(values_array, 80)
            )
            self.adaptive_thresholds[f"{indicator_name}_low"] = float(
                np.percentile(values_array, 20)
            )
            self.adaptive_thresholds[f"{indicator_name}_median"] = float(
                np.median(values_array)
            )

            logger.info(
                f"Updated adaptive thresholds for {indicator_name}: "
                f"low={self.adaptive_thresholds[f'{indicator_name}_low']:.2f}, "
                f"high={self.adaptive_thresholds[f'{indicator_name}_high']:.2f}"
            )

            updated = True

        if updated:
            self._save_thresholds()

    def _record_transformation(
        self,
        indicator_name: str,
        indicator_value: float,
        overlay_name: str,
        overlay_value: float,
        confidence: float,
    ):
        """
        Record a transformation for learning and confidence adjustment.

        Args:
            indicator_name: Name of the indicator
            indicator_value: Value of the indicator
            overlay_name: Name of the overlay
            overlay_value: Value assigned to the overlay
            confidence: Confidence in the transformation
        """
        # Add to transformation history
        self.transformation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "indicator_name": indicator_name,
                "indicator_value": indicator_value,
                "overlay_name": overlay_name,
                "overlay_value": overlay_value,
                "confidence": confidence,
            }
        )

        # Trim history if it gets too large
        if len(self.transformation_history) > 1000:
            self.transformation_history = self.transformation_history[-1000:]

        # Update confidence score for this transformation
        key = f"{indicator_name}_{overlay_name}"
        if key not in self.confidence_scores:
            self.confidence_scores[key] = confidence
        else:
            # Gradually update confidence with new data
            self.confidence_scores[key] = (
                0.9 * self.confidence_scores[key] + 0.1 * confidence
            )

    def apply_numeric_to_state(self, state: WorldState, indicators: Dict[str, float]):
        """
        Apply numeric indicators to update a WorldState's symbolic overlays.

        Args:
            state: WorldState to update
            indicators: Dictionary of indicator values

        Returns:
            List of applied transformations
        """
        transformations = []

        for indicator_name, value in indicators.items():
            # Transform the numeric indicator to symbolic
            overlay_name, overlay_value, confidence = self.numeric_to_symbolic(
                indicator_name, value
            )

            # Skip if the overlay doesn't exist in the state and it's not a standard one
            if not state.overlays.has_overlay(overlay_name):
                # If it's not a core overlay but has high confidence, create it
                if (
                    overlay_name not in ["hope", "despair", "rage", "fatigue", "trust"]
                    and confidence > 0.7
                ):
                    # Create the overlay as a dynamic secondary one
                    state.overlays.add_overlay(
                        name=overlay_name,
                        value=overlay_value,
                        category="secondary",
                        description=f"Discovered from {indicator_name}",
                    )
                else:
                    # Skip this transformation
                    continue

            # Calculate influence based on confidence
            current_value = getattr(state.overlays, overlay_name, 0.5)
            influence_weight = min(0.2, confidence / 5)  # 0.0-0.2 based on confidence

            # Update the overlay with weighted influence
            new_value = (
                current_value * (1 - influence_weight)
                + overlay_value * influence_weight
            )
            setattr(state.overlays, overlay_name, new_value)

            # Record the transformation
            transformations.append(
                {
                    "indicator": indicator_name,
                    "indicator_value": value,
                    "overlay": overlay_name,
                    "from_value": current_value,
                    "to_value": new_value,
                    "confidence": confidence,
                }
            )

            # Update transformation record
            self._record_transformation(
                indicator_name, value, overlay_name, new_value, confidence
            )

        return transformations

    def get_confidence(self, overlay_name: str) -> float:
        """Get overall confidence score for an overlay's current state"""
        # Average confidence scores related to this overlay
        related_scores = [
            v
            for k, v in self.confidence_scores.items()
            if k.endswith(f"_{overlay_name}")
        ]
        if related_scores:
            return sum(related_scores) / len(related_scores)
        return 0.5


# Create a singleton instance
_transformer_instance = None


def get_numeric_transformer() -> SymbolicNumericTransformer:
    """
    Get the singleton transformer instance.

    Returns:
        SymbolicNumericTransformer instance
    """
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = SymbolicNumericTransformer()
    return _transformer_instance
