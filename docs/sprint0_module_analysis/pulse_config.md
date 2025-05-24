# Module Analysis: `core/pulse_config.py`

## Module Intent/Purpose

The `pulse_config.py` module serves as a centralized configuration hub for the Pulse system. It provides a standardized location for:
- Defining system-wide constants and settings
- Managing runtime flags for module toggles
- Providing utilities for loading and managing configuration data from files (JSON and YAML)
- Establishing threshold values for simulation and forecasting logic
- Maintaining feature pipeline configurations

Its primary role is to prevent hardcoding of configuration values throughout the codebase by providing a unified location for all configurable aspects of the Pulse system.

## Operational Status/Completeness

The module appears largely operational but with some signs of ongoing development:

- Core functionality for loading, saving, and updating configuration is in place and well-tested
- The configuration loader for YAML files is fully implemented with error handling
- The thresholds system for simulation has a complete implementation with persistence
- The module contains a mix of stable constants and configuration alongside runtime-modifiable settings

However, there are indications that certain aspects are still under development:

- The presence of "lowered from 0.6" comment on line 42 suggests active tuning
- The version banner indicates "v0.4", suggesting non-final status
- Some feature toggles are explicitly disabled (e.g., `"estimate_missing_variables": False`)

## Implementation Gaps / Unfinished Next Steps

Several areas appear to be placeholders or suggest future expansion:

1. **Shadow Model Monitoring**: The `SHADOW_MONITOR_CONFIG` uses placeholder variable names (`"var1", "var2"`) in its `critical_variables` list, indicating this feature is likely not fully implemented or connected to real variables yet.

2. **Model Registry**: The `MODEL_REGISTRY` contains paths to model files that may or may not exist yet. The three model types defined (symbolic, statistical, ML) suggest an architecture that might still be in development.

3. **Feature Pipeline Integration**: The module defines feature pipeline configurations but doesn't directly handle pipeline execution, suggesting there might be planned expansion to better integrate with these pipelines.

4. **Mode-Specific Behaviors**: The `SYMBOLIC_PROCESSING_MODES` dictionary has different modes, but currently "retrodiction" is disabled while other modes are enabled. This suggests potential expansion or refinement of the mode-specific behavior.

5. **Default Configuration Handling**: The default config path is defined but not explicitly used in the module's own functions, which might indicate a planned future implementation for default configuration handling.

## Connections & Dependencies

### Direct Project Module Imports
- `core.path_registry` - For accessing the `PATHS` constant for dynamic path management

### External Library Dependencies
- `os` - For file path manipulation and directory operations
- `yaml` - For parsing and loading YAML configuration files
- `json` - For loading and saving threshold configuration
- `typing` (Dict, List, Any) - For type hints

### Input/Output Files
- Reads JSON thresholds configuration from `THRESHOLD_CONFIG_PATH`
- Reads YAML configuration files from the `config_dir` (default: "config")
- Writes updated threshold values back to the thresholds JSON file
- May read files defined in `MODEL_REGISTRY` paths, though this is not directly implemented in this module

## Function and Class Example Usages

### ConfigLoader Class
```python
# Create a loader for the default config directory
config_loader = ConfigLoader()

# Load a specific configuration file
simulation_config = config_loader.load_config("simulation_config.yaml")

# Get a specific value with default fallback
log_level = config_loader.get_config_value("logging_config.yaml", "level", default="INFO")

# Reload a configuration after external changes
updated_config = config_loader.reload_config("simulation_config.yaml")
```

### Threshold Management
```python
# Load the current thresholds
thresholds = load_thresholds()

# Update a threshold value (persists to file)
update_threshold("CONFIDENCE_THRESHOLD", 0.75)

# Access a threshold via the global constant
if confidence > CONFIDENCE_THRESHOLD:
    proceed_with_forecast()
```

### Config Retrieval Function
```python
# Get entire config
pipeline_config = get_config("pipeline_config.yaml")

# Get specific value with default
host = get_config("server_config.yaml", "host", "localhost")
```

## Hardcoding Issues

Several hardcoded values are present:

