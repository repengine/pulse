"""
PATCHED: strategos_digest_builder.py
Adds:
- PulseMirror trust coherence gate before digest is finalized.
"""

from trust_system.pulse_mirror_core import check_forecast_coherence

def build_digest_from_forecasts(forecast_batch, mode="full"):
    """
    Main digest builder for Pulse forecasts.
    Ensures forecast batch coherence before compressing.

    Returns:
        dict digest if valid, else error dict
    """
    status, issues = check_forecast_coherence(forecast_batch)
    if status == "fail":
        return {
            "digest_status": "rejected",
            "reason": "Forecast batch failed coherence check",
            "issues": issues
        }

    # Proceed with normal digest construction
    digest = {
        "digest_status": "accepted",
        "digest_mode": mode,
        "summary": [],
        "symbolic_clusters": {},
        "arc_tags": {},
        "metadata": {
            "version": "v0.100.2",
            "source": "strategos_digest_builder.py"
        }
    }

    for f in forecast_batch:
        digest["summary"].append({
            "trace_id": f.get("trace_id"),
            "symbolic_tag": f.get("symbolic_tag"),
            "confidence": f.get("confidence"),
            "arc": f.get("arc_label"),
            "trust": f.get("trust_label")
        })

    return digest
