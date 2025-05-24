# SPARC Analysis: `simulation_engine/` Directory Overview

**Analysis Date:** 2025-05-14 (Updated: 2025-05-14)
**Analyzer:** Roo (Orchestrated by SPARC)

## 1. Overall Purpose and Functionality

The `simulation_engine/` directory houses the core logic for the Pulse system's simulation capabilities. Its primary responsibilities include:
*   **Simulation Execution:** Running simulations forward in time ([`simulator_core.py`](simulation_engine/simulator_core.py:1), [`turn_engine.py`](simulation_engine/turn_engine.py:1)) and backward for retrodiction ([`simulate_backward.py`](simulation_engine/simulate_backward.py:1), [`historical_retrodiction_runner.py`](simulation_engine/historical_retrodiction_runner.py:1)).
*   **World State Management:** Defining, mutating, and monitoring the state of the simulated world ([`worldstate.py`](simulation_engine/worldstate.py:1), [`state_mutation.py`](simulation_engine/state_mutation.py:1), [`worldstate_monitor.py`](simulation_engine/worldstate_monitor.py:1), [`variables/worldstate_variables.py`](simulation_engine/variables/worldstate_variables.py:1)).
*   **Rule Application:** Implementing and managing causal rules that govern system dynamics ([`rule_engine.py`](simulation_engine/rule_engine.py:1), [`causal_rules.py`](simulation_engine/causal_rules.py:1), `rules/` subdirectory). This includes rule registration ([`rules/rule_registry.py`](simulation_engine/rules/rule_registry.py:1)), mutation ([`rule_mutation_engine.py`](simulation_engine/rule_mutation_engine.py:1)), and reverse application ([`rules/reverse_rule_engine.py`](simulation_engine/rules/reverse_rule_engine.py:1)).
*   **Specialized Simulation Modes:** Supporting batch simulations ([`batch_runner.py`](simulation_engine/batch_runner.py:1)) and reinforcement learning environments ([`rl_env.py`](simulation_engine/rl_env.py:1), [`train_rl_agent.py`](simulation_engine/train_rl_agent.py:1)).
*   **Supporting Services & Utilities:** Providing services for running simulations ([`services/simulation_runner.py`](simulation_engine/services/simulation_runner.py:1)) and utilities for I/O, logging, and timeline building ([`utils/worldstate_io.py`](simulation_engine/utils/worldstate_io.py:1), [`utils/simulation_trace_logger.py`](simulation_engine/utils/simulation_trace_logger.py:1)).
*   **System Dynamics:** Incorporating logic for decay ([`decay_logic.py`](simulation_engine/decay_logic.py:1)) and detecting simulation drift ([`simulation_drift_detector.py`](simulation_engine/simulation_drift_detector.py:1)).

## 2. Key Modules and Subdirectories

The `simulation_engine/` directory is structured with core modules at the top level and specialized functionalities within subdirectories.

