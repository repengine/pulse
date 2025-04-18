"""
pulse_memory_guardian.py

Manages retention and pruning of forecast memory.

Usage:
    prune_memory(memory, max_entries=1000, dry_run=True)
"""

from memory.forecast_memory import ForecastMemory

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
