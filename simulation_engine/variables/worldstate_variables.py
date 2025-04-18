"""
worldstate_variables.py

Defines the WorldstateVariables class used to store and manipulate key
simulation variables inside the Pulse simulation. Provides dict-like access,
attribute-style access, and utility methods for controlled updates and decay.

Author: Pulse v0.4
"""

from core.variable_registry import get_default_variable_state

class WorldstateVariables:
    def __init__(self, **kwargs):
        # Start with registry defaults
        defaults = get_default_variable_state()
        for k, v in defaults.items():
            setattr(self, k, v)
        # Overwrite with any provided values
        for k, v in kwargs.items():
            setattr(self, k, v)

    # -------- Dict Emulation --------
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __iter__(self):
        return iter(self.__dict__)

    def items(self):
        return self.__dict__.items()

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def get(self, key, default=None):
        return getattr(self, key, default)

    def copy(self):
        return self.__dict__.copy()

    def as_dict(self):
        return self.copy()

    # -------- Update & Decay Logic --------
    def update_variable(self, name: str, value: float):
        if hasattr(self, name):
            setattr(self, name, value)

    def decay_variable(self, name: str, rate: float = 0.01):
        if hasattr(self, name):
            current = getattr(self, name)
            setattr(self, name, max(0.0, current - rate))

    def __repr__(self):
        return f"WorldstateVariables({self.__dict__})"
