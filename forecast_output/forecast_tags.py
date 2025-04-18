"""
forecast_tags.py

Central registry for forecast symbolic tags and descriptions.

Usage:
    from forecast_output.forecast_tags import ForecastTag, get_tag_label, is_valid_tag, get_tag_by_label

    tag = ForecastTag.HOPE
    label = get_tag_label(tag)  # "Hope Rising"
    tag2 = get_tag_by_label("Hope Rising")  # ForecastTag.HOPE
    is_valid = is_valid_tag("Hope Rising")  # True
"""

from enum import Enum, auto

class ForecastTag(Enum):
    HOPE = auto()
    DESPAIR = auto()
    RAGE = auto()
    FATIGUE = auto()
    COLLAPSE_RISK = auto()
    SYMBOLIC_DRAIN = auto()
    HOPE_RAGE_CONFLICT = auto()
    SYMBOLIC_EXHAUSTION = auto()
    NEUTRAL = auto()

TAG_DESCRIPTIONS = {
    ForecastTag.HOPE: "Hope Rising",
    ForecastTag.DESPAIR: "Despair Dominant",
    ForecastTag.RAGE: "Rage Spike",
    ForecastTag.FATIGUE: "Fatigue Plateau",
    ForecastTag.COLLAPSE_RISK: "Collapse Risk",
    ForecastTag.SYMBOLIC_DRAIN: "Symbolic Drain",
    ForecastTag.HOPE_RAGE_CONFLICT: "Hope-Rage Conflict",
    ForecastTag.SYMBOLIC_EXHAUSTION: "Symbolic Exhaustion",
    ForecastTag.NEUTRAL: "Neutral",
}

LABEL_TO_TAG = {v: k for k, v in TAG_DESCRIPTIONS.items()}

def get_tag_label(tag: ForecastTag) -> str:
    """Return the human-readable label for a ForecastTag."""
    return TAG_DESCRIPTIONS.get(tag, "Unknown")

def get_tag_by_label(label: str):
    """Return the ForecastTag for a given label, or None if not found."""
    return LABEL_TO_TAG.get(label)

def is_valid_tag(label: str) -> bool:
    """Check if a label is a valid forecast tag."""
    return label in LABEL_TO_TAG
