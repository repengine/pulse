# Module Analysis: `core/variable_registry.py`

## 1. Module Intent/Purpose

The [`core/variable_registry.py`](core/variable_registry.py:1) module serves as a "Unified Variable Intelligence Layer." Its primary purpose is to act as a central repository and manager for all variables used within the Pulse system. This includes:
*   Storing static definitions of variables (e.g., type, default value, range, description).
*   Providing a runtime wrapper for dynamic aspects like search, ranking, tagging.
*   Intending to support trust/fragility performance tracking (though this seems less developed in the current code).
*   Managing persistence of variable definitions and potentially their runtime values.
*   Offering forecasting capabilities and live data binding.

## 2. Key Functionalities

*   **Static Variable Definitions**: A large, hardcoded dictionary `VARIABLE_REGISTRY` ([`core/variable_registry.py:20`](core/variable_registry.py:20)) stores metadata for numerous economic and market variables. Each entry includes `type`, `default`, `range`, and `description`.
*   **Helper Functions**:
    *   [`get_default_variable_state()`](core/variable_registry.py:332): Returns a dictionary of all registered variables with their default values.
    *   [`validate_variables(variable_dict)`](core/variable_registry.py:335): Checks a given dictionary of variables against the `VARIABLE_REGISTRY` for missing or unexpected keys.
    *   [`get_variables_by_type(var_type)`](core/variable_registry.py:342): Lists variables of a specific type.
*   **`VariableRegistry` Class**:
    *   **Initialization & Persistence**: Loads variable definitions from a JSON file ([`REGISTRY_PATH`](core/variable_registry.py:347), defaulting to `configs/variable_registry.json`) on instantiation, updating the initial static `VARIABLE_REGISTRY`. It can also save changes back to this file. It attempts to load persisted runtime values from `./data/variable_values.json`.
    *   **Registration**: [`register_variable(name, meta)`](core/variable_registry.py:412) allows adding or updating variable definitions.
    *   **Lookup & Filtering**: Provides methods to get a variable's definition ([`get(name)`](core/variable_registry.py:423)), list all variables ([`all()`](core/variable_registry.py:427)), filter by tag ([`filter_by_tag(tag)`](core/variable_registry.py:430)), filter by type ([`filter_by_type(var_type)`](core/variable_registry.py:433)), and list variables ranked by a "trust_weight" (though "trust_weight" is not consistently present in the static definitions).
    *   **External Ingestion**: [`bind_external_ingestion(loader)`](core/variable_registry.py:444) allows attaching callable functions to ingest external data.
    *   **Snapshot Analysis**: [`flag_missing_variables(snapshot)`](core/variable_registry.py:449) and [`score_variable_activity(snapshot)`](core/variable_registry.py:453) provide basic analysis on data snapshots.
    *   **Live Data**: [`bind_data_source(signal_provider_fn)`](core/variable_registry.py:458) and [`get_live_value(var_name)`](core/variable_registry.py:461) allow fetching live values for variables.
    *   **Forecasting**: Includes methods to get/set forecast values ([`get_forecast_value(variable_name)`](core/variable_registry.py:479), [`set_forecast_value(variable_name, value)`](core/variable_registry.py:483)) and an example forecast generator ([`_generate_example_forecasts()`](core/variable_registry.py:395)).
    *   **Tagging**: Methods to add and retrieve tags for variables ([`add_variable_tag(variable_name, tag)`](core/variable_registry.py:502), [`get_variable_tags(variable_name)`](core/variable_registry.py:508)).
*   **Singleton Instance**: A global singleton instance `registry = VariableRegistry()` ([`core/variable_registry.py:514`](core/variable_registry.py:514)) is created for easy access throughout the project.

## 3. Role within `core/` Directory

This module is central to the `core/` functionality, acting as the definitive source and manager for all system variables. It underpins any module that needs to understand, access, or manipulate variable data, such as the [`core/variable_accessor.py`](core/variable_accessor.py:1) module, simulation engines, data ingestion pipelines, and forecasting components.

