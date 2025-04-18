""" 
forecast_integrity_engine.py

Final validation layer for Pulse forecast output.
Rejects or flags forecasts based on:
- Low confidence
- High fragility
- Missing symbolic coherence
- Recent symbolic hallucinations (if tagged)

Supports configuration of filtering thresholds and symbolic tag guards.

Author: Pulse v0.10
"""

def validate_forecast(metadata: dict, min_conf=0.5, max_frag=0.7, blocked_tags=None, required_keys=None) -> bool:
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
    if not metadata:
        return False

    confidence = metadata.get("confidence", 0)
    fragility = metadata.get("fragility", 1)
    driver = str(metadata.get("symbolic_driver", "")).lower()

    if required_keys:
        for k in required_keys:
            if k not in metadata:
                return False

    if confidence < min_conf:
        return False
    if fragility > max_frag:
        return False
    if blocked_tags and driver in [tag.lower() for tag in blocked_tags]:
        return False

    return True