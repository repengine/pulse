# Analysis Report: `intelligence/intelligence_core.py`

**Version:** 1.3 (as per docstring)

## 1. Module Intent/Purpose

The [`intelligence_core.py`](intelligence/intelligence_core.py:1) module serves as the central orchestrator for the Pulse simulation and learning cycles. Its primary role is to manage and coordinate interactions between several key components of the intelligence system:

*   [`FunctionRouter`](intelligence/function_router.py:13) (for dynamic function calls)
*   [`SimulationExecutor`](intelligence/simulation_executor.py:15) (for running simulations)
*   [`Observer`](intelligence/intelligence_observer.py:16) (for monitoring, learning, and proposing upgrades)
*   [`UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:17) (for handling upgrade proposals)

It is responsible for initializing the simulation environment (WorldState), running forecast and retrodiction cycles, and triggering post-cycle audits and learning processes.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined purpose.
*   The core functionalities of initializing a world state, running forecast cycles, running retrodiction cycles, and performing post-cycle audits are implemented.
*   Type hinting is used extensively, improving code clarity and maintainability.
*   Docstrings are present for the class and most methods, explaining their purpose, arguments, and return values.
*   A comment on line 48 ([`self.loaded_modules`](intelligence/intelligence_core.py:48)) suggests a potential area for refactoring: `"# This attribute is no longer directly managed here, consider removing if unused."` This indicates that while the module is functional, there might be minor remnants of previous designs.
*   The version is marked as "stable v1.3" in the module docstring.

There are no obvious major placeholders (e.g., `TODO`, `FIXME`, `NotImplementedError` for core features).

## 3. Implementation Gaps / Unfinished Next Steps

*   **`loaded_modules` Attribute:** As noted in the code (line 48), the [`self.loaded_modules`](intelligence/intelligence_core.py:48) attribute might be vestigial. If it's truly unused, it should be removed to clean up the class. If it has an indirect purpose or is used by other components that inspect `IntelligenceCore`, this should be clarified.
*   **Sandbox Interaction:** While the [`UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:17) is a dependency and an attribute, its methods are not directly called within `IntelligenceCore` in the provided code, apart from the `Observer` proposing upgrades which might implicitly interact with it. The `IntelligenceCore` itself doesn't seem to actively manage or query the sandbox. The actual handling of the `upgrade_id` returned by [`self.observer.propose_symbolic_upgrades_live()`](intelligence/intelligence_core.py:152) is limited to a print statement. A more complete implementation might involve passing this `upgrade_id` to the `sandbox` for processing or tracking.
*   **Error Handling and Resilience:** The module has basic error handling (e.g., checking if `ws_obj` is `None` before calling `snapshot()` on line 120), but comprehensive error handling for simulation failures, module loading issues, or observer errors is not explicitly detailed.
*   **Configuration:** The module relies on default values (e.g., `start_year = 2023` if not found) and hardcoded module paths in [`load_standard_modules()`](intelligence/intelligence_core.py:51). A more flexible system might involve external configuration for these.
*   **Batch Processing:** The `_batch_tag` parameter in [`run_forecast_cycle()`](intelligence/intelligence_core.py:95) is mentioned as "internal use." The extent and completeness of batch processing capabilities are not fully clear from this module alone.

## 4. Connections & Dependencies

### Direct Imports from Other Project Modules:

