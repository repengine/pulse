# SPARC Module Analysis: `intelligence/function_router.py`

**File Path:** [`intelligence/function_router.py`](intelligence/function_router.py:1)
**Analysis Date:** 2025-05-13

## 1. Module Intent/Purpose (SPARC: Specification)

The primary purpose of the [`intelligence/function_router.py`](intelligence/function_router.py:1) module is to provide a dynamic function routing mechanism. It defines the `FunctionRouter` class, which is responsible for:

*   Loading Python modules dynamically based on string identifiers ("verbs").
*   Executing specific functions within these loaded modules.
*   Implementing retry and back-off logic for module imports to enhance robustness.
*   Centralizing logging for its operations (though basic, via `print` to `sys.stderr`).
*   Allowing for the addition of custom paths to `sys.path` for module discovery.

It acts as a central dispatcher, decoupling the calling code from the direct knowledge of where specific functionalities (like "forecast", "compress") are implemented.

## 2. Operational Status/Completeness

*   The module appears largely **complete and operational** for its defined scope.
*   Core functionalities like module loading, retry logic ([`FunctionRouter.load_module()`](intelligence/function_router.py:64)), function execution ([`FunctionRouter.run_function()`](intelligence/function_router.py:112)), and utility methods like [`FunctionRouter.available_functions()`](intelligence/function_router.py:145) are implemented.
*   No explicit `TODO` comments or obvious placeholders indicating unfinished critical functionality were found.
*   The custom exception [`PulseImportError`](intelligence/function_router.py:28) is defined and used.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Externalized Verb Configuration:** The `verbs` dictionary ([`intelligence/function_router.py:40-46`](intelligence/function_router.py:40)) is hardcoded. A significant improvement would be to load this routing configuration from an external file (e.g., JSON, YAML) or allow dynamic registration of verbs. This would enhance flexibility and maintainability without requiring code changes for route updates.
*   **Advanced Logging:** The current logging ([`FunctionRouter._log()`](intelligence/function_router.py:192)) uses `print` to `sys.stderr`. Integrating with Python's standard `logging` module would offer more advanced features like log levels, different handlers, and formatting.
*   **Security of `additional_paths`:** While not a direct gap, the mechanism to add paths to `sys.path` ([`FunctionRouter.__init__()`](intelligence/function_router.py:48)) should be used with caution, especially if paths are derived from external or untrusted sources, to prevent potential code injection vulnerabilities. Documentation should highlight this.
*   **Asynchronous Operations:** For I/O-bound functions that the router might call, there's no built-in support for asynchronous execution. This could be a future extension if performance in such scenarios becomes critical.

## 4. Connections & Dependencies

*   **Internal Project Modules (Direct Imports):**
    *   [`intelligence.intelligence_config`](intelligence/intelligence_config.py): Imports `FUNCTION_ROUTER_MAX_RETRIES` and `FUNCTION_ROUTER_RETRY_SLEEP` ([`intelligence/function_router.py:22-25`](intelligence/function_router.py:22-25)).
*   **Internal Project Modules (Dynamically Imported via `verbs`):**
    *   `intelligence.simulation_executor`
    *   `forecast_output.forecast_compressor`
    *   `GPT.gpt_alignment_trainer`
    *   `intelligence.intelligence_core`
*   **External Libraries / Standard Library:**
    *   `importlib`: For dynamic module loading ([`importlib.import_module()`](intelligence/function_router.py:78)).
    *   `inspect`: For listing functions in a module ([`inspect.getmembers()`](intelligence/function_router.py:160), [`inspect.isfunction()`](intelligence/function_router.py:160)).
    *   `os`: Imported ([`intelligence/function_router.py:16`](intelligence/function_router.py:16)) but not directly used in the visible code.
    *   `sys`: For `sys.path` manipulation and `sys.stderr` ([`intelligence/function_router.py:17`](intelligence/function_router.py:17)).
    *   `time`: For `time.sleep()` in retry logic ([`intelligence/function_router.py:18`](intelligence/function_router.py:18)).
    *   `types.ModuleType`: For type hinting.
    *   `typing` (Any, Dict, List, Optional, Tuple): For type hinting.
*   **Interactions:** The router itself does not directly interact with files, databases, or message queues. However, the functions it dispatches to (e.g., `run_chunked_forecast`) are likely to have such interactions.
*   **Input/Output Files:** Not directly managed by the router.

## 5. Function and Class Example Usages

*   **`PulseImportError` Class ([`intelligence/function_router.py:28`](intelligence/function_router.py:28))**
    ```python
    # Conceptual example
    try:
        router.load_module("some.non_existent_module")
    except PulseImportError as e:
        logging.error(f"Module import failed after retries: {e}")
    ```

