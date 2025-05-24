# Module Analysis: `symbolic_system/gravity/cli.py`

## 1. Module Intent/Purpose

The primary role of [`symbolic_system/gravity/cli.py`](../../symbolic_system/gravity/cli.py:1) is to provide a command-line interface (CLI) for interacting with the Symbolic Gravity system. This includes enabling, disabling, and configuring the system's parameters, such as gravity strength, learning rate, and regularization, via command-line arguments. It also provides a function to print the current status of the Symbolic Gravity system.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined purpose.
- It defines functions to add gravity-specific arguments to an `argparse.ArgumentParser` ([`add_gravity_arguments()`](../../symbolic_system/gravity/cli.py:23)).
- It handles the parsing of these arguments ([`handle_gravity_arguments()`](../../symbolic_system/gravity/cli.py:77)).
- It initializes the gravity system based on these arguments ([`initialize_from_args()`](../../symbolic_system/gravity/cli.py:119)).
- It includes a utility to display the system's status ([`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160)).
There are no obvious placeholders (e.g., `pass`, `NotImplementedError`) or "TODO" comments within the code.

## 3. Implementation Gaps / Unfinished Next Steps

- **No direct command-line execution:** The module provides functions to integrate with a larger CLI setup (by adding arguments to an existing parser) but doesn't seem to be set up to be run as a standalone script (e.g., via `if __name__ == "__main__":`). This is likely by design, assuming it's meant to be part of a larger application's CLI.
- **Status Output Format:** The [`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160) function directly prints to `stdout`. For more flexible integration, this could be refactored to return a structured data object (e.g., a dictionary or a custom status object) that could then be formatted for display by the calling CLI or UI.
- **Configuration Persistence:** The CLI arguments configure the system for the current session. There's no indication of loading from or saving to a persistent configuration file for gravity settings, though this might be handled by the broader application.

## 4. Connections & Dependencies

### Direct Imports from Other Project Modules:
- [`symbolic_system.gravity.gravity_config.ResidualGravityConfig`](../../symbolic_system/gravity/gravity_config.py:14)
- From [`symbolic_system.gravity.integration`](../../symbolic_system/gravity/integration.py:15):
    - [`initialize_gravity_system()`](../../symbolic_system/gravity/integration.py:16)
    - [`enable_gravity_system()`](../../symbolic_system/gravity/integration.py:16)
    - [`disable_gravity_system()`](../../symbolic_system/gravity/integration.py:16)
    - [`get_gravity_fabric()`](../../symbolic_system/gravity/integration.py:17)
    - [`get_pillar_system()`](../../symbolic_system/gravity/integration.py:17)

### External Library Dependencies:
- `argparse` (standard library)
- `logging` (standard library)
- `typing` (standard library: `Dict`, `Any`, `Optional`)

### Interaction with Other Modules via Shared Data:
- The module interacts with the core gravity system by calling initialization, enabling/disabling functions, and retrieving status information from the "gravity fabric" and "pillar system" via functions imported from [`symbolic_system.gravity.integration`](../../symbolic_system/gravity/integration.py:15). The exact nature of this shared data (internal state of the gravity system) is managed within those imported modules.

### Input/Output Files:
- **Input:** Command-line arguments.
- **Output:**
    - Log messages via the `logging` module.
    - Status information printed to `stdout` by [`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160).

## 5. Function and Class Example Usages

### [`add_gravity_arguments(parser: argparse.ArgumentParser)`](../../symbolic_system/gravity/cli.py:23)
Intended to be used to extend an existing `ArgumentParser` object with Symbolic Gravity specific options.
```python
import argparse

# Assuming 'main_parser' is the main ArgumentParser for an application
main_parser = argparse.ArgumentParser(description="Main Application CLI")
# ... add other application arguments ...

# Add gravity system arguments
from symbolic_system.gravity.cli import add_gravity_arguments
add_gravity_arguments(main_parser)

# args = main_parser.parse_args()
# ... then use initialize_from_args(args)
```

