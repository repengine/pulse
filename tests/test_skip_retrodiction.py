import pytest

from unittest.mock import patch, MagicMock
from simulation_engine.simulator_core import simulate_forward
from simulation_engine.worldstate import WorldState

@patch("simulation_engine.state_mutation.adjust_overlay")
@patch("simulation_engine.state_mutation.update_numeric_variable")
@patch("simulation_engine.state_mutation.adjust_capital")
def test_simulate_forward_retrodiction_strict(mock_adjust_capital, mock_update_numeric_variable, mock_adjust_overlay):
    """Test simulate_forward in retrodiction strict_injection mode with new APIs."""
    ws = WorldState()
    ws.overlays.hope = 0.1
    ws.variables.data["energy_cost"] = 1.0
    ws.capital.nvda = 100.0

    mock_loader = MagicMock()
    # Configure the mock to return the same value for the same turn number
    # regardless of how many times it's called, instead of using side_effect
    mock_loader.get_snapshot_by_turn = MagicMock(side_effect=lambda turn: {
        0: {"hope": 0.6, "energy_cost": 2.0, "nvda": 150.0},
        1: {"hope": 0.7, "energy_cost": 3.0, "nvda": 200.0},
        2: {"hope": 0.8, "energy_cost": 4.0, "nvda": 250.0}
    }.get(turn, {}))

    results = simulate_forward(
        ws,
        turns=3,
        retrodiction_mode=True,
        retrodiction_loader=mock_loader,
        injection_mode="strict_injection"
    )

    assert len(results) == 3
    assert mock_loader.get_snapshot_by_turn.call_count == 6  # Called twice per turn
    # Each turn: 1 overlay, 1 variable, 1 capital adjustment
    assert mock_adjust_overlay.call_count == 3
    assert mock_update_numeric_variable.call_count == 3
    assert mock_adjust_capital.call_count == 3

@patch("simulation_engine.state_mutation.adjust_overlay")
@patch("simulation_engine.state_mutation.update_numeric_variable")
@patch("simulation_engine.state_mutation.adjust_capital")
def test_simulate_forward_retrodiction_seed(mock_adjust_capital, mock_update_numeric_variable, mock_adjust_overlay):
    """Test simulate_forward in retrodiction seed_then_free mode (should not inject)."""
    ws = WorldState()
    mock_loader = MagicMock()
    # Configure the mock to return the same value for the same turn number
    # regardless of how many times it's called, instead of using side_effect
    mock_loader.get_snapshot_by_turn = MagicMock(side_effect=lambda turn: {
        0: {"hope": 0.6, "energy_cost": 2.0, "nvda": 150.0},
        1: {"hope": 0.7, "energy_cost": 3.0, "nvda": 200.0},
        2: {"hope": 0.8, "energy_cost": 4.0, "nvda": 250.0}
    }.get(turn, {}))

    results = simulate_forward(
        ws,
        turns=3,
        retrodiction_mode=True,
        retrodiction_loader=mock_loader,
        injection_mode="seed_then_free"
    )

    assert len(results) == 3
    # No injection in seed_then_free mode
    assert mock_adjust_overlay.call_count == 0
    assert mock_update_numeric_variable.call_count == 0
    assert mock_adjust_capital.call_count == 0