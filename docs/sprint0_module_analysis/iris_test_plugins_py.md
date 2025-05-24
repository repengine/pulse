# Module Analysis: `iris/test_plugins.py`

## 1. Module Intent/Purpose

The primary role of [`iris/test_plugins.py`](iris/test_plugins.py:1) is to serve as a testing script for various data intake plugins, specifically those located within the `iris_plugins_variable_ingestion` subdirectory. It aims to:
*   Initialize instances of these plugins.
*   Verify basic connectivity and data fetching capabilities by calling a `fetch_signals()` method on each plugin.
*   Log the outcome of these tests (success, failure, disabled, no signals).
*   Generate a summary report in JSON format ([`plugin_test_results.json`](plugin_test_results.json:191)) detailing the test results for each plugin, including a few sample signals if fetched successfully.

## 2. Operational Status/Completeness

*   The module appears to be operational for its defined scope of testing a hardcoded list of plugins.
*   It includes basic error handling for scenarios like disabled plugins or exceptions during data fetching.
*   A [`MockPluginManager`](iris/test_plugins.py:25) is implemented as a fallback if the actual [`IrisPluginManager`](iris/iris_plugins.py:0) (presumably from [`iris/iris_plugins.py`](iris/iris_plugins.py:0)) is not found, indicating some level of resilience or utility during development phases.
*   Plugins are dynamically imported, which is suitable for its current design.
*   No explicit `TODO`, `FIXME`, or obvious placeholder comments indicating unfinished sections were found in the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Limited Test Depth:** The tests are primarily connectivity and basic fetch checks. They do not validate the schema, content, or correctness of the data returned by `fetch_signals()`.
*   **Lack of Granular Assertions:** While the script logs errors, the main execution flow in `main()` doesn't use fine-grained assertions for each plugin test that would integrate cleanly with a test runner like `pytest` for individual pass/fail status per plugin. The `test_plugin` function contains an `assert False` for disabled plugins, which could halt a sequential test run.
*   **Configuration Management for Plugins:** The script doesn't appear to manage or vary configurations (e.g., API keys, test parameters) for the plugins. These are likely handled within the individual plugins themselves, limiting the test script's ability to test different configurations or states.
*   **Static Plugin List:** The set of plugins to be tested is hardcoded. A more extensible approach might involve dynamically discovering plugin modules within the target directory.
*   **Mixed Testing Styles:** The script includes a `pytest` fixture ([`plugin_instance`](iris/test_plugins.py:94)) but the main testing logic is within the [`main()`](iris/test_plugins.py:132) function, which executes procedurally. This suggests a potential for more idiomatic `pytest` usage that isn't fully realized in the primary execution path.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`iris.iris_plugins.IrisPluginManager`](iris/iris_plugins.py:0) (conditional import, with a mock fallback if not found).
*   Dynamically imports plugin modules from the [`iris/iris_plugins_variable_ingestion/`](iris/iris_plugins_variable_ingestion/) directory:
    *   [`alpha_vantage_plugin`](iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:0)
    *   [`open_meteo_plugin`](iris/iris_plugins_variable_ingestion/open_meteo_plugin.py:0)
    *   [`worldbank_plugin`](iris/iris_plugins_variable_ingestion/worldbank_plugin.py:0)
    *   [`reddit_plugin`](iris/iris_plugins_variable_ingestion/reddit_plugin.py:0)
    *   [`who_gho_plugin`](iris/iris_plugins_variable_ingestion/who_gho_plugin.py:0)
    *   [`newsapi_plugin`](iris/iris_plugins_variable_ingestion/newsapi_plugin.py:0)
    *   [`github_plugin`](iris/iris_plugins_variable_ingestion/github_plugin.py:0)
    *   [`google_trends_plugin`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:0)

### External Library Dependencies:
*   `logging` (Python standard library)
*   `sys` (Python standard library)
*   `os` (Python standard library)
*   `json` (Python standard library)
*   `typing` (Python standard library: `Dict`, `Any`)
*   `pytest` (for a fixture, though main execution is script-based)
*   `importlib.util` (Python standard library, for dynamic module loading)