### [`handle_gravity_arguments(args: argparse.Namespace)`](../../symbolic_system/gravity/cli.py:77)
Parses the `args` namespace (populated by `ArgumentParser.parse_args()`) and extracts gravity-related options into a dictionary. This dictionary is then used to create a [`ResidualGravityConfig`](../../symbolic_system/gravity/gravity_config.py:14) object.

### [`initialize_from_args(args: argparse.Namespace)`](../../symbolic_system/gravity/cli.py:119)
This is the main entry point for setting up the gravity system from CLI arguments. It calls [`handle_gravity_arguments()`](../../symbolic_system/gravity/cli.py:77), creates a config, initializes the system, and enables/disables it.
```python
# import argparse # (if not already imported)
# from symbolic_system.gravity.cli import initialize_from_args, add_gravity_arguments

# parser = argparse.ArgumentParser()
# add_gravity_arguments(parser)
# parsed_args = parser.parse_args() # e.g., ['--enable-gravity', '--gravity-lambda', '0.5']

# if initialize_from_args(parsed_args):
#     print("Symbolic Gravity system initialized via CLI arguments.")
# else:
#     print("No Symbolic Gravity CLI arguments provided or system not initialized.")
```

### [`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160)
Prints a formatted status report of the Symbolic Gravity system to the console.
```python
# from symbolic_system.gravity.cli import print_gravity_status
# from symbolic_system.gravity.integration import initialize_gravity_system, enable_gravity_system
# from symbolic_system.gravity.gravity_config import ResidualGravityConfig

# Initialize and enable first (if not done via CLI args)
# initialize_gravity_system(ResidualGravityConfig()) # Using default config
# enable_gravity_system()

# print_gravity_status()
```
*(Note: The example for `print_gravity_status` assumes the system is already initialized and enabled, as the function itself relies on `get_gravity_fabric` and `get_pillar_system` which expect an initialized system.)*

## 6. Hardcoding Issues

- **Argument Names & Destinations:** The argument names (e.g., `'--enable-gravity'`, `'--gravity-lambda'`) and their `dest` attributes (e.g., `'enable_gravity'`, `'gravity_lambda'`) are hardcoded strings. This is standard practice for `argparse` but means changes require code modification.
- **Status Print Format:** The text and formatting in [`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160) (e.g., `"--- Symbolic Gravity System Status ---"`, f-string formats like `:.4f`) are hardcoded.
- **Default `enabled` state in `initialize_from_args`:** `enabled = gravity_options.pop('enabled', True)` ([`cli.py:141`](../../symbolic_system/gravity/cli.py:141)) defaults to `True` if neither `--enable-gravity` nor `--disable-gravity` is specified but other gravity options *are* given. This behavior might be intentional but is a hardcoded default.

No secrets, sensitive paths, or overly complex magic numbers/strings were identified beyond typical CLI argument definitions and print formatting.

## 7. Coupling Points

- **High coupling with `symbolic_system.gravity.integration`:** The module is tightly coupled with functions from [`integration.py`](../../symbolic_system/gravity/integration.py:15) for initializing, enabling/disabling, and fetching the core components of the gravity system. Changes to the API of these integration functions would directly impact this CLI module.
- **High coupling with `symbolic_system.gravity.gravity_config.ResidualGravityConfig`:** The CLI options directly map to the fields of the [`ResidualGravityConfig`](../../symbolic_system/gravity/gravity_config.py:14) dataclass. Changes to this config class (e.g., renaming fields, changing types) would require corresponding changes in [`handle_gravity_arguments()`](../../symbolic_system/gravity/cli.py:77) and [`add_gravity_arguments()`](../../symbolic_system/gravity/cli.py:23).
- **Dependency on `argparse`:** The module's core functionality relies on the `argparse` library. While standard, it's a structural dependency.
- **Interaction with `GravityFabric` and `PillarSystem` (indirect):** Through `get_gravity_fabric()` and `get_pillar_system()`, the [`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160) function depends on the interfaces of `GravityFabric` (specifically its `generate_diagnostic_report()` method) and `PillarSystem` (its `as_dict()` method).

## 8. Existing Tests

