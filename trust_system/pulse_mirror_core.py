"""
pulse_mirror_core.py

Performs self-consistency checks on simulation state and forecast outputs.

Usage:
    warnings = check_coherence(forecasts)
"""

from typing import List, Dict, Callable

def check_coherence(forecasts: List[Dict], custom_checks: List[Callable[[Dict], str]] = None) -> List[str]:
    """
    Returns a list of detected inconsistencies or warnings.
    Optionally accepts custom check functions.
    """
    warnings = []
    for f in forecasts:
        if f.get("confidence", 0.5) < 0.2 and f.get("status") == "🟢 Trusted":
            warnings.append(f"Low confidence but trusted: {f.get('trace_id')}")
        if custom_checks:
            for check in custom_checks:
                msg = check(f)
                if msg:
                    warnings.append(msg)
    return warnings