## 4. Dependencies

### Internal Pulse Modules:
*   [`core.path_registry.PATHS`](core/path_registry.py:1): Used to get file paths for storing the registry and variable values.

### External Libraries:
*   `json`: For loading and saving variable definitions and values.
*   `os`: For file system operations (checking existence, creating directories).
*   `typing`: For type hinting (Dict, Any, Tuple, Set, List, Optional, Callable).
*   `contextlib.suppress`: Used to ignore exceptions during file loading.
*   `random` (in [`_generate_example_forecasts()`](core/variable_registry.py:395)): For creating placeholder forecast data.

## 5. Adherence to SPARC Principles

*   **Module Intent/Purpose**:
    *   Clearly stated in the module docstring (lines 1-9). The module attempts to cover a broad range of functionalities related to variable management.
*   **Operational Status/Completeness**:
    *   The static definition part (`VARIABLE_REGISTRY` dictionary) is extensive.
    *   The `VariableRegistry` class provides many foundational methods for registration, lookup, persistence, and basic forecasting/live data hooks.
    *   Features like "trust/fragility performance tracking" mentioned in the docstring seem less developed or absent in the provided code. The `trust_weight` key is used for sorting but not consistently defined for all variables.
    *   Tagging functionality ([`add_variable_tag`](core/variable_registry.py:502), [`get_variable_tags`](core/variable_registry.py:508), [`filter_by_tag`](core/variable_registry.py:430)) appears to operate on a separate `_variable_tags` dictionary rather than integrating tags into the main `self.variables` metadata.
*   **Implementation Gaps / Unfinished Next Steps**:
    *   **Trust/Fragility Tracking**: This core advertised feature needs significant implementation.
    *   **Tagging Integration**: Tags should ideally be part of the main variable metadata in `self.variables` for consistency and easier persistence/querying, rather than a separate `_variable_tags` dictionary. The `filter_by_tag` method currently expects tags within `v.get("tags", [])` which contradicts how tags are added via `add_variable_tag`.
    *   **Error Handling**: The use of `suppress(Exception)` ([`core/variable_registry.py:379`](core/variable_registry.py:379), [`core/variable_registry.py:390`](core/variable_registry.py:390)) and `except Exception as exc: # noqa: BLE001` ([`core/variable_registry.py:466`](core/variable_registry.py:466)) hides potential issues during file operations or data fetching. More specific exception handling and logging would be beneficial.
    *   **Forecasting**: The [`_generate_example_forecasts()`](core/variable_registry.py:395) method is a placeholder. A robust forecasting mechanism would require integration with actual forecasting models.
    *   **Runtime Value Persistence**: The `_runtime_values` are loaded but there's no explicit save mechanism shown for them, unlike `self.variables`.
    *   The `_external_ingesters` list is populated but not actively used in other methods shown.
*   **Connections & Dependencies**:
    *   Relies on [`core.path_registry.PATHS`](core/path_registry.py:1) for file locations.
    *   The singleton pattern makes it a global dependency for any part of the system needing variable information.
