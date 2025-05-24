"""
forecast_integrity_engine.py

Final validation layer for Pulse forecast forecast_output.
Rejects or flags forecasts based on:
- Low confidence
- High fragility
- Missing symbolic coherence
- Recent symbolic hallucinations (if tagged)

Supports configuration of filtering thresholds and symbolic tag guards.

Author: Pulse v0.10
"""

from core.pulse_config import CONFIDENCE_THRESHOLD
from core.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"


def validate_forecast(
    metadata: dict, min_conf=None, max_frag=None, blocked_tags=None, required_keys=None
) -> bool:
    """
    Returns True if forecast is valid for export, False if it should be discarded.

    Args:
        metadata (dict): Forecast metadata
        min_conf (float): Minimum required confidence
        max_frag (float): Maximum allowed fragility
        blocked_tags (list[str]): Optional symbolic tags that trigger rejection
        required_keys (list[str]): Optional list of metadata keys that must exist

    Returns:
        bool: True if forecast is valid
    """
    min_conf = min_conf if min_conf is not None else CONFIDENCE_THRESHOLD
    max_frag = max_frag if max_frag is not None else 0.7

    confidence = metadata.get("confidence")
    fragility = metadata.get("fragility")
    driver = metadata.get("symbolic_driver", "").lower()

    if confidence is None or fragility is None:
        return False
    if confidence < min_conf or fragility > max_frag:
        return False
    if blocked_tags and driver in [tag.lower() for tag in blocked_tags]:
        return False
    if required_keys and not all(k in metadata for k in required_keys):
        return False

    return True


def infer_causal_links(forecast_history: list) -> dict:
    """
    Placeholder for causal inference logic.
    Analyze forecast history to infer possible causal relationships.
    """
    # TODO: Integrate with do-calculus or causal graph library
    # For now, just return empty dict
    return {}
