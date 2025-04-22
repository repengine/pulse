"""
capital_digest_formatter.py

Generates markdown-formatted summaries of shortview capital forecasts and symbolic alignment insights.
Useful for Strategos Digest, CLI operator views, and learning log snapshots.

Author: Pulse v0.34

Changelog:
- Improved robustness and error handling.
- Enhanced documentation and inline comments.
- Added minimal inline tests.
"""

from typing import Dict, Any, Optional

def format_shortview_markdown(forecast: Dict[str, Any]) -> str:
    """
    Formats a symbolic-capital shortview forecast as markdown.

    Args:
        forecast (Dict[str, Any]): Forecast dictionary with keys:
            - duration_days (int, optional)
            - symbolic_fragility (float, optional)
            - symbolic_change (dict, optional)
            - capital_delta (dict, optional)
            - portfolio_alignment (dict, optional)

    Returns:
        str: Markdown-formatted summary.
    """
    lines = [
        "### 🧠 Shortview Capital Forecast"
    ]

    # Duration
    duration = forecast.get('duration_days')
    if isinstance(duration, int):
        lines.append(f"**Duration:** {duration} days")
    else:
        lines.append("**Duration:** ? days")

    # Fragility Index
    fragility = forecast.get('symbolic_fragility')
    try:
        fragility_str = f"{float(fragility):.3f}"
    except (TypeError, ValueError):
        fragility_str = "?"
    lines.append(f"**Fragility Index:** {fragility_str}")

    lines.append("")
    lines.append("**Symbolic Overlay Changes:**")
    symbolic_change = forecast.get("symbolic_change", {})
    if isinstance(symbolic_change, dict) and symbolic_change:
        for k, v in symbolic_change.items():
            try:
                lines.append(f"- `{k}` → {float(v):+0.3f}")
            except (TypeError, ValueError):
                lines.append(f"- `{k}` → ?")
    else:
        lines.append("- _No changes_")
    lines.append("")

    lines.append("**Capital Delta:**")
    capital_delta = forecast.get("capital_delta", {})
    if isinstance(capital_delta, dict) and capital_delta:
        for a, d in capital_delta.items():
            try:
                lines.append(f"- `{a}`: {float(d):+0.2f}")
            except (TypeError, ValueError):
                lines.append(f"- `{a}`: ?")
    else:
        lines.append("- _No delta_")
    lines.append("")

    tags = forecast.get("portfolio_alignment", {})
    if isinstance(tags, dict) and tags:
        lines.append("**Alignment Tags:**")
        for k, v in tags.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    else:
        lines.append("")

    return "\n".join(lines)

def render_portfolio_snapshot(snapshot: Dict[str, float]) -> str:
    """
    Renders a markdown snapshot of the portfolio.

    Args:
        snapshot (Dict[str, float]): Asset-value mapping.

    Returns:
        str: Markdown-formatted snapshot.
    """
    lines = ["### 💼 Portfolio Snapshot"]
    if not isinstance(snapshot, dict) or not snapshot:
        lines.append("_No assets_")
        return "\n".join(lines)
    for asset, val in snapshot.items():
        try:
            lines.append(f"- `{asset}`: {float(val):.2f}")
        except (TypeError, ValueError):
            lines.append(f"- `{asset}`: ?")
    return "\n".join(lines)

def summarize_alignment_tags(tags: Dict[str, str]) -> str:
    """
    Summarizes portfolio alignment tags as markdown.

    Args:
        tags (Dict[str, str]): Tag-value mapping.

    Returns:
        str: Markdown-formatted tags.
    """
    lines = ["### 🏷️ Portfolio Alignment"]
    if not isinstance(tags, dict) or not tags:
        lines.append("_No tags_")
        return "\n".join(lines)
    for k, v in tags.items():
        lines.append(f"- **{k}**: {v}")
    return "\n".join(lines)

# Minimal inline tests for demonstration
def _test():
    # Test with valid data
    mock = {
        "duration_days": 2,
        "symbolic_fragility": 0.287,
        "symbolic_change": {"hope": 0.1, "despair": -0.05},
        "capital_delta": {"SPY": 21.4, "BTC": -4.2},
        "portfolio_alignment": {"bias": "growth-aligned"}
    }
    print(format_shortview_markdown(mock))
    # Test with missing/invalid data
    mock2 = {
        "duration_days": None,
        "symbolic_fragility": "bad",
        "symbolic_change": {"hope": "bad", "fear": None},
        "capital_delta": {},
        "portfolio_alignment": {}
    }
    print(format_shortview_markdown(mock2))
    # Test snapshot and tags
    print(render_portfolio_snapshot({"SPY": 100.0, "BTC": "bad"}))
    print(render_portfolio_snapshot({}))
    print(summarize_alignment_tags({"bias": "neutral"}))
    print(summarize_alignment_tags({}))

if __name__ == "__main__":
    _test()
