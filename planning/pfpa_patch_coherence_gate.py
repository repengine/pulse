"""
PATCHED: pfpa_logger.py
Adds:
- PulseMirror coherence gate before logging forecast to memory archive.
"""

from trust.pulse_mirror_core import check_forecast_coherence

PFPA_ARCHIVE = []

def log_forecast_to_pfpa(forecast_obj, outcome=None, status="open"):
    """
    Logs forecast to PFPA memory if it passes PulseMirror coherence gate.
    """
    # Wrap in a list for coherence check
    status_flag, issues = check_forecast_coherence([forecast_obj])
    if status_flag == "fail":
        print(f"[PFPA] ❌ Forecast rejected due to coherence issues:")
        for i in issues:
            print("  -", i)
        return None

    entry = {
        "trace_id": forecast_obj.get("trace_id"),
        "status": status,
        "confidence": forecast_obj.get("confidence"),
        "symbolic_tag": forecast_obj.get("symbolic_tag"),
        "arc_label": forecast_obj.get("arc_label"),
        "trust_label": forecast_obj.get("trust_label"),
        "fragility": forecast_obj.get("fragility"),
        "forecast": forecast_obj.get("forecast"),
        "timestamp": forecast_obj.get("timestamp"),
        "outcome": outcome
    }

    PFPA_ARCHIVE.append(entry)
    print(f"[PFPA] ✅ Forecast stored: {entry['trace_id']}")
    return entry