*   **Function and Class Example Usages**:
    ```python
    # Assuming 'registry' is the singleton instance from core.variable_registry
    # from core.variable_registry import registry

    # --- Example for VariableRegistry class (mocked for standalone execution) ---
    import json
    import os
    from typing import Dict, Any, List, Optional, Callable
    from contextlib import suppress

    # Mock PATHS for the example
    class MockPATHS:
        def get(self, key, default):
            if key == "VARIABLE_REGISTRY":
                return "mock_variable_registry.json"
            if key == "variable_values_path":
                return "mock_variable_values.json"
            return default

    PATHS = MockPATHS()

    # Minimal VARIABLE_REGISTRY for example
    VARIABLE_REGISTRY_STATIC: Dict[str, Dict[str, Any]] = {
        "us_10y_yield": {"type": "economic", "default": 0.05, "range": [0.00, 0.10], "description": "US 10-Year Treasury Yield"},
        "cpi_yoy": {"type": "economic", "default": 0.03, "range": [0.00, 0.15], "description": "Consumer Price Index, YoY"}
    }

    class VariableRegistry:
        _external_ingesters: List[Callable[[], Dict[str, float]]] = []

        def __init__(self, path: Optional[str] = None) -> None:
            self.path = path or PATHS.get("VARIABLE_REGISTRY", "configs/variable_registry.json")
            self.variables: Dict[str, Dict[str, Any]] = VARIABLE_REGISTRY_STATIC.copy() # Use the static one for example
            self._forecast_values = {}
            self._runtime_values = {}
            self._variable_tags = {}
            self._initialized = False
            self._load()
            self._load_persisted_values()
            self._generate_example_forecasts() # Simplified
            self._initialized = True

        def _load(self) -> None:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    with suppress(Exception):
                        updated = json.load(f)
                        self.variables.update(updated)

        def _save(self) -> None:
            # print(f"Saving to {self.path}") # For debug
            os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.variables, f, indent=2)
        
        def _load_persisted_values(self):
            values_path = PATHS.get('variable_values_path', './data/variable_values.json')
            if os.path.exists(values_path):
                with open(values_path, 'r') as f:
                    with suppress(Exception):
                        self._runtime_values = json.load(f)

        def _generate_example_forecasts(self):
            import random
            for var_name, var_def in self.variables.items():
                if 'range' in var_def:
                    low, high = var_def['range']
                    self._forecast_values[var_name] = round(random.uniform(low, high), 4)
                else:
                    self._forecast_values[var_name] = var_def.get('default', 0)

        def register_variable(self, name: str, meta: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
            meta = meta or metadata or {}
            self.variables[name] = meta
            self._save()

        def get(self, name: str) -> Optional[Dict[str, Any]]:
            return self.variables.get(name)

        def all(self) -> List[str]:
            return list(self.variables.keys())
            
        def get_forecast_value(self, variable_name):
            return self._forecast_values.get(variable_name)

        def set_live_value(self, variable_name, value):
            self._runtime_values[variable_name] = value
            # Persist runtime values (example addition)
            values_path = PATHS.get('variable_values_path', './data/variable_values.json')
            os.makedirs(os.path.dirname(values_path) or '.', exist_ok=True)
            with open(values_path, "w", encoding="utf-8") as f:
                json.dump(self._runtime_values, f, indent=2)


    # Create a mock registry file for the example to load
    if not os.path.exists("mock_variable_registry.json"):
        with open("mock_variable_registry.json", "w") as f:
            json.dump({"gdp_growth_annual": {"type": "economic", "default": 0.02, "range": [-0.10, 0.10], "description": "Real GDP Growth"}}, f)

    # Example Usage
    registry_instance = VariableRegistry() # Uses mock_variable_registry.json

    # Register a new variable
    registry_instance.register_variable("new_custom_index", {"type": "custom", "default": 100.0, "description": "A new index"})
    print(f"All variables: {registry_instance.all()}")

    # Get variable definition
    cpi_def = registry_instance.get("cpi_yoy")
    if cpi_def:
        print(f"CPI YoY Default: {cpi_def.get('default')}")

    # Get a forecast value (generated by _generate_example_forecasts)
    forecast_cpi = registry_instance.get_forecast_value("cpi_yoy")
    print(f"Forecast for CPI YoY: {forecast_cpi}")

    # Set and get a live value
    registry_instance.set_live_value("us_10y_yield", 0.045)
    # To verify, you'd typically have a get_live_value method or check _runtime_values
    print(f"Live US 10Y Yield (from internal dict): {registry_instance._runtime_values.get('us_10y_yield')}")

    # Clean up mock files
    if os.path.exists("mock_variable_registry.json"): os.remove("mock_variable_registry.json")
    if os.path.exists("mock_variable_values.json"): os.remove("mock_variable_values.json")
    ```
