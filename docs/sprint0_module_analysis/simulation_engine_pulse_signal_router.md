# SPARC Module Analysis: simulation_engine/pulse_signal_router.py

**Date of Analysis:** 2025-05-14
**Analyzer:** Roo
**Pulse Version Context:** v0.4 (as per module docstring)

## Module Intent/Purpose (SPARC Specification)

The primary role of the [`simulation_engine/pulse_signal_router.py`](simulation_engine/pulse_signal_router.py:1) module is to act as a central dispatcher for incoming symbolic, narrative, or signal-driven events. It translates these external signals into concrete changes within Pulse's `WorldState`. This involves updating worldstate variables, adjusting symbolic overlays (e.g., "hope", "despair"), and optionally influencing capital allocations. Essentially, it allows abstract narrative events like "ai_panic" or "fed_cut" to have tangible, simulated effects through a defined symbolic causality mechanism.

## Operational Status/Completeness

The module appears to be operational and relatively complete for its defined purpose. It has a clear structure for defining signal handlers and a main routing function.
- No obvious `TODO` comments or major placeholders were identified within this specific module.
- The error handling within signal handlers (e.g., `try-except AttributeError` for missing state variables) suggests a degree of robustness.

## Implementation Gaps / Unfinished Next Steps

- **Extensibility of Signal Handlers:** While new signals can be added by defining new functions and mapping them in `_signal_handlers`, a more dynamic or plugin-based approach for adding signal handlers could be considered for larger-scale systems or if signals become very numerous.
- **Configuration of Signal Effects:** The effects of signals (e.g., the exact amount `ai_policy_risk` increases during an `_ai_panic`) are hardcoded within the handler functions. These could potentially be made configurable.
- **Granularity of Logging:** Logging is present, but more detailed context or structured logging for signal impacts could be beneficial for audit and analysis.

## Connections & Dependencies

### Direct Imports (Project Modules):
- [`engine.worldstate`](simulation_engine/pulse_signal_router.py:21): Specifically, the `WorldState` class is imported and used as the primary data structure being mutated.
- [`engine.state_mutation`](simulation_engine/pulse_signal_router.py:22): Functions `adjust_overlay` and `adjust_capital` are used to modify the `WorldState`.
- [`engine.variables.worldstate_variables`](simulation_engine/pulse_signal_router.py:23): The `WorldstateVariables` class is imported, likely for type hinting or direct interaction, although direct usage within `pulse_signal_router.py` itself is primarily through `state.variables`.

### Direct Imports (External Libraries):
- `logging` (Python Standard Library): Used for logging errors, warnings, and informational messages.
- `typing.Callable, typing.Dict` (Python Standard Library): Used for type hinting.

### Touched Project Files (for dependency mapping):
To understand the full context and dependencies, the following project files were read:
- [`simulation_engine/pulse_signal_router.py`](simulation_engine/pulse_signal_router.py:1) (The module being analyzed)
- [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1) (Defines `WorldState`, `SymbolicOverlays`, `CapitalExposure`, `Variables`)
- [`simulation_engine/state_mutation.py`](simulation_engine/state_mutation.py:1) (Defines `adjust_overlay`, `adjust_capital`, `update_numeric_variable`, `decay_overlay`)
- [`simulation_engine/variables/worldstate_variables.py`](simulation_engine/variables/worldstate_variables.py:1) (Defines `WorldstateVariables` class)
- [`core/variable_registry.py`](core/variable_registry.py:1) (Used by `WorldstateVariables` to get default states)
- [`core/path_registry.py`](core/path_registry.py:1) (Used by `variable_registry` and `pulse_learning_log`)
- [`core/pulse_learning_log.py`](core/pulse_learning_log.py:1) (Used by `state_mutation` for logging learning events)
- [`core/bayesian_trust_tracker.py`](core/bayesian_trust_tracker.py:1) (Used by `pulse_learning_log`)
- [`symbolic_system/context.py`](symbolic_system/context.py:1) (Used by `state_mutation` to check if symbolic processing is enabled)
- [`core/pulse_config.py`](core/pulse_config.py:1) (Used by `state_mutation` and `symbolic_system.context` for global and mode-specific configurations)

### Interactions (Shared Data, Files, DBs, Queues):
- **`WorldState` Object:** The module's primary interaction is by modifying the passed `WorldState` object. This object acts as the central shared data structure.
- **Logging System:** Interacts with Python's `logging` module, which typically writes to console or files as configured elsewhere.
- **No direct file I/O, database, or queue interactions** are apparent within this module itself. Dependencies like `pulse_learning_log` handle their own persistence.