1. **Default Thresholds**: 
   - `CONFIDENCE_THRESHOLD` defaults to 0.4
   - `DEFAULT_FRAGILITY_THRESHOLD` defaults to 0.7

2. **Simulation Constants**:
   - `DEFAULT_DECAY_RATE` is hardcoded to 0.1
   - `MAX_SIMULATION_FORKS` is hardcoded to 1000

3. **File Paths**:
   - `CONFIG_PATH` is hardcoded to join the directory of the current file with "default_config.json"
   - `THRESHOLD_CONFIG_PATH` is hardcoded similarly

4. **Module Configuration Values**:
   - Ensemble weights are hardcoded (`{"simulation": 0.7, "ai": 0.3}`)
   - Shadow monitor configuration has a hardcoded threshold (0.35) and window steps (10)

5. **Model Registry Paths**:
   - Model paths like "models/symbolic_model.pkl" are hardcoded

## Coupling Points

The module has several coupling points with other parts of the system:

1. **Path Registry Coupling**: The module attempts to import `PATHS` from `core.path_registry` and falls back to an empty dict if not available, creating a loose coupling.

2. **Configuration File Format Coupling**: The module is tightly coupled to the structure of the YAML and JSON configuration files it expects to load.

3. **Global State Coupling**: The `update_threshold` function directly modifies the global state via `globals()[name] = value`, creating coupling between configuration updates and any code that references these global constants.

4. **Feature Pipeline Path Coupling**: The `FEATURE_PIPELINES` dictionary references specific module paths that must exist in the project structure.

5. **Implicit Coupling through Constants**: Many parts of the system likely depend on the constants defined here, making changes to these values potentially impactful across the codebase.

## Existing Tests

The module has thorough test coverage in `tests/test_pulse_config.py`. The tests cover:

1. **Threshold Management**:
   - Loading thresholds from existing and non-existent files
   - Saving thresholds
   - Updating threshold values and verifying both in-memory and persisted updates

2. **ConfigLoader Class**:
   - Loading configuration from existing and non-existent files
   - Loading all configuration files in a directory
   - Getting configuration values with defaults
   - Reloading configuration after file changes

3. **Config Retrieval Function**:
   - Getting entire config objects
   - Getting specific values with defaults
   - Handling non-existent files and keys

The test coverage appears comprehensive and handles error cases and edge conditions. Tests use fixtures to create temporary files and mock the global configuration paths, showing good isolation practices.

## Module Architecture and Flow

The module architecture can be broken down into several components:

1. **Constants and Defaults**:
   - Basic constants are defined at the module level
   - These constants are used throughout the Pulse system
   - Some constants have fallback values if configuration loading fails

2. **Threshold Management System**:
   - Functions to load/save thresholds from JSON
   - Update mechanism that both updates runtime values and persists changes
   - Default values are provided as fallbacks

3. **ConfigLoader Class**:
   - Object-oriented approach to configuration management
   - Handles YAML file loading with error handling
   - Caches loaded configs for performance
   - Provides convenience methods for value retrieval and reload

4. **Helper Functions**:
   - `get_config` wrapper for simplified access to the configuration system

5. **Module Toggles and Feature Flags**:
   - Dictionaries defining what features/modules are enabled
   - Allows for runtime control of system behavior

The flow typically involves:
1. Module constants being accessed directly
2. Configuration being loaded on demand through the helper functions
3. Thresholds being updated at runtime when needed, with changes persisting between runs

## Naming Conventions

The module largely follows Python naming conventions:

- **Constants** use `UPPER_SNAKE_CASE` (e.g., `CONFIDENCE_THRESHOLD`, `MAX_SIMULATION_FORKS`)
- **Functions** use `snake_case` (e.g., `load_thresholds`, `update_threshold`)
- **Classes** use `PascalCase` (e.g., `ConfigLoader`)
- **Private variables** use a leading underscore (e.g., `_thresholds`)

There are a few inconsistencies:
- The `config_loader` instance is in `snake_case` despite being a singleton/global instance
- The `PATHS` constant is imported and used as-is, maintaining consistency with its source module

Generally, the naming is descriptive and makes the purpose of elements clear. Type hints are used for function returns and variable declarations, improving code readability and maintainability.