*   [`intelligence.function_router.FunctionRouter`](intelligence/function_router.py:13)
*   [`intelligence.worldstate_loader.load_initial_state`](intelligence/worldstate_loader.py:14)
*   [`intelligence.simulation_executor.SimulationExecutor`](intelligence/simulation_executor.py:15)
*   [`intelligence.intelligence_observer.Observer`](intelligence/intelligence_observer.py:16)
*   [`intelligence.upgrade_sandbox_manager.UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:17)
*   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py:18) (for type hinting)

### External Library Dependencies:

*   [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) (standard library)
*   `typing` (standard library: `Any`, `Dict`, `List`, `Optional`, `Union`, `Tuple`)

### Interaction with Other Modules via Shared Data:

*   **WorldState:** The [`WorldState`](simulation_engine/worldstate.py:18) object is central. It's initialized via [`load_initial_state()`](intelligence/worldstate_loader.py:14), passed to and modified by the [`SimulationExecutor`](intelligence/simulation_executor.py:15), and its snapshot is passed to the [`Observer`](intelligence/intelligence_observer.py:16).
*   **Module Loading:** The [`FunctionRouter`](intelligence/function_router.py:13) is used to load other modules dynamically based on string paths (e.g., `"simulation_engine.turn_engine"`).
*   **Divergence Reports & Upgrade Proposals:** The [`Observer`](intelligence/intelligence_observer.py:16) generates divergence reports and upgrade proposals, which are handled within the `IntelligenceCore` (though the proposal handling is currently just a print statement).

### Input/Output Files:

*   **Input:**
    *   Baseline files for [`WorldState`](simulation_engine/worldstate.py:18) initialization (CSV or JSON), specified by the `source` parameter in [`initialize_worldstate()`](intelligence/intelligence_core.py:64). If `source` is `None`, it defaults to `"default"`, implying a default file or generation mechanism within [`load_initial_state()`](intelligence/worldstate_loader.py:14).
*   **Output:**
    *   The module itself doesn't directly write files. However, components it orchestrates might (e.g., logs from the simulation or observer, exported forecasts from [`forecast_engine.forecast_generator`](forecast_engine/forecast_generator.py:59)).
    *   The print statement on line 153 ([`print(f"[IntelligenceCore] 🚀 Upgrade proposal submitted: {upgrade_id}")`](intelligence/intelligence_core.py:153)) outputs to standard output.

## 5. Function and Class Example Usages

### `IntelligenceCore` Class

**Intended Usage:**
The [`IntelligenceCore`](intelligence/intelligence_core.py:20) is designed to be the main entry point and coordinator for running simulations and learning cycles. It's initialized with its dependencies (router, executor, observer, sandbox).

```python
# Hypothetical setup
from intelligence.function_router import FunctionRouter
from intelligence.simulation_executor import SimulationExecutor
from intelligence.intelligence_observer import Observer
from intelligence.upgrade_sandbox_manager import UpgradeSandboxManager
from intelligence.intelligence_core import IntelligenceCore

# Initialize dependencies (simplified)
router = FunctionRouter()
# SimulationExecutor might need a WorldState or config
# For simplicity, assume it can be initialized or gets worldstate later
# executor = SimulationExecutor(router=router, initial_worldstate=None) # Example
# observer = Observer(config={}, router=router) # Example
# sandbox = UpgradeSandboxManager(config={}) # Example

# Actual initialization requires concrete instances of dependencies
# This is a conceptual example based on the __init__ signature
# core = IntelligenceCore(router=router, executor=executor, observer=observer, sandbox=sandbox)

# --- More realistic setup would involve full instantiation of dependencies ---

# Example of a more complete (but still illustrative) setup:
# Assume config objects are loaded elsewhere
# config_main = {...}
# config_observer = {...}
# config_sandbox = {...}

# router = FunctionRouter()
# initial_ws = load_initial_state("path/to/baseline.json") # Or from default
# executor = SimulationExecutor(router=router, initial_worldstate=initial_ws)
# observer = Observer(config=config_observer, router=router)
# sandbox = UpgradeSandboxManager(config=config_sandbox)

# core = IntelligenceCore(router, executor, observer, sandbox)

# 1. Load standard modules (optional, if not loaded by router/executor already)
# core.load_standard_modules()

# 2. Initialize WorldState (can be done implicitly by run_forecast_cycle or explicitly)
# world_state = core.initialize_worldstate(source="path/to/your/baseline_data.csv", start_year=2024)
# Or, to use defaults:
# world_state = core.initialize_worldstate()

# 3. Run a forecast cycle
# final_snapshot = core.run_forecast_cycle(turns=24)
# print("Forecast complete. Final snapshot:", final_snapshot)
# print("Last worldstate time:", core.last_worldstate.current_time if core.last_worldstate else "N/A")

# 4. Run a retrodiction cycle
# retro_results = core.run_retrodiction_cycle(start_date="2023-01-01", days=30)
# print("Retrodiction results:", retro_results)
```

### Key Methods:

*   **`__init__(self, router, executor, observer, sandbox)`:**
    Initializes the core with its dependencies.
*   **`load_standard_modules(self)`:**
    Loads a predefined set of modules (e.g., turn engine, causal rules) using the `FunctionRouter`.
    ```python
    # core.load_standard_modules()
    # print(f"Loaded modules: {core.router.get_loaded_module_names()}") # Assuming router has such a method
    ```
*   **`initialize_worldstate(self, source=None, **overrides)`:**
    Creates the initial [`WorldState`](simulation_engine/worldstate.py:18) from a file or defaults, applying any overrides.
    ```python
    # ws = core.initialize_worldstate(source="data/custom_baseline.json", population_growth_rate=0.02)
    # ws_default = core.initialize_worldstate()
    ```
*   **`run_forecast_cycle(self, turns=12, *, _batch_tag=None)`:**
    Runs a simulation for a specified number of turns. Initializes [`WorldState`](simulation_engine/worldstate.py:18) if not done, executes the simulation, and triggers a post-cycle audit.
    ```python
    # forecast_result = core.run_forecast_cycle(turns=10)
    ```
*   **`run_retrodiction_cycle(self, start_date, days=90)`:**
    Executes a retrodiction process for a given period.
    ```python
    # retro_result = core.run_retrodiction_cycle(start_date="2022-06-01", days=60)
    ```
*   **`_post_cycle_audit(self, snapshot)`:**
    Internal method called after a forecast cycle. It uses the `Observer` to check for symbolic divergence and propose upgrades. This is not typically called directly by the user.

## 6. Hardcoding Issues

*   **Default Start Year:** In [`_extract_start_year()`](intelligence/intelligence_core.py:79), if a start year isn't found in the `WorldState` metadata, it defaults to `2023`. This is hardcoded (lines 90, 92).
    ```python
    # return state.get("metadata", {}).get("start_year", 2023) # Line 90
    # return getattr(state, "metadata", {}).get("start_year", 2023) # Line 92
    ```
    A similar default `2023` is used in [`run_forecast_cycle()`](intelligence/intelligence_core.py:112) if `self.last_worldstate` is `None`.
*   **Default WorldState Source:** In [`initialize_worldstate()`](intelligence/intelligence_core.py:75), if `source` is `None`, it defaults to the string `"default"`. The actual file path or logic this `"default"` string maps to is within the [`load_initial_state()`](intelligence/worldstate_loader.py:14) function and not visible here, but the string itself is hardcoded in `IntelligenceCore`.
    ```python
    # self.last_worldstate = load_initial_state(source or "default", **overrides) # Line 75
    ```
*   **Module Paths for `load_standard_modules`:** The paths to standard modules are hardcoded strings within the [`load_standard_modules()`](intelligence/intelligence_core.py:51) method (lines 56-59).
    ```python
    # "turn_engine": "simulation_engine.turn_engine", # Line 56
    # "causal_rules": "simulation_engine.causal_rules", # Line 57
    # "retrodiction": "simulation_engine.historical_retrodiction_runner", # Line 58
    # "forecast_engine": "forecast_engine.forecast_generator", # Line 59
    ```
    The list `self.loaded_modules` is also updated with hardcoded names (line 61).
*   **Default Turns for Forecast:** [`run_forecast_cycle()`](intelligence/intelligence_core.py:95) has a default `turns` value of `12`.
*   **Default Days for Retrodiction:** [`run_retrodiction_cycle()`](intelligence/intelligence_core.py:124) has a default `days` value of `90`.
*   **Print Statement:** The message printed upon upgrade proposal submission is hardcoded (line 153).
    ```python
    # print(f"[IntelligenceCore] 🚀 Upgrade proposal submitted: {upgrade_id}") # Line 153
    ```

## 7. Coupling Points

*   **Tight Coupling with Dependencies:** The [`IntelligenceCore`](intelligence/intelligence_core.py:20) is tightly coupled to its four main dependencies: [`FunctionRouter`](intelligence/function_router.py:13), [`SimulationExecutor`](intelligence/simulation_executor.py:15), [`Observer`](intelligence/intelligence_observer.py:16), and [`UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:17). These are injected via the constructor, which is good practice (Dependency Injection), but the `IntelligenceCore` directly calls methods on these objects and understands their roles.
*   **`WorldState` Object:** The structure and methods of the [`WorldState`](simulation_engine/worldstate.py:18) object (e.g., presence of `metadata`, `snapshot()` method) are implicitly relied upon.
*   **`SimulationExecutor` Interface:** Specific methods like [`run_chunked_forecast()`](intelligence/simulation_executor.py:114) and [`run_retrodiction_forecast()`](intelligence/simulation_executor.py:139) are expected on the `executor`.
*   **`Observer` Interface:** Specific methods like [`observe_symbolic_divergence()`](intelligence/intelligence_observer.py:151) and [`propose_symbolic_upgrades_live()`](intelligence/intelligence_observer.py:152) are expected on the `observer`.
*   **`FunctionRouter` for Module Loading:** The mechanism of loading modules via string paths is a contract with the `FunctionRouter`.
*   **`load_initial_state` Function:** Relies on this function from [`intelligence.worldstate_loader`](intelligence/worldstate_loader.py:14) for `WorldState` creation.