### Input/Output Files:
- **Input:** The module receives signals as string inputs to the [`route_signal()`](simulation_engine/pulse_signal_router.py:87) function.
- **Output:** The module doesn't directly produce output files. Its "output" is the mutation of the `WorldState` object and log messages.

## Function and Class Example Usages

### Function: [`route_signal(state: WorldState, signal: str) -> bool`](simulation_engine/pulse_signal_router.py:87)
This is the main public function of the module.
```python
from engine.worldstate import WorldState
from engine.pulse_signal_router import route_signal

# Initialize a WorldState object (potentially with some default variables set)
sim_state = WorldState()
sim_state.variables.ai_policy_risk = 0.1
sim_state.variables.fed_funds_rate = 0.5
sim_state.variables.crypto_instability = 0.0
sim_state.variables.media_sentiment_score = 0.5
sim_state.variables.energy_price_index = 0.2
sim_state.variables.public_trust_level = 0.7

# Route an "ai_panic" signal
handled = route_signal(sim_state, "ai_panic")
if handled:
    print(f"AI Panic signal processed. Current AI Policy Risk: {sim_state.variables.ai_policy_risk}")
    print(f"Despair overlay: {sim_state.overlays.despair}, Fatigue overlay: {sim_state.overlays.fatigue}")

# Route a "fed_cut" signal
handled = route_signal(sim_state, "fed_cut")
if handled:
    print(f"Fed Cut signal processed. Current Fed Funds Rate: {sim_state.variables.fed_funds_rate}")
    print(f"Hope overlay: {sim_state.overlays.hope}, SPY Capital: {sim_state.capital.spy}")

# Attempt to route an unknown signal
handled = route_signal(sim_state, "market_boom_unexpected")
if not handled:
    print("Unknown signal 'market_boom_unexpected' was not processed.")
```

### Internal Handler Functions (e.g., [`_ai_panic(state)`](simulation_engine/pulse_signal_router.py:26))
These are private helper functions, invoked by [`route_signal()`](simulation_engine/pulse_signal_router.py:87) based on the `_signal_handlers` mapping.
```python
# Conceptual usage (not called directly from outside the module)
# from engine.state_mutation import adjust_overlay, adjust_capital
# from engine.worldstate import WorldState

# def _ai_panic_example(state: WorldState):
#     adjust_overlay(state, "despair", +0.02)
#     adjust_overlay(state, "fatigue", +0.01)
#     try:
#         state.variables.ai_policy_risk = min(1.0, state.variables.ai_policy_risk + 0.2)
#     except AttributeError:
#         logging.error("State missing ai_policy_risk attribute.")

# sim_state_example = WorldState()
# sim_state_example.variables.ai_policy_risk = 0.1
# _ai_panic_example(sim_state_example)
# print(f"Despair: {sim_state_example.overlays.despair}, AI Policy Risk: {sim_state_example.variables.ai_policy_risk}")
```

## Hardcoding Issues (SPARC Critical)

Several instances of hardcoding are present, primarily concerning the magnitude of changes and specific keys:

1.  **Overlay Adjustment Values:** In all handler functions (e.g., [`_ai_panic()`](simulation_engine/pulse_signal_router.py:26), [`_fed_cut()`](simulation_engine/pulse_signal_router.py:34)), the delta values for `adjust_overlay` are hardcoded (e.g., `+0.02`, `+0.015`).
    *   Example: [`adjust_overlay(state, "despair", +0.02)`](simulation_engine/pulse_signal_router.py:27)
2.  **Variable Adjustment Values:** The amounts by which state variables are changed are hardcoded.
    *   Example: `state.variables.ai_policy_risk + 0.2` in [`_ai_panic()`](simulation_engine/pulse_signal_router.py:30)
    *   Example: `state.variables.fed_funds_rate - 0.25` in [`_fed_cut()`](simulation_engine/pulse_signal_router.py:36)
3.  **Capital Adjustment Values:** The amounts for `adjust_capital` are hardcoded.
    *   Example: `adjust_capital(state, "spy", +400)` in [`_fed_cut()`](simulation_engine/pulse_signal_router.py:40)
