"""
variable_registry.py

Defines all canonical simulation variable names with categories and metadata.
Used for dynamic UI, validation, variable pruning, and pulse_grow expansion.
"""

VARIABLE_REGISTRY = {
    "fed_funds_rate": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.10],
        "description": "US Federal Funds Rate"
    },
    "inflation_index": {
        "type": "economic",
        "default": 0.03,
        "range": [0.00, 0.15],
        "description": "Consumer price inflation rate"
    },
    "unemployment_rate": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.25]
    },
    "market_volatility_index": {
        "type": "market",
        "default": 0.20,
        "range": [0.00, 1.00],
        "description": "Simulated VIX"
    },
    "public_trust_level": {
        "type": "governance",
        "default": 0.60,
        "range": [0.00, 1.00]
    },
    "crypto_instability": {
        "type": "market",
        "default": 0.30,
        "range": [0.00, 1.00]
    },
    "ai_policy_risk": {
        "type": "governance",
        "default": 0.20,
        "range": [0.00, 1.00]
    },
    "energy_price_index": {
        "type": "economic",
        "default": 0.50,
        "range": [0.00, 2.00]
    },
    "geopolitical_stability": {
        "type": "governance",
        "default": 0.70,
        "range": [0.00, 1.00]
    },
    "media_sentiment_score": {
        "type": "narrative",
        "default": 0.40,
        "range": [0.00, 1.00]
    },
    "hope": {
        "type": "symbolic",
        "default": 0.50,
        "range": [0.00, 1.00],
        "description": "Symbolic overlay: Hope"
    },
    "despair": {
        "type": "symbolic",
        "default": 0.50,
        "range": [0.00, 1.00],
        "description": "Symbolic overlay: Despair"
    },
    "rage": {
        "type": "symbolic",
        "default": 0.50,
        "range": [0.00, 1.00]
    },
    "fatigue": {
        "type": "symbolic",
        "default": 0.50,
        "range": [0.00, 1.00]
    }
}

def get_default_variable_state():
    """
    Returns a dictionary with all variables initialized to their default values.
    Useful for worldstate bootstrapping.
    """
    return {k: v["default"] for k, v in VARIABLE_REGISTRY.items()}


def validate_variables(variable_dict):
    """
    Validates input dictionary keys against known variables in the registry.
    Returns (valid, missing, unexpected) tuple.
    """
    known_keys = set(VARIABLE_REGISTRY.keys())
    input_keys = set(variable_dict.keys())
    missing = known_keys - input_keys
    unexpected = input_keys - known_keys
    return (len(missing) == 0 and len(unexpected) == 0, missing, unexpected)