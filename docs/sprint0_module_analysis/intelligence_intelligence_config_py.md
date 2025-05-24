# Module Analysis: `intelligence/intelligence_config.py`

## 1. Module Intent/Purpose

The primary role of [`intelligence/intelligence_config.py`](intelligence/intelligence_config.py:1) is to serve as a centralized store for constants and settings used throughout the Pulse Intelligence system. It aims to provide a single source of truth for configurations related to various components within the `intelligence` module, such as the Function Router, Observer, Upgrade Sandbox Manager, WorldState Loader, and Simulation Executor, including LLM (GPT and Gemini) configurations.

## 2. Operational Status/Completeness

The module appears to be operational and reasonably complete for its intended purpose as a configuration file. It defines several key configuration parameters with default values.
- There are no explicit "TODO" comments.
- A comment at the end, `# Add other intelligence-specific configurations here` ([`intelligence/intelligence_config.py:49`](intelligence/intelligence_config.py:49)), suggests it's designed to be extensible.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility Placeholder:** The comment `# Add other intelligence-specific configurations here` ([`intelligence/intelligence_config.py:49`](intelligence/intelligence_config.py:49)) indicates that more configurations might be planned or could be added as the intelligence module evolves.
*   **Simulation Executor Configuration:** There's a section heading `# Simulation Executor Configuration` ([`intelligence/intelligence_config.py:27`](intelligence/intelligence_config.py:27)) but no actual configuration variables are defined under it, implying this section is incomplete or its configurations are pending.
*   **No Validation/Typing for Environment Variables:** While `GEMINI_API_KEY` ([`intelligence/intelligence_config.py:39`](intelligence/intelligence_config.py:39)) and `LLM_PROVIDER` ([`intelligence/intelligence_config.py:47`](intelligence/intelligence_config.py:47)) are loaded from environment variables, there's no explicit validation (e.g., for format, presence if mandatory, or type casting beyond Python's default behavior for `os.getenv`).
*   **Dynamic Configuration Loading:** The module currently uses static definitions. For more complex scenarios, a system to load configurations from files (e.g., YAML, JSON) or a more robust environment variable management system (like Pydantic settings) might be a logical next step, though not explicitly implied as "unfinished."

## 4. Connections & Dependencies

*   **Direct imports from other project modules:** None observed in this file. It's designed to be imported by other modules within the `intelligence` package.
*   **External library dependencies:**
    *   `os` ([`intelligence/intelligence_config.py:11`](intelligence/intelligence_config.py:11)): Used for accessing environment variables (e.g., `GEMINI_API_KEY`, `LLM_PROVIDER`).
*   **Interaction with other modules via shared data:**
    *   This module *provides* configuration data (constants) to other modules. It doesn't directly interact by reading shared data itself, but its defined paths like `OBSERVER_MEMORY_DIR` ([`intelligence/intelligence_config.py:18`](intelligence/intelligence_config.py:18)), `UPGRADE_SANDBOX_DIR` ([`intelligence/intelligence_config.py:21`](intelligence/intelligence_config.py:21)), and `WORLDSTATE_DEFAULT_SOURCE` ([`intelligence/intelligence_config.py:24`](intelligence/intelligence_config.py:24)) point to file system locations that other modules would use.
*   **Input/output files (logs, data files, metadata):**
    *   Defines paths for data storage:
        *   `OBSERVER_MEMORY_DIR: str = "data/intelligence_observer_memory"` ([`intelligence/intelligence_config.py:18`](intelligence/intelligence_config.py:18))
        *   `UPGRADE_SANDBOX_DIR: str = "data/upgrade_sandbox"` ([`intelligence/intelligence_config.py:21`](intelligence/intelligence_config.py:21))
        *   `WORLDSTATE_DEFAULT_SOURCE: str = "data/baselines/default.csv"` ([`intelligence/intelligence_config.py:24`](intelligence/intelligence_config.py:24))
    *   It doesn't directly read/write these files but provides the paths for other components.

## 5. Function and Class Example Usages

This module contains only constants (variables). There are no functions or classes defined.
Other modules would use these constants like so:

```python
# In another module, e.g., intelligence/function_router.py
from intelligence import intelligence_config

class FunctionRouter:
    def __init__(self):
        self.max_retries = intelligence_config.FUNCTION_ROUTER_MAX_RETRIES
        self.retry_sleep = intelligence_config.FUNCTION_ROUTER_RETRY_SLEEP
        # ...

# In a module using LLM
from intelligence import intelligence_config

def get_llm_client():
    if intelligence_config.LLM_PROVIDER == "gemini":
        api_key = intelligence_config.GEMINI_API_KEY
        model_name = intelligence_config.GEMINI_DEFAULT_MODEL
        # Initialize Gemini client
    else: # Default to GPT
        model_name = intelligence_config.GPT_FALLBACK_MODEL # Or another GPT-specific config
        # Initialize GPT client
    # ...
```

## 6. Hardcoding Issues

