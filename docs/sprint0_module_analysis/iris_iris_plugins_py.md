# Module Analysis: `iris/iris_plugins.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/iris_plugins.py`](iris/iris_plugins.py:1) module is to manage dynamic ingestion plugins for the Iris system. It provides the `IrisPluginManager` class, which is responsible for registering, running, listing, and autoloading these plugins. Each plugin is expected to be a callable that returns a list of signal dictionaries, which are then aggregated by the manager.

## 2. Operational Status/Completeness

The module appears to be largely functional and complete for its core responsibilities. It implements:
*   Plugin registration ([`register_plugin()`](iris/iris_plugins.py:24)).
*   Execution of all registered plugins with aggregation of results ([`run_plugins()`](iris/iris_plugins.py:34)).
*   Listing of registered plugin names ([`list_plugins()`](iris/iris_plugins.py:51)).
*   An autoloading mechanism for discovering and registering plugins from specific locations ([`autoload()`](iris/iris_plugins.py:60)).
*   Basic error logging for individual plugin failures during execution.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Plugin Subclass Check:** In the [`autoload()`](iris/iris_plugins.py:60) method, there's a potential logical error in lines 87-89: `if inspect.isclass(cls) and issubclass(cls, IrisPluginManager) and cls is not IrisPluginManager:`. It checks if a class `cls` from a plugin module is a subclass of `IrisPluginManager` itself. It's more likely that plugin classes should inherit from a dedicated base plugin class (e.g., `IrisIngestionPlugin`, as hinted in comments like line 65, though not defined in this file). This check might prevent correct loading of class-based plugins if they don't (and shouldn't) inherit from `IrisPluginManager`.
*   **Autoload Strategy:** The [`autoload()`](iris/iris_plugins.py:60) method directly imports [`finance_plugins`](iris/iris_plugins.py:68) and [`vi_plugin`](iris/iris_plugins.py:69) before scanning the `iris_plugins_variable_ingestion` directory. This could potentially be streamlined into a more generic discovery mechanism.
*   **Base Plugin Class:** The module relies on an implicit contract for plugins (callable, returns `List[Dict]`, or class with `fetch_signals` and `enabled` attribute). Defining an abstract base class for plugins could make this contract explicit and provide a clearer structure for plugin development.

## 4. Connections & Dependencies

*   **Direct Project Imports:**
    *   [`from .iris_plugins_finance import finance_plugins`](iris/iris_plugins.py:68)
    *   [`from .iris_plugins_variable_ingestion import vi_plugin`](iris/iris_plugins.py:69)
    *   Dynamically imports modules from the `iris_plugins_variable_ingestion/` subdirectory during [`autoload()`](iris/iris_plugins.py:74-79).
*   **External Library Dependencies:**
    *   `logging`
    *   `typing` (Callable, List, Dict)
    *   `os`
    *   `importlib`
    *   `inspect`
*   **Interaction via Shared Data:**
    *   The manager calls registered plugin functions/methods. These plugins are expected to return data in a specific format (`List[Dict]`, representing signals).
*   **Input/Output Files:**
    *   The module itself does not directly read from or write to files for its primary operation.
    *   The associated test script, [`iris/test_plugins.py`](iris/test_plugins.py:1), writes test results to `plugin_test_results.json` ([`iris/test_plugins.py:191`](iris/test_plugins.py:191)).

## 5. Function and Class Example Usages

### `IrisPluginManager` Class

```python
from iris.iris_plugins import IrisPluginManager

# Initialize the plugin manager
manager = IrisPluginManager()

# Autoload default plugins (e.g., finance, variable ingestion)
manager.autoload()

# Example of a custom plugin function
def my_custom_data_plugin():
    # This function would fetch data from a source
    return [
        {"name": "custom_signal_1", "value": 123.45, "source": "my_source"},
        {"name": "custom_signal_2", "value": "active", "source": "my_source"}
    ]

# Register the custom plugin
manager.register_plugin(my_custom_data_plugin)

# List all registered plugins
print("Registered plugins:", manager.list_plugins())

# Run all plugins and collect aggregated signals
all_signals = manager.run_plugins()

# Process the collected signals
for signal in all_signals:
    print(f"Signal: {signal['name']}, Value: {signal['value']}, Source: {signal['source']}")
```

## 6. Hardcoding Issues

*   **Plugin Names for Autoload:** The specific plugin names `finance_plugins` and `vi_plugin` are hardcoded for initial autoloading in [`autoload()`](iris/iris_plugins.py:68-70).
*   **Plugin Directory Name:** The subdirectory name `iris_plugins_variable_ingestion` is hardcoded in [`autoload()`](iris/iris_plugins.py:74) for dynamic plugin discovery.
*   **Plugin Function Suffix:** The suffix `_plugin` is used as a convention to identify plugin functions during directory scanning in [`autoload()`](iris/iris_plugins.py:83).
*   **'enabled' Attribute:** The attribute name `enabled` is hardcoded when checking class-based plugins in [`autoload()`](iris/iris_plugins.py:89).
*   **Test Script Hardcoding:** The test script [`iris/test_plugins.py`](iris/test_plugins.py:1) hardcodes:
    *   The output filename `plugin_test_results.json` ([`iris/test_plugins.py:191`](iris/test_plugins.py:191)).
    *   Names of plugin modules (e.g., `"alpha_vantage_plugin"`) for dynamic import and testing ([`iris/test_plugins.py:63-70`](iris/test_plugins.py:63-70)).

