"""
PATCHED: pulse_memory_guardian.py
Adds:
- Coherence-aware pruning: discards incoherent forecasts based on contradiction scan.
"""

import logging
from trust_system.pulse_mirror_core import check_forecast_coherence

logger = logging.getLogger("pulse_memory_guardian")

def prune_incoherent_forecasts(memory_batch, verbose=True):
    """
    Discards forecasts that fail symbolic, capital, or trust coherence tests.
    Returns a list of retained coherent forecasts.

    Args:
        memory_batch (list): A batch of forecast objects to be checked for coherence.
        verbose (bool): If True, logs detailed information about pruned forecasts.

    Returns:
        list: A list of retained coherent forecasts.
    """
    retained = []
    for forecast in memory_batch:
        status, issues = check_forecast_coherence([forecast])
        if status == "pass":
            retained.append(forecast)
        elif verbose:
            logger.info(f"[Guardian] Pruned forecast {forecast.get('trace_id')} due to:")
            for issue in issues:
                logger.info("  - %s", issue)
    return retained
