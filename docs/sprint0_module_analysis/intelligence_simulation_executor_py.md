# Module Analysis: `intelligence/simulation_executor.py`

## 1. Module Intent/Purpose

The primary role of the [`intelligence/simulation_executor.py`](intelligence/simulation_executor.py:) module is to execute simulation and retrodiction forecasts. It integrates with the `FunctionRouter` to call various simulation and forecast generation functions, interacts with LLM providers (GPT and Gemini) for analysis, and handles forecast compression. It supports chunked simulation runs and Monte Carlo paths, managing the lifecycle of these processes, including temporary file handling for intermediate results.

## 2. Operational Status/Completeness

The module appears to be in a relatively stable and functional state, indicated by the "stable v1.3" in its docstring.
*   It has implemented logic for both forward (chunked) simulations and retrodiction.
*   It includes error handling, retry logic for LLM calls, and fallback mechanisms (e.g., retrodiction falling back to forward simulation).
*   Configuration for LLM providers (GPT and Gemini) is present, including API key handling and model selection.
*   Schema validation for forecasts using `ForecastSchema` is implemented.

There are no obvious major placeholders like `pass` in critical functions or widespread "TODO" comments indicating large unfinished sections. However, some print statements suggest areas for potential refinement or more robust logging (e.g., `"[Executor] Warning: Configured GPT model..."`).

## 3. Implementation Gaps / Unfinished Next Steps

*   **LLM Prompt Detail:** The LLM prompt (lines 287-298) mentions that "rules themselves are not provided in detail here to save token space." This could be an area for future enhancement if more detailed rule-based analysis by the LLM is desired, perhaps with a more sophisticated way to summarize or select relevant rules for the prompt.
*   **Retrodiction LLM Integration:** The [`run_retrodiction_forecast`](intelligence/simulation_executor.py:371) method explicitly states, "Assuming retrodiction doesn't use the LLM call currently" (line 376). This implies that LLM-based analysis for retrodiction forecasts is a potential future feature.
*   **Error Handling in `generate_forecast`:** The handling of non-dict returns from `forecast_engine.generate_forecast` (lines 267-273) is basic. More specific error types or handling strategies could be implemented.
*   **Configuration Management:** While it imports specific config items, the direct use of `ai_config` from `config` (line 35) "for OPENAI_API_KEY for now" suggests a temporary or transitional state for configuration handling.
*   **Gemini JSON Parsing:** The Gemini JSON parsing logic (lines 159-171) includes a fallback to `{"raw_text": text_output}`. This could be refined to be more robust or to attempt more sophisticated extraction if the LLM doesn't strictly adhere to JSON in its output.
*   **`pulse_rules` in Forecast:** Adding `RULES` to each forecast sample (line 279) is noted with a comment "Consider if this is too large/needed per sample." This suggests an optimization or refinement opportunity.

## 4. Connections & Dependencies

### Direct Imports from Other Project Modules:
*   [`forecast_engine.forecast_compressor`](forecast_engine/forecast_compressor.py:) (`compress_mc_samples`)
*   [`intelligence.forecast_schema`](intelligence/forecast_schema.py:) (`ForecastSchema`)
*   [`intelligence.function_router`](intelligence/function_router.py:) (`FunctionRouter`)
*   [`pipeline.gpt_caller`](pipeline/gpt_caller.py:) (`GPTCaller`)
*   [`intelligence.intelligence_config`](intelligence/intelligence_config.py:) (various GPT and Gemini config constants)
*   [`config`](config/) (`ai_config`)
*   [`core.variable_registry`](core/variable_registry.py:) (`VARIABLE_REGISTRY`)
*   [`engine.causal_rules`](simulation_engine/causal_rules.py:) (`RULES`)
*   [`engine.worldstate`](simulation_engine/worldstate.py:) (`WorldState`)

### External Library Dependencies:
*   `google.generativeai` (as `genai`)
*   `numpy` (as `np`)
*   `pydantic` (`ValidationError`)
*   Standard Python libraries: `random`, `sys`, `warnings`, `time`, `json`, `os`, `tempfile`, `typing`.

### Interaction with Other Modules via Shared Data:
*   **Function Calls via `FunctionRouter`:** The module heavily relies on the `FunctionRouter` to execute functions from other modules, such as:
    *   `turn_engine.initialize_worldstate`
    *   `turn_engine.run_turn`
    *   `forecast_engine.generate_forecast`
    *   `retrodiction.run_retrodiction_test`
    *   `retrodiction.get_snapshot_loader`
    *   `engine.simulator_core.simulate_forward`
*   **Configuration Objects:** Uses `ai_config` and constants from `intelligence_config`.
*   **Registries:** Accesses `VARIABLE_REGISTRY` and `RULES`.

### Input/Output Files:
*   **Input:** Potentially configuration files implicitly via `intelligence_config` and `config`.
*   **Output:**
    *   Temporary JSONL file for Monte Carlo samples (e.g., `*.jsonl` in a temp directory, path printed to console). This file is created, written to, read from, and then deleted.
    *   Log messages to standard output (console).

