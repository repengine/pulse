# Module Analysis: `scripts/run_causal_benchmarks.py`

## Table of Contents

- [Module Intent/Purpose](#module-intentpurpose)
- [Operational Status/Completeness](#operational-statuscompleteness)
- [Implementation Gaps / Unfinished Next Steps](#implementation-gaps--unfinished-next-steps)
- [Connections & Dependencies](#connections--dependencies)
- [Function and Class Example Usages](#function-and-class-example-usages)
- [Hardcoding Issues](#hardcoding-issues)
- [Coupling Points](#coupling-points)
- [Existing Tests](#existing-tests)
- [Module Architecture and Flow](#module-architecture-and-flow)
- [Naming Conventions](#naming-conventions)

## Module Intent/Purpose

The primary role of [`scripts/run_causal_benchmarks.py`](scripts/run_causal_benchmarks.py:3) is to execute a set of causal-only benchmark scenarios for the simulation engine. It achieves this by running simulations with the "gravity" mechanism explicitly disabled (using the `--gravity-off` flag). This allows for the isolated measurement and performance analysis of the purely causal components of the system, without interference from the gravity correction mechanism. The script defines or loads benchmark scenarios, executes them, collects key performance metrics (like accuracy and drift), and stores the results in a structured format (JSONL) for subsequent analysis.

## Operational Status/Completeness

The module appears to be largely complete and operational for its defined purpose.
- It can load scenarios from a configuration file or use hardcoded defaults.
- It can execute scenarios either programmatically within the same process or by spawning a subprocess.
- It calculates and stores metrics.
- It includes command-line argument parsing for configuration.

Obvious placeholders or TODOs:
- The script mentions that the `DEFAULT_SCENARIOS` (hardcoded in the script at line [`scripts/run_causal_benchmarks.py:48`](scripts/run_causal_benchmarks.py:48)) "could be moved to a configuration file in the future." This suggests an intended improvement for better configurability.
- The metric calculation in [`calculate_metrics()`](scripts/run_causal_benchmarks.py:240) is functional but could be expanded for more detailed analysis if required.

## Implementation Gaps / Unfinished Next Steps

- **Externalized Default Scenarios:** As noted above, the `DEFAULT_SCENARIOS` are hardcoded (lines [`scripts/run_causal_benchmarks.py:48-73`](scripts/run_causal_benchmarks.py:48-73)). Moving these to the [`DEFAULT_SCENARIOS_FILE`](scripts/run_causal_benchmarks.py:43) (`config/causal_benchmark_scenarios.yaml`) would be a logical next step for consistency and ease of modification without code changes.
- **Advanced Metrics:** The current metrics ([`calculate_metrics()`](scripts/run_causal_benchmarks.py:240)) focus on accuracy and drift. More sophisticated benchmarking might require additional metrics (e.g., execution time per scenario, memory usage, specific causal link performance).
- **Integration with a Broader Benchmarking Framework:** The script is standalone. It could potentially be integrated into a larger, more comprehensive benchmarking or CI/CD system that regularly runs these tests and tracks performance over time.
- **Visualization of Results:** While results are saved, there's no built-in visualization. A follow-up script or integration with a plotting library could be useful for analyzing benchmark trends.

There are no strong indications that development started on a significantly different path and then deviated, but the hardcoded scenarios suggest a quicker initial implementation path was taken with the intent to refine later.

## Connections & Dependencies

### Direct Imports from Other Project Modules:
- [`core.path_registry.PATHS`](core/path_registry.py) (from [`scripts/run_causal_benchmarks.py:35`](scripts/run_causal_benchmarks.py:35))
- [`core.pulse_config.SHADOW_MONITOR_CONFIG`](core/pulse_config.py) (from [`scripts/run_causal_benchmarks.py:36`](scripts/run_causal_benchmarks.py:36)) - Note: `SHADOW_MONITOR_CONFIG` is imported but not explicitly used in the provided code.
- [`engine.batch_runner.run_batch_from_config()`](simulation_engine/batch_runner.py) (from [`scripts/run_causal_benchmarks.py:37`](scripts/run_causal_benchmarks.py:37))
- [`forecast_output.forecast_generator.generate_forecast()`](forecast_output/forecast_generator.py) (from [`scripts/run_causal_benchmarks.py:38`](scripts/run_causal_benchmarks.py:38)) - Note: `generate_forecast` is imported but not explicitly used in the provided code.
- [`analytics.forecast_pipeline_runner.run_forecast_pipeline()`](learning/forecast_pipeline_runner.py) (from [`scripts/run_causal_benchmarks.py:39`](scripts/run_causal_benchmarks.py:39)) - Note: `run_forecast_pipeline` is imported but not explicitly used in the provided code.

### External Library Dependencies:
- `os` ([`scripts/run_causal_benchmarks.py:22`](scripts/run_causal_benchmarks.py:22))
- `sys` ([`scripts/run_causal_benchmarks.py:23`](scripts/run_causal_benchmarks.py:23))
- `json` ([`scripts/run_causal_benchmarks.py:24`](scripts/run_causal_benchmarks.py:24))
- `yaml` ([`scripts/run_causal_benchmarks.py:25`](scripts/run_causal_benchmarks.py:25))
- `argparse` ([`scripts/run_causal_benchmarks.py:26`](scripts/run_causal_benchmarks.py:26))
- `datetime` ([`scripts/run_causal_benchmarks.py:27`](scripts/run_causal_benchmarks.py:27))
- `subprocess` ([`scripts/run_causal_benchmarks.py:28`](scripts/run_causal_benchmarks.py:28))
- `pathlib.Path` ([`scripts/run_causal_benchmarks.py:29`](scripts/run_causal_benchmarks.py:29))
- `typing.Dict, List, Any, Optional` ([`scripts/run_causal_benchmarks.py:30`](scripts/run_causal_benchmarks.py:30))
- `random` (conditionally imported in [`main()`](scripts/run_causal_benchmarks.py:388) at line [`scripts/run_causal_benchmarks.py:422`](scripts/run_causal_benchmarks.py:422))
- `numpy` (conditionally imported as `np` in [`main()`](scripts/run_causal_benchmarks.py:388) at line [`scripts/run_causal_benchmarks.py:423`](scripts/run_causal_benchmarks.py:423))

### Interaction with Other Modules via Shared Data:
- **Configuration Files:** Reads benchmark scenarios from a YAML or JSON file (e.g., [`config/causal_benchmark_scenarios.yaml`](config/causal_benchmark_scenarios.yaml) as specified by [`DEFAULT_SCENARIOS_FILE`](scripts/run_causal_benchmarks.py:43)).
- **Output Files:** Writes results to JSONL files in the directory specified by [`DEFAULT_OUTPUT_DIR`](scripts/run_causal_benchmarks.py:42) (e.g., `forecasts/causal_only_benchmarks/`). Each scenario run (programmatic or subprocess) generates its own output file, and a summary JSONL file is also created.
- **Subprocess Execution:** When using the "subprocess" method, it interacts with [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py) by executing it as a command-line tool, passing configuration via a temporary JSON file.

### Input/Output Files:
- **Input:**
    - Benchmark scenario configuration file (YAML or JSON), e.g., [`config/causal_benchmark_scenarios.yaml`](config/causal_benchmark_scenarios.yaml).
    - (Potentially) Temporary JSON configuration file when using the "subprocess" method (e.g., `temp_benchmark_config_<scenario_name>.json`).
- **Output:**
    - Individual scenario result files (JSONL), e.g., `forecasts/causal_only_benchmarks/causal_benchmark_results_YYYYMMDD_HHMMSS_<scenario_name>.jsonl`.
    - Aggregated results file (JSONL), e.g., `forecasts/causal_only_benchmarks/causal_benchmark_results_YYYYMMDD_HHMMSS.jsonl`.
    - Summary report file (JSON), e.g., `forecasts/causal_only_benchmarks/summary_causal_benchmark_results_YYYYMMDD_HHMMSS.jsonl`.

## Function and Class Example Usages

- **[`load_scenarios_from_file(file_path: str)`](scripts/run_causal_benchmarks.py:76):**
  ```python
  # scenarios_config_path = "config/causal_benchmark_scenarios.yaml"
  # scenarios = load_scenarios_from_file(scenarios_config_path)
  ```
  This function is used to load a list of benchmark scenario dictionaries from a specified YAML or JSON file. If the file doesn't exist or an error occurs, it returns `DEFAULT_SCENARIOS`.

- **[`run_scenario_programmatically(scenario: Dict[str, Any], output_path: str)`](scripts/run_causal_benchmarks.py:103):**
  ```python
  # scenario_config = {"name": "my_test", "configs": [{"turns": 1}]}
  # results_file_path = "forecasts/causal_only_benchmarks/benchmark_run.jsonl"
  # result_summary = run_scenario_programmatically(scenario_config, results_file_path)
  ```
  This function takes a single scenario dictionary and an output path. It calls [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) directly with `gravity_enabled=False` and then calculates metrics.

- **[`run_scenario_subprocess(scenario: Dict[str, Any], output_path: str)`](scripts/run_causal_benchmarks.py:150):**
  ```python
  # scenario_config = {"name": "my_subprocess_test", "configs": [{"turns": 1}]}
  # results_file_path = "forecasts/causal_only_benchmarks/benchmark_run.jsonl"
  # result_summary = run_scenario_subprocess(scenario_config, results_file_path)
  ```
  This function also takes a scenario and output path but executes the benchmark by creating a temporary config file and running [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py) as a subprocess with the `--gravity-off` flag.

- **[`calculate_metrics(results: List[Dict[str, Any]], scenario: Dict[str, Any])`](scripts/run_causal_benchmarks.py:240):**
  ```python
  # simulation_outputs = [{"forecasts": [{"accuracy": 0.9, "drift": 0.1, "variables": {"X": {"accuracy": 0.9, "drift": 0.1}}}]}]
  # scenario_info = {"name": "test_metrics"}
  # metrics = calculate_metrics(simulation_outputs, scenario_info)
  ```
  This function processes the raw results from a simulation run (a list of dictionaries) and computes accuracy and drift metrics, both overall and per variable.

- **[`run_causal_benchmarks(scenarios: List[Dict[str, Any]], output_dir: str, output_file: str, method: str = "programmatic")`](scripts/run_causal_benchmarks.py:323):**
  ```python
  # benchmark_scenarios = [...] # list of scenario dicts
  # out_dir = "forecasts/causal_only_benchmarks"
  # out_file = "final_results.jsonl"
  # run_causal_benchmarks(benchmark_scenarios, out_dir, out_file, method="programmatic")
  ```
  This is the main orchestrator function. It iterates through a list of scenarios, runs each one using the specified method (`"programmatic"` or `"subprocess"`), and saves all results and a summary.

- **[`main()`](scripts/run_causal_benchmarks.py:388):**
  This function handles command-line argument parsing (for config file, output paths, method, and seed) and then calls [`run_causal_benchmarks()`](scripts/run_causal_benchmarks.py:323) to execute the benchmarks. It's the entry point when the script is run directly.
  ```bash
  python scripts/run_causal_benchmarks.py --config my_scenarios.yaml --output-dir results/causal --output my_results.jsonl --method subprocess --seed 42
  ```

## Hardcoding Issues

- **`DEFAULT_SCENARIOS`:** (Lines [`scripts/run_causal_benchmarks.py:48-73`](scripts/run_causal_benchmarks.py:48-73)) A list of benchmark scenarios is hardcoded as a fallback. The script notes these could be moved to a configuration file.
- **`DEFAULT_OUTPUT_DIR`:** (Line [`scripts/run_causal_benchmarks.py:42`](scripts/run_causal_benchmarks.py:42)) Default output directory path `forecasts/causal_only_benchmarks` is defined using [`PATHS.get()`](core/path_registry.py:0), which is good, but the fallback string is hardcoded.
- **`DEFAULT_SCENARIOS_FILE`:** (Line [`scripts/run_causal_benchmarks.py:43`](scripts/run_causal_benchmarks.py:43)) Default scenarios configuration file path `config/causal_benchmark_scenarios.yaml` is defined using [`PATHS.get()`](core/path_registry.py:0), with a hardcoded fallback.
- **`DEFAULT_OUTPUT_FILENAME`:** (Line [`scripts/run_causal_benchmarks.py:44`](scripts/run_causal_benchmarks.py:44)) The pattern for the default output filename `causal_benchmark_results_{datetime}.jsonl` is hardcoded.
- **Temporary Config Filename Pattern:** In [`run_scenario_subprocess()`](scripts/run_causal_benchmarks.py:150), the temporary config file path is generated using an f-string: `f"temp_benchmark_config_{scenario_name}.json"` (line [`scripts/run_causal_benchmarks.py:167`](scripts/run_causal_benchmarks.py:167)). While functional, using the `tempfile` module for generating temporary file names might be more robust.
- **Subprocess Command:** The command to run [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py) in [`run_scenario_subprocess()`](scripts/run_causal_benchmarks.py:150) has the script path `"simulation_engine/batch_runner.py"` hardcoded (line [`scripts/run_causal_benchmarks.py:178`](scripts/run_causal_benchmarks.py:178)). This assumes a specific project structure relative to where `run_causal_benchmarks.py` is executed.
- **Metric Keys:** Keys used in [`calculate_metrics()`](scripts/run_causal_benchmarks.py:240) like `"accuracy"`, `"drift"`, `"variables"`, `"overall"`, `"by_variable"`, `"summary"` are hardcoded strings. This is typical but worth noting.

## Coupling Points

- **[`engine.batch_runner`](simulation_engine/batch_runner.py):** Tightly coupled, as this script's core function is to run benchmarks using [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) (either directly or via subprocess). The `--gravity-off` / `gravity_enabled=False` parameter is a key part of this interaction.
- **[`core.path_registry.PATHS`](core/path_registry.py):** Relies on this for default file paths, making it dependent on the path definitions within the registry.
- **Configuration File Structure:** Implicitly coupled to the expected structure of the benchmark scenario configuration files (YAML/JSON) and the output structure of [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) (for metric calculation).
- **Output Data Format (JSONL):** The script produces and consumes JSONL for results, creating a dependency on this format for any downstream analysis tools.
- **Command-Line Interface of `batch_runner.py`:** When using the "subprocess" method, it's coupled to the CLI arguments of [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py) (e.g., `--config`, `--output`, `--gravity-off`).

## Existing Tests

The corresponding test file is [`tests/test_causal_benchmarks.py`](tests/test_causal_benchmarks.py).

- **Test Coverage:** The tests cover several key aspects of the module:
    - **`test_gravity_off_flag_integration()` ([`tests/test_causal_benchmarks.py:23`](tests/test_causal_benchmarks.py:23)):** Verifies that the `gravity_enabled` flag is correctly passed to [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) and subsequently to [`simulate_forward()`](simulation_engine/simulator_core.py:0).
    - **`test_conditional_gravity_application()` ([`tests/test_causal_benchmarks.py:52`](tests/test_causal_benchmarks.py:52)):** Checks that gravity correction within [`simulate_forward()`](simulation_engine/simulator_core.py:0) (specifically, the call to `simulate_turn`) is conditional based on the `gravity_enabled` flag.
    - **`test_load_scenarios_from_file()` ([`tests/test_causal_benchmarks.py:86`](tests/test_causal_benchmarks.py:86)):** Tests loading scenarios from a valid JSON file and the fallback mechanism for a non-existent file.
    - **`test_run_scenario_programmatically()` ([`tests/test_causal_benchmarks.py:115`](tests/test_causal_benchmarks.py:115)):** Tests the programmatic scenario execution, ensuring [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) is called with `gravity_enabled=False`.
    - **`test_calculate_metrics()` ([`tests/test_causal_benchmarks.py:140`](tests/test_causal_benchmarks.py:140)):** Validates the metric calculation logic with sample results.
    - **`test_run_causal_benchmarks()` ([`tests/test_causal_benchmarks.py:177`](tests/test_causal_benchmarks.py:177)):** Tests the main orchestrator function, checking if it calls scenario runners correctly and produces output and summary files.

- **Nature of Tests:** The tests are primarily unit tests, using `unittest.mock.patch` extensively to isolate components and verify interactions (e.g., checking if functions are called with expected arguments). They also use `tempfile` for creating temporary files for testing file operations.

- **Gaps/Problematic Tests:**
    - **Subprocess Execution Path:** There are no explicit tests for the `method="subprocess"` path in [`run_causal_benchmarks()`](scripts/run_causal_benchmarks.py:323) or for the [`run_scenario_subprocess()`](scripts/run_causal_benchmarks.py:150) function itself. Testing this would involve mocking `subprocess.run` or performing actual subprocess calls with a controlled environment.
    - **YAML Loading:** [`test_load_scenarios_from_file()`](tests/test_causal_benchmarks.py:86) only tests with a JSON file, not a YAML file, though the main script supports YAML.
    - **Error Handling in `run_scenario_*`:** While the main functions have `try-except` blocks, the tests don't specifically trigger and verify these error handling paths (e.g., what happens if [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) raises an exception).
    - **CLI Argument Parsing:** The [`main()`](scripts/run_causal_benchmarks.py:388) function's argument parsing and conditional logic (e.g., seed setting, scenario loading based on file existence) are not directly tested. This would typically involve using a test runner that can simulate command-line invocations or by directly calling `main()` with mocked `sys.argv`.
    - **Output File Content Verification:** [`test_run_causal_benchmarks()`](tests/test_causal_benchmarks.py:177) checks for the existence of output and summary files but doesn't deeply inspect their content beyond basic structure in the summary.

Overall, the existing tests provide good coverage for the programmatic execution path and core logic but could be expanded to cover subprocess execution, more error cases, and CLI interactions more thoroughly.

## Module Architecture and Flow

1.  **Initialization & Configuration (Entry Point: `main()`):**
    *   Parses command-line arguments (`--config`, `--output`, `--output-dir`, `--method`, `--seed`).
    *   Sets random seed if provided.
    *   Loads benchmark scenarios:
        *   Attempts to load from the file specified by `--config` using [`load_scenarios_from_file()`](scripts/run_causal_benchmarks.py:76).
        *   If the file doesn't exist or fails to load, it uses `DEFAULT_SCENARIOS`.
    *   Calls [`run_causal_benchmarks()`](scripts/run_causal_benchmarks.py:323) with loaded scenarios and arguments.

2.  **Benchmark Execution Orchestration (`run_causal_benchmarks()`):**
    *   Ensures the output directory exists.
    *   Iterates through each scenario:
        *   Prints progress.
        *   Calls either [`run_scenario_programmatically()`](scripts/run_causal_benchmarks.py:103) or [`run_scenario_subprocess()`](scripts/run_causal_benchmarks.py:150) based on the `method` argument.
        *   Appends the result of the scenario run to an aggregated list (`all_results`).
        *   Writes the individual scenario result immediately to the main output JSONL file.
    *   After all scenarios, generates a summary report (JSON) containing timestamps, counts of successful/failed scenarios, and brief metrics for each.

3.  **Single Scenario Execution (Two Methods):**
    *   **`run_scenario_programmatically()`:**
        *   Calls [`run_batch_from_config()`](simulation_engine/batch_runner.py:0) from [`engine.batch_runner`](simulation_engine/batch_runner.py) with `gravity_enabled=False`.
        *   Passes the scenario's `configs` and a unique output path for this specific scenario's detailed results.
        *   Calls [`calculate_metrics()`](scripts/run_causal_benchmarks.py:240) on the results.
        *   Returns a dictionary with scenario info, timestamp, metrics, and output path.
    *   **`run_scenario_subprocess()`:**
        *   Creates a temporary JSON config file from the scenario's `configs`.
        *   Constructs a command to execute [`simulation_engine/batch_runner.py`](simulation_engine/batch_runner.py) using `sys.executable`.
        *   Crucially adds the `--gravity-off` flag to the command, along with `--config` pointing to the temp file and `--output` for the scenario's detailed results.
        *   Runs the command using `subprocess.run()`.
        *   If successful, loads results from the output file produced by the subprocess.
        *   Calls [`calculate_metrics()`](scripts/run_causal_benchmarks.py:240).
        *   Removes the temporary config file.
        *   Returns a dictionary with scenario info, timestamp, metrics, stdout/stderr, and output path.

4.  **Metric Calculation (`calculate_metrics()`):**
    *   Takes the list of simulation results (from [`run_batch_from_config()`](simulation_engine/batch_runner.py:0)) and the scenario config.
    *   Initializes a metrics dictionary.
    *   Extracts all individual forecasts from the results.
    *   Calculates overall accuracy and drift.
    *   Calculates per-variable accuracy and drift.
    *   Compiles a summary section with key overall metrics and best/worst performing variables.

5.  **Output:**
    *   Individual scenario results are written to `<output_dir>/<output_file_base>_<scenario_name>.jsonl`.
    *   All scenario summaries are appended to `<output_dir>/<output_file>`.
    *   A final summary report is written to `<output_dir>/summary_<output_file>`.

The control flow is primarily sequential, driven by the list of scenarios. The choice between programmatic and subprocess execution offers flexibility. Error handling is present at scenario execution and file loading stages.

## Naming Conventions

- **Variables and Functions:** Generally follow PEP 8 (snake_case), e.g., [`load_scenarios_from_file`](scripts/run_causal_benchmarks.py:76), [`output_dir`](scripts/run_causal_benchmarks.py:325), [`scenario_name`](scripts/run_causal_benchmarks.py:114).
- **Constants:** Uppercase with underscores, e.g., [`DEFAULT_OUTPUT_DIR`](scripts/run_causal_benchmarks.py:42), [`DEFAULT_SCENARIOS`](scripts/run_causal_benchmarks.py:48).
- **Classes (in tests):** PascalCase, e.g., [`TestCausalBenchmarks`](tests/test_causal_benchmarks.py:20).
- **File Paths:** Variables holding paths like `output_path`, `temp_config_path` are clear.
- **Clarity:** Names are generally descriptive and understandable.
    - `run_scenario_programmatically` vs. `run_scenario_subprocess` clearly distinguishes the two methods.
    - `calculate_metrics` is self-explanatory.
- **Potential AI Assumption Errors/Deviations:**
    - No obvious AI-like naming errors (e.g., overly verbose or generic names not fitting Python conventions).
    - The naming seems consistent with typical Python project standards.
    - The use of f-strings for filenames (e.g., [`DEFAULT_OUTPUT_FILENAME`](scripts/run_causal_benchmarks.py:44)) is modern and clear.

Overall, the naming conventions are good and adhere well to Python standards, contributing to the module's readability.