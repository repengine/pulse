# Module Analysis: `core/variable_accessor.py`

## 1. Module Intent/Purpose

The [`core/variable_accessor.py`](core/variable_accessor.py:1) module is designed to abstract and centralize access to worldstate variables and overlays. Its primary purpose is to provide safe getter and setter functions for these data points, ensuring that interactions with the simulation state's variables and overlays are managed consistently. It also includes a mechanism to validate variable and overlay names against a canonical registry ([`core/variable_registry.py`](core/variable_registry.py:1)), if available.

## 2. Key Functionalities

*   **Safe Variable Retrieval**: The [`get_variable(state, name, default)`](core/variable_accessor.py:11) function allows fetching a variable's value from the `state.variables` dictionary. It checks if the variable name exists in the `VARIABLE_REGISTRY` and returns a default value if the variable is not found.
*   **Safe Variable Setting**: The [`set_variable(state, name, value)`](core/variable_accessor.py:26) function allows setting a variable's value in the `state.variables` (which can be a dictionary or an object). It also checks against the `VARIABLE_REGISTRY`.
*   **Safe Overlay Retrieval**: The [`get_overlay(state, name, default)`](core/variable_accessor.py:42) function allows fetching an overlay's value from `state.overlays` (expected to be an object with attributes). It validates the overlay name against `VARIABLE_REGISTRY` and checks if its type is "symbolic".
*   **Safe Overlay Setting**: The [`set_overlay(state, name, value)`](core/variable_accessor.py:57) function allows setting an overlay's value in `state.overlays`. Similar validation for name and type ("symbolic") is performed.

## 3. Role within `core/` Directory

This module acts as a crucial interface or an abstraction layer within the `core/` directory for interacting with the dynamic data of the simulation (worldstate). By channeling variable and overlay access through these functions, the system can enforce consistency, validation, and potentially logging or other cross-cutting concerns related to state access.

## 4. Dependencies

### Internal Pulse Modules:
*   [`core.variable_registry.VARIABLE_REGISTRY`](core/variable_registry.py:1): Used to validate the names of variables and overlays and to check the type of overlays.

### External Libraries:
*   `typing.Any`: Used for type hinting the `state` parameter, indicating flexibility in the structure of the state object as long as it conforms to expected attributes (`.variables`, `.overlays`).

## 5. Adherence to SPARC Principles

*   **Module Intent/Purpose**:
    *   Clearly stated in the module docstring (lines 1-7). The module fulfills this intent by providing abstracted access.
*   **Operational Status/Completeness**:
    *   The module appears largely complete for its defined scope. It provides the fundamental get/set operations for both variables and overlays.
*   **Implementation Gaps / Unfinished Next Steps**:
    *   The sections for optional logging or warning about unknown variables/overlays are currently implemented as `pass` statements ([`core/variable_accessor.py:22`](core/variable_accessor.py:22), [`core/variable_accessor.py:35`](core/variable_accessor.py:35), [`core/variable_accessor.py:53`](core/variable_accessor.py:53), [`core/variable_accessor.py:66`](core/variable_accessor.py:66)). Implementing actual logging or a more robust warning mechanism would be a clear next step.
*   **Connections & Dependencies**:
    *   Strong dependency on the `VARIABLE_REGISTRY` from [`core/variable_registry.py`](core/variable_registry.py:1).
    *   Relies on the `state` object having a specific structure:
        *   `state.variables`: Expected to be a dictionary or an object where variables are stored.
        *   `state.overlays`: Expected to be an object where overlays are stored as attributes.
