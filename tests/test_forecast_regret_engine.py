"""
forecast_regret_engine.py

Runs past simulations through a regret lens, analyzes missed/wrong forecasts, builds learning loop.

Author: Pulse AI Engine
"""

from typing import List, Dict, Any, Optional
import pytest

DEFAULT_REGRET_THRESHOLD = 0.5


def analyze_regret(
    forecasts: List[Dict[str, Any]],
    actuals: Dict[str, Any],
    regret_threshold: float = DEFAULT_REGRET_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Compare forecasts to actuals, flag regret cases.

    Args:
        forecasts: List of forecast dicts (should include 'retrodiction_score').
        actuals: Dict of actual outcomes (used for advanced regret types).
        regret_threshold: Threshold below which a forecast is flagged as regret.

    Returns:
        List of regret dicts with trace_id, reason, and score.
    """
    regrets = []
    for f in forecasts:
        score = f.get("retrodiction_score", 1.0)
        if score < regret_threshold:
            regrets.append(
                {
                    "trace_id": f.get("trace_id"),
                    "reason": "Low retrodiction score",
                    "score": score,
                }
            )
        # Advanced: flag false positives/negatives if actuals provided
        if actuals:
            for asset, actual_val in actuals.get("capital", {}).items():
                forecast_val = f.get("forecast_capital", {}).get(asset)
                if forecast_val is not None:
                    # Under-forecasting
                    if forecast_val < actual_val * (1 - regret_threshold):
                        regrets.append(
                            {
                                "trace_id": f.get("trace_id"),
                                "reason": "Under-forecasted asset",
                                "asset": asset,
                                "forecast": forecast_val,
                                "actual": actual_val,
                            }
                        )
                    # Over-forecasting
                    if forecast_val > actual_val * (1 + regret_threshold):
                        regrets.append(
                            {
                                "trace_id": f.get("trace_id"),
                                "reason": "Over-forecasted asset",
                                "asset": asset,
                                "forecast": forecast_val,
                                "actual": actual_val,
                            }
                        )
    return regrets


def analyze_misses(
    forecasts: List[Dict[str, Any]], actuals: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Analyze causes of missed scenarios, including symbolic tag drift and missing overlays.

    Args:
        forecasts: List of forecast dicts.
        actuals: Dict of actual outcomes.

    Returns:
        List of miss dicts with trace_id and reason.
    """
    misses = []
    for f in forecasts:
        # Missed asset
        if "missed_asset" in f:
            misses.append(
                {
                    "trace_id": f.get("trace_id"),
                    "reason": "Missed asset",
                    "asset": f["missed_asset"],
                }
            )
        # Symbolic tag drift
        if actuals and "symbolic_tag" in f and "symbolic_tag" in actuals:
            if f["symbolic_tag"] != actuals["symbolic_tag"]:
                misses.append(
                    {
                        "trace_id": f.get("trace_id"),
                        "reason": "Symbolic tag drift",
                        "forecast_tag": f["symbolic_tag"],
                        "actual_tag": actuals["symbolic_tag"],
                    }
                )
        # Missed overlay
        if actuals and "overlay" in actuals and "forecast_overlay" in f:
            for k, v in actuals["overlay"].items():
                if abs(f["forecast_overlay"].get(k, 0) - v) > 0.1:
                    misses.append(
                        {
                            "trace_id": f.get("trace_id"),
                            "reason": "Missed overlay",
                            "overlay_key": k,
                            "forecast": f["forecast_overlay"].get(k, None),
                            "actual": v,
                        }
                    )
    return misses


def feedback_loop(
    regrets: List[Dict[str, Any]], log_path: Optional[str] = None
) -> None:
    """
    Adjust symbolic weights/rules based on regret analysis (stub).
    Optionally logs regrets to a file.

    Args:
        regrets: List of regret dicts.
        log_path: Optional path to write regrets as JSON.
    """
    print(f"Regret feedback: {len(regrets)} cases flagged for review.")
    if log_path:
        import json

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(regrets, f, indent=2)
            print(f"Regret feedback written to {log_path}")
        except Exception as e:
            print(f"Failed to write regret feedback: {e}")


def summarize_regrets(regrets: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Summarize regret reasons for quick diagnostics.

    Args:
        regrets: List of regret dicts.

    Returns:
        Dict mapping reason to count.
    """
    summary = {}
    for r in regrets:
        reason = r.get("reason", "unknown")
        summary[reason] = summary.get(reason, 0) + 1
    return summary


# ------------------- TEST CASES -------------------


@pytest.fixture
def sample_forecasts():
    return [
        {
            "trace_id": "a",
            "retrodiction_score": 0.4,
            "forecast_capital": {"nvda": 100, "msft": 200},
            "symbolic_tag": "hope",
            "forecast_overlay": {"hope": 0.5},
        },
        {
            "trace_id": "b",
            "retrodiction_score": 0.8,
            "forecast_capital": {"nvda": 120, "msft": 180},
            "symbolic_tag": "despair",
            "forecast_overlay": {"hope": 0.2},
        },
        {
            "trace_id": "c",
            "retrodiction_score": 0.3,
            "missed_asset": "spy",
            "symbolic_tag": "hope",
            "forecast_overlay": {"hope": 0.7},
        },
    ]


@pytest.fixture
def sample_actuals():
    return {
        "capital": {"nvda": 110, "msft": 210},
        "symbolic_tag": "hope",
        "overlay": {"hope": 0.6},
    }


def test_analyze_regret_basic(sample_forecasts, sample_actuals):
    regrets = analyze_regret(sample_forecasts, sample_actuals, regret_threshold=0.5)
    assert any(r["reason"] == "Low retrodiction score" for r in regrets)
    assert all("trace_id" in r for r in regrets)


def test_analyze_regret_over_under(sample_forecasts, sample_actuals):
    regrets = analyze_regret(sample_forecasts, sample_actuals, regret_threshold=0.1)
    # Should flag under/over forecasted assets
    assert any(
        r["reason"] in ("Under-forecasted asset", "Over-forecasted asset")
        for r in regrets
    )


def test_analyze_misses(sample_forecasts, sample_actuals):
    misses = analyze_misses(sample_forecasts, sample_actuals)
    assert any(m["reason"] == "Missed asset" for m in misses)
    assert any(m["reason"] == "Missed overlay" for m in misses)


def test_feedback_loop(tmp_path):
    regrets = [{"trace_id": "a", "reason": "Low retrodiction score", "score": 0.4}]
    log_path = tmp_path / "regrets.json"
    feedback_loop(regrets, log_path=str(log_path))
    import json

    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["trace_id"] == "a"


def test_summarize_regrets():
    regrets = [
        {"reason": "Low retrodiction score"},
        {"reason": "Low retrodiction score"},
        {"reason": "Missed asset"},
    ]
    summary = summarize_regrets(regrets)
    assert summary["Low retrodiction score"] == 2
    assert summary["Missed asset"] == 1
