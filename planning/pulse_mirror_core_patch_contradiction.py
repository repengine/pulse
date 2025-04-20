"""
PATCHED: pulse_mirror_core.py
Enhancement:
Integrates forecast_contradiction_sentinel for contradiction validation.

If symbolic, capital, or trust contradictions are found in a batch,
they will be reported as coherence failures.
"""

from trust.forecast_contradiction_sentinel import scan_forecast_batch

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