*   **`FunctionRouter` Class ([`intelligence/function_router.py:32`](intelligence/function_router.py:32))**
    ```python
    # Initialize the router
    router = FunctionRouter() # Optionally: additional_paths=["/path/to/custom_modules"]

    # Load a module explicitly (optional, as run_function also loads)
    # router.load_module("intelligence.simulation_executor", alias="sim_exec")

    # Run a function using a configured verb
    try:
        forecast_params = {"model_id": "ARIMA", "steps": 10}
        result = router.run_function("forecast", **forecast_params)
        print(f"Forecast result: {result}")
    except KeyError as e:
        print(f"Error: Unknown verb - {e}")
    except AttributeError as e:
        print(f"Error: Misconfigured function for verb - {e}")
    except Exception as e:
        print(f"Error during function execution: {e}")

    # List functions in a loaded module (module is loaded and aliased by its verb name)
    # For the "forecast" verb, the module "intelligence.simulation_executor" is loaded with alias "forecast".
    # available = router.available_functions("forecast")
    # print(f"Available functions in 'forecast' module: {available}")

    # List all modules currently loaded by the router
    # loaded_mods = router.list_loaded_modules()
    # print(f"Loaded modules: {loaded_mods}")
    ```

## 6. Hardcoding Issues (SPARC Critical)

*   **`verbs` Dictionary ([`intelligence/function_router.py:40-46`](intelligence/function_router.py:40)):** This is the most significant instance of hardcoding. The mapping of command-line interface (CLI) verbs to specific module paths and function names is directly embedded within the class definition.
    *   `"forecast": ("intelligence.simulation_executor", "run_chunked_forecast")`
    *   `"compress": ("forecast_output.forecast_compressor", "compress_forecasts")`
    *   `"retrodict": ("intelligence.simulation_executor", "run_retrodiction_forecast")`
    *   `"train-gpt": ("GPT.gpt_alignment_trainer", "run_alignment_cycle")`
    *   `"status": ("intelligence.intelligence_core", "assemble_status_report")`
    This practice reduces flexibility, as any changes or additions to routable functions require direct modification of the [`FunctionRouter`](intelligence/function_router.py:32) source code.
*   **Logging Prefix:** The string `"[Router]"` is hardcoded in the [`_log()`](intelligence/function_router.py:192) method ([`intelligence/function_router.py:201`](intelligence/function_router.py:201)). This is a minor issue.
*   **No Hardcoded Secrets/Credentials:** The module does not appear to contain any hardcoded secrets, API keys, or sensitive file paths.

## 7. Coupling Points

*   **`intelligence.intelligence_config`:** The router is coupled to this module for retry parameters (`FUNCTION_ROUTER_MAX_RETRIES`, `FUNCTION_ROUTER_RETRY_SLEEP`). Changes to these constant names in the config file would break the router.
*   **Target Modules and Functions (via `verbs`):** The router is tightly coupled to the existence and specific function names within the modules defined in the `verbs` dictionary. Refactoring in those target modules (e.g., changing a function name like `run_chunked_forecast`) would require a corresponding update in the router's `verbs` dictionary.
*   **Python's Import System:** Fundamentally reliant on `importlib`, `sys.path`, and Python's module resolution mechanisms.

## 8. Existing Tests (SPARC Refinement)

*   **Status:** No specific test files for [`intelligence/function_router.py`](intelligence/function_router.py:1) were provided or are evident from the current context.
*   **Assessment:** This is a **critical gap** from a SPARC (and general software engineering) perspective. Without unit tests, the reliability and correctness of the router, especially its error handling, retry logic, and dynamic loading, cannot be assured.
*   **Recommended Test Coverage:**
    *   Successful loading and execution of functions for all configured verbs.
    *   Correct handling of unknown/invalid verbs (`KeyError`).
    *   Robustness of module import retry logic (simulating import failures).
    *   Correct raising of [`PulseImportError`](intelligence/function_router.py:28) after max retries.
    *   Handling of cases where a target function does not exist or is not callable within a loaded module (`AttributeError`).
    *   Correct behavior of [`FunctionRouter.available_functions()`](intelligence/function_router.py:145) and [`FunctionRouter.list_loaded_modules()`](intelligence/function_router.py:163).
    *   Functionality of `additional_paths` in `__init__`.
    *   Proper propagation of exceptions raised by the target functions.
    *   Module unloading functionality.

## 9. Module Architecture and Flow (SPARC Architecture)

*   **Core Component:** The [`FunctionRouter`](intelligence/function_router.py:32) class is the central piece.
*   **Initialization ([`FunctionRouter.__init__()`](intelligence/function_router.py:48)):**
    *   Sets up an internal dictionary `self.modules` to cache loaded modules.
    *   Optionally extends `sys.path` with `additional_paths`.
