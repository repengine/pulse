# Analysis Report: `intelligence/function_router.py`

## 1. Module Intent/Purpose

The primary role of the [`intelligence/function_router.py`](intelligence/function_router.py:1) module is to dynamically load and route function calls based on a predefined set of "verbs". It acts as a central dispatcher, allowing other parts of the system to invoke functionalities in different modules using simple string commands. Key features include:
*   Dynamic module loading with retry and back-off mechanisms for robustness.
*   Centralized logging for module loading and function execution.
*   A configurable mapping of verbs to specific functions within other modules.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined purpose.
*   It has a clear structure and implements the core functionalities described (loading, routing, logging).
*   The retry logic for module imports ([`PulseImportError`](intelligence/function_router.py:28), [`load_module()`](intelligence/function_router.py:64)) suggests a consideration for resilience in a potentially complex environment where modules might not be immediately available.
*   There are no obvious placeholders like `TODO` or `FIXME` comments in the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility of Verbs:** While the `verbs` dictionary ([`verbs`](intelligence/function_router.py:40)) is clear, there's no built-in mechanism for other modules or configurations to dynamically extend or modify this mapping at runtime beyond direct modification of the dictionary or creating new instances of `FunctionRouter`. This might be a deliberate design choice for simplicity or an area for future enhancement if more dynamic routing is needed.
*   **Error Handling Granularity:** The [`run_function()`](intelligence/function_router.py:112) method catches general `Exception` ([`except Exception as exc:`](intelligence/function_router.py:141)) during the execution of the target function. While it logs and re-raises the exception, more specific error handling or classification based on the type of error from the routed function could be beneficial for higher-level error management strategies.
*   **Configuration Source:** The retry parameters ([`FUNCTION_ROUTER_MAX_RETRIES`](intelligence/function_router.py:23), [`FUNCTION_ROUTER_RETRY_SLEEP`](intelligence/function_router.py:24)) are imported from [`intelligence.intelligence_config`](intelligence/intelligence_config.py). If this router is intended to be a more generic component, these might be better passed during instantiation or configured through a more abstract mechanism.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`intelligence.intelligence_config`](intelligence/intelligence_config.py): For configuration values `FUNCTION_ROUTER_MAX_RETRIES` and `FUNCTION_ROUTER_RETRY_SLEEP`.
*   The modules specified in the `verbs` dictionary are dynamically imported:
    *   [`intelligence.simulation_executor`](intelligence/simulation_executor.py) (for "forecast", "retrodict" verbs)
    *   [`forecast_output.forecast_compressor`](forecast_output/forecast_compressor.py) (for "compress" verb)
    *   [`GPT.gpt_alignment_trainer`](GPT/gpt_alignment_trainer.py) (for "train-gpt" verb)
    *   [`intelligence.intelligence_core`](intelligence/intelligence_core.py) (for "status" verb)

### External Library Dependencies:
*   `importlib`: Standard Python library for dynamic module importing.
*   `inspect`: Standard Python library for introspection (used in [`available_functions()`](intelligence/function_router.py:145)).
*   `os`: Standard Python library (implicitly, though not directly used in a way that creates a strong dependency for the core logic).
*   `sys`: Standard Python library for `sys.path` manipulation and `sys.stderr` for logging.
*   `time`: Standard Python library for `time.sleep` in retry logic.
*   `types`: For `ModuleType` hint.
*   `typing`: For type hints (`Any`, `Dict`, `List`, `Optional`, `Tuple`).

### Interaction with Other Modules via Shared Data:
*   The primary interaction is through dynamic function calls. It doesn't appear to directly interact via shared files, databases, or message queues itself, but the functions it calls might.

### Input/Output Files:
*   **Logging:** The module logs its operations to `sys.stderr` via the [`_log()`](intelligence/function_router.py:193) method. No other direct file I/O is apparent within this module.

## 5. Function and Class Example Usages

### Class: `FunctionRouter`
```python
from intelligence.function_router import FunctionRouter

# Initialize the router
router = FunctionRouter()

# Example: Run a forecast
try:
    forecast_results = router.run_function("forecast", model_id="model123", data_points=[1, 2, 3])
    print("Forecast successful:", forecast_results)
except KeyError as e:
    print(f"Error: {e}") # Verb not found
except AttributeError as e:
    print(f"Error: {e}") # Function not callable
except Exception as e:
    print(f"Function execution failed: {e}")

# Example: Load an additional module (if needed for other purposes)
try:
    router.load_module("custom_module.utils", alias="utils")
    utils_functions = router.available_functions("utils")
    print("Available functions in utils:", utils_functions)
except PulseImportError as e:
    print(f"Failed to load module: {e}")

# List loaded modules
print("Loaded modules:", router.list_loaded_modules())
```

### Class: `PulseImportError`
This is a custom exception raised by the router.
```python
from intelligence.function_router import FunctionRouter, PulseImportError

router = FunctionRouter()
try:
    router.load_module("non_existent_module.non_existent_function")
except PulseImportError as e:
    print(f"Caught expected import error: {e}")
```

## 6. Hardcoding Issues

*   **Verb Definitions:** The `verbs` dictionary ([`verbs`](intelligence/function_router.py:40)) which maps command strings to module and function paths is hardcoded within the class definition. While this is clear and simple, it means changing or adding verbs requires modifying the source code of this class. For greater flexibility, these mappings could be loaded from a configuration file or passed during instantiation.
    *   `"forecast": ("intelligence.simulation_executor", "run_chunked_forecast")`
    *   `"compress": ("forecast_output.forecast_compressor", "compress_forecasts")`
    *   `"retrodict": ("intelligence.simulation_executor", "run_retrodiction_forecast")`
    *   `"train-gpt": ("GPT.gpt_alignment_trainer", "run_alignment_cycle")`
    *   `"status": ("intelligence.intelligence_core", "assemble_status_report")`
