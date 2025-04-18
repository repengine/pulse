"""
trust_audit.py

Provides a strategic summary of recent foresight memory including:
- Trust band counts
- Confidence / fragility / retrodiction averages
- Age stats and decay tag counts

Used as a strategic checkpoint after simulations.

Author: Pulse v0.2
"""

from forecast_output.pfpa_logger import PFPA_ARCHIVE
from statistics import mean
from utils.log_utils import get_logger
from core.pulse_config import CONFIDENCE_THRESHOLD, MODULES_ENABLED
from core.module_registry import MODULE_REGISTRY

if not MODULE_REGISTRY.get("trust_audit", {}).get("enabled", MODULES_ENABLED.get("trust_audit", True)):
    raise RuntimeError("Trust audit module is disabled in config.")

logger = get_logger(__name__)


def trust_band(trace):
    c = trace.get("confidence", 0)
    if c >= 0.75:
        return "🟢 Trusted"
    elif c >= 0.5:
        return "⚠️ Moderate"
    else:
        return "🔴 Fragile"


def audit_trust():
    logger.info("Starting trust audit...")


def audit_forecasts(memory=None, recent_n: int = 10) -> None:
    """
    Runs a trust audit on recent forecasts.
    """
    logger.info("\n🧭 TRUST AUDIT REPORT\n")

    forecasts = memory or PFPA_ARCHIVE[-recent_n:]
    bands = {"🟢 Trusted": 0, "⚠️ Moderate": 0, "🔴 Fragile": 0}
    confidences, fragilities, retros, priorities, ages = [], [], [], [], []

    for f in forecasts:
        band = trust_band(f)
        bands[band] += 1
        confidences.append(f.get("confidence", 0))
        fragilities.append(f.get("fragility_score", 0))
        retros.append(f.get("retrodiction_score", 0))
        priorities.append(f.get("priority_score", 0))
        ages.append(f.get("age_hours", 0))

    logger.info(f"🟢 Trusted : {bands['🟢 Trusted']}")
    logger.info(f"⚠️ Moderate: {bands['⚠️ Moderate']}")
    logger.info(f"🔴 Fragile : {bands['🔴 Fragile']}")

    avg_conf = round(mean(confidences), 3) if confidences else "N/A"
    avg_frag = round(mean(fragilities), 3) if fragilities else "N/A"
    avg_retros = round(mean(retros), 3) if retros else "N/A"
    avg_priority = round(mean(priorities), 3) if priorities else "N/A"
    avg_age = round(mean(ages), 2) if ages else "N/A"
    max_age = round(max(ages), 2) if ages else "N/A"

    logger.info(f"\nAvg Confidence : {avg_conf}")
    logger.info(f"Avg Fragility  : {avg_frag}")
    logger.info(f"Avg Retrodict  : {avg_retros}")
    logger.info(f"Avg Priority   : {avg_priority}")
    logger.info(f"Avg Age        : {avg_age}h | Max: {max_age}h")


if __name__ == "__main__":
    audit_forecasts()
