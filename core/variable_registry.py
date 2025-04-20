"""
variable_registry.py

Defines all canonical simulation variable names with categories and metadata.
Used for dynamic UI, validation, variable pruning, and pulse_grow expansion.

- Each variable should have: type, default, range, and description.
- Add new variables here for consistency and validation.
"""
from typing import Dict, Any, Tuple, Set, List

VARIABLE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Economic variables
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
        "range": [0.00, 0.25],
        "description": "Unemployment rate"
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
        "range": [0.00, 1.00],
        "description": "Public trust in institutions"
    },
    "crypto_instability": {
        "type": "market",
        "default": 0.30,
        "range": [0.00, 1.00],
        "description": "Crypto market instability index"
    },
    "ai_policy_risk": {
        "type": "governance",
        "default": 0.20,
        "range": [0.00, 1.00],
        "description": "AI policy/regulation risk"
    },
    "energy_price_index": {
        "type": "economic",
        "default": 0.50,
        "range": [0.00, 2.00],
        "description": "Energy price index"
    },
    "geopolitical_stability": {
        "type": "governance",
        "default": 0.70,
        "range": [0.00, 1.00],
        "description": "Geopolitical stability index"
    },
    "media_sentiment_score": {
        "type": "narrative",
        "default": 0.40,
        "range": [0.00, 1.00],
        "description": "Media sentiment score"
    },
    # Symbolic overlays
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
        "range": [0.00, 1.00],
        "description": "Symbolic overlay: Rage"
    },
    "fatigue": {
        "type": "symbolic",
        "default": 0.50,
        "range": [0.00, 1.00],
        "description": "Symbolic overlay: Fatigue"
    }
}


def get_default_variable_state() -> Dict[str, float]:
    """
    Returns a dictionary with all variables initialized to their default values.
    Useful for worldstate bootstrapping.
    """
    return {k: v["default"] for k, v in VARIABLE_REGISTRY.items()}


def validate_variables(variable_dict: Dict[str, Any]) -> Tuple[bool, Set[str], Set[str]]:
    """
    Validates input dictionary keys against known variables in the registry.
    Returns (valid, missing, unexpected) tuple.
    Args:
        variable_dict: Dictionary of variable values to validate.
    Returns:
        Tuple[bool, Set[str], Set[str]]: (all_valid, missing_keys, unexpected_keys)
    """
    known_keys = set(VARIABLE_REGISTRY.keys())
    input_keys = set(variable_dict.keys())
    missing = known_keys - input_keys
    unexpected = input_keys - known_keys
    return (len(missing) == 0 and len(unexpected) == 0, missing, unexpected)


def get_variables_by_type(var_type: str) -> List[str]:
    """
    Returns a list of variable names for a given type/category.
    Args:
        var_type (str): The variable type/category (e.g., 'economic', 'symbolic').
    Returns:
        List[str]: List of variable names matching the type.
    """
    return [k for k, v in VARIABLE_REGISTRY.items() if v.get("type") == var_type]