*   **Logging Prefix:** The log prefix `"[Router]"` in [`_log()`](intelligence/function_router.py:201) is hardcoded.
*   **Error Messages:** Some parts of error messages are hardcoded strings, which is typical but worth noting (e.g., "Unknown verb:", "is not callable for verb").

## 7. Coupling Points

*   **`intelligence.intelligence_config`:** Tightly coupled for retry parameters ([`FUNCTION_ROUTER_MAX_RETRIES`](intelligence/function_router.py:23), [`FUNCTION_ROUTER_RETRY_SLEEP`](intelligence/function_router.py:24)). Changes to how configuration is managed in the project could necessitate changes here.
*   **Target Modules and Functions:** The router is inherently coupled to the existence and signature of the modules and functions defined in its `verbs` dictionary. If [`intelligence.simulation_executor.run_chunked_forecast()`](intelligence/simulation_executor.py) changes its expected arguments, calls through the router might break without the router itself changing.
*   **`sys.path` Modification:** The constructor ([`__init__()`](intelligence/function_router.py:48)) can modify `sys.path`. While this is a common pattern for dynamic loading, it's a global state change that can have side effects if not managed carefully.

## 8. Existing Tests

Based on the `list_files` output for the `tests` directory, there does **not** appear to be a dedicated test file for [`intelligence/function_router.py`](intelligence/function_router.py:1) (e.g., no `tests/intelligence/test_function_router.py` or `tests/test_function_router.py`). This indicates a significant gap in unit testing for this module.
Without specific tests, it's hard to assess coverage or the nature of existing tests for this particular module. It might be tested indirectly via integration tests for the CLI or other components that use it, but dedicated unit tests are missing.

**Obvious Gaps:**
*   Unit tests for successful function routing.
*   Tests for handling unknown verbs.
*   Tests for non-callable target functions.
*   Tests for the module loading mechanism, including successful loads and `PulseImportError` on failure after retries.
*   Tests for `sys.path` modification.
*   Tests for `available_functions()`, `list_loaded_modules()`, and `unload_module()`.

## 9. Module Architecture and Flow

*   **Architecture:** The module is designed around the [`FunctionRouter`](intelligence/function_router.py:32) class.
    *   An instance of this class holds a dictionary of loaded modules (`self.modules`) and a predefined dictionary mapping verbs to target module/function pairs (`self.verbs`).
    *   Configuration for retry behavior (`MAX_RETRIES`, `RETRY_SLEEP`) is taken from class attributes, which are initialized from [`intelligence.intelligence_config`](intelligence/intelligence_config.py).
*   **Key Components:**
    *   [`FunctionRouter`](intelligence/function_router.py:32): The main class.
    *   [`PulseImportError`](intelligence/function_router.py:28): Custom exception for import failures.
    *   [`verbs`](intelligence/function_router.py:40): Hardcoded dictionary defining the routing map.
    *   [`_log()`](intelligence/function_router.py:193): Private static method for centralized logging.
*   **Primary Data/Control Flows:**
    1.  **Initialization (`__init__()`):**
        *   Optionally adds paths to `sys.path`.
        *   Initializes `self.modules` dictionary.
    2.  **Loading a Module (`load_module()`):**
        *   Attempts to import the specified module path using `importlib.import_module()`.
        *   If import fails, it retries up to `MAX_RETRIES` times with `RETRY_SLEEP` seconds delay between attempts.
        *   If successful, stores the module object in `self.modules`.
        *   If all retries fail, raises `PulseImportError`.
    3.  **Running a Function (`run_function()`):**
        *   Takes a `verb` string and `**kwargs`.
        *   Looks up the `module_path` and `func_name` from the `self.verbs` dictionary.
        *   Calls [`load_module()`](intelligence/function_router.py:64) to ensure the target module is loaded (using the verb as an alias).
        *   Retrieves the module from `self.modules`.
        *   Uses `getattr()` to get the function from the module.
        *   Checks if the retrieved attribute is callable.
        *   Executes the function with `**kwargs`.
        *   Logs success or failure and re-raises exceptions from the target function.
    4.  **Other Methods:** Provide utilities to list loaded modules, available functions in a module, and unload modules.

## 10. Naming Conventions

*   **Classes:** `FunctionRouter`, `PulseImportError` follow PascalCase (PEP 8).
*   **Methods:** `load_module`, `run_function`, `_get_module`, `_log` follow snake_case (PEP 8). Private helper methods are prefixed with a single underscore.
*   **Class Attributes/Constants:** `MAX_RETRIES`, `RETRY_SLEEP` are uppercase (PEP 8 for constants). The `verbs` dictionary is lowercase, which is acceptable for a collection.
*   **Variables:** `module_path`, `func_name`, `attempts` generally follow snake_case.
*   **Module Name:** `function_router.py` is snake_case.
*   **Configuration Imports:** `FUNCTION_ROUTER_MAX_RETRIES`, `FUNCTION_ROUTER_RETRY_SLEEP` are uppercase, consistent with constants.

**Potential AI Assumption Errors or Deviations:**
*   The naming seems largely consistent with PEP 8 and common Python practices.
*   The comment `# noqa: BLE001` on line 82 ([`except Exception as exc: # noqa: BLE001`](intelligence/function_router.py:82)) indicates a deliberate choice to catch a broad exception, likely because the specific exceptions from `importlib.import_module` can vary and the goal is simply to retry on any import-related failure. This is a common pattern when dealing with dynamic imports where exact exception types are less critical than the success/failure of the import itself.

The naming conventions are clear and do not immediately suggest AI assumption errors.