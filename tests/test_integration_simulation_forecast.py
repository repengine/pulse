# test_integration_simulation_forecast.py
"""
Integration test: run a simulation turn and check forecast licensing end-to-end.
"""
import pytest
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from forecast_output.forecast_licenser import license_forecast

def test_simulation_turn_and_license():
    state = WorldState()
    run_turn(state)
    # Simulate a forecast dict from state
    forecast = {
        "trace_id": "integration-test",
        "confidence": 0.96,
        "fragility": 0.2
    }
    result = license_forecast(forecast)
    assert result["license_status"] == "✅ Licensed"