## 7. Coupling Points

*   **Plugin Structure:** The manager is tightly coupled to the expected structure of plugin modules within the `iris_plugins_variable_ingestion/` directory. It assumes they are `.py` files and may contain functions ending with `_plugin` or specific classes.
*   **Plugin Contract:** Relies on an implicit contract for plugin callables (no arguments, return `List[Dict]`) and class-based plugins (must have an `enabled` attribute and a `fetch_signals` method).
*   **Specific Module Knowledge:** The [`autoload()`](iris/iris_plugins.py:60) method has explicit knowledge of `.iris_plugins_finance` and `.iris_plugins_variable_ingestion` modules.

## 8. Existing Tests

*   A test script exists at [`iris/test_plugins.py`](iris/test_plugins.py:1).
*   **Nature of Tests:** This script primarily functions as an integration test for various individual data ingestion plugins (e.g., Alpha Vantage, Open-Meteo, WorldBank) rather than a focused unit test suite for the `IrisPluginManager` class itself. It dynamically loads and attempts to run `fetch_signals()` for these plugins.
*   **`IrisPluginManager` Testing:**
    *   The script includes a [`MockPluginManager`](iris/test_plugins.py:25) and a [`MockPlugin`](iris/test_plugins.py:97) fixture. It attempts to import the real `IrisPluginManager` but uses the mock as a fallback ([`iris/test_plugins.py:34-38`](iris/test_plugins.py:34-38)).
    *   Direct unit tests for methods like [`IrisPluginManager.register_plugin()`](iris/iris_plugins.py:24), [`IrisPluginManager.run_plugins()`](iris/iris_plugins.py:34) with various scenarios (e.g., multiple plugins, failing plugins), [`IrisPluginManager.list_plugins()`](iris/iris_plugins.py:51), and the detailed logic within [`IrisPluginManager.autoload()`](iris/iris_plugins.py:60) (especially the dynamic loading and class checking) are not apparent in [`iris/test_plugins.py`](iris/test_plugins.py:1).
*   **Coverage:** Coverage for the `IrisPluginManager` class itself by [`iris/test_plugins.py`](iris/test_plugins.py:1) appears to be indirect and potentially low. The tests focus more on the successful execution of individual plugins that the manager would handle.

## 9. Module Architecture and Flow

*   **Central Class:** The `IrisPluginManager` class is the core component.
*   **Plugin Storage:** It maintains an internal list (`self.plugins`) of registered plugin callables.
*   **Registration:** The [`register_plugin()`](iris/iris_plugins.py:24) method appends new plugin callables to this list.
*   **Execution:** The [`run_plugins()`](iris/iris_plugins.py:34) method iterates through the `self.plugins` list, executes each callable, collects the returned signals (lists of dictionaries), and extends a main list with these signals. It includes a `try-except` block to catch and log errors from individual plugins, allowing other plugins to continue executing.
*   **Listing:** The [`list_plugins()`](iris/iris_plugins.py:51) method provides the names of the registered plugin functions.
*   **Autoloading:** The [`autoload()`](iris/iris_plugins.py:60) method is responsible for discovering and registering plugins automatically.
    1.  It performs direct imports for `finance_plugins` from `.iris_plugins_finance` and `vi_plugin` from `.iris_plugins_variable_ingestion`.
    2.  It then scans the `iris_plugins_variable_ingestion/` subdirectory.
    3.  For each `.py` file (not starting with `_`):
        *   It dynamically imports the module.
        *   It iterates through the module's attributes, registering any callable attribute whose name ends with `_plugin`.
        *   It iterates through the module's classes, attempting to register an instance's `fetch_signals` method if the class is (incorrectly) identified as a subclass of `IrisPluginManager` and has an `enabled` attribute set to `True`.
*   **Typical Control Flow:**
    1.  Instantiate `IrisPluginManager`.
    2.  Call [`autoload()`](iris/iris_plugins.py:60) to register default plugins, and/or call [`register_plugin()`](iris/iris_plugins.py:24) to add custom plugins.
    3.  Call [`run_plugins()`](iris/iris_plugins.py:34) to execute all registered plugins and retrieve the aggregated list of signals.
    4.  Optionally, call [`list_plugins()`](iris/iris_plugins.py:51) to see which plugins are active.

## 10. Naming Conventions

*   **Class Names:** `IrisPluginManager` follows CapWords (PEP 8).
*   **Method Names:** `register_plugin`, `run_plugins`, `list_plugins`, `autoload` use snake_case (PEP 8).
*   **Variable Names:** `plugin_fn`, `aggregated_signals`, `var_dir`, `mod_name` generally follow snake_case.
*   **Clarity:** Names are generally clear and indicative of their purpose (e.g., `plugin_fn` for a plugin function).
*   **Potential Confusion:** The comment in [`autoload()`](iris/iris_plugins.py:65) refers to "enabled `IrisIngestionPlugin` subclasses", but the code at line 87 checks `issubclass(cls, IrisPluginManager)`. This discrepancy between comment and code could lead to confusion or indicate a bug.
*   **Standard Practices:** Use of `logger = logging.getLogger(__name__)` is standard.