## 5. Function and Class Example Usages

### Class: `SimulationExecutor`

**Intended Usage:**
To instantiate and use the executor to run simulations or retrodictions.

```python
# from intelligence.simulation_executor import SimulationExecutor # Assuming import
# from intelligence.function_router import FunctionRouter # Assuming import

# router = FunctionRouter() # Optional, one will be created if not provided
# executor = SimulationExecutor(router=router)
executor = SimulationExecutor() # Router will be created internally

# Example: Run a chunked forward forecast
start_year = 2023
world_state, forecast_results = executor.run_chunked_forecast(
    start_year=start_year,
    total_turns=104, # e.g., 2 years of weekly turns
    chunk_size=52,   # Process in 1-year chunks
    n_paths=10,      # Run 10 Monte Carlo paths
    mc_seed=42
)

if world_state:
    print(f"Simulation ended. Final world state turn: {world_state.current_turn}")
# forecast_results will contain the compressed output of the 10 paths

# Example: Run a retrodiction forecast
# start_date_str = "2023-01-01"
# retro_results = executor.run_retrodiction_forecast(start_date=start_date_str, days=90)
# print(f"Retrodiction results: {retro_results}")
```

### Method: `_call_llm(prompt: str)`

**Intended Usage:**
Internal method to interact with the configured LLM (GPT or Gemini), including retry logic. It's not typically called directly from outside the class.

```python
# Inside SimulationExecutor class:
# prompt = "Analyze the following data: {...}"
# llm_response = self._call_llm(prompt)
# if "error" in llm_response:
#     print(f"LLM Error: {llm_response['error']}")
# else:
#     analysis_summary = llm_response.get("output")
#     structured_data = llm_response.get("struct")
```

### Method: `run_chunked_forecast(...)`

**Intended Usage:**
To execute a forward simulation over a number of turns, potentially in chunks, and across multiple Monte Carlo paths. It handles worldstate initialization, turn execution, forecast generation, optional LLM analysis, and forecast compression.

```python
# (See SimulationExecutor example above)
# def my_chunk_callback(turns_done):
#     print(f"Chunk completed. Total turns processed: {turns_done}")

# world_state, forecast_results = executor.run_chunked_forecast(
#     start_year=2024,
#     total_turns=52 * 3, # 3 years
#     chunk_size=52,
#     on_chunk_end=my_chunk_callback,
#     n_paths=5
# )
```

### Method: `run_retrodiction_forecast(start_date: str, days: int)`

**Intended Usage:**
To execute a retrodiction forecast starting from a specific date for a given number of days. It attempts the retrodiction and falls back to a forward simulation if the retrodiction fails.

```python
# (See SimulationExecutor example above)
# results = executor.run_retrodiction_forecast(start_date="2022-06-01", days=60)
```

## 6. Hardcoding Issues

*   **LLM Prompt Template:** The prompt template for LLM analysis (lines 287-298) is hardcoded within the [`run_chunked_forecast`](intelligence/simulation_executor.py:225) method. This could be externalized to a configuration file or a separate constants module for easier modification.
*   **Default Chunk Size/Total Turns (in docstring/defaults):** While parameters, the default values like `total_turns=312` and `chunk_size=52` in [`run_chunked_forecast`](intelligence/simulation_executor.py:225) might represent common use cases but are effectively hardcoded defaults.
*   **Error Messages:** Various error messages printed to the console (e.g., `"[Executor] OpenAI API key not found..."`) are hardcoded strings.
*   **Temporary File Suffix:** `suffix='.jsonl'` for `tempfile.NamedTemporaryFile` (line 248) is hardcoded.
*   **Compression Alpha:** `alpha=0.9` in `compress_mc_samples(read_mc_samples, alpha=0.9)` (line 345) is a hardcoded parameter for the compression algorithm. This might be better as a configurable parameter of `SimulationExecutor` or `run_chunked_forecast`.

## 7. Coupling Points

*   **`FunctionRouter`:** Tightly coupled. The `SimulationExecutor` is highly dependent on the `FunctionRouter` to delegate tasks to other parts of the simulation and forecasting engine.
*   **`intelligence_config` and `config.ai_config`:** Tightly coupled for LLM API keys, models, and retry parameters. Changes in these configuration modules directly impact the executor's behavior.
*   **`GPTCaller` / `genai` (Google Gemini client):** Directly instantiates and uses these clients based on configuration.
*   **`forecast_engine.forecast_compressor`:** Directly calls `compress_mc_samples`.
*   **`ForecastSchema`:** Used for validating the structure of generated forecasts.
*   **`WorldState`:** Relies on `WorldState` objects being returned and passed to functions via the router.
*   **`VARIABLE_REGISTRY` and `RULES`:** Directly accesses these global registries/constants for inclusion in forecast data. This creates a global state dependency.
*   **Temporary File System:** Interacts with the file system for temporary storage of Monte Carlo samples.

## 8. Existing Tests

No specific test file (e.g., `tests/test_simulation_executor.py`) was found in the provided file listing for the `tests/` directory. This indicates a **gap in dedicated unit/integration tests** for this module.

