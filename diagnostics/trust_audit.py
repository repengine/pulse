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


def audit_forecasts(memory=None, recent_n=10):
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

    logger.info(f"\nAvg Confidence : {round(mean(confidences), 3) if confidences else 'N/A'}")
    logger.info(f"Avg Fragility  : {round(mean(fragilities), 3) if fragilities else 'N/A'}")
    logger.info(f"Avg Retrodict  : {round(mean(retros), 3) if retros else 'N/A'}")
    logger.info(f"Avg Priority   : {round(mean(priorities), 3) if priorities else 'N/A'}")
    logger.info(f"Avg Age        : {round(mean(ages), 2)}h | Max: {round(max(ages or [0]), 2)}h")


if __name__ == "__main__":
    audit_forecasts()
