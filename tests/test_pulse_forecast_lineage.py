import os
import json
import tempfile
import pytest
from forecast_output import pulse_forecast_lineage as pfl

@pytest.fixture
def sample_forecasts():
    return [
        {"trace_id": "A", "parent_id": None, "symbolic_tag": "Hope", "confidence": 0.9, "symbolic_arc": {"hope": 0.7}, "prompt_hash": "abc12345"},
        {"trace_id": "B", "parent_id": "A", "symbolic_tag": "Hope", "confidence": 0.8, "symbolic_arc": {"hope": 0.6}},
        {"trace_id": "C", "parent_id": "A", "symbolic_tag": "Despair", "confidence": 0.5, "symbolic_arc": {"despair": 0.8}},
        {"trace_id": "D", "parent_id": "B", "symbolic_tag": "Hope", "confidence": 0.7, "symbolic_arc": {"hope": 0.5}},
    ]

def test_build_forecast_lineage(sample_forecasts):
    lineage = pfl.build_forecast_lineage(sample_forecasts)
    assert lineage == {"A": ["B", "C"], "B": ["D"]}

def test_detect_drift(sample_forecasts):
    drifts = pfl.detect_drift(sample_forecasts, drift_key="symbolic_tag")
    assert drifts == [
        "Drift: B → C [symbolic_tag: Hope → Despair]",
        "Drift: C → D [symbolic_tag: Despair → Hope]"
    ]

def test_flag_divergence(sample_forecasts):
    forks = pfl.flag_divergence(sample_forecasts)
    assert forks == ["Divergence: C from parent A"]

def test_fork_count(sample_forecasts):
    fc = pfl.fork_count(sample_forecasts)
    assert fc == {"A": 2, "B": 1}

def test_drift_score(sample_forecasts):
    ds = pfl.drift_score(sample_forecasts, drift_key="symbolic_tag")
    assert ds == {"A": 1, "B": 1}

def test_get_symbolic_arc(sample_forecasts):
    arc = pfl.get_symbolic_arc(sample_forecasts[0])
    assert arc == {"hope": 0.7}

def test_get_confidence(sample_forecasts):
    conf = pfl.get_confidence(sample_forecasts[0])
    assert conf == 0.9

def test_get_prompt_hash(sample_forecasts):
    ph = pfl.get_prompt_hash(sample_forecasts[0])
    assert ph == "abc12345"

def test_symbolic_color():
    assert pfl.symbolic_color("Hope") == "green"
    assert pfl.symbolic_color("Despair") == "red"
    assert pfl.symbolic_color(None) == "black"

def test_confidence_color():
    assert pfl.confidence_color(0.9) == "green"
    assert pfl.confidence_color(0.7) == "yellow"
    assert pfl.confidence_color(0.5) == "orange"
    assert pfl.confidence_color(0.2) == "red"
    assert pfl.confidence_color(None) == "black"

def test_export_graphviz_dot_color_by(sample_forecasts):
    if pfl.graphviz is None:
        pytest.skip("graphviz not installed")
    with tempfile.TemporaryDirectory() as tmpdir:
        for color_by in ("arc", "confidence", "none"):
            dot_path = os.path.join(tmpdir, f"lineage_{color_by}.dot")
            pfl.export_graphviz_dot(sample_forecasts, dot_path, color_by=color_by)
            assert os.path.exists(dot_path)
            with open(dot_path, "r") as f:
                content = f.read()
                assert "digraph" in content

def test_save_output(tmp_path):
    data = {"a": 1}
    out_file = tmp_path / "out.json"
    pfl.save_output(data, str(out_file))
    with open(out_file, "r") as f:
        loaded = json.load(f)
    assert loaded == data

def test_print_summary(capsys, sample_forecasts):
    pfl.print_summary(sample_forecasts)
    out = capsys.readouterr().out
    assert "Forecasts: 4" in out
    assert "Unique parents: 2" in out