- As per the file listing for `tests/symbolic_system/gravity/`, there is no specific test file named `test_cli.py` or similar that would directly target the functionalities of [`symbolic_system/gravity/cli.py`](../../symbolic_system/gravity/cli.py:1).
- The existing test file [`test_residual_gravity_engine.py`](../../tests/symbolic_system/gravity/test_residual_gravity_engine.py) likely focuses on the core engine logic rather than the CLI integration aspects like argument parsing or status printing.
- **Gaps:** There are no apparent tests for:
    - Correct parsing of various combinations of CLI arguments.
    - Correct initialization and enabling/disabling of the system based on arguments.
    - The output format and content of [`print_gravity_status()`](../../symbolic_system/gravity/cli.py:160).

## 9. Module Architecture and Flow

1.  **Argument Definition (`add_gravity_arguments`)**:
    *   Takes an `argparse.ArgumentParser` instance.
    *   Adds a dedicated argument group "Symbolic Gravity Options".
    *   Defines arguments for enabling/disabling gravity, setting lambda, eta, regularization, and enabling debug logging.

2.  **Argument Handling (`handle_gravity_arguments`)**:
    *   Takes a parsed `argparse.Namespace` object.
    *   Checks for the presence and values of the gravity-specific arguments.
    *   Populates a dictionary (`gravity_options`) with keys corresponding to `ResidualGravityConfig` fields (e.g., `lambda_`, `eta`).
    *   Returns this dictionary or `None` if no gravity options were specified.

3.  **Initialization from Arguments (`initialize_from_args`)**:
    *   Calls [`handle_gravity_arguments()`](../../symbolic_system/gravity/cli.py:77) to get processed options.
    *   If options are present:
        *   Extracts the `enabled` status (defaulting to `True` if other gravity args are present but enable/disable is not explicitly set).
        *   Creates a [`ResidualGravityConfig`](../../symbolic_system/gravity/gravity_config.py:14) instance using the remaining options.
        *   Calls [`initialize_gravity_system()`](../../symbolic_system/gravity/integration.py:16) with this config.
        *   Calls [`enable_gravity_system()`](../../symbolic_system/gravity/integration.py:16) or [`disable_gravity_system()`](../../symbolic_system/gravity/integration.py:16) based on the `enabled` flag.
        *   Logs the action.
    *   Returns `True` if initialized, `False` otherwise.

4.  **Status Printing (`print_gravity_status`)**:
    *   Retrieves the `GravityFabric` and `PillarSystem` instances using `get_gravity_fabric()` and `get_pillar_system()`.
    *   Calls `fabric.generate_diagnostic_report()` to get status data.
    *   Prints formatted statistics about the engine, pillars, symbolic tension, and variable improvements.

The overall flow is designed for integration into a larger application's main CLI script, where `add_gravity_arguments` would be called during parser setup, and `initialize_from_args` would be called after parsing arguments. `print_gravity_status` could be triggered by a specific command or option.

## 10. Naming Conventions

- **Functions:** Use `snake_case` (e.g., [`add_gravity_arguments()`](../../symbolic_system/gravity/cli.py:23), [`handle_gravity_arguments()`](../../symbolic_system/gravity/cli.py:77)), which is consistent with PEP 8.
- **Variables:** Generally use `snake_case` (e.g., `gravity_group`, `gravity_options`).
- **Argument Parser `dest` attributes:** Use `snake_case` (e.g., `enable_gravity`, `gravity_lambda`).
- **Class Imports:** `ResidualGravityConfig` uses `PascalCase`, which is standard for class names.
- **Logger Name:** `logger = logging.getLogger(__name__)` is standard.
- **Constants/Globals:** No module-level constants are defined, other than the logger.
- **Clarity:** Names are generally descriptive and clearly indicate their purpose (e.g., `enable_gravity`, `gravity_lambda`).
- **Potential AI Assumption Errors:** The author is listed as "Pulse v3.5", suggesting AI generation. The naming conventions are standard and do not show obvious AI errors. The use of `lambda_` for the `gravity_lambda` option in [`handle_gravity_arguments()`](../../symbolic_system/gravity/cli.py:101) is a common Python idiom to avoid clashing with the `lambda` keyword, which is good practice.

The naming conventions appear consistent and follow Python community standards (PEP 8).