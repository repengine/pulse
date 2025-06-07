#!/usr/bin/env python3
"""
Enhanced Retrodiction Curriculum Usage Example

This script demonstrates how to use the EnhancedRetrodictionCurriculum class
for adaptive data selection in historical retrodiction training.

Usage:
    python examples/historical_retrodiction/curriculum_example.py
"""

from recursive_training.advanced_metrics.retrodiction_curriculum import (
    EnhancedRetrodictionCurriculum
)
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Demonstrate EnhancedRetrodictionCurriculum usage."""
    print("=== Enhanced Retrodiction Curriculum Example ===\n")

    # 1. Basic curriculum initialization
    print("1. Creating curriculum with default configuration...")
    curriculum = EnhancedRetrodictionCurriculum()
    print(
        f"   Default uncertainty threshold multiplier: {
            curriculum.uncertainty_threshold_multiplier}")
    print(f"   Default sampling ratio: {curriculum.uncertainty_sampling_ratio}")

    # 2. Custom configuration
    print("\n2. Creating curriculum with custom configuration...")
    custom_config = {
        "uncertainty_threshold_multiplier": 2.0,
        "performance_degradation_threshold": 0.15,
        "uncertainty_sampling_ratio": 0.4,
        "cost_control": {"max_cost": 50.0}
    }
    custom_curriculum = EnhancedRetrodictionCurriculum(custom_config)
    print(
        f"   Custom uncertainty threshold multiplier: {
            custom_curriculum.uncertainty_threshold_multiplier}")
    print(f"   Custom sampling ratio: {custom_curriculum.uncertainty_sampling_ratio}")

    # 3. Data selection simulation
    print("\n3. Simulating data selection for training...")

    # Mock model for demonstration
    class MockModel:
        """Mock model for demonstration purposes."""

        def predict(self, data):
            return [0.5] * len(data)

        def predict_proba(self, data):
            return [[0.3, 0.7]] * len(data)

    mock_model = MockModel()

    # Select data for multiple iterations
    for iteration in range(3):
        print(f"\n   Iteration {iteration}:")

        # Select data for training
        selected_data = curriculum.select_data_for_training(
            current_iteration=iteration,
            recent_metrics={"mse": 0.1 + iteration * 0.05, "rule_type": "hybrid"},
            model=mock_model
        )
        print(f"     Selected {len(selected_data)} data points")

        # Update curriculum based on performance
        curriculum.update_curriculum(
            current_iteration=iteration,
            recent_metrics={"mse": 0.1 + iteration * 0.05, "rule_type": "hybrid"},
            model=mock_model
        )

        # Get current state
        state = curriculum.get_curriculum_state()
        print(f"     Updated sampling ratio: {state['uncertainty_sampling_ratio']:.3f}")
        print(
            f"     Updated threshold multiplier: {
                state['uncertainty_threshold_multiplier']:.3f}")

    # 4. Curriculum state inspection
    print("\n4. Final curriculum state:")
    final_state = curriculum.get_curriculum_state()
    for key, value in final_state.items():
        if key != "base_curriculum_state":  # Skip empty dict
            print(f"   {key}: {value}")

    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()