### Interaction with Other Modules via Shared Data:
*   The script primarily interacts by instantiating plugin classes and calling their methods. Data sharing is implicit through these method calls.
*   Individual plugins are responsible for their own external data interactions (APIs, etc.).

### Input/Output Files:
*   **Output:** [`plugin_test_results.json`](plugin_test_results.json:191) - Stores a summary of plugin test results.
*   **Input:** None directly managed by this script. Individual plugins might read their own configuration files or environment variables for API keys, but this is not orchestrated by `test_plugins.py`.

## 5. Function and Class Example Usages

*   **`MockPluginManager()` ([`iris/test_plugins.py:25`](iris/test_plugins.py:25))**:
    *   A fallback class if [`IrisPluginManager`](iris/iris_plugins.py:0) cannot be imported.
    *   It's assigned to the `IrisPluginManager` name and potentially injected into plugin modules.
*   **`import_plugin(plugin_name: str)` ([`iris/test_plugins.py:46`](iris/test_plugins.py:46))**:
    *   Helper function to dynamically load a plugin module by name from the `iris_plugins_variable_ingestion` directory.
    *   Example: `alpha_vantage_module = import_plugin("alpha_vantage_plugin")`
*   **`plugin_instance()` (pytest fixture) ([`iris/test_plugins.py:94`](iris/test_plugins.py:94))**:
    *   Provides a generic `MockPlugin` object with a basic `fetch_signals()` method for testing purposes. Not directly used in the `main()` test flow.
*   **`test_plugin(plugin_instance, plugin_name: str)` ([`iris/test_plugins.py:108`](iris/test_plugins.py:108))**:
    *   Core test execution logic for a single plugin. It takes a plugin object, calls its `fetch_signals()` method, and returns a dictionary with the status and fetched signals.
    *   Example from `main()`: `results["Alpha Vantage"] = test_plugin(alpha_plugin, "Alpha Vantage")`
*   **`main()` ([`iris/test_plugins.py:132`](iris/test_plugins.py:132))**:
    *   The main entry point when the script is run. It instantiates each hardcoded plugin, calls `test_plugin` for it, aggregates results, logs a summary, and writes detailed results to `plugin_test_results.json`.

## 6. Hardcoding Issues

*   **Plugin Names & Modules:** The list of plugin module names (e.g., `"alpha_vantage_plugin"`) and their corresponding display names (e.g., `"Alpha Vantage"`) are hardcoded ([`iris/test_plugins.py:63-80`](iris/test_plugins.py:63), [`iris/test_plugins.py:136-166`](iris/test_plugins.py:136)).
*   **Plugin Directory Path:** The subdirectory `"iris_plugins_variable_ingestion"` is hardcoded in path constructions ([`iris/test_plugins.py:41`](iris/test_plugins.py:41), [`iris/test_plugins.py:48`](iris/test_plugins.py:48)).
*   **Output Filename:** The name of the results file, `"plugin_test_results.json"`, is hardcoded ([`iris/test_plugins.py:191`](iris/test_plugins.py:191)).
*   **Logging Configuration:** The logging format string is hardcoded ([`iris/test_plugins.py:19`](iris/test_plugins.py:19)).
*   **Mock Data/Behavior:**
    *   [`MockPluginManager`](iris/test_plugins.py:25) attributes (e.g., `plugin_name`, `enabled`, `concurrency`).
    *   [`MockPlugin`](iris/test_plugins.py:97) (in the `plugin_instance` fixture) returns hardcoded signal data.
*   **Signal Truncation Limit:** The number of example signals saved per plugin in the JSON output (3) is hardcoded ([`iris/test_plugins.py:196`](iris/test_plugins.py:196)).

## 7. Coupling Points

