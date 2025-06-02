"""
config.py

Enhanced configuration management for the symbolic system.
Provides centralized configuration with custom profiles for different
market regimes and variable-specific overlay mappings.

This module supports:
- Loading/saving configuration from a JSON file
- Profile-based configuration with defaults
- Flexible setting and retrieval of nested configuration values
- Multiple profiles for different market conditions
"""

import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SymbolicConfig:
    """Configuration manager for the symbolic system"""

    def __init__(self, config_file: str = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file, or None to use default
        """
        self._config_file = config_file or os.path.join(
            os.path.dirname(__file__), "..", "config", "symbolic_config.json"
        )
        self._config = self._load_config()
        self._active_profile = "default"

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default if it doesn't exist.

        Returns:
            Dictionary containing configuration data
        """
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, "r") as f:
                    loaded_config = json.load(f)
                logger.info(f"Loaded symbolic configuration from {self._config_file}")
                return loaded_config
            except Exception as e:
                logger.error(
                    f"Error loading symbolic config from {self._config_file}: {e}"
                )

        # Default configuration
        default_config = {
            "version": "1.0",
            "profiles": {
                "default": {
                    "overlay_thresholds": {"dominance": 0.65, "activation": 0.3},
                    "variable_mappings": {},
                    "interaction_strengths": {
                        "hope->trust": 0.01,
                        "despair->fatigue": 0.015,
                        "fatigue->hope": -0.02,
                    },
                },
                "high_volatility": {
                    "overlay_thresholds": {"dominance": 0.6, "activation": 0.25},
                    "interaction_strengths": {
                        "hope->trust": 0.005,  # Weaker interaction in volatile markets
                        "despair->fatigue": 0.02,  # Stronger impact of despair
                        "fatigue->hope": -0.03,  # Stronger suppression of hope
                    },
                    "variable_mappings": {
                        "volatility_index": {
                            "high_impact": ["fear", "despair"],
                            "threshold": 25.0,
                        }
                    },
                },
                "recession": {
                    "overlay_thresholds": {
                        "dominance": 0.7,  # Requires stronger evidence for dominance
                        "activation": 0.4,  # Higher activation threshold
                    },
                    "interaction_strengths": {
                        "hope->trust": 0.02,  # Stronger impact of hope on trust
                        "despair->fatigue": 0.01,  # Less impact of despair on fatigue
                        "rage->trust": -0.03,  # Stronger effect of rage on trust
                    },
                },
            },
        }

        # Ensure the config directory exists
        os.makedirs(os.path.dirname(self._config_file), exist_ok=True)

        # Save the default configuration
        try:
            with open(self._config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            logger.info(
                f"Created default symbolic configuration at {self._config_file}"
            )
        except Exception as e:
            logger.error(
                f"Error saving default symbolic config to {self._config_file}: {e}"
            )

        return default_config

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self._config_file, "w") as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Saved symbolic configuration to {self._config_file}")
        except Exception as e:
            logger.error(f"Error saving symbolic config to {self._config_file}: {e}")

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from the active profile.
        Supports dot notation for nested keys.

        Args:
            key: Configuration key (e.g., "overlay_thresholds.dominance")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        profile = self._config.get("profiles", {}).get(self._active_profile, {})

        # Handle nested keys with dot notation
        if "." in key:
            parts = key.split(".")
            value = profile
            for part in parts:
                if not isinstance(value, dict):
                    return default
                value = value.get(part, {})
            return value if value != {} else default

        return profile.get(key, default)

    def set_value(self, key: str, value: Any):
        """
        Set a configuration value in the active profile.
        Supports dot notation for nested keys.

        Args:
            key: Configuration key (e.g., "overlay_thresholds.dominance")
            value: Value to set
        """
        if "profiles" not in self._config:
            self._config["profiles"] = {}

        if self._active_profile not in self._config["profiles"]:
            self._config["profiles"][self._active_profile] = {}

        profile = self._config["profiles"][self._active_profile]

        # Handle nested keys with dot notation
        if "." in key:
            parts = key.split(".")
            target = profile
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        else:
            profile[key] = value

        self.save_config()

    def set_active_profile(self, profile_name: str):
        """
        Set the active symbolic profile.

        Args:
            profile_name: Name of the profile to activate
        """
        if profile_name in self._config.get("profiles", {}):
            self._active_profile = profile_name
            logger.info(f"Switched to symbolic profile: {profile_name}")
        else:
            logger.warning(
                f"Profile '{profile_name}' not found, staying with {
                    self._active_profile}")

    def get_active_profile(self) -> str:
        """Get the name of the active profile"""
        return self._active_profile

    def get_available_profiles(self) -> List[str]:
        """Get names of all available profiles"""
        return list(self._config.get("profiles", {}).keys())

    def create_profile(self, name: str, base_profile: str = "default"):
        """
        Create a new profile by copying an existing one.

        Args:
            name: Name of the new profile
            base_profile: Name of the profile to use as a base
        """
        if base_profile not in self._config.get("profiles", {}):
            base_profile = "default"

        if "profiles" not in self._config:
            self._config["profiles"] = {}

        import copy

        self._config["profiles"][name] = copy.deepcopy(
            self._config["profiles"].get(base_profile, {})
        )
        logger.info(f"Created new profile '{name}' based on '{base_profile}'")
        self.save_config()

    def get_variable_mapping(self, variable_name: str) -> Dict[str, Any]:
        """
        Get variable-specific overlay mapping configuration.

        Args:
            variable_name: Name of the variable

        Returns:
            Mapping configuration or empty dict if not found
        """
        mappings = self.get_value("variable_mappings", {})
        return mappings.get(variable_name, {})

    def detect_market_regime(self, state_variables: Dict[str, float]) -> str:
        """
        Simple market regime detection based on key variables.
        This can be expanded with more sophisticated detection logic.

        Args:
            state_variables: Dictionary of current variable values

        Returns:
            Name of the detected regime profile
        """
        # Simple detection based on volatility index
        if "volatility_index" in state_variables:
            vix = state_variables["volatility_index"]
            if vix > 30:
                return "high_volatility"

        # Example detection logic for recession regime
        if "gdp_growth" in state_variables and "unemployment_rate" in state_variables:
            gdp = state_variables["gdp_growth"]
            unemployment = state_variables["unemployment_rate"]

            if gdp < 0 and unemployment > 6.0:
                return "recession"

        # Default regime
        return "default"

    def auto_select_profile(self, state_variables: Dict[str, float]):
        """
        Automatically select the appropriate profile based on market conditions.

        Args:
            state_variables: Dictionary of current variable values
        """
        regime = self.detect_market_regime(state_variables)
        self.set_active_profile(regime)
        return regime


# Create singleton instance
_config_instance = None


def get_symbolic_config() -> SymbolicConfig:
    """
    Get the singleton symbolic configuration instance.

    Returns:
        SymbolicConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = SymbolicConfig()
    return _config_instance
