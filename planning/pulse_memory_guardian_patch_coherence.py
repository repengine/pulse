"""
PATCHED: pulse_memory_guardian.py
Adds:
- Coherence-aware pruning: discards incoherent forecasts based on contradiction scan.
"""

from trust_system.pulse_mirror_core import check_forecast_coherence

def prune_incoherent_forecasts(memory_batch, verbose=True):
    """
    Discards forecasts that fail symbolic, capital, or trust coherence tests.

    Returns:
        list of retained coherent forecasts
    """
    retained = []
    for forecast in memory_batch:
        status, issues = check_forecast_coherence([forecast])
        if status == "pass":
            retained.append(forecast)
        elif verbose:
            print(f"[Guardian] Pruned forecast {forecast.get('trace_id')} due to:")
            for issue in issues:
                print("  -", issue)
    return retained
