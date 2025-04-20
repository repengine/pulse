"""
pulse_mirror_core.py

Performs self-consistency checks on simulation state and forecast outputs.

Usage:
    warnings = check_coherence(forecasts)
"""

from typing import List, Dict, Callable
from trust_system.forecast_contradiction_sentinel import scan_forecast_batch

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

def check_trust_loop_integrity(forecasts: List[Dict]) -> List[str]:
    """
    Checks for trust loop integrity failures:
    - Trusted but low retrodiction or high fragility.
    - Fragile but high confidence.
    """
    issues = []
    for f in forecasts:
        conf = f.get("confidence", 0)
        frag = f.get("fragility", f.get("fragility_score", 0))
        retro = f.get("retrodiction_score", 1.0)
        label = f.get("trust_label", "")
        tid = f.get("trace_id", "unknown")
        if label == "🟢 Trusted" and retro < 0.5:
            issues.append(f"Trusted forecast {tid} has low retrodiction ({retro})")
        if label == "🟢 Trusted" and frag > 0.7:
            issues.append(f"Trusted forecast {tid} is fragile ({frag})")
        if label == "🔴 Fragile" and conf > 0.7:
            issues.append(f"Fragile forecast {tid} has high confidence ({conf})")
    return issues

def check_forecast_coherence(forecast_batch):
    """
    Perform PulseMirror coherence scan on forecast batch.

    Returns:
        - 'pass' or 'fail'
        - List of contradiction flags or summary
    """
    results = scan_forecast_batch(forecast_batch)
    symbolic = results["symbolic_conflicts"]
    capital = results["capital_conflicts"]
    trust = results["confidence_flags"]

    issues = []
    if symbolic:
        issues.extend([f"Symbolic: {x[0]} ⟷ {x[1]} – {x[2]}" for x in symbolic])
    if capital:
        issues.extend([f"Capital: {x[0]} ⟷ {x[1]} – {x[2]}" for x in capital])
    if trust:
        issues.extend([f"Trust mismatch: {t}" for t in trust])

    status = "fail" if issues else "pass"
    return status, issues
