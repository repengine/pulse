"""
digest_trace_hooks.py

Optional module to enhance Strategos Digest entries with trace summaries.

Functions:
- summarize_trace_for_digest(trace_id): Returns a summary string for a trace, or None if not found.
- symbolic_digest_section(...): Returns symbolic digest section if overlays are enabled.

Robust to missing keys and malformed trace data.

Note: Overlays may contain sensitive or verbose data. Consider filtering/redacting if needed.
"""

from analytics.trace_audit_engine import load_trace
from typing import Optional
from engine.pulse_config import USE_SYMBOLIC_OVERLAYS
import logging

logger = logging.getLogger(__name__)


def summarize_trace_for_digest(
    trace_id: str, overlays_maxlen: int = 120
) -> Optional[str]:
    """
    Extracts a short summary from a trace ID for digest attachment.

    Args:
        trace_id (str): The trace identifier.
        overlays_maxlen (int): Maximum length for overlays string in summary.

    Returns:
        Optional[str]: Summary string or None if trace not found or malformed.

    Example:
        >>> summarize_trace_for_digest("trace_123")
        '(Trust: 0.95, Forks: 2, Overlays: {hope: 0.1, despair: 0.0, ...})'

    Note:
        Overlays may contain sensitive or verbose data. Consider filtering/redacting if needed.
    """
    try:
        trace = load_trace(trace_id)
        if not trace or "output" not in trace or not isinstance(trace["output"], dict):
            return None

        output = trace["output"]
        overlays = output.get("overlays", {})
        trust = output.get("trust", "N/A")
        forks = output.get("forks", [])

        # Truncate overlays if too large for summary
        overlays_str = str(overlays)
        if len(overlays_str) > overlays_maxlen:
            overlays_str = f"{overlays_str[: overlays_maxlen - 3]}..."

        return f"(Trust: {trust}, Forks: {len(forks)}, Overlays: {overlays_str})"
    except Exception as e:
        logger.warning(f"Failed to summarize trace {trace_id}: {e}")
        return None


def symbolic_digest_section(*args, **kwargs) -> str:
    """
    Returns symbolic digest section if overlays are enabled.

    Returns:
        str: Symbolic digest section, or empty string if overlays are disabled.
    """
    if not USE_SYMBOLIC_OVERLAYS:
        return ""
    # ...existing code...
    return ""


# --- Simple test for manual validation ---
if __name__ == "__main__":
    # Replace with a real trace_id for actual test
    test_id = "test_trace_id"
    print("Test summarize_trace_for_digest:", summarize_trace_for_digest(test_id))
