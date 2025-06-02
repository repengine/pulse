"""
integration_example.py

Example of integrating the Symbolic Gravity system into a Pulse simulation.
This demonstrates how to transition from the overlay system to the
pillar-based gravity fabric approach.

Author: Pulse v3.5
"""

import logging
import numpy as np
from typing import Optional

from engine.simulation_executor import SimulationExecutor

from symbolic_system.gravity.gravity_config import ResidualGravityConfig
from symbolic_system.gravity.integration import (
    initialize_gravity_system,
    enable_gravity_system,
    pre_simulation_hook,
    post_simulation_hook,
    record_prediction_residual,
    apply_gravity_correction,
    get_gravity_fabric,
    get_pillar_system,
)

logger = logging.getLogger(__name__)


def configure_simulation_with_gravity(
    simulation: SimulationExecutor,
    gravity_config: Optional[ResidualGravityConfig] = None,
) -> None:
    """
    Configure a simulation executor to use the Symbolic Gravity system.

    Parameters
    ----------
    simulation : SimulationExecutor
        The simulation executor to configure
    gravity_config : ResidualGravityConfig, optional
        Configuration for the gravity system. Uses defaults if None.
    """
    # Initialize the gravity system
    initialize_gravity_system(gravity_config)

    # Enable the gravity system
    enable_gravity_system()

    # Register pre-simulation hook
    simulation.register_pre_step_hook(pre_simulation_hook)

    # Register post-simulation hook
    simulation.register_post_step_hook(post_simulation_hook)

    logger.info("Simulation configured to use Symbolic Gravity system")


def example_with_simulation() -> None:
    """
    Example of using the Symbolic Gravity system with a simulation.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create a simulation executor
    simulation = SimulationExecutor()

    # Configure with custom gravity settings
    gravity_config = ResidualGravityConfig(
        lambda_=0.3, eta=0.02, beta=0.85, regularization=0.001, debug_logging=True
    )

    # Configure simulation with gravity
    configure_simulation_with_gravity(simulation, gravity_config)

    # ... Rest of simulation setup ...

    # Inside the simulation loop
    for step in range(100):
        # Run simulation step
        simulation.step_forward()

        # Get current state
        state = simulation.get_current_state()

        # Example of directly adjusting a pillar based on simulation outcomes
        if getattr(state, "market_stress", 0) > 0.7:
            pillar_system = get_pillar_system()
            pillar_system.adjust_pillar("despair", 0.05)
            pillar_system.adjust_pillar("hope", -0.03)

        # Example of recording residuals for a variable
        predicted_value = getattr(state, "spx_predicted", 0.0)
        actual_value = getattr(state, "spx_actual", 0.0)

        if actual_value != 0.0:  # Only record if we have actual data
            record_prediction_residual("SPX", predicted_value, actual_value)

        # Example of applying a correction to a prediction
        raw_prediction = getattr(state, "vix_predicted", 0.0)
        corrected_prediction = apply_gravity_correction("VIX", raw_prediction)

        # Store the corrected prediction
        state.vix_corrected = corrected_prediction

    # Print gravity system status at the end
    fabric = get_gravity_fabric()
    report = fabric.generate_diagnostic_report()

    print("Simulation completed with Symbolic Gravity")
    print(
        f"SPX Improvement: {
            report['fabric_stats']['variable_improvements'].get(
                'SPX',
                {}).get(
                'percentage_improvement',
                0):.2f}%")
    print(
        f"VIX Improvement: {
            report['fabric_stats']['variable_improvements'].get(
                'VIX',
                {}).get(
                'percentage_improvement',
                0):.2f}%")


def example_standalone_usage() -> None:
    """
    Example of using the Symbolic Gravity system as a standalone component.
    """
    # Initialize with default settings
    initialize_gravity_system()
    enable_gravity_system()

    # Get system components
    pillar_system = get_pillar_system()
    fabric = get_gravity_fabric()

    # Set initial pillar values
    pillar_system.adjust_pillar("hope", 0.4)
    pillar_system.adjust_pillar("despair", 0.3)
    pillar_system.adjust_pillar("rage", 0.1)

    # Simulate some predictions and residuals
    for i in range(50):
        # Simulate a prediction for SPX
        true_value = 3500 + i * 10 + np.random.normal(0, 20)

        # Model predicts with a systematic bias when hope is high
        model_bias = 5.0 * pillar_system.get_pillar_value("hope")
        predicted_value = true_value - model_bias + np.random.normal(0, 10)

        # Record the residual
        fabric.record_residual("SPX", predicted_value, true_value)

        # Change pillar values for the next iteration
        if i % 10 == 0:
            pillar_system.adjust_pillar("hope", 0.05)
            pillar_system.adjust_pillar("despair", -0.03)

    # Print results
    print("\nStandalone Example Results:")

    # Get latest prediction residuals
    recent_residuals = fabric.get_recent_residuals("SPX", 5)
    print("\nRecent SPX Residuals:")
    for point in recent_residuals:
        print(
            f"  Predicted: {point.predicted:.2f}, Actual: {point.actual:.2f}, "
            f"Residual: {point.residual:.2f}, Corrected: {point.corrected:.2f}"
        )

    # Get improvement metrics
    original_mae, corrected_mae = fabric.get_mean_absolute_error("SPX")
    improvement_pct = fabric.get_improvement_percentage("SPX")

    print(f"\nOriginal MAE: {original_mae:.2f}")
    print(f"Corrected MAE: {corrected_mae:.2f}")
    print(f"Improvement: {improvement_pct:.2f}%")

    # Get pillar contributions
    contributions = fabric.get_pillar_contributions()
    print("\nPillar Contributions:")
    for pillar, contribution in contributions.items():
        if abs(contribution) > 0.01:
            print(f"  {pillar}: {contribution:.4f}")

    # Get engine weights
    top_contributors = fabric.gravity_engine.get_top_contributors()
    print("\nTop Contributing Pillars:")
    for name, weight in top_contributors:
        print(f"  {name}: {weight:.4f}")


if __name__ == "__main__":
    # Run the standalone example
    example_standalone_usage()

    # Uncomment to run the simulation example
    # example_with_simulation()