## 8. Existing Tests

Based on the file listing provided for the `tests/` directory, there does **not** appear to be a specific test file named `test_intelligence_core.py` or a similar direct counterpart for this module.
*   Files like [`test_integration_simulation_forecast.py`](tests/test_integration_simulation_forecast.py) might cover some functionality of `IntelligenceCore` as part of broader integration tests, but dedicated unit tests for `IntelligenceCore` itself are not apparent.

**Assessment:**
*   **Coverage:** Likely low or indirect for unit-level testing of `IntelligenceCore`. Integration tests might provide some coverage.
*   **Nature of Tests:** Unknown without specific test files for this module.
*   **Gaps:** A dedicated test suite for `IntelligenceCore` (e.g., `tests/intelligence/test_intelligence_core.py` or `tests/test_intelligence_core.py`) is a significant gap. Such tests would typically mock its dependencies (`FunctionRouter`, `SimulationExecutor`, `Observer`, `UpgradeSandboxManager`) to verify:
    *   Correct initialization.
    *   Proper delegation of calls to its dependencies.
    *   Correct handling of `WorldState` (initialization, updates).
    *   Logic within its own methods (e.g., `_extract_start_year`, flow in `run_forecast_cycle`).
    *   Interaction logic in `_post_cycle_audit`.