*   **Hardcoding Issues**:
    *   The initial `VARIABLE_REGISTRY` ([`core/variable_registry.py:20`](core/variable_registry.py:20)) is very large and hardcoded directly in the Python file. While it's updated from a JSON file, this initial static block makes the module lengthy and harder to maintain directly.
    *   Default file paths like `configs/variable_registry.json` and `./data/variable_values.json` are used if not found in `PATHS`.
*   **Coupling Points**:
    *   The `VariableRegistry` class is tightly coupled to the specific structure of the variable definition dictionaries (e.g., expecting keys like `type`, `default`, `range`, `description`, `tags`, `trust_weight`).
    *   The singleton `registry` instance creates a global state, which can make dependencies less explicit and testing more complex if not managed carefully.
*   **Existing Tests**:
    *   No tests are provided within this module. External tests would be crucial given its centrality.
*   **Module Architecture and Flow**:
    *   The module defines a large static dictionary, some helper functions, and a comprehensive `VariableRegistry` class.
    *   The class initializes by loading data from files, then provides methods for interaction.
    *   The use of a class-level list `_external_ingesters` ([`core/variable_registry.py:360`](core/variable_registry.py:360)) means all instances of `VariableRegistry` (if more than the singleton were created) would share this list.
*   **Naming Conventions**:
    *   Generally follows Python standards (`snake_case` for functions/methods, `UPPER_SNAKE_CASE` for constants, `PascalCase` for the class).
    *   Some internal variable names like `_forecast_values`, `_runtime_values` are clear.
    *   The parameter `meta` and `metadata` in [`register_variable`](core/variable_registry.py:412) for the same purpose could be consolidated.

## 6. Overall Assessment

*   **Completeness**:
    *   The module provides a very comprehensive list of predefined economic and market variables.
    *   The `VariableRegistry` class offers a wide array of functionalities for managing these variables.
    *   However, some advertised features (like trust/fragility tracking) are not fully implemented. The tagging system also seems disjointed.
*   **Quality**:
    *   The code is generally well-structured with clear separation of concerns within the `VariableRegistry` class (persistence, registration, lookup, forecasting hooks).
    *   Type hinting is used, improving readability.
    *   The sheer size of the initial `VARIABLE_REGISTRY` hardcoded in the `.py` file is a drawback for maintainability; relying solely on the JSON file for definitions would be cleaner.
    *   The singleton pattern is convenient but has standard trade-offs.
    *   Error handling could be more robust.
*   **File Size**: The module is quite long (over 500 lines), primarily due to the large static `VARIABLE_REGISTRY` definition. This violates the "Keep each file under 500 lines" custom instruction.

## 7. Suggested Improvements

*   **Refactor Static `VARIABLE_REGISTRY`**: Move the entire static `VARIABLE_REGISTRY` definition from the Python file into the `variable_registry.json` file and load it entirely from there. This would significantly shorten the Python module and make variable definitions easier to manage externally.
*   **Implement Missing Features**: Develop the "trust/fragility performance tracking" system.
*   **Improve Tagging**: Integrate the `_variable_tags` directly into the `self.variables` metadata for each variable. Ensure `filter_by_tag` and `add_variable_tag` work consistently with this integrated structure.
*   **Enhance Error Handling**: Replace broad exception suppression with specific handling and logging.
*   **Develop Forecasting**: Integrate with actual forecasting models instead of random generation.
*   **Persistence for Runtime Values**: Implement a `_save_persisted_values()` method for `_runtime_values` if they are meant to be persisted across sessions.
*   **Utilize `_external_ingesters`**: Show how these bound ingester functions are called and used.
*   **Consolidate Parameters**: Use a single parameter name (e.g., `metadata`) in [`register_variable`](core/variable_registry.py:412) instead of `meta` or `metadata`.
*   **Unit Tests**: Add comprehensive unit tests for the `VariableRegistry` class and helper functions.
*   **Documentation**: Add more detailed docstrings for methods, especially explaining the expected structure of data for parameters like `snapshot` or the return values of bound callables.