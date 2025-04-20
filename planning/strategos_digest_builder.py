"""
strategos_digest_builder.py

Combines symbolic arc, capital deltas, and confidence into a foresight digest report.

Usage:
    from strategos_digest_builder import build_digest
    digest_md = build_digest(batch, fmt="markdown")

Author: Pulse AI Engine
"""

from typing import List, Dict, Any
import json
from trust_system.pulse_mirror_core import check_forecast_coherence

def build_digest(forecast_batch: List[Dict[str, Any]], fmt: str = "markdown") -> str:
    """
    Given a batch of forecasts, return a digest string in the requested format.
    Supported formats: markdown, json, html

    Args:
        forecast_batch: List of forecast dicts.
        fmt: Output format ("markdown", "json", "html").

    Returns:
        Digest string.
    """
    # Add trust coherence gate
    status, issues = check_forecast_coherence(forecast_batch)
    if status == "fail":
        return json.dumps({
            "digest_status": "rejected",
            "reason": "Forecast batch failed coherence check",
            "issues": issues
        }, indent=2) if fmt == "json" else (
            "# Strategos Digest\n\n❌ Forecast batch failed coherence check.\n" +
            "\n".join(f"- {i}" for i in issues)
        )

    if not forecast_batch:
        return "# Strategos Digest\n\n_No forecasts available._" if fmt == "markdown" else "[]"
    if fmt == "json":
        return json.dumps(forecast_batch, indent=2)
    if fmt == "html":
        lines = ["<h1>Strategos Digest</h1>"]
        for f in forecast_batch:
            lines.append("<hr>")
            lines.append(f"<b>Trace ID:</b> {f.get('trace_id', 'N/A')}<br>")
            lines.append(f"<b>Turn:</b> {f.get('turn', 'N/A')}<br>")
            lines.append(f"<b>Confidence:</b> {f.get('confidence', 'N/A')}<br>")
            lines.append(f"<b>Fragility:</b> {f.get('fragility', 'N/A')}<br>")
            lines.append(f"<b>Trust Label:</b> {f.get('trust_label', 'N/A')}<br>")
            lines.append(f"<b>Symbolic Tag:</b> {f.get('symbolic_tag', 'N/A')}<br>")
            overlays = f.get("overlays") or f.get("symbolic_change")
            if overlays:
                lines.append(f"<b>Symbolic Drift:</b> {overlays}<br>")
            capital = f.get("exposure_delta") or f.get("capital_delta")
            if capital:
                lines.append("<b>Exposure Delta:</b><ul>")
                for k, v in capital.items():
                    lines.append(f"<li>{k} → {v:.2f}</li>")
                lines.append("</ul>")
        return "\n".join(lines)
    # Default: markdown
    lines = ["# Strategos Digest\n"]
    for f in forecast_batch:
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"Trace ID      : {f.get('trace_id', 'N/A')}")
        lines.append(f"Turn          : {f.get('turn', 'N/A')}")
        lines.append(f"Confidence    : {f.get('confidence', 'N/A')}")
        lines.append(f"Fragility     : {f.get('fragility', 'N/A')}")
        lines.append(f"Trust Label   : {f.get('trust_label', 'N/A')}")
        lines.append(f"Symbolic Tag  : {f.get('symbolic_tag', 'N/A')}")
        overlays = f.get("overlays") or f.get("symbolic_change")
        if overlays:
            lines.append("Symbolic Drift:")
            lines.append(f"  {overlays}")
        capital = f.get("exposure_delta") or f.get("capital_delta")
        if capital:
            lines.append("Exposure Delta:")
            for k, v in capital.items():
                lines.append(f"  {k}  → {v:.2f}")
        lines.append("")
    return "\n".join(lines)