*   **Function and Class Example Usages**:
    ```python
    from typing import Any
    # Assume VARIABLE_REGISTRY is mocked for this example
    VARIABLE_REGISTRY = {
        "population": {"type": "numeric"},
        "economic_index": {"type": "numeric"},
        "policy_focus": {"type": "symbolic"}
    }

    class MockState:
        def __init__(self):
            self.variables = {"population": 1000.0, "economic_index": 75.5}
            # Mocking overlays as an object with attributes
            self.overlays = type('MockOverlays', (), {"policy_focus": 0.75})()

    # In a real scenario, these would be imported from core.variable_accessor
    def get_variable(state: Any, name: str, default: float = 0.0) -> float:
        if name not in VARIABLE_REGISTRY:
            pass # Log/warn
        return state.variables.get(name, default)

    def set_variable(state: Any, name: str, value: float) -> None:
        if name not in VARIABLE_REGISTRY:
            pass # Log/warn
        if isinstance(state.variables, dict):
            state.variables[name] = value
        else:
            setattr(state.variables, name, value)

    def get_overlay(state: Any, name: str, default: float = 0.0) -> float:
        if name not in VARIABLE_REGISTRY or VARIABLE_REGISTRY[name].get("type") != "symbolic":
            pass # Log/warn
        return getattr(state.overlays, name, default)

    def set_overlay(state: Any, name: str, value: float) -> None:
        if name not in VARIABLE_REGISTRY or VARIABLE_REGISTRY[name].get("type") != "symbolic":
            pass # Log/warn
        setattr(state.overlays, name, value)

    # Example Usage
    current_state = MockState()

    # Get a variable
    pop = get_variable(current_state, "population")
    print(f"Population: {pop}") # Output: Population: 1000.0

    # Set a variable
    set_variable(current_state, "economic_index", 78.0)
    print(f"Updated Economic Index: {current_state.variables['economic_index']}") # Output: 78.0

    # Get an overlay
    policy = get_overlay(current_state, "policy_focus")
    print(f"Policy Focus: {policy}") # Output: Policy Focus: 0.75

    # Set an overlay
    set_overlay(current_state, "policy_focus", 0.9)
    print(f"Updated Policy Focus: {current_state.overlays.policy_focus}") # Output: 0.9

    # Get a non-existent variable with default
    gdp = get_variable(current_state, "gdp", 0.0)
    print(f"GDP: {gdp}") # Output: GDP: 0.0 (assuming "gdp" is not in VARIABLE_REGISTRY)
    ```
*   **Hardcoding Issues**:
    *   The default value for missing variables/overlays in getter functions is hardcoded to `0.0` ([`core/variable_accessor.py:11`](core/variable_accessor.py:11), [`core/variable_accessor.py:42`](core/variable_accessor.py:42)). This might be acceptable for many numeric variables but could be less suitable for others.
    *   The check for overlay type `VARIABLE_REGISTRY[name].get("type") != "symbolic"` ([`core/variable_accessor.py:52`](core/variable_accessor.py:52), [`core/variable_accessor.py:65`](core/variable_accessor.py:65)) hardcodes "symbolic" as the expected type for overlays accessed via these functions. If other types of overlays need similar access, this logic would need extension or generalization.
*   **Coupling Points**:
    *   Tightly coupled with the structure of the `VARIABLE_REGISTRY` dictionary (expects it to be a dictionary and to contain type information for overlays).
    *   Tightly coupled with the expected structure of the `state` object (i.e., presence of `state.variables` and `state.overlays`, and their respective types - dict/object for variables, object with attributes for overlays).
*   **Existing Tests**:
    *   No tests are provided within this module. External tests would be needed to verify its functionality.
*   **Module Architecture and Flow**:
    *   The architecture is simple and procedural, consisting of four public functions.
    *   The flow within each function is:
        1.  Validate the `name` against `VARIABLE_REGISTRY`.
        2.  (Placeholder for logging/warning if validation fails).
        3.  Perform the get or set operation on the `state` object.
    *   The [`set_variable`](core/variable_accessor.py:26) function handles two cases for `state.variables`: if it's a dictionary or an object.
*   **Naming Conventions**:
    *   Follows Python standard `snake_case` for function names (e.g., [`get_variable`](core/variable_accessor.py:11), [`set_overlay`](core/variable_accessor.py:57)) and parameters.
    *   Names are generally descriptive and clear.

## 6. Overall Assessment

*   **Completeness**:
    *   The module is mostly complete for its stated goal of providing safe access to variables and overlays. The main area for improvement is the implementation of actual logging or error handling for invalid/unknown names instead of `pass`.
*   **Quality**:
    *   The code quality is good. It is well-commented, uses type hints, and the logic is straightforward and easy to understand.
    *   It provides a valuable abstraction layer that can help in maintaining and evolving the system by centralizing state access logic.
    *   The design choice to rely on a global `VARIABLE_REGISTRY` promotes consistency but also introduces a global state dependency that needs to be managed carefully.
    *   The flexibility in `state.variables` (dict or object) in [`set_variable`](core/variable_accessor.py:26) is a good feature, accommodating different state representations.

## 7. Suggested Improvements

*   Implement the placeholder logging/warning mechanisms (e.g., using Python's `logging` module).
*   Consider if the hardcoded default value `0.0` is universally appropriate or if it should be more flexible (e.g., type-dependent defaults based on `VARIABLE_REGISTRY`, or allowing the caller to specify a typed default).
*   Clarify or make more flexible the "symbolic" type check for overlays if other types of overlays are anticipated.
*   Add unit tests to ensure the functions behave as expected under various conditions (e.g., variable exists, variable missing, state.variables is dict, state.variables is object).