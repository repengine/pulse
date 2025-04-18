"""
variable_accessor.py

Abstracts access to worldstate variables and overlays.
"""

def get_variable(state, name, default=0.0):
    return state.variables.get(name, default)

def set_variable(state, name, value):
    state.variables[name] = value

def get_overlay(state, name, default=0.0):
    return state.overlays.get(name, default)

def set_overlay(state, name, value):
    state.overlays[name] = value