*   **`IrisPluginManager` Interface:** The script (and by extension, the plugins it tests) expects an `IrisPluginManager` class or a mock with a compatible interface.
*   **Individual Plugin Classes:** Tightly coupled to the specific class names and expected `fetch_signals()` method signature of each plugin it imports from `iris_plugins_variable_ingestion`.
*   **File System Structure:** Relies on the `iris_plugins_variable_ingestion` directory being present at a specific relative path.
*   **`fetch_signals()` Method:** All tested plugins must implement this method, and it's expected to return a list of dictionaries.
*   **Signal Dictionary Structure:** For logging example signals, the script expects each signal dictionary to have `"name"`, `"value"`, and `"source"` keys ([`iris/test_plugins.py:181`](iris/test_plugins.py:181)).

## 8. Existing Tests

*   This module is, in itself, a test execution script. It does not have separate unit tests for its own logic (e.g., for `import_plugin` or the result processing in `main`).
*   The tests it performs are high-level integration tests, checking if plugins can be instantiated and can fetch data without raising exceptions.
*   **Coverage:** It aims to cover a predefined list of plugins. The depth of testing for each plugin is shallow (one `fetch_signals()` call).
*   **Nature of Tests:** Primarily functional/connectivity tests.
*   **Gaps/Problematic Areas:**
    *   Does not validate the content, schema, or accuracy of the data returned by plugins.
    *   Error handling within `test_plugin` logs issues but might not integrate well with `pytest`'s standard reporting for individual test failures if `main()` is the primary execution path.
    *   Not structured as a typical `pytest` discoverable test file (e.g., using top-level `test_` functions or `Test` classes). The `main()` function acts as the test runner.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Sets up basic logging.
    *   Modifies `sys.path` to enable imports from the parent directory and the `iris_plugins_variable_ingestion` subdirectory.
    *   Defines `MockPluginManager` as a fallback.
2.  **Dynamic Plugin Loading:**
    *   Attempts to import the actual `IrisPluginManager`. If it fails, uses the mock.
    *   The `import_plugin()` function dynamically loads each specified plugin module from `iris_plugins_variable_ingestion/`.
    *   Plugin classes are retrieved from these modules using `getattr()`.
    *   If the mock manager is active, it's injected into the loaded plugin modules.
3.  **Main Test Orchestration (`main()` function):**
    *   Iterates through a hardcoded list of plugins.
    *   For each plugin:
        *   Instantiates the plugin's main class.
        *   Calls `test_plugin()` with the instance and a display name.
        *   Stores the result.
4.  **Individual Plugin Test (`test_plugin()` function):**
    *   Logs the test initiation.
    *   Checks if the plugin is enabled; if not, logs a warning and (problematically for batch runs) asserts `False`.
    *   Calls the plugin's `fetch_signals()` method.
    *   Logs success (with signal count) or a warning if no signals are returned.
    *   Catches and logs any exceptions during the process.
    *   Returns a dictionary containing the test status, any fetched signals (or an error message).
5.  **Results Reporting:**
    *   The `main()` function processes the collected results.
    *   Logs a summary of success/failure/disabled status for each plugin.
    *   If signals were fetched, logs one example signal.
    *   Saves a more detailed (though signals are truncated to 3 per plugin) report to `plugin_test_results.json`.
6.  **Script Execution:**
    *   The `if __name__ == "__main__":` block ensures `main()` is called when the script is run directly.

## 10. Naming Conventions

*   **Variables & Functions:** Generally follow `snake_case` (e.g., `plugin_name`, `file_path`, `import_plugin`, `test_plugin`), adhering to PEP 8.
*   **Classes:** Use `PascalCase` (e.g., `MockPluginManager`, `AlphaVantagePlugin`), adhering to PEP 8.
*   **Modules:** Dynamically imported plugin modules are expected to be `snake_case_plugin.py` (e.g., `alpha_vantage_plugin.py`).
*   **Constants:** `logger` is lowercase.
*   **Strings for Display:** Plugin names used as keys in dictionaries and for logging are human-readable with spaces (e.g., "Alpha Vantage"), which is acceptable for these purposes.
*   The naming is largely consistent and follows Python community standards. No significant deviations or potential AI assumption errors in naming were noted.