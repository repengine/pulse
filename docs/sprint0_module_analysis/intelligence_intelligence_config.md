# SPARC Analysis Report: intelligence/intelligence_config.py

**Module Path:** [`intelligence/intelligence_config.py`](intelligence/intelligence_config.py:1)

## 1. Module Intent/Purpose (Specification)

This module serves as a centralized configuration hub for the Pulse Intelligence system. Its primary role is to define and provide constants and settings that are utilized by various components within the `intelligence` package. These components include, but are not limited to, the Function Router, Observer, Upgrade Sandbox Manager, and Simulation Executor. The module aims to consolidate configuration parameters, making them easier to manage and modify.

## 2. Operational Status/Completeness

The module appears to be largely operational for its defined scope, providing a set of core configurations. However, it contains a placeholder comment:
```python
# Add other intelligence-specific configurations here
```
([`intelligence/intelligence_config.py:49`](intelligence/intelligence_config.py:49))
This indicates that the module is designed to be extensible and may not yet contain all planned or future configurations.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility:** The comment on line 49 ([`intelligence/intelligence_config.py:49`](intelligence/intelligence_config.py:49)) explicitly points to future extensions.
*   **Error Handling for `GEMINI_API_KEY`:** While [`GEMINI_API_KEY`](intelligence/intelligence_config.py:39) is loaded from an environment variable, there's no explicit fallback or error handling within this configuration file if the key is not set and `LLM_PROVIDER` is 'gemini'. Consuming modules would need to handle this.
*   **Configuration Validation:** There's no validation logic within this module itself (e.g., checking if path strings are valid, or if retry counts are positive). This responsibility would lie with the consuming modules or a dedicated configuration loading/validation mechanism.

## 4. Connections & Dependencies