4.  **Overlay Names:** Strings like `"despair"`, `"hope"`, `"fatigue"`, `"trust"` are hardcoded when calling `adjust_overlay`.
5.  **Variable Names:** Strings for state variable names like `"ai_policy_risk"`, `"fed_funds_rate"`, `"crypto_instability"`, etc., are hardcoded when accessing `state.variables`.
6.  **Capital Asset Names:** Strings like `"spy"`, `"msft"`, `"ibit"`, `"nvda"` are hardcoded for `adjust_capital`.
7.  **Signal Strings:** The keys in the `_signal_handlers` dictionary (e.g., `"ai_panic"`, `"fed_cut"`) are hardcoded signal identifiers. This is somewhat expected for a dispatcher, but the mapping itself is static within the code.
    *   Example: [`_signal_handlers: Dict[str, Callable] = { "ai_panic": _ai_panic, ... }`](simulation_engine/pulse_signal_router.py:74)

**SPARC Implication:** Hardcoding these values reduces flexibility and maintainability. Changes to signal impacts require direct code modification. Ideally, these could be sourced from a configuration file or a more dynamic rule system.

## Coupling Points

- **`WorldState` Object Structure:** The module is tightly coupled to the structure of the `WorldState` object, including its `overlays`, `capital`, and `variables` attributes, and the specific names of attributes within them (e.g., `state.variables.ai_policy_risk`). Changes to `WorldState`'s structure would likely require changes in this module.
- **`state_mutation` Module:** Strong coupling with [`adjust_overlay()`](simulation_engine/state_mutation.py:94) and [`adjust_capital()`](simulation_engine/state_mutation.py:151) functions from the [`engine.state_mutation`](simulation_engine/state_mutation.py:1) module. The behavior of `pulse_signal_router.py` depends on the correct implementation of these mutation functions.
- **`_signal_handlers` Dictionary:** The core routing logic depends entirely on this internal dictionary. Adding or modifying signal handling requires direct modification of this dictionary and associated handler functions.

## Existing Tests (SPARC Refinement)

- A single internal test function [`_test_route_signal()`](simulation_engine/pulse_signal_router.py:113) exists within the module.
- **Coverage:**
    - It tests the successful handling of known signals (`"ai_panic"`, `"fed_cut"`).
    - It tests the correct non-handling of an unknown signal (`"unknown_signal"`).
    - It initializes necessary variables on a `WorldState` instance for the tests to run.
