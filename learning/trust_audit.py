"""
trust_audit.py

Provides a strategic summary of recent foresight memory including:
- Trust band counts
- Confidence / fragility / retrodiction averages
- Age stats and decay tag counts

Used as a strategic checkpoint after simulations.

Author: Pulse v0.2
"""

from forecast_output.pfpa_logger import get_latest_forecasts
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


def trust_loop_integrity_issues(forecasts):
    """
    Detects trust loop integrity failures:
    - Trusted forecasts with low retrodiction or high fragility.
    - Fragile forecasts with high confidence.
    Returns a list of warnings.
    """
    issues = []
    for f in forecasts:
        conf = f.get("confidence", 0)
        frag = f.get("fragility", f.get("fragility_score", 0))
        retro = f.get("retrodiction_score", 1.0)
        label = f.get("trust_label", "")
        tid = f.get("trace_id", "unknown")
        # Trusted but low retrodiction
        if label == "🟢 Trusted" and retro < 0.5:
            issues.append(f"⚠️ Trusted forecast {tid} has low retrodiction ({retro})")
        # Trusted but high fragility
        if label == "🟢 Trusted" and frag > 0.7:
            issues.append(f"⚠️ Trusted forecast {tid} is fragile ({frag})")
        # Fragile but high confidence
        if label == "🔴 Fragile" and conf > 0.7:
            issues.append(f"⚠️ Fragile forecast {tid} has high confidence ({conf})")
    return issues


def audit_trust():
    logger.info("Starting trust audit...")


def audit_forecasts(memory=None, recent_n: int = 10) -> None:
    """
    Runs a trust audit on recent forecasts, including trust loop integrity check.
    """
    logger.info("\n🧭 TRUST AUDIT REPORT\n")

    forecasts = memory or get_latest_forecasts(recent_n)
    bands = {"🟢 Trusted": 0, "⚠️ Moderate": 0, "🔴 Fragile": 0}
    confidences, fragilities, retros, priorities, ages = [], [], [], [], []

    # Expand compressed forecasts (with "examples" field) into individual forecasts
    expanded_forecasts = []
    for f in forecasts:
        if isinstance(f, dict) and "examples" in f and isinstance(f["examples"], list):
            # Compressed forecast: add each example
            for example in f["examples"]:
                if isinstance(example, dict):
                    expanded_forecasts.append(example)
                else:
                    logger.warning(
                        f"Skipping non-dictionary example in compressed forecast: {type(example)}"
                    )
        elif isinstance(f, dict):
            expanded_forecasts.append(f)
        else:
            logger.warning(f"Skipping non-dictionary forecast of type {type(f)}")

    for f in expanded_forecasts:
        band = trust_band(f)
        bands[band] += 1
        confidences.append(f.get("confidence", 0))
        fragilities.append(f.get("fragility_score", f.get("fragility", 0)))
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
    logger.info(f"Avg Retrodict. : {avg_retros}")
    logger.info(f"Avg Priority   : {avg_priority}")
    logger.info(f"Avg Age (h)    : {avg_age}")
    logger.info(f"Max Age (h)    : {max_age}")

    # Trust loop integrity check
    issues = trust_loop_integrity_issues(expanded_forecasts)
    if issues:
        logger.warning("\n⚠️ TRUST LOOP INTEGRITY ISSUES DETECTED:")
        for issue in issues:
            logger.warning(issue)
    else:
        logger.info("\n✅ Trust loop integrity: No critical issues detected.")


if __name__ == "__main__":
    audit_forecasts()
