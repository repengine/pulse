"""
worldstate_variables.py

Defines the WorldstateVariables class used to store and manipulate key
simulation variables inside the Pulse simulation. Provides dict-like access,
attribute-style access, and utility methods for controlled updates and decay.

Author: Pulse v0.4
"""

class WorldstateVariables:
    def __init__(self, **kwargs):
        # Default values
        self.fed_funds_rate: float = 0.05
        self.inflation_index: float = 0.03
        self.unemployment_rate: float = 0.05
        self.ai_policy_risk: float = 0.2
        self.geopolitical_stability: float = 0.7
        self.media_sentiment_score: float = 0.4
        self.market_volatility_index: float = 0.2
        self.public_trust_level: float = 0.6
        self.energy_price_index: float = 0.5
        self.crypto_instability: float = 0.3

        # Overwrite defaults with any provided init values
        for k, v in kwargs.items():
            if hasattr(self, k):
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
