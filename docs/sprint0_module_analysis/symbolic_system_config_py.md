# Module Analysis: `symbolic_system/config.py`

## 1. Module Intent/Purpose

The primary role of the [`symbolic_system/config.py`](../../../symbolic_system/config.py) module is to provide enhanced and centralized configuration management for the symbolic system. It supports loading and saving configurations from a JSON file, profile-based configurations with defaults for different market regimes (e.g., "default", "high_volatility", "recession"), and flexible setting/retrieval of nested configuration values. It also includes functionality to detect market regimes based on input state variables and automatically switch to the appropriate configuration profile.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- It successfully loads configurations from a file or creates a default one if not found.
- It handles multiple profiles and allows switching between them.
- Get/set operations for configuration values, including nested ones, are implemented.
- Basic market regime detection logic is present.
- A singleton pattern is used to provide a global access point to the configuration.

There are no obvious placeholders like "TODO" or "FIXME" comments in the code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Sophistication of Regime Detection:** The [`detect_market_regime()`](../../../symbolic_system/config.py:234) method is explicitly described as "simple" and that it "can be expanded with more sophisticated detection logic." This is a clear area for future enhancement. The current logic only considers `volatility_index`, `gdp_growth`, and `unemployment_rate`.
*   **Variable Mappings Usage:** While [`get_variable_mapping()`](../../../symbolic_system/config.py:221) exists, and "variable_mappings" are present in the default "high_volatility" profile, the actual utilization of these mappings within the broader symbolic system isn't detailed within this module. The extent of its current use or planned integration is unclear from this module alone.
*   **Error Handling in Regime Detection:** The [`detect_market_regime()`](../../../symbolic_system/config.py:234) method doesn't explicitly handle cases where expected `state_variables` (like `volatility_index`, `gdp_growth`, `unemployment_rate`) might be missing, other than implicitly falling through to the default regime. More robust error or warning logging could be added.
*   **Dynamic Profile Creation/Management:** While new profiles can be created based on existing ones, there's no functionality for deleting profiles or more advanced management directly through the class methods.

## 4. Connections & Dependencies

*   **Direct imports from other project modules:** None apparent within this specific file.
*   **External library dependencies:**
    *   `os`: For path manipulations (e.g., [`os.path.join()`](../../../symbolic_system/config.py:32), [`os.path.dirname()`](../../../symbolic_system/config.py:33), [`os.path.exists()`](../../../symbolic_system/config.py:44), [`os.makedirs()`](../../../symbolic_system/config.py:101)).
    *   `json`: For loading and saving the configuration file ([`json.load()`](../../../symbolic_system/config.py:47), [`json.dump()`](../../../symbolic_system/config.py:106)).
    *   `logging`: For logging information, warnings, and errors.
    *   `typing`: For type hinting (`Dict`, `Any`, `List`, `Optional`).
    *   `copy`: For [`copy.deepcopy()`](../../../symbolic_system/config.py:215) when creating new profiles.
*   **Interaction with other modules via shared data:**
    *   The module reads from and writes to a JSON configuration file, by default located at `config/symbolic_config.json` relative to the project root (one level up from `symbolic_system`). This file is the primary means of sharing configuration data.
