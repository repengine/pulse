"""
digest_trace_hooks.py

Optional module to enhance Strategos Digest entries with trace summaries.
"""

from memory.trace_audit_engine import load_trace
from typing import Optional, Dict, Any


def summarize_trace_for_digest(trace_id: str) -> Optional[str]:
    """
    Extracts a short summary from a trace ID for digest attachment.
    """
    trace = load_trace(trace_id)
    if not trace:
        return None

    overlays = trace["output"].get("overlays", {})
    trust = trace["output"].get("trust", "N/A")
    forks = trace["output"].get("forks", [])

    summary = f"(Trust: {trust}, Forks: {len(forks)}, Overlays: {overlays})"
    return summary
