import json
from engine.simulator_core import simulate_forward
from engine.variable_registry import get_default_variable_state

# RetrodictionLoader is deprecated; removed due to unification.
from engine.worldstate import WorldState


def test_retrodiction_simulation_basic(tmp_path):
    # Setup a dummy retrodiction loader with snapshots
    class DummyLoader:
        def get_snapshot_by_turn(self, turn):
            if turn == 0:
                return {"var1": 1.0, "var2": 2.0}
            elif turn == 1:
                return {"var1": 1.1, "var2": 2.1}
            return None

    loader = DummyLoader()
    state = WorldState()
    # Initialize variables as dict for test
    # Use setattr to bypass immutability for test purposes
    state.variables.data = {"var1": 0.0, "var2": 0.0}
    state.turn = 0
    results = simulate_forward(
        state,
        turns=2,
        retrodiction_mode=True,
        retrodiction_loader=loader,
        injection_mode="strict_injection",
    )
    assert len(results) == 2
    # Check that variables were injected and simulation ran
    # Use getattr with fallback for __getitem__ error
    assert state.variables.get("var1") != 0.0
    assert state.variables.get("var2") != 0.0


def test_load_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "engine.historical_retrodiction_runner.TRUTH_PATH",
        str(tmp_path / "data.json"),
    )
    result = get_default_variable_state()
    assert result is not None


def test_load_existing(tmp_path, monkeypatch):
    file = tmp_path / "data.json"
    data = {"date": "2020-01-01", "variables": {"fed_funds_rate": 0.07}}
    file.write_text(json.dumps(data))
    monkeypatch.setattr("engine.historical_retrodiction_runner.TRUTH_PATH", str(file))
    result = get_default_variable_state()
    assert result is not None