| Module/File Path                                                              | Analysis Status | Link to Report                                                                 | Key Findings/Notes Summary (High-Level) |
| :---------------------------------------------------------------------------- | :-------------- | :----------------------------------------------------------------------------- | :-------------------------------------- |
| **Top-Level Modules**                                                         |                 |                                                                                |                                         |
| [`simulation_engine/__init__.py`](simulation_engine/__init__.py:1)                         | Pending         |                                                                                | Package initializer.                    |
| [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py:1)                 | Completed       | [`simulation_engine_batch_runner.md`](docs/sprint0_module_analysis/simulation_engine_batch_runner.md:1) | Orchestrates batch simulation runs.     |
| [`simulation_engine/causal_rules.py`](simulation_engine/causal_rules.py:1)                 | Pending         |                                                                                | Defines/manages causal rule structures. |
| [`simulation_engine/decay_logic.py`](simulation_engine/decay_logic.py:1)                  | Completed       | [`simulation_engine_decay_logic.md`](docs/sprint0_module_analysis/simulation_engine_decay_logic.md:1) | Applies decay to state variables.       |
| [`simulation_engine/historical_retrodiction_runner.py`](simulation_engine/historical_retrodiction_runner.py:1) | Pending         |                                                                                | Manages historical retrodiction runs.   |
| [`simulation_engine/pulse_signal_router.py`](simulation_engine/pulse_signal_router.py:1)          | Pending         |                                                                                | Routes signals within the simulation.   |
| [`simulation_engine/rl_env.py`](simulation_engine/rl_env.py:1)                         | Pending         |                                                                                | Defines RL environment for simulation.  |
| [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:1)                  | Pending         |                                                                                | Core engine for applying rules.         |
| [`simulation_engine/rule_mutation_engine.py`](simulation_engine/rule_mutation_engine.py:1)      | Pending         |                                                                                | Manages mutation of rules.              |
| [`simulation_engine/simulate_backward.py`](simulation_engine/simulate_backward.py:1)            | Completed       | [`simulation_engine_simulate_backward.md`](docs/sprint0_module_analysis/simulation_engine_simulate_backward.md:1) | Performs backward simulation.           |
| [`simulation_engine/simulation_drift_detector.py`](simulation_engine/simulation_drift_detector.py:1) | Pending         |                                                                                | Detects drift in simulation state.    |
| [`simulation_engine/simulator_core.py`](simulation_engine/simulator_core.py:1)              | Pending         |                                                                                | Central simulation execution logic.     |
| [`simulation_engine/state_mutation.py`](simulation_engine/state_mutation.py:1)              | Pending         |                                                                                | Handles changes to the world state.     |
| [`simulation_engine/train_rl_agent.py`](simulation_engine/train_rl_agent.py:1)              | Pending         |                                                                                | Trains RL agents using the environment. |
| [`simulation_engine/turn_engine.py`](simulation_engine/turn_engine.py:1)                  | Pending         |                                                                                | Manages simulation turns/steps.         |
| [`simulation_engine/worldstate_monitor.py`](simulation_engine/worldstate_monitor.py:1)          | Pending         |                                                                                | Monitors the world state for events.    |
| [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1)                    | Pending         |                                                                                | Defines the simulation world state.     |
| **Subdirectory: `rules/`**                                                    |                 |                                                                                | Rule definition, management, and utilities. |
| [`simulation_engine/rules/__init__.py`](simulation_engine/rules/__init__.py:1)                   | Pending         |                                                                                | Package initializer.                    |
| [`simulation_engine/rules/rule_registry.py`](simulation_engine/rules/rule_registry.py:1)        | Pending         |                                                                                | Registry for simulation rules.          |
| [`simulation_engine/rules/reverse_rule_engine.py`](simulation_engine/rules/reverse_rule_engine.py:1) | Pending         |                                                                                | Engine for applying rules in reverse.   |
| [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:1)           | Pending         |                                                                                | Defines static, unchanging rules.       |
| **Subdirectory: `services/`**                                                 |                 |                                                                                | Services for simulation execution.      |
| [`simulation_engine/services/__init__.py`](simulation_engine/services/__init__.py:1)                | Pending         |                                                                                | Package initializer.                    |
| [`simulation_engine/services/simulation_runner.py`](simulation_engine/services/simulation_runner.py:1) | Pending         |                                                                                | Service to run simulations.             |
| **Subdirectory: `utils/`**                                                    |                 |                                                                                | Utility functions for simulation.       |
| [`simulation_engine/utils/__init__.py`](simulation_engine/utils/__init__.py:1)                    | Pending         |                                                                                | Package initializer.                    |
| [`simulation_engine/utils/worldstate_io.py`](simulation_engine/utils/worldstate_io.py:1)         | Pending         |                                                                                | Handles I/O for world state data.       |
| [`simulation_engine/utils/simulation_trace_logger.py`](simulation_engine/utils/simulation_trace_logger.py:1) | Pending   |                                                                                | Logs simulation traces.                 |
| **Subdirectory: `variables/`**                                                |                 |                                                                                | World state variable definitions.       |
| [`simulation_engine/variables/__init__.py`](simulation_engine/variables/__init__.py:1)              | Pending         |                                                                                | Package initializer.                    |
| [`simulation_engine/variables/worldstate_variables.py`](simulation_engine/variables/worldstate_variables.py:1) | Pending   |                                                                                | Defines variables in the world state.   |

## 3. Architectural Patterns and Observations

