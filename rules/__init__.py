"""
Rules package initializer.

This package contains the rule engine components for the Pulse system,
including rule matching, reverse rule engineering, and rule registry functionality.
"""

# Import key modules to make them available at package level
from . import reverse_rule_engine
from . import reverse_rule_mapper
from . import rule_matching_utils
from . import rule_registry
from . import static_rules

__all__ = [
    "reverse_rule_engine",
    "reverse_rule_mapper",
    "rule_matching_utils",
    "rule_registry",
    "static_rules",
]