While other tests like [`tests/test_integration_simulation_forecast.py`](tests/test_integration_simulation_forecast.py) might cover some functionality of the `SimulationExecutor` indirectly, the absence of a dedicated test suite means:
*   It's harder to verify the correctness of individual methods within `SimulationExecutor` in isolation.
*   Refactoring the `SimulationExecutor` carries a higher risk without targeted tests.
*   Edge cases, error handling (like LLM retries, API key issues, file system errors for temp files), and different configurations (GPT vs. Gemini, LLM disabled) may not be thoroughly tested.

## 9. Module Architecture and Flow

**Architecture:**
The `SimulationExecutor` class is the central component.
1.  **Initialization (`__init__`)**:
    *   Sets up a `FunctionRouter`.
    *   Initializes an LLM client (`GPTCaller` or `genai.GenerativeModel` for Gemini) based on `LLM_PROVIDER` configuration from `intelligence_config`. It handles API key presence and potential initialization errors, falling back to `llm_provider = "none"` if setup fails.
2.  **LLM Interaction (`_call_llm`)**:
    *   A private helper method to abstract calls to either GPT or Gemini.
    *   Includes retry logic with exponential backoff, configured via constants from `intelligence_config`.
    *   Standardizes the output structure from different LLMs.
    *   Handles JSON parsing from LLM responses.
3.  **Chunked Forward Forecast (`run_chunked_forecast`)**:
    *   The main method for running forward simulations.
    *   Optionally seeds `random` for Monte Carlo determinism.
    *   Manages multiple simulation `n_paths` (Monte Carlo).
    *   For each path:
        *   Initializes `WorldState` via `FunctionRouter`.
        *   Iteratively runs simulation turns in `chunk_size` blocks until `total_turns` are completed, using `FunctionRouter` to call `turn_engine.run_turn`.
        *   Calls an optional `on_chunk_end` callback.
        *   Generates a forecast via `FunctionRouter` (`forecast_engine.generate_forecast`).
        *   Appends `VARIABLE_REGISTRY` keys and `RULES` to the forecast.
        *   If an LLM is configured and no prior error occurred, it constructs a prompt with the `WorldState` snapshot and calls `_call_llm` for analysis. The LLM output is added to the forecast.
        *   Validates the forecast against `ForecastSchema`.
        *   Writes each path's forecast to a temporary JSONL file.
    *   After all paths, reads all forecasts from the temporary file.
    *   Compresses the collected forecasts using `compress_mc_samples`.
    *   Cleans up the temporary file.
    *   Returns the final `WorldState` of the last path and the (compressed) list of forecasts.
4.  **Retrodiction Forecast (`run_retrodiction_forecast`)**:
    *   Attempts to run a retrodiction via `FunctionRouter` (`retrodiction.run_retrodiction_test`).
    *   If it fails, it falls back to a forward simulation in "retrodiction mode," potentially using a `retrodiction_loader`.

**Primary Data/Control Flows:**
*   **Control Flow:** Primarily orchestrated by the `SimulationExecutor` methods, which delegate specific tasks (like running a turn, generating a forecast) to other modules via the `FunctionRouter`. Configuration dictates which LLM provider is used.
*   **Data Flow:**
    *   `WorldState` objects are passed around and modified by simulation steps.
    *   Forecast data (dictionaries) are generated, potentially augmented by LLM analysis, validated, and then collected.
    *   For Monte Carlo runs, individual forecast dictionaries are written to a temporary file, then read back and aggregated/compressed.
    *   Configuration data is read from `intelligence_config` and `config.ai_config`.

## 10. Naming Conventions

*   **Class Name:** `SimulationExecutor` - Clear and follows PascalCase (PEP 8).
*   **Method Names:**
    *   `run_chunked_forecast`, `run_retrodiction_forecast`: Descriptive, verb-noun, snake_case (PEP 8).
    *   `_call_llm`: Protected member indicated by a single underscore, snake_case (PEP 8).
*   **Variable Names:** Generally follow snake_case (e.g., `start_year`, `total_turns`, `mc_seed`, `llm_provider`, `last_exception`).
    *   Some abbreviations are used: `ws` for `world_state`, `ve` for `ValidationError`, `ae` for `AttributeError`. These are common and generally acceptable within limited scopes.
    *   `prompt_data` is clear.
*   **Constants:** Imported constants like `GPT_FALLBACK_MODEL`, `MAX_GPT_RETRIES` are uppercase (PEP 8).
*   **File Name:** `simulation_executor.py` - snake_case, descriptive.

**Potential AI Assumption Errors or Deviations:**
*   The naming seems largely consistent with Python conventions (PEP 8).
*   No obvious AI-generated-sounding names that deviate significantly from common Python practices were observed.
*   The use of `gpt_caller` and `gemini_client` clearly distinguishes the LLM clients.
*   The prefix `"[Executor]"` in print statements is a good convention for identifying log sources.

Overall, the naming conventions are good and contribute to the readability of the module.