*   **State Management:** A clear separation exists for managing the simulation's `worldstate` ([`worldstate.py`](simulation_engine/worldstate.py:1), [`variables/worldstate_variables.py`](simulation_engine/variables/worldstate_variables.py:1)), with dedicated modules for mutation ([`state_mutation.py`](simulation_engine/state_mutation.py:1)) and monitoring ([`worldstate_monitor.py`](simulation_engine/worldstate_monitor.py:1)).
*   **Rule-Based System:** The system heavily relies on a rule engine ([`rule_engine.py`](simulation_engine/rule_engine.py:1)) and a dedicated `rules/` subdirectory for defining, registering ([`rules/rule_registry.py`](simulation_engine/rules/rule_registry.py:1)), and managing causal relationships ([`causal_rules.py`](simulation_engine/causal_rules.py:1)). This includes capabilities for rule mutation ([`rule_mutation_engine.py`](simulation_engine/rule_mutation_engine.py:1)) and reverse execution ([`rules/reverse_rule_engine.py`](simulation_engine/rules/reverse_rule_engine.py:1)).
*   **Simulation Lifecycle Management:** Core modules like [`simulator_core.py`](simulation_engine/simulator_core.py:1) and [`turn_engine.py`](simulation_engine/turn_engine.py:1) manage the progression of simulations. Specialized runners exist for batch operations ([`batch_runner.py`](simulation_engine/batch_runner.py:1)) and historical retrodiction ([`historical_retrodiction_runner.py`](simulation_engine/historical_retrodiction_runner.py:1), [`simulate_backward.py`](simulation_engine/simulate_backward.py:1)).
*   **Modularity:** The use of subdirectories (`rules/`, `services/`, `utils/`, `variables/`) indicates an attempt at modular design, separating concerns like rule definitions, service layers, utility functions, and variable schemas.
*   **Extensibility for AI/ML:** The presence of [`rl_env.py`](simulation_engine/rl_env.py:1) and [`train_rl_agent.py`](simulation_engine/train_rl_agent.py:1) suggests the architecture is designed to integrate with or support reinforcement learning applications.

## 4. Overall Impression and Role in System Dynamics

The `simulation_engine/` directory is a critical and complex part of the Pulse system, serving as the powerhouse for modeling and exploring system dynamics. It provides a comprehensive suite of tools for:
*   Defining and evolving a world state.
*   Applying causal rules to drive changes.
*   Running simulations under various conditions (forward, backward, batch).
*   Integrating with learning components.

This directory is central to Pulse's ability to understand past events (retrodiction) and explore potential future scenarios. Its architecture appears to support a sophisticated, rule-driven approach to simulation with considerations for state management, modularity, and integration with AI/ML techniques.

## 5. General SPARC Concerns for this Directory (Anticipated)

*   **Hardcoding:** Rule definitions, simulation parameters, default values within modules like [`decay_logic.py`](simulation_engine/decay_logic.py:1) or [`simulate_backward.py`](simulation_engine/simulate_backward.py:1).
*   **Testability:** Ensuring the complex interactions within a simulation can be effectively unit and integration tested, especially for modules with tight coupling (e.g., [`batch_runner.py`](simulation_engine/batch_runner.py:1)).
*   **Modularity & Cohesion:** While subdirectories exist, ensuring high cohesion within modules and low coupling between them will be important for maintainability.
*   **Performance:** Efficiency of the simulation loop, rule application, and state updates, especially for long runs or complex states.
*   **Configuration Management:** How simulation parameters, rule sets, and world state initializations are configured and managed across different simulation runs.
*   **Logging and Observability:** Consistent and effective logging ([`decay_logic.py`](simulation_engine/decay_logic.py:1) currently uses `print`) and tracing ([`utils/simulation_trace_logger.py`](simulation_engine/utils/simulation_trace_logger.py:1)) are crucial for debugging and analysis.

## 6. Cross-Directory Dependencies (Anticipated)

*   Likely dependencies on `core/` for configurations, registries, and core data structures.
*   Possible interactions with `intelligence/` for receiving simulation commands or providing results for higher-level reasoning.
*   Potential use of `forecast_engine/` if simulations directly trigger or consume forecasts.
*   Interaction with `memory/` for persisting or retrieving simulation states, historical data, or learned rule parameters.
*   Dependencies on `iris/` for signal inputs that might trigger or modify simulations via [`pulse_signal_router.py`](simulation_engine/pulse_signal_router.py:1).

---
*This document has been updated to reflect a comprehensive overview of the `simulation_engine/` directory and its contents.*