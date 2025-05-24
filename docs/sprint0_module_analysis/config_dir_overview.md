# Config Directory Overview

## Directory Path

[`config/`](config/)

## Overall Purpose & Role

The `config/` directory serves as the central repository for various configuration settings used throughout the Pulse project. It manages parameters and settings that control the behavior of different system components, allowing for customization and adaptation without modifying core code.

## Key Configuration Areas Managed

The `config/` directory manages configurations for several key areas:

*   **Adaptive Thresholds:** Dynamic thresholds and statistical data for system adaptation (e.g., [`config/adaptive_thresholds.json`](config/adaptive_thresholds.json)).
*   **AI Services:** Settings for integrating with AI models, including API keys and default model names (e.g., [`config/ai_config.py`](config/ai_config.py), [`config/simulation_config.yaml`](config/simulation_config.yaml)).
*   **Core System:** Fundamental parameters governing core system behavior (e.g., [`config/core_config.yaml`](config/core_config.yaml)).
*   **Residual-Gravity Overlay:** Detailed parameters for the gravity-based system component (e.g., [`config/gravity_config.py`](config/gravity_config.py)).
*   **Simulation Engine:** Configuration for running simulations, including default parameters and scenario presets (e.g., [`config/simulation_config.yaml`](config/simulation_config.yaml)).
*   **Symbolic System:** Settings for the symbolic reasoning system, including thresholds, mappings, and interaction strengths, organized into profiles (e.g., [`config/symbolic_config.json`](config/symbolic_config.json)).

## Common Patterns & Structure

*   **Varied Formats:** Configuration is stored in multiple formats, including JSON (.json), Python (.py), and YAML (.yaml).
*   **Component-Specific Files:** Configuration is generally organized into files corresponding to the system component they configure (e.g., `ai_config.py`, `simulation_config.yaml`).
*   **Environment Variable Loading:** Sensitive information, such as API keys, is configured to be loaded from environment variables, enhancing security.
*   **Structured Data:** JSON and YAML files utilize structured formats to organize related parameters. Python files use constants.

## How Configurations are Loaded/Used

The method of loading and utilizing configurations appears to vary based on the file format:

*   Python configuration files are likely imported directly as modules.
*   JSON and YAML files are likely parsed using appropriate libraries (e.g., `json`, `PyYAML`) by the modules that require the configuration.

The configurations provide parameters and settings that influence the runtime behavior of the respective system components.

## General Observations & Impressions

The `config/` directory provides a clear separation of configuration from application logic, which is a good practice for maintainability and flexibility. The use of different formats suggests that the choice of format might be driven by the specific needs or complexity of the configuration area. Loading sensitive data from environment variables is a positive security measure.

## Potential Areas for Improvement

*   **Configuration Format Consistency:** While different formats can be justified, exploring opportunities to standardize the format for certain types of configurations could improve consistency.
*   **Centralized Loading/Validation:** Implementing a more centralized mechanism for loading and potentially validating configurations could enhance robustness and provide a single point of access for configuration data across the application.
*   **Documentation:** While the file names are somewhat indicative, more detailed inline comments or a dedicated configuration guide could improve understanding for developers.