*   **Module Loading ([`FunctionRouter.load_module()`](intelligence/function_router.py:64)):**
    *   Takes a `module_path` (e.g., "my_package.my_module") and an optional `alias`.
    *   Uses `importlib.import_module()` to load the module.
    *   Implements a retry loop (`MAX_RETRIES` times with `RETRY_SLEEP` intervals) if the import fails.
    *   Logs success or failure attempts.
    *   Raises [`PulseImportError`](intelligence/function_router.py:28) if all retries fail.
    *   Stores successfully loaded modules in `self.modules` using the alias or module path as the key.
*   **Function Execution ([`FunctionRouter.run_function()`](intelligence/function_router.py:112)):**
    1.  Receives a `verb` string and `**kwargs` for the target function.
    2.  Looks up the `verb` in the hardcoded `self.verbs` dictionary to get the `module_path` and `func_name`. Raises `KeyError` if `verb` is not found.
    3.  Calls [`self.load_module()`](intelligence/function_router.py:64) to load (or ensure loaded) the target module, using the `verb` itself as the alias for the module in the cache.
    4.  Retrieves the loaded module object from `self.modules`.
    5.  Uses `getattr()` to get the function object from the module.
    6.  Checks if the retrieved object is callable. Raises `AttributeError` if not.
    7.  Logs the impending function call.
    8.  Executes the function: `func(**kwargs)`.
    9.  If the target function raises an exception, it's logged and re-raised.
    10. Returns the result from the target function.
*   **Utility Methods:**
    *   [`FunctionRouter.available_functions()`](intelligence/function_router.py:145): Lists public functions in a loaded module using `inspect`.
    *   [`FunctionRouter.list_loaded_modules()`](intelligence/function_router.py:163): Returns keys of cached modules.
    *   [`FunctionRouter.unload_module()`](intelligence/function_router.py:99): Removes a module from the cache.
*   **Logging ([`FunctionRouter._log()`](intelligence/function_router.py:192)):** A static method providing simple print-based logging to `sys.stderr`.

## 10. Naming Conventions (SPARC Maintainability)

*   **Overall:** The module generally adheres to PEP 8 naming conventions.
*   **Classes:** `PulseImportError`, `FunctionRouter` use CapWords.
*   **Methods & Functions:** `load_module`, `run_function`, `_get_module`, `_log` use snake_case. Private/internal helper methods are prefixed with an underscore.
*   **Variables:** `module_path`, `func_name`, `attempts` are descriptive and use snake_case.
*   **Constants (Class Level):** `MAX_RETRIES`, `RETRY_SLEEP` use ALL_CAPS_SNAKE_CASE.
*   **Docstrings:** Present for the module, classes, and public methods, providing good descriptions of their purpose, arguments, and potential exceptions.
*   **Clarity:** Names are generally clear and self-explanatory, contributing to good maintainability. No significant ambiguities that might confuse AI or human developers were noted.

## 11. SPARC Compliance Summary

*   **Specification (✅ Good):** The module's purpose as a dynamic function router is well-defined and implemented.
*   **Modularity/Architecture (⚠️ Mixed):**
    *   **Good:** The `FunctionRouter` class itself is a modular component that decouples callers from target function implementations.
    *   **Concern:** The hardcoding of the `verbs` dictionary ([`intelligence/function_router.py:40-46`](intelligence/function_router.py:40)) significantly reduces architectural flexibility and modularity from a configuration perspective. It creates a tight coupling between the router's code and the system's command structure.
*   **Refinement Focus:**
    *   **Testability (⚠️ Concern/Gap):** The module is designed in a way that is inherently testable. However, the *absence of provided tests* is a major gap. Robust testing is crucial for such a central routing component.
    *   **Security (✅ Good, with minor note):**
        *   No direct hardcoding of secrets, API keys, or sensitive data paths was found within this module.
        *   The primary hardcoding issue (the `verbs` map) is related to configuration, not direct secrets.
        *   The `additional_paths` feature should be used with care to avoid loading code from untrusted locations.
    *   **Maintainability (✅ Good):** Code is clear, follows PEP 8, is well-documented with docstrings, and includes basic centralized logging. The retry logic for imports also contributes to robustness.
*   **No Hardcoding (Principle) (❌ Violated):** The `verbs` dictionary is hardcoded, which is the most significant deviation from SPARC principles in this module.

**Overall:** The [`FunctionRouter`](intelligence/function_router.py:32) is a well-structured and mostly maintainable module that fulfills its core purpose. The main areas for SPARC-aligned improvement are externalizing the `verbs` configuration to eliminate hardcoding and the critical need for comprehensive unit tests.