"""
strategos_digest_builder.py

Combines symbolic arc, capital deltas, and confidence into a foresight digest report.
Supports user configuration for included fields.

Usage:
    from strategos_digest_builder import build_digest
    digest_md = build_digest(batch, fmt="markdown", config={"fields": ["trace_id", "confidence"]})

Author: Pulse AI Engine
"""

from typing import List, Dict, Any
import json

DEFAULT_FIELDS = [
    "trace_id", "turn", "confidence", "fragility", "trust_label", "symbolic_tag", "overlays", "exposure_delta"
]

def build_digest(forecast_batch: List[Dict[str, Any]], fmt: str = "markdown", config: dict = None) -> str:
    """
    Given a batch of forecasts, return a digest string in the requested format.
    Supported formats: markdown, json, html

    Args:
        forecast_batch: List of forecast dicts.
        fmt: Output format ("markdown", "json", "html").
        config: Dict with customization options (e.g., fields to include).

    Returns:
        Digest string.
    """
    fields = config.get("fields") if config and "fields" in config else DEFAULT_FIELDS
    if not forecast_batch:
        return "# Strategos Digest\n\n_No forecasts available._" if fmt == "markdown" else "[]"
    if fmt == "json":
        return json.dumps([{k: f.get(k) for k in fields} for f in forecast_batch], indent=2)
    if fmt == "html":
        lines = ["<h1>Strategos Digest</h1>"]
        for f in forecast_batch:
            lines.append("<hr>")
            for k in fields:
                v = f.get(k, "N/A")
                lines.append(f"<b>{k}:</b> {v}<br>")
        return "\n".join(lines)
    # Default: markdown
    lines = ["# Strategos Digest\n"]
    for f in forecast_batch:
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for k in fields:
            v = f.get(k, "N/A")
            lines.append(f"{k.capitalize():<14}: {v}")
        lines.append("")
    return "\n".join(lines)

# Example usage:
# build_digest(batch, fmt="markdown", config={"fields": ["trace_id", "confidence"]})
