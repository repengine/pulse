"""
pulse_memory_guardian.py

Manages retention and pruning of forecast memory.

Usage:
    prune_memory(memory, max_entries=1000, dry_run=True)
"""

import logging
from typing import Dict, Any, Optional
from analytics.forecast_memory import ForecastMemory
from trust_system.trust_engine import TrustEngine

logger = logging.getLogger(__name__)


def prune_memory(
    memory: ForecastMemory, max_entries: int = 1000, dry_run: bool = False
):
    """
    Prunes memory to retain only the most recent max_entries forecasts.
    If dry_run is True, only prints what would be pruned.
    """
    excess = len(memory._memory) - max_entries
    if excess > 0:
        if dry_run:
            logger.info(f"[MemoryGuardian] Would prune {excess} oldest forecasts.")
        else:
            memory._memory = memory._memory[-max_entries:]
            logger.info(f"[MemoryGuardian] Pruned {excess} oldest forecasts.")


# --- Variable Fossilization & Archiving ---
def archive_variable_fossil(
    variable_name: str, data: Dict[str, Any], dry_run: bool = False
):
    """
    Archives a variable as a 'fossil' for future analysis.
    In a real implementation, this would persist to disk or a database.
    """
    if dry_run:
        logger.info(f"[MemoryGuardian] Would archive variable fossil: {variable_name}")
    else:
        # Stub: Replace with actual persistence logic
        logger.info(
            f"[MemoryGuardian] Archived variable fossil: {variable_name} | Data: {data}"
        )


def soft_retire_variable(
    variable_name: str, data: Dict[str, Any], dry_run: bool = False
):
    """
    Soft-retires a variable (marks as inactive, but not deleted).
    """
    if dry_run:
        logger.info(f"[MemoryGuardian] Would soft-retire variable: {variable_name}")
    else:
        # Stub: Replace with actual status update logic
        logger.info(f"[MemoryGuardian] Soft-retired variable: {variable_name}")


def reconsider_variable(
    variable_name: str,
    data: Dict[str, Any],
    regime: str = "alternate",
    dry_run: bool = False,
):
    """
    Reconsiders a soft-retired variable under a different symbolic regime.
    """
    if dry_run:
        logger.info(
            f"[MemoryGuardian] Would reconsider variable: {variable_name} under regime: {regime}"
        )
    else:
        # Stub: Replace with actual reconsideration logic
        logger.info(
            f"[MemoryGuardian] Reconsidered variable: {variable_name} under regime: {regime}"
        )


def prune_incoherent_forecasts(memory_batch, verbose=True):
    """
    Discards forecasts that fail symbolic, capital, or trust coherence tests.

    Returns:
        list of retained coherent forecasts
    """
    retained = []
    for forecast in memory_batch:
        status, issues = TrustEngine.check_forecast_coherence([forecast])
        if status == "pass":
            retained.append(forecast)
        elif verbose:
            logger.warning(
                f"[Guardian] Pruned forecast {forecast.get('trace_id')} due to:"
            )
            for issue in issues:
                logger.warning("  - %s", issue)
    return retained


def prune_memory_advanced(
    memory: ForecastMemory,
    max_entries: int = 1000,
    dry_run: bool = False,
    min_confidence: Optional[float] = None,
):
    """
    Prunes memory to retain only the most recent max_entries forecasts, or by confidence if min_confidence is set.
    If dry_run is True, only prints what would be pruned.
    """
    if min_confidence is not None:
        if dry_run:
            to_prune = [
                f
                for f in memory._memory
                if float(f.get("confidence", 0)) < min_confidence
            ]
            logger.info(
                f"[MemoryGuardian] Would prune {len(to_prune)} forecasts below confidence {min_confidence}."
            )
        else:
            memory._memory = [
                f
                for f in memory._memory
                if float(f.get("confidence", 0)) >= min_confidence
            ]
            logger.info(
                f"[MemoryGuardian] Pruned forecasts below confidence {min_confidence}."
            )
    else:
        prune_memory(memory, max_entries=max_entries, dry_run=dry_run)