*   **Input/output files:**
    *   Input: `config/symbolic_config.json` (if it exists).
    *   Output: `config/symbolic_config.json` (created with defaults if it doesn't exist, or overwritten on save).
    *   Logs: Uses the standard Python `logging` module.

## 5. Function and Class Example Usages

### `SymbolicConfig` Class

```python
from symbolic_system.config import get_symbolic_config, SymbolicConfig

# Get the singleton instance
config_manager = get_symbolic_config()

# Get a value from the default profile
dominance_threshold = config_manager.get_value("overlay_thresholds.dominance")
print(f"Default dominance threshold: {dominance_threshold}")

# Set the active profile
config_manager.set_active_profile("high_volatility")
print(f"Active profile: {config_manager.get_active_profile()}")

# Get a value from the new active profile
dominance_threshold_hv = config_manager.get_value("overlay_thresholds.dominance")
print(f"High volatility dominance threshold: {dominance_threshold_hv}")

# Set a value
config_manager.set_value("new_setting", 123)
config_manager.save_config() # Values are saved automatically on set, but can be called explicitly

# Create a new profile
config_manager.create_profile("custom_profile", base_profile="high_volatility")
config_manager.set_active_profile("custom_profile")
config_manager.set_value("overlay_thresholds.activation", 0.28)

# Get variable specific mapping
mapping = config_manager.get_variable_mapping("volatility_index")
print(f"Mapping for volatility_index: {mapping}")

# Auto-select profile based on state variables
current_state = {"volatility_index": 35.0, "gdp_growth": -0.5, "unemployment_rate": 7.0}
detected_regime = config_manager.auto_select_profile(current_state)
print(f"Detected regime: {detected_regime}, Active profile: {config_manager.get_active_profile()}")
```

### [`get_symbolic_config()`](../../../symbolic_system/config.py:276)

This function is the standard way to access the `SymbolicConfig` instance.

```python
from symbolic_system.config import get_symbolic_config

config = get_symbolic_config()
api_key = config.get_value("api_keys.some_service", default="not_set")
```

## 6. Hardcoding Issues

*   **Default Configuration Path:** The default configuration file path is constructed as `os.path.join(os.path.dirname(__file__), "..", "config", "symbolic_config.json")`. While this makes the default location predictable relative to the module, the `../config/` part implies a specific directory structure.
*   **Default Profile Values:** The entire default configuration, including profile names ("default", "high_volatility", "recession") and their specific values (thresholds, interaction strengths), is hardcoded within the [`_load_config()`](../../../symbolic_system/config.py:37) method. This is standard for providing initial defaults but means changes to these base defaults require code modification if the JSON file is not present.
*   **Regime Detection Thresholds:** The thresholds used in [`detect_market_regime()`](../../../symbolic_system/config.py:234) (e.g., `vix > 30`, `gdp < 0 and unemployment > 6.0`) are hardcoded. Ideally, these thresholds might also be configurable, perhaps within a special section of the "default" profile or a dedicated "regime_detection" configuration block.
*   **Version String:** `"version": "1.0"` is hardcoded in the default configuration.

## 7. Coupling Points

*   **File System:** Tightly coupled to the file system for loading/saving `symbolic_config.json`. The location is somewhat flexible via the `config_file` constructor argument but defaults to a specific relative path.
*   **Other Symbolic System Modules:** Any module in the symbolic system that requires configuration will depend on this module, likely via the [`get_symbolic_config()`](../../../symbolic_system/config.py:276) function. The structure of the configuration (e.g., keys like "overlay_thresholds", "variable_mappings") creates an implicit contract with consuming modules.
*   **State Variable Structure:** The [`detect_market_regime()`](../../../symbolic_system/config.py:234) and [`auto_select_profile()`](../../../symbolic_system/config.py:262) methods expect `state_variables` to be a dictionary with specific keys (e.g., "volatility_index", "gdp_growth"). This couples it to whatever system component provides these state variables.

## 8. Existing Tests

*   A `tests/symbolic_system/` directory exists.
*   Within `tests/symbolic_system/`, there is an [`__init__.py`](../../../tests/symbolic_system/__init__.py) and a `gravity/` subdirectory.
*   There does not appear to be a specific test file named `test_config.py` or similar directly within `tests/symbolic_system/`.
*   **Conclusion:** Specific unit tests for [`symbolic_system/config.py`](../../../symbolic_system/config.py) are likely missing or are located elsewhere, not following a direct `test_module_name.py` convention in the immediate `tests/symbolic_system/` directory. Test coverage for this module is therefore unascertainable from the provided file listing for this specific path.

## 9. Module Architecture and Flow

*   **Class-based Singleton:** The core logic is encapsulated in the [`SymbolicConfig`](../../../symbolic_system/config.py:22) class. A global singleton instance (`_config_instance`) is managed and accessed via the [`get_symbolic_config()`](../../../symbolic_system/config.py:276) factory function.
*   **Initialization:** On instantiation, [`SymbolicConfig`](../../../symbolic_system/config.py:22) attempts to load configuration from a JSON file. If the file doesn't exist or an error occurs, it creates and saves a default configuration structure.
*   **Profiles:** Configuration is organized into profiles (e.g., "default", "high_volatility"). One profile is "active" at any time.
*   **Data Storage:** The configuration data is stored in memory as a Python dictionary (`self._config`) and persisted to a JSON file.
*   **Access and Modification:** Methods like [`get_value()`](../../../symbolic_system/config.py:122) and [`set_value()`](../../../symbolic_system/config.py:148) provide an interface to interact with the configuration of the active profile, supporting dot-notation for nested keys. Changes are typically saved to the file immediately after being set in memory.
*   **Regime Detection:** The [`detect_market_regime()`](../../../symbolic_system/config.py:234) method takes current market state variables and returns a profile name. [`auto_select_profile()`](../../../symbolic_system/config.py:262) uses this to switch the active profile.

## 10. Naming Conventions

*   **Class Name:** [`SymbolicConfig`](../../../symbolic_system/config.py:22) follows PascalCase, which is standard for Python classes (PEP 8).
*   **Method Names:** Method names like [`_load_config()`](../../../symbolic_system/config.py:37), [`get_value()`](../../../symbolic_system/config.py:122), [`set_active_profile()`](../../../symbolic_system/config.py:179) use snake_case, which is standard (PEP 8).
*   **Private Methods/Attributes:** Prefixed with a single underscore (e.g., `_config_file`, `_load_config`), indicating they are intended for internal use, which is a common convention.
*   **Global Singleton Instance:** `_config_instance` uses a leading underscore, common for module-level "private" variables.
*   **Variable Names:** Generally use snake_case (e.g., `active_profile`, `config_file`, `state_variables`).
*   **Constants/Configuration Keys:** Keys within the JSON configuration (e.g., "overlay_thresholds", "interaction_strengths", "hope->trust") use snake_case or descriptive strings. The `->` in interaction strength keys is a bit unconventional but clear in its intent.
*   **Logging:** `logger = logging.getLogger(__name__)` is standard.

Overall, the naming conventions are consistent and largely adhere to PEP 8. There are no obvious AI assumption errors in naming. The use of `->` in some configuration keys is a minor stylistic choice but doesn't impede understanding.