## 9. Module Architecture and Flow

**Architecture:**
The [`IntelligenceCore`](intelligence/intelligence_core.py:20) acts as a facade or a central controller in a layered architecture.
1.  **Dependencies:** It relies on injected components for specialized tasks:
    *   [`FunctionRouter`](intelligence/function_router.py:13): Dynamic code/module loading.
    *   [`SimulationExecutor`](intelligence/simulation_executor.py:15): Running actual simulation steps.
    *   [`Observer`](intelligence/intelligence_observer.py:16): Monitoring simulation outputs, learning, and identifying need for changes.
    *   [`UpgradeSandboxManager`](intelligence/upgrade_sandbox_manager.py:17): (Presumably) Managing the application or testing of proposed system upgrades.
2.  **State Management:** It holds the `last_worldstate` from simulation runs.
3.  **Workflow Orchestration:** It defines high-level workflows like `run_forecast_cycle` and `run_retrodiction_cycle`.

**Control Flow:**

*   **Initialization (`__init__`, `load_standard_modules`, `initialize_worldstate`):**
    1.  An `IntelligenceCore` instance is created with its dependencies.
    2.  [`load_standard_modules()`](intelligence/intelligence_core.py:51) can be called to ensure necessary sub-modules are loaded by the `router`.
    3.  [`initialize_worldstate()`](intelligence/intelligence_core.py:64) is called (either directly or by `run_forecast_cycle`) to set up the initial simulation state using [`load_initial_state()`](intelligence/worldstate_loader.py:14). The result is stored in `self.last_worldstate`.

