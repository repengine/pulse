"""
Consolidated variables module.
"""

from simulation_engine.variables.worldstate_variables import WorldstateVariables
from core.variable_accessor import get_variable, set_variable, get_overlay, set_overlay

__all__ = [
    "WorldstateVariables",
    "get_variable",
    "set_variable",
    "get_overlay",
    "set_overlay",
]