*   **Direct Imports:**
    *   [`os`](https://docs.python.org/3/library/os.html): Used to access environment variables for [`GEMINI_API_KEY`](intelligence/intelligence_config.py:39) and [`LLM_PROVIDER`](intelligence/intelligence_config.py:47).
*   **Interactions (Shared Data, Files, DBs, Queues):**
    *   This module primarily *defines* paths and settings that other modules will use to interact with files or external services. It does not directly interact with them itself.
    *   It provides configuration that implies interaction with Large Language Models (GPT and Gemini).
*   **Input/Output Files (Defined Paths):**
    *   [`OBSERVER_MEMORY_DIR`](intelligence/intelligence_config.py:18): `"data/intelligence_observer_memory"`
    *   [`UPGRADE_SANDBOX_DIR`](intelligence/intelligence_config.py:21): `"data/upgrade_sandbox"`
    *   [`WORLDSTATE_DEFAULT_SOURCE`](intelligence/intelligence_config.py:24): `"data/baselines/default.csv"`

## 5. Function and Class Example Usages

This module consists solely of configuration constants (module-level variables). It does not define any functions or classes.

**Example of how constants would be used by other modules:**
```python
# In another module, e.g., intelligence/function_router.py
# from intelligence import intelligence_config
#
# class FunctionRouter:
#     def __init__(self):
#         self.max_retries = intelligence_config.FUNCTION_ROUTER_MAX_RETRIES
#         self.retry_sleep = intelligence_config.FUNCTION_ROUTER_RETRY_SLEEP
#
#     def some_operation(self):
#         for attempt in range(self.max_retries):
#             try:
#                 # ... perform operation ...
#                 return result
#             except SomeTransientError:
#                 if attempt < self.max_retries - 1:
#                     time.sleep(self.retry_sleep)
#                 else:
#                     raise
```

## 6. Hardcoding Issues (SPARC Critical)

The module contains several hardcoded values, which is expected for a configuration file. However, their nature (paths, default models, retry counts) means changes to these require direct code modification.

*   **Function Router:**
    *   [`FUNCTION_ROUTER_MAX_RETRIES: int = 3`](intelligence/intelligence_config.py:14)
    *   [`FUNCTION_ROUTER_RETRY_SLEEP: float = 1.5`](intelligence/intelligence_config.py:15)
*   **Directory Paths:**
    *   [`OBSERVER_MEMORY_DIR: str = "data/intelligence_observer_memory"`](intelligence/intelligence_config.py:18)
    *   [`UPGRADE_SANDBOX_DIR: str = "data/upgrade_sandbox"`](intelligence/intelligence_config.py:21)
*   **WorldState Loader:**
    *   [`WORLDSTATE_DEFAULT_SOURCE: str = "data/baselines/default.csv"`](intelligence/intelligence_config.py:24)
    *   [`WORLDSTATE_INJECT_LIVE_DEFAULT: bool = True`](intelligence/intelligence_config.py:25)
*   **GPT Configuration:**
    *   [`GPT_FALLBACK_MODEL: str = "gpt-4"`](intelligence/intelligence_config.py:31)
    *   [`MAX_GPT_RETRIES: int = 3`](intelligence/intelligence_config.py:33)
    *   [`GPT_RETRY_SLEEP: int = 5`](intelligence/intelligence_config.py:35)
*   **Gemini Configuration:**
    *   [`GEMINI_DEFAULT_MODEL: str = "gemini-pro"`](intelligence/intelligence_config.py:41)
    *   [`MAX_GEMINI_RETRIES: int = 3`](intelligence/intelligence_config.py:43)
    *   [`GEMINI_RETRY_SLEEP: int = 5`](intelligence/intelligence_config.py:45)
*   **LLM Provider Default:**
    *   The default value for [`LLM_PROVIDER`](intelligence/intelligence_config.py:47) is `"gpt"` if the environment variable `LLM_PROVIDER` is not set.

**Security Note:**
*   [`GEMINI_API_KEY`](intelligence/intelligence_config.py:39) is correctly sourced from an environment variable (`os.getenv("GEMINI_API_KEY")`), which aligns with SPARC principles for handling secrets. No secrets are directly hardcoded.

## 7. Coupling Points

*   **High Coupling with Intelligence Sub-modules:** Any module within the `intelligence` package that relies on these configurations (e.g., Function Router, Observer, LLM clients) will be directly coupled to the names and types of these constants.
*   **File System Structure:** The hardcoded relative paths (e.g., `"data/intelligence_observer_memory"`) create coupling with the project's directory structure. If these directories are moved or renamed, these configurations must be updated.
*   **LLM Service Defaults:** Default model names like `"gpt-4"` and `"gemini-pro"` couple the system to specific versions/offerings of these LLMs.

## 8. Existing Tests (SPARC Refinement)

This module, being a collection of constants, would typically not have dedicated unit tests for itself. The correctness and impact of these configurations are usually verified through:
*   **Integration Tests:** Tests in consuming modules (e.g., testing the Function Router's retry mechanism using `FUNCTION_ROUTER_MAX_RETRIES`).
*   **System Tests:** End-to-end tests that ensure the intelligence components behave as expected with these configurations.

No specific test files or test cases for `intelligence_config.py` itself are apparent from analyzing this file alone. A broader search in the `tests/` directory would be needed to ascertain full test coverage of how these configurations are used.

## 9. Module Architecture and Flow (SPARC Architecture)

*   **Structure:** The module has a simple, flat structure. It defines a series of global constants.
*   **Grouping:** Configurations are loosely grouped by comments indicating the component they relate to (e.g., `# Function Router Configuration`, `# GPT Configuration`).
*   **Data Flow:** This module acts as a source of static data (configuration values). Other modules read from it. There is no complex control flow within this module.
*   **Environment Interaction:** It interacts with the environment at import time to fetch `GEMINI_API_KEY` and `LLM_PROVIDER` using [`os.getenv()`](https://docs.python.org/3/library/os.html#os.getenv).

## 10. Naming Conventions (SPARC Maintainability)

*   **Constants:** All configuration variables are named using `UPPER_SNAKE_CASE` (e.g., [`FUNCTION_ROUTER_MAX_RETRIES`](intelligence/intelligence_config.py:14), [`GPT_FALLBACK_MODEL`](intelligence/intelligence_config.py:31)). This adheres to Python's PEP 8 guidelines for constants.
*   **Clarity:** The names are generally descriptive and clearly indicate the purpose of each configuration parameter (e.g., [`OBSERVER_MEMORY_DIR`](intelligence/intelligence_config.py:18), [`MAX_GEMINI_RETRIES`](intelligence/intelligence_config.py:43)).
*   **Type Hinting:** Type hints are used for all constants, improving readability and maintainability (e.g., `FUNCTION_ROUTER_MAX_RETRIES: int`).

No obvious AI assumption errors in naming are present. The conventions are standard and human-readable.

## 11. SPARC Compliance Summary

*   **Specification:** The module's purpose is clearly defined through its docstring and the nature of its content (configuration settings).
*   **Modularity/Architecture:**
    *   It serves as a centralized point for intelligence-related configurations, promoting modularity by separating configuration from logic.
    *   Its architecture is simple and appropriate for a configuration file.
*   **Refinement Focus:**
    *   **Testability:** While not directly testable with unit tests, its design allows consuming modules to be tested with various configurations. The lack of internal validation logic simplifies its own structure but places the burden on consumers.
    *   **Security:** Good practice is followed for [`GEMINI_API_KEY`](intelligence/intelligence_config.py:39) by loading it from an environment variable. No sensitive secrets are directly hardcoded.
    *   **Maintainability:**
        *   Clear naming conventions (PEP 8 for constants) are used.
        *   Type hints enhance readability.
        *   The grouping of configurations by component aids understanding.
        *   The placeholder for future configurations ([`intelligence/intelligence_config.py:49`](intelligence/intelligence_config.py:49)) indicates an awareness of ongoing development.
*   **No Hardcoding (Critical Interpretation):**
    *   The module *intentionally* hardcodes default values, paths, and operational parameters, which is the function of a configuration file of this type.
    *   Crucially, sensitive information like API keys is *not* hardcoded but sourced from the environment.
    *   The hardcoded paths and default model names are items that might be externalized further in a more advanced configuration system (e.g., to YAML/JSON files, or a dedicated configuration service), but for this stage, their presence here is functional.

Overall, the module demonstrates reasonable adherence to SPARC principles for a configuration file. It centralizes settings, uses clear naming, and handles the one explicit secret (API key) appropriately. The main areas for future refinement would involve how these configurations are loaded and validated at a higher system level, rather than issues within this specific file's structure.