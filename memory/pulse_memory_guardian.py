"""
pulse_memory_guardian.py

Manages retention and pruning of forecast memory.

Usage:
    prune_memory(memory, max_entries=1000, dry_run=True)
"""

from memory.forecast_memory import ForecastMemory
from trust_system.pulse_mirror_core import check_forecast_coherence

def prune_memory(memory: ForecastMemory, max_entries: int = 1000, dry_run: bool = False):
    """
    Prunes memory to retain only the most recent max_entries forecasts.
    If dry_run is True, only prints what would be pruned.
    """
    excess = len(memory._memory) - max_entries
    if excess > 0:
        if dry_run:
            print(f"[MemoryGuardian] Would prune {excess} oldest forecasts.")
        else:
            memory._memory = memory._memory[-max_entries:]
            print(f"[MemoryGuardian] Pruned {excess} oldest forecasts.")

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
