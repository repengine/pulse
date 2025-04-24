"""
Consolidated core utilities: configuration, variable accessors, and learning log.

Imports core modules and re-exports key functions and constants.
"""

from core.pulse_config import STARTUP_BANNER, CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD, DEFAULT_DECAY_RATE, OVERLAY_NAMES
from core.variable_accessor import get_variable, set_variable, get_overlay
from core.pulse_learning_log import (
    log_learning_event,
    log_variable_weight_change,
    log_symbolic_upgrade,
    log_revision_trigger,
    log_arc_regret,
    log_learning_summary,
)
from core.path_registry import PATHS

__all__ = [
    "STARTUP_BANNER",
    "CONFIDENCE_THRESHOLD",
    "DEFAULT_FRAGILITY_THRESHOLD",
    "DEFAULT_DECAY_RATE",
    "OVERLAY_NAMES",
    "get_variable",
    "set_variable",
    "get_overlay",
    "log_learning_event",
    "log_variable_weight_change",
    "log_symbolic_upgrade",
    "log_revision_trigger",
    "log_arc_regret",
    "log_learning_summary",
    "PATHS",
]