- **Quality & Gaps:**
    - **Basic Assertions:** The test uses simple `assert` statements on the boolean return of [`route_signal()`](simulation_engine/pulse_signal_router.py:87). It does *not* assert the correctness of the state changes themselves (e.g., that `ai_policy_risk` was actually incremented by the expected amount). This is a significant gap in test quality.
    - **No Edge Cases Tested:** Does not test edge cases like signals that might try to push values beyond their `min/max` bounds (though the underlying `state_mutation` functions or `WorldstateVariables` setters might handle this, it's not explicitly tested here).
    - **No Testing for Malformed Signals:** The [`route_signal()`](simulation_engine/pulse_signal_router.py:87) function checks `isinstance(signal, str)`, but the test doesn't explicitly pass non-string signals to verify this error path.
    - **No Testing of All Handlers:** The test only covers a subset of the defined signal handlers. Each handler's specific logic and potential `AttributeError` paths are not individually tested.
    - **Test Location:** The test is an internal function (prefixed with `_`) and includes a `print` statement upon success, suggesting it's meant for ad-hoc execution rather than integration into a formal test suite (though it could be called by one).
    - **Dependency on `WorldState` Initialization:** The test directly manipulates `s.variables` to set up the test state. This is acceptable for a unit-level test but highlights the dependency.

**SPARC Testability Assessment:** The current test provides a very basic sanity check of the routing mechanism but lacks depth in verifying the actual impact of signals on the `WorldState`. Test coverage for individual signal handlers and their specific state mutations is missing. To improve testability and coverage, dedicated unit tests for each signal handler, asserting specific state changes, would be beneficial. These should be part of a formal test suite (e.g., using `pytest` or `unittest`).

## Module Architecture and Flow (SPARC Architecture)

- **Dispatch Table Design:** The module uses a common and effective design pattern for routing: a dictionary (`_signal_handlers`) mapping signal strings to handler functions.
- **Handler Functions:** Each distinct type of signal event (or group of similar events) has a dedicated private handler function (e.g., [`_ai_panic()`](simulation_engine/pulse_signal_router.py:26), [`_fed_cut()`](simulation_engine/pulse_signal_router.py:34)). These functions encapsulate the logic for how a specific signal mutates the `WorldState`.
- **Central Routing Function:** The [`route_signal()`](simulation_engine/pulse_signal_router.py:87) function is the public entry point. It performs:
    1.  Input validation (checks if the signal is a string).
    2.  Signal normalization (converts to lowercase).
    3.  Lookup in the `_signal_handlers` dispatch table.
    4.  Invocation of the appropriate handler if found.
    5.  Logging of the outcome (handled, unknown, or error during handling).
- **State Modification Delegation:** The actual modification of `WorldState` attributes (overlays, capital, variables) is delegated to:
    - Direct attribute assignment on `state.variables` (e.g., `state.variables.ai_policy_risk = ...`).
    - Functions from the [`engine.state_mutation`](simulation_engine/state_mutation.py:1) module (`adjust_overlay`, `adjust_capital`).
- **Error Handling:** Handler functions include `try-except AttributeError` blocks to gracefully handle cases where expected variables might be missing from the `WorldState`. The main [`route_signal()`](simulation_engine/pulse_signal_router.py:87) function also has a general `try-except Exception` to catch errors during handler execution.

**Modularity:**
- The module is reasonably modular, focusing on the single responsibility of routing signals.
- It depends on `WorldState` and `state_mutation` modules, which is appropriate given its role.
- The use of private handler functions and a central dispatch table promotes internal organization.

## Naming Conventions (SPARC Maintainability)

- **Module Name:** [`pulse_signal_router.py`](simulation_engine/pulse_signal_router.py:1) is clear and descriptive of its function.
- **Function Names:**
    - Public function [`route_signal()`](simulation_engine/pulse_signal_router.py:87) is clear.
    - Private handler functions are prefixed with an underscore (e.g., [`_ai_panic()`](simulation_engine/pulse_signal_router.py:26), [`_fed_cut()`](simulation_engine/pulse_signal_router.py:34)), which is a standard Python convention for internal use. Their names are descriptive of the signal they handle.
- **Variable Names:**
    - `_signal_handlers` clearly indicates its purpose as a dispatch table for signal handlers.
    - `state` for `WorldState` instances is a common and acceptable short name in this context.
    - `signal`, `sig`, `handler` are clear within their scope.
- **Clarity:** The code is generally clear and easy to follow. Docstrings are present for the module and the main public function, explaining their purpose, arguments, and returns. Handler functions, while private, could benefit from brief docstrings explaining the specific narrative event they represent and its intended impact.

**SPARC Maintainability Assessment:** Naming conventions are good and follow Python best practices. The code structure is logical. Adding docstrings to handler functions would further improve maintainability. The primary maintainability concern stems from the hardcoding issues mentioned earlier.

## SPARC Compliance Summary

- **Specification:** The module's purpose is well-defined in its docstring and generally adhered to.
- **Modularity/Architecture:** The module exhibits good modularity with a clear dispatch-based architecture. It appropriately delegates state changes.
- **Refinement - Testability:** Basic test exists, but coverage is low, especially regarding the actual state changes caused by signals. Significant room for improvement by adding comprehensive unit tests for each handler and edge cases.
- **Refinement - Security (Hardcoding):**
    - **No direct secrets, API keys, or sensitive paths** were found within this module.
    - However, numerous instances of **hardcoded numerical values and string keys** (for overlays, variables, assets, signals) are present. This impacts flexibility and maintainability, violating the "No Hardcoding" principle in spirit, even if not direct security credentials. These should ideally be configurable.
- **Refinement - Maintainability:** Good naming and structure. Docstrings are adequate for public interfaces. The main maintainability challenge is the hardcoding of signal effects.
- **Overall SPARC Alignment:**
    - **Strengths:** Clear purpose, logical architecture, good naming.
    - **Weaknesses:** Significant hardcoding of signal parameters, limited test coverage for actual outcomes.
    - **Recommendations:**
        1.  Externalize the configuration of signal effects (deltas, target keys) rather than hardcoding them in functions.
        2.  Expand test coverage significantly to include validation of state changes for each signal and edge case testing.
        3.  Consider a more dynamic registration mechanism for signal handlers if the number of signals is expected to grow substantially.
        4.  Add brief docstrings to internal handler functions for clarity.