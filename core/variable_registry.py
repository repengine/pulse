"""
variable_registry.py

Unified Variable Intelligence Layer
Combines static definition registry with dynamic runtime wrapper for search, ranking, tagging,
and trust/fragility performance tracking.

Pulse Version: v0.28
"""

import json
import os
from typing import Dict, Any, Tuple, Set, List, Optional
from core.path_registry import PATHS

# === Canonical Static Variable Dictionary ===
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

# === Default Bootstrap ===
def get_default_variable_state() -> Dict[str, float]:
    return {k: v["default"] for k, v in VARIABLE_REGISTRY.items()}

def validate_variables(variable_dict: Dict[str, Any]) -> Tuple[bool, Set[str], Set[str]]:
    known_keys = set(VARIABLE_REGISTRY.keys())
    input_keys = set(variable_dict.keys())
    missing = known_keys - input_keys
    unexpected = input_keys - known_keys
    return (len(missing) == 0 and len(unexpected) == 0, missing, unexpected)

def get_variables_by_type(var_type: str) -> List[str]:
    return [k for k, v in VARIABLE_REGISTRY.items() if v.get("type") == var_type]


# === Extended Runtime Accessor ===
REGISTRY_PATH = PATHS.get("VARIABLE_REGISTRY", "configs/variable_registry.json")

class VariableRegistry:
    def __init__(self, path: Optional[str] = None):
        self.path = path or REGISTRY_PATH
        self.variables: Dict[str, Dict] = VARIABLE_REGISTRY.copy()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    updated = json.load(f)
                    self.variables.update(updated)
                except Exception:
                    pass

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.variables, f, indent=2)

    def register_variable(self, name: str, meta: Dict[str, Any]):
        self.variables[name] = meta
        self._save()

    def get(self, name: str) -> Optional[Dict]:
        return self.variables.get(name)

    def all(self) -> List[str]:
        return list(self.variables.keys())

    def filter_by_tag(self, tag: str) -> List[str]:
        return [k for k, v in self.variables.items() if tag in v.get("tags", [])]

    def filter_by_type(self, var_type: str) -> List[str]:
        return [k for k, v in self.variables.items() if v.get("type") == var_type]

    def list_trust_ranked(self) -> List[str]:
        return sorted(self.variables.keys(), key=lambda k: self.variables[k].get("trust_weight", 1.0), reverse=True)

if __name__ == "__main__":
    vr = VariableRegistry()
    print("Variables loaded:", vr.all())