The module's purpose is to centralize configurations, so many values are "hardcoded" by design, but intended to be the single source of truth.
*   **File Paths:**
    *   `OBSERVER_MEMORY_DIR: str = "data/intelligence_observer_memory"` ([`intelligence/intelligence_config.py:18`](intelligence/intelligence_config.py:18))
    *   `UPGRADE_SANDBOX_DIR: str = "data/upgrade_sandbox"` ([`intelligence/intelligence_config.py:21`](intelligence/intelligence_config.py:21))
    *   `WORLDSTATE_DEFAULT_SOURCE: str = "data/baselines/default.csv"` ([`intelligence/intelligence_config.py:24`](intelligence/intelligence_config.py:24))
    These are relative paths. Depending on the project structure and deployment, making these configurable via environment variables or a higher-level configuration system might be beneficial.
*   **Retry Logic Parameters:**
    *   `FUNCTION_ROUTER_MAX_RETRIES: int = 3` ([`intelligence/intelligence_config.py:14`](intelligence/intelligence_config.py:14))
    *   `FUNCTION_ROUTER_RETRY_SLEEP: float = 1.5` ([`intelligence/intelligence_config.py:15`](intelligence/intelligence_config.py:15))
    *   `MAX_GPT_RETRIES: int = 3` ([`intelligence/intelligence_config.py:33`](intelligence/intelligence_config.py:33))
    *   `GPT_RETRY_SLEEP: int = 5` ([`intelligence/intelligence_config.py:35`](intelligence/intelligence_config.py:35))
    *   `MAX_GEMINI_RETRIES: int = 3` ([`intelligence/intelligence_config.py:43`](intelligence/intelligence_config.py:43))
    *   `GEMINI_RETRY_SLEEP: int = 5` ([`intelligence/intelligence_config.py:45`](intelligence/intelligence_config.py:45))
*   **Model Names (Defaults):**
    *   `GPT_FALLBACK_MODEL: str = "gpt-4"` ([`intelligence/intelligence_config.py:31`](intelligence/intelligence_config.py:31))
    *   `GEMINI_DEFAULT_MODEL: str = "gemini-pro"` ([`intelligence/intelligence_config.py:41`](intelligence/intelligence_config.py:41))
*   **LLM Provider Default:**
    *   `LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gpt").lower()` ([`intelligence/intelligence_config.py:47`](intelligence/intelligence_config.py:47)) - The default "gpt" is hardcoded if the environment variable is not set.
*   **Secrets:**
    *   `GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")` ([`intelligence/intelligence_config.py:39`](intelligence/intelligence_config.py:39)) - This correctly loads a secret from an environment variable, which is good practice. No secrets are directly hardcoded.

## 7. Coupling Points

*   **High Cohesion (Good):** The module groups intelligence-related configurations, which is good.
*   **Coupling (Expected):** Any module within the `intelligence` system that requires these configurations will be coupled to this file. This is the intended design for a config file.
    *   Modules like Function Router, Observer, Upgrade Sandbox Manager, WorldState Loader, and any component using LLMs (GPT/Gemini) will import and use these constants.
*   **Implicit Coupling via File Paths:** The defined file paths (e.g., `OBSERVER_MEMORY_DIR`) create an implicit coupling with the file system structure and the components that read/write to these locations.

## 8. Existing Tests

*   Based on the file listing of the `tests` directory, there does not appear to be a specific test file named `test_intelligence_config.py` or similar.
*   The file [`tests/test_pulse_config.py`](tests/test_pulse_config.py) might test general project configuration loading, but it's unlikely to cover the specific constants defined in `intelligence_config.py` unless those are integrated into a larger configuration object tested there.
*   **Gaps:**
    *   No tests to ensure environment variables are correctly read (e.g., `GEMINI_API_KEY`, `LLM_PROVIDER`).
    *   No tests to verify the types or basic validity of the configured constants (though Python's type hints provide some static checking).
    *   For a configuration module, tests could ensure that default values are as expected and that environment variables override defaults correctly.

## 9. Module Architecture and Flow

*   **Architecture:** This is a simple Python module acting as a namespace for configuration constants. It's not an executable script but a collection of variable definitions.
*   **Key Components:**
    *   Configuration sections for different parts of the intelligence module (Function Router, Observer, LLMs, etc.).
    *   Type hints for constants.
    *   Use of `os.getenv` for loading sensitive or environment-specific values.
*   **Primary Data/Control Flows:**
    *   **Data Flow:** Defines constants that are read by other modules. No internal data processing.
    *   **Control Flow:** Not applicable in the traditional sense, as it's not a script with execution logic. Other modules import it to access its defined variables. The `os.getenv` calls are the only "runtime" operations during module import.

## 10. Naming Conventions

*   **Constants:** All top-level variables are in `UPPER_SNAKE_CASE` (e.g., `FUNCTION_ROUTER_MAX_RETRIES`, `GEMINI_API_KEY`), which is the standard Python convention for constants. This is consistent.
*   **Module Name:** `intelligence_config.py` is descriptive and follows Python module naming conventions.
*   **Type Hints:** Type hints are used (e.g., `: int`, `: float`, `: str`, `: str | None`), which is good practice.
*   **Comments:** The module docstring and comments are clear and explain the purpose of configurations.
*   **No AI Assumption Errors:** Naming seems conventional and human-generated.
*   **PEP 8 Adherence:** The naming and general structure appear to adhere well to PEP 8 guidelines.