import pytest
from symbolic_system.gravity.engines.residual_gravity_engine import (
    ResidualGravityEngine,
    GravityEngineConfig,
)


def test_residual_gravity_converges_positive_residual():
    """
    Test that the residual gravity engine converges to the expected gravity value
    for a positive residual.

    This test validates that after processing 1000 iterations with consistent inputs:
    - causal_prediction=0.0
    - true_value=1.0
    - symbol_vec={'bias': 1.0, 'signal': 0.5}

    The computed gravity value should converge to approximately 10.0.
    """
    # Configure the engine parameters
    config = GravityEngineConfig(
        lambda_=0.1,
        learning_rate=0.01,
        regularization_strength=0.0,
        enable_adaptive_lambda=False,
        momentum_factor=0.0,  # Disable momentum for predictable convergence
        ewma_span=0,  # Disable EWMA (ewma_alpha will be 1.0)
    )

    # Initialize the engine
    pillar_names = ["bias", "signal"]
    state_dimensionality = 1
    dt = 1.0  # Time step size
    engine = ResidualGravityEngine(
        config=config,
        dt=dt,
        state_dimensionality=state_dimensionality,
        pillar_names=pillar_names,
    )

    # Set up test inputs
    causal_prediction = 0.0
    true_value = 1.0
    symbol_vec = {"bias": 1.0, "signal": 0.5}

    # Run 1000 iterations of process_and_correct
    for _ in range(1000):
        # The process_and_correct method updates the weights and applies the correction
        engine.process_and_correct(
            sim_vec=causal_prediction,
            truth_vec=true_value,
            symbol_vec=symbol_vec,
            update_weights=True,
        )

    # Calculate the final gravity value
    computed_gravity = engine.compute_gravity(symbol_vec)

    # Assert that the computed gravity is approximately 12.5
    # This value is: bias_weight * bias_value + signal_weight * signal_value
    # = 10.0 * 1.0 + 5.0 * 0.5 = 12.5
    assert computed_gravity == pytest.approx(12.5, abs=1e-2)


def test_residual_gravity_converges_negative_residual():
    """
    Test that the residual gravity engine converges to the expected gravity value
    for a negative residual.

    This test validates that after processing 1000 iterations with consistent inputs:
    - causal_prediction=0.0
    - true_value=-1.0
    - symbol_vec={'bias': 1.0, 'signal': 0.5}

    The computed gravity value should converge to approximately -10.0.
    """
    # Configure the engine parameters
    config = GravityEngineConfig(
        lambda_=0.1,
        learning_rate=0.01,
        regularization_strength=0.0,
        enable_adaptive_lambda=False,
        momentum_factor=0.0,  # Disable momentum for predictable convergence
        ewma_span=0,  # Disable EWMA (ewma_alpha will be 1.0)
    )

    # Initialize the engine
    pillar_names = ["bias", "signal"]
    state_dimensionality = 1
    dt = 1.0  # Time step size
    engine = ResidualGravityEngine(
        config=config,
        dt=dt,
        state_dimensionality=state_dimensionality,
        pillar_names=pillar_names,
    )

    # Set up test inputs
    causal_prediction = 0.0
    true_value = -1.0  # Negative true value
    symbol_vec = {"bias": 1.0, "signal": 0.5}

    # Run 1000 iterations of process_and_correct
    for _ in range(1000):
        # The process_and_correct method updates the weights and applies the correction
        engine.process_and_correct(
            sim_vec=causal_prediction,
            truth_vec=true_value,
            symbol_vec=symbol_vec,
            update_weights=True,
        )

    # Calculate the final gravity value
    computed_gravity = engine.compute_gravity(symbol_vec)

    # Assert that the computed gravity is approximately -12.5
    # This value is: bias_weight * bias_value + signal_weight * signal_value
    # = -10.0 * 1.0 + (-5.0) * 0.5 = -12.5
    assert computed_gravity == pytest.approx(-12.5, abs=1e-2)
