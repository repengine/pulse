import pytest
from output.strategos_digest_builder import build_digest

@pytest.fixture
def sample_forecasts():
    return [
        {"trace_id": "t1", "confidence": 0.9, "symbolic_tag": "A", "overlays": {"hope": 1}, "turn": 1},
        {"trace_id": "t2", "confidence": 0.5, "symbolic_tag": "B", "overlays": {"hope": 0}, "turn": 2},
    ]

def test_digest_full_template(sample_forecasts):
    digest = build_digest(sample_forecasts, fmt="markdown", config={}, template="full")
    assert "Strategos Digest" in digest
    assert "trace_id" in digest or "Trace_id" in digest

def test_digest_short_template(sample_forecasts):
    digest = build_digest(sample_forecasts, fmt="markdown", config={}, template="short")
    assert "confidence" in digest

def test_digest_symbolic_only_template(sample_forecasts):
    digest = build_digest(sample_forecasts, fmt="markdown", config={}, template="symbolic_only")
    assert "overlays" in digest

def test_digest_empty():
    digest = build_digest([], fmt="markdown")
    assert "No forecasts available" in digest

def test_digest_json(sample_forecasts):
    digest = build_digest(sample_forecasts, fmt="json")
    assert digest.startswith("[") and digest.endswith("]")

def test_digest_html(sample_forecasts):
    digest = build_digest(sample_forecasts, fmt="html")
    assert "<h1>Strategos Digest</h1>" in digest
