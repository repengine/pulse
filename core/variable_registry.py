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
    "fed_funds_rate": {"type": "economic", "default": 0.05, "range": [0.00, 0.10], "description": "US Federal Funds Rate"},
    "inflation_index": {"type": "economic", "default": 0.03, "range": [0.00, 0.15], "description": "Consumer price inflation rate"},
    "unemployment_rate": {"type": "economic", "default": 0.05, "range": [0.00, 0.25], "description": "Unemployment rate"},
    "market_volatility_index": {"type": "market", "default": 0.20, "range": [0.00, 1.00], "description": "Simulated VIX"},
    "public_trust_level": {"type": "governance", "default": 0.60, "range": [0.00, 1.00], "description": "Public trust in institutions"},
    "crypto_instability": {"type": "market", "default": 0.30, "range": [0.00, 1.00], "description": "Crypto market instability index"},
    "ai_policy_risk": {"type": "governance", "default": 0.20, "range": [0.00, 1.00], "description": "AI policy/regulation risk"},
    "energy_price_index": {"type": "economic", "default": 0.50, "range": [0.00, 2.00], "description": "Energy price index"},
    "geopolitical_stability": {"type": "governance", "default": 0.70, "range": [0.00, 1.00], "description": "Geopolitical stability index"},
    "media_sentiment_score": {"type": "narrative", "default": 0.40, "range": [0.00, 1.00], "description": "Media sentiment score"},
    # Symbolic overlays
    "hope": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Hope"},
    "despair": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Despair"},
    "rage": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Rage"},
    "fatigue": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Fatigue"},
    # --- Expanded variables for coverage ---
    # Economic/Market Sectors
    "tech_sector_volatility": {"type": "market", "default": 0.18, "range": [0.00, 1.00], "description": "Tech sector volatility index"},
    "health_sector_volatility": {"type": "market", "default": 0.15, "range": [0.00, 1.00], "description": "Healthcare sector volatility index"},
    "energy_sector_volatility": {"type": "market", "default": 0.22, "range": [0.00, 1.00], "description": "Energy sector volatility index"},
    "financial_sector_volatility": {"type": "market", "default": 0.19, "range": [0.00, 1.00], "description": "Financial sector volatility index"},
    "housing_market_index": {"type": "economic", "default": 0.60, "range": [0.00, 2.00], "description": "Housing market price index"},
    "oil_price_index": {"type": "economic", "default": 0.70, "range": [0.00, 2.00], "description": "Oil price index"},
    "food_price_index": {"type": "economic", "default": 0.55, "range": [0.00, 2.00], "description": "Food price index"},
    "retail_sales_index": {"type": "economic", "default": 0.50, "range": [0.00, 2.00], "description": "Retail sales index"},
    "manufacturing_index": {"type": "economic", "default": 0.65, "range": [0.00, 2.00], "description": "Manufacturing output index"},
    "services_index": {"type": "economic", "default": 0.68, "range": [0.00, 2.00], "description": "Services sector index"},
    # Regional/Global
    "us_inflation_index": {"type": "economic", "default": 0.03, "range": [0.00, 0.15], "description": "US inflation rate"},
    "eu_inflation_index": {"type": "economic", "default": 0.025, "range": [0.00, 0.15], "description": "EU inflation rate"},
    "asia_inflation_index": {"type": "economic", "default": 0.04, "range": [0.00, 0.15], "description": "Asia inflation rate"},
    "us_unemployment_rate": {"type": "economic", "default": 0.045, "range": [0.00, 0.25], "description": "US unemployment rate"},
    "eu_unemployment_rate": {"type": "economic", "default": 0.07, "range": [0.00, 0.25], "description": "EU unemployment rate"},
    "asia_unemployment_rate": {"type": "economic", "default": 0.06, "range": [0.00, 0.25], "description": "Asia unemployment rate"},
    "us_public_trust_level": {"type": "governance", "default": 0.62, "range": [0.00, 1.00], "description": "US public trust in institutions"},
    "eu_public_trust_level": {"type": "governance", "default": 0.58, "range": [0.00, 1.00], "description": "EU public trust in institutions"},
    "asia_public_trust_level": {"type": "governance", "default": 0.65, "range": [0.00, 1.00], "description": "Asia public trust in institutions"},
    # Market/Asset Classes
    "sp500_index": {"type": "market", "default": 0.50, "range": [0.00, 2.00], "description": "S&P 500 normalized index"},
    "nasdaq_index": {"type": "market", "default": 0.52, "range": [0.00, 2.00], "description": "NASDAQ normalized index"},
    "bitcoin_price_index": {"type": "market", "default": 0.60, "range": [0.00, 2.00], "description": "Bitcoin price index"},
    "gold_price_index": {"type": "market", "default": 0.65, "range": [0.00, 2.00], "description": "Gold price index"},
    "bond_yield_index": {"type": "market", "default": 0.40, "range": [0.00, 2.00], "description": "Bond yield index"},
    # Social/Narrative
    "social_media_sentiment": {"type": "narrative", "default": 0.45, "range": [0.00, 1.00], "description": "Social media sentiment score"},
    "news_sentiment_score": {"type": "narrative", "default": 0.48, "range": [0.00, 1.00], "description": "News sentiment score"},
    "policy_sentiment_score": {"type": "narrative", "default": 0.50, "range": [0.00, 1.00], "description": "Policy sentiment score"},
    # Symbolic overlays (expanded)
    "optimism": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Optimism"},
    "pessimism": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Pessimism"},
    "fear": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Fear"},
    "confidence": {"type": "symbolic", "default": 0.50, "range": [0.00, 1.00], "description": "Symbolic overlay: Confidence"},
    # Add 60+ more plausible variables (abbreviated for brevity)
    **{f"sector_{i}_growth": {"type": "economic", "default": 0.5, "range": [0.0, 2.0], "description": f"Sector {i} growth index"} for i in range(1, 31)},
    **{f"region_{i}_stability": {"type": "governance", "default": 0.7, "range": [0.0, 1.0], "description": f"Region {i} stability index"} for i in range(1, 31)},
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

    def bind_data_source(self, signal_provider_fn: callable):
        """
        Attach a signal-fetching function that returns {var_name: value} dicts.
        """
        self._signal_provider = signal_provider_fn

    def get_live_value(self, var_name: str) -> Optional[float]:
        if hasattr(self, "_signal_provider") and var_name in self.variables:
            try:
                signal_map = self._signal_provider()
                return signal_map.get(var_name)
            except Exception as e:
                print(f"[VariableRegistry] Error fetching {var_name}: {e}")
        return None

if __name__ == "__main__":
    vr = VariableRegistry()
    print("Variables loaded:", vr.all())