*   **Forecast Cycle (`run_forecast_cycle`):**
    1.  If `self.last_worldstate` is `None`, [`initialize_worldstate()`](intelligence/intelligence_core.py:64) is called.
    2.  The `start_year` is extracted from `self.last_worldstate`.
    3.  Delegates to [`self.executor.run_chunked_forecast()`](intelligence/simulation_executor.py:114) to perform the simulation.
    4.  Updates `self.last_worldstate` with the result from the executor.
    5.  A `snapshot` of the final `WorldState` is taken.
    6.  Calls [`_post_cycle_audit()`](intelligence/intelligence_core.py:143) with the snapshot.

*   **Post-Cycle Audit (`_post_cycle_audit`):**
    1.  Calls [`self.observer.observe_symbolic_divergence()`](intelligence/intelligence_observer.py:151) with the snapshot.
    2.  If the observer proposes upgrades via [`self.observer.propose_symbolic_upgrades_live()`](intelligence/intelligence_observer.py:152), an `upgrade_id` is received.
    3.  A message about the upgrade proposal is printed. (Further handling of the upgrade is not detailed in this module).

*   **Retrodiction Cycle (`run_retrodiction_cycle`):**
    1.  Delegates directly to [`self.executor.run_retrodiction_forecast()`](intelligence/simulation_executor.py:139).
    2.  Returns the result from the executor.

## 10. Naming Conventions

*   **Class Name:** [`IntelligenceCore`](intelligence/intelligence_core.py:20) - PascalCase, clear and descriptive.
*   **Method Names:**
    *   Public methods: `load_standard_modules`, `initialize_worldstate`, `run_forecast_cycle`, `run_retrodiction_cycle` - snake_case, action-oriented and clear.
    *   Private/Internal methods: `_extract_start_year`, `_post_cycle_audit` - snake_case with a leading underscore, correctly indicating intended privacy.
*   **Variable Names:** Generally snake_case (e.g., `last_worldstate`, `start_year`, `divergence_report`).
    *   `ws_obj` (line 114, 119, 120) is a bit short but understandable in context as "WorldState object".
*   **Type Hinting:** Uses standard types from `typing` module. Class names used in type hints are correctly cased (e.g., `WorldState`, `FunctionRouter`).
*   **Module Paths (Strings):** Module paths like `"simulation_engine.turn_engine"` are consistent with Python's dot notation for modules.
*   **Constants/Defaults:**
    *   Default string `"default"` for `source` is lowercase.
    *   Default integer `2023` for `start_year`.
*   **PEP 8:** The code largely adheres to PEP 8 naming conventions (PascalCase for classes, snake_case for functions and variables).
*   **AI Assumption Errors:** No obvious AI-generated naming errors are apparent. The names seem human-readable and conventional for a Python project.
*   **Consistency:** Naming is generally consistent throughout the module.

The comment on line 48 regarding `self.loaded_modules` is an example of good self-documentation about potential inconsistencies or areas for review.

---
This report is based on the provided code for `intelligence/intelligence_core.py`.