import json
import pytest
from simulation_engine.historical_retrodiction_runner import load_historical_baseline
from core.variable_registry import get_default_variable_state

def test_load_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        'simulation_engine.historical_retrodiction_runner.TRUTH_PATH',
        str(tmp_path / "data.json")
    )
    result = load_historical_baseline("2099-01-01")
    assert result == get_default_variable_state()

def test_load_existing(tmp_path, monkeypatch):
    file = tmp_path / "data.json"
    data = {"date": "2020-01-01", "variables": {"fed_funds_rate": 0.07}}
    file.write_text(json.dumps(data))
    monkeypatch.setattr(
        'simulation_engine.historical_retrodiction_runner.TRUTH_PATH',
        str(file)
    )
    result = load_historical_baseline("2020-01-01")
    defaults = get_default_variable_state()
    assert result["fed_funds_rate"] == 0.07
    # Missing variables should be imputed from defaults
    assert result["inflation_index"] == defaults["inflation_index"]