# Module Analysis: `simulation_engine.utils.pulse_variable_forecaster`

**File Path:** [`simulation_engine/utils/pulse_variable_forecaster.py`](../../simulation_engine/utils/pulse_variable_forecaster.py)

## 1. Module Intent/Purpose

The primary role of this module is to forecast future value trajectories of a selected simulation variable. It achieves this by running multiple Monte Carlo-style simulation rollouts using the existing simulation engine's [`run_turn`](../../simulation_engine/turn_engine.py:0) and [`WorldState`](../../simulation_engine/worldstate.py:0) components. The module supports visualizing these trajectories and their mean, as well as exporting the raw forecast data. It is designed to be used as a command-line tool.

## 2. Operational Status/Completeness

- **Status:** Appears functional and relatively complete for its defined scope.
- **Version:** v0.5.0, as indicated in the module's docstring ([`simulation_engine/utils/pulse_variable_forecaster.py:8`](../../simulation_engine/utils/pulse_variable_forecaster.py:8)).
- **Completeness:**
    - Implements core functionalities: simulation, data aggregation (mean), plotting, and data export.
    - Includes a [`main`](../../simulation_engine/utils/pulse_variable_forecaster.py:77) function for CLI operation with arguments for customization.
    - No explicit TODOs or obvious placeholders are present in the code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Initial State Configuration:** The [`WorldState()`](../../simulation_engine/utils/pulse_variable_forecaster.py:37) is re-initialized as new for every simulation run. There's no apparent mechanism to start simulations from a specific pre-existing or loaded world state, which might be crucial for more contextualized forecasts.
- **Handling of Non-Numeric Variables:** The docstring ([`simulation_engine/utils/pulse_variable_forecaster.py:5`](../../simulation_engine/utils/pulse_variable_forecaster.py:5)) mentions forecasting "symbolic or capital variables." However, the current implementation for averaging ([`mean()`](../../simulation_engine/utils/pulse_variable_forecaster.py:50)) and plotting ([`matplotlib.pyplot`](../../simulation_engine/utils/pulse_variable_forecaster.py:13)) is geared towards numeric data. The behavior or utility for non-numeric symbolic variables is unclear and likely unsupported by these functions.
- **Advanced Statistical Output:** The forecasting currently provides only the mean trajectory. Additional statistical measures like median, confidence intervals, or variance could enhance the forecast's utility.
- **Error Handling for Variable Unavailability:** If a tracked variable is consistently `None` across all runs at a particular step, the [`mean`](../../simulation_engine/utils/pulse_variable_forecaster.py:50) calculation might result in errors or an empty list for that step, potentially affecting the plot.
- **Configuration Management:** Default parameters (e.g., simulation horizon ([`simulation_engine/utils/pulse_variable_forecaster.py:80`](../../simulation_engine/utils/pulse_variable_forecaster.py:80)), number of runs ([`simulation_engine/utils/pulse_variable_forecaster.py:81`](../../simulation_engine/utils/pulse_variable_forecaster.py:81))) are hardcoded as `argparse` defaults. Integration with a centralized configuration system could be beneficial.
- **Simulation Model Flexibility:** The module uses a fixed simulation progression via [`run_turn(state)`](../../simulation_engine/utils/pulse_variable_forecaster.py:40). It doesn't offer ways to easily switch between different simulation models, parameters, or rule sets for forecasting purposes.

## 4. Connections & Dependencies

### Internal Project Dependencies:
- [`simulation_engine.turn_engine.run_turn`](../../simulation_engine/turn_engine.py:0): Used to advance the simulation state by one step ([`simulation_engine/utils/pulse_variable_forecaster.py:17`](../../simulation_engine/utils/pulse_variable_forecaster.py:17)).
- [`simulation_engine.worldstate.WorldState`](../../simulation_engine/worldstate.py:0): Used to initialize and manage the simulation state ([`simulation_engine/utils/pulse_variable_forecaster.py:18`](../../simulation_engine/utils/pulse_variable_forecaster.py:18)). The forecaster relies on the structure of `WorldState.variables`.

### External Library Dependencies:
- `argparse` ([`simulation_engine/utils/pulse_variable_forecaster.py:11`](../../simulation_engine/utils/pulse_variable_forecaster.py:11)): For command-line argument parsing.
- `json` ([`simulation_engine/utils/pulse_variable_forecaster.py:12`](../../simulation_engine/utils/pulse_variable_forecaster.py:12)): For saving forecast data.
- `matplotlib.pyplot` ([`simulation_engine/utils/pulse_variable_forecaster.py:13`](../../simulation_engine/utils/pulse_variable_forecaster.py:13)): For plotting forecast trajectories.
- `statistics.mean` ([`simulation_engine/utils/pulse_variable_forecaster.py:14`](../../simulation_engine/utils/pulse_variable_forecaster.py:14)): For calculating the average trajectory.
- `typing` (List, Dict, Optional) ([`simulation_engine/utils/pulse_variable_forecaster.py:15`](../../simulation_engine/utils/pulse_variable_forecaster.py:15)): For type hinting.

### Data Interaction:
- **Input:** Implicitly relies on the initial state provided by [`WorldState()`](../../simulation_engine/utils/pulse_variable_forecaster.py:37) and how it's affected by [`run_turn()`](../../simulation_engine/utils/pulse_variable_forecaster.py:40). No direct file inputs for initial state.
- **Output:**
    - JSON file: If `--export-data` CLI argument is provided, saves raw trajectory data (e.g., `forecast_data.json`). Generated by [`save_forecast_data`](../../simulation_engine/utils/pulse_variable_forecaster.py:71).
    - Image file (e.g., PNG): If `--export-plot` CLI argument is provided, saves the forecast plot (e.g., `forecast_plot.png`). Generated by [`plot_forecast`](../../simulation_engine/utils/pulse_variable_forecaster.py:54).

## 5. Function and Class Example Usages

### [`simulate_forward(variable: str, steps: int, runs: int = 10)`](../../simulation_engine/utils/pulse_variable_forecaster.py:21)
- **Description:** Performs multiple simulation runs to forecast a variable's trajectory.
- **Example Usage:**
  ```python
  results = simulate_forward(variable="market_price", steps=30, runs=100)
  # results will be a dict: {"trajectories": [[...], ...], "average": [...]}
  ```

### [`plot_forecast(all_runs: List[List[float]], avg: List[float], var_name: str, export: Optional[str] = None)`](../../simulation_engine/utils/pulse_variable_forecaster.py:54)
- **Description:** Plots the forecasted trajectories and their mean.
- **Example Usage:**
  ```python
  plot_forecast(results["trajectories"], results["average"], "market_price", export="market_price_forecast.png")
  ```

### [`save_forecast_data(path: str, results: Dict[str, List[float]], var_name: str)`](../../simulation_engine/utils/pulse_variable_forecaster.py:71)
- **Description:** Saves the raw forecast data to a JSON file.
- **Example Usage:**
  ```python
  save_forecast_data("market_price_data.json", results, "market_price")
  ```

### Command-Line Interface ([`main`](../../simulation_engine/utils/pulse_variable_forecaster.py:77))
- **Description:** Allows running the forecaster from the command line.
- **Example Usage:**
  ```bash
  python simulation_engine/utils/pulse_variable_forecaster.py --var "stock_A_value" --horizon 24 --runs 50 --export-data "stock_A_forecast.json" --export-plot "stock_A_plot.png"
  ```

## 6. Hardcoding Issues

- **CLI Default Values:**
    - `--horizon` defaults to `12` ([`simulation_engine/utils/pulse_variable_forecaster.py:80`](../../simulation_engine/utils/pulse_variable_forecaster.py:80)).
    - `--runs` defaults to `10` ([`simulation_engine/utils/pulse_variable_forecaster.py:81`](../../simulation_engine/utils/pulse_variable_forecaster.py:81)).
- **Plotting Aesthetics:**
    - Figure size: `(10, 5)` ([`simulation_engine/utils/pulse_variable_forecaster.py:55`](../../simulation_engine/utils/pulse_variable_forecaster.py:55)).
    - Colors and alpha for plot lines (e.g., `color="gray"`, `alpha=0.3`, `color="blue"`) are fixed ([`simulation_engine/utils/pulse_variable_forecaster.py:57-58`](../../simulation_engine/utils/pulse_variable_forecaster.py:57-58)).
- **Output Messages:** Informational print statements (e.g., "Forecast plot saved to...") are hardcoded strings ([`simulation_engine/utils/pulse_variable_forecaster.py:67`](../../simulation_engine/utils/pulse_variable_forecaster.py:67), [`simulation_engine/utils/pulse_variable_forecaster.py:74`](../../simulation_engine/utils/pulse_variable_forecaster.py:74)).

## 7. Coupling Points

- **`WorldState`:** The module is tightly coupled to the [`WorldState`](../../simulation_engine/worldstate.py:0) class, especially its `variables` attribute, which is expected to be a dictionary ([`simulation_engine/utils/pulse_variable_forecaster.py:42-43`](../../simulation_engine/utils/pulse_variable_forecaster.py:42-43)). Any changes to `WorldState`'s structure or how variables are accessed could break this module.
- **`run_turn`:** The forecasting logic entirely depends on the behavior of the [`run_turn`](../../simulation_engine/turn_engine.py:0) function to progress the simulation. Changes in `run_turn` directly impact forecast outcomes.
- **Data Type Assumption:** Assumes that variables being forecasted and averaged are numeric or `None`.

## 8. Existing Tests

- Based on the provided project file structure and the contents of the module itself, no dedicated automated test file (e.g., `test_pulse_variable_forecaster.py`) was identified for this module.
- The module can be run via its CLI ([`if __name__ == "__main__":`](../../simulation_engine/utils/pulse_variable_forecaster.py:92)), which allows for manual testing and validation of its core functionality.

## 9. Module Architecture and Flow

1.  **Initialization (CLI):** The [`main()`](../../simulation_engine/utils/pulse_variable_forecaster.py:77) function parses command-line arguments (`--var`, `--horizon`, `--runs`, export paths).
2.  **Simulation ([`simulate_forward()`](../../simulation_engine/utils/pulse_variable_forecaster.py:21)):**
    *   Iterates for the specified number of `runs`.
    *   In each run, a new [`WorldState()`](../../simulation_engine/utils/pulse_variable_forecaster.py:37) is created.
    *   The simulation progresses for the specified number of `steps` (horizon).
    *   In each step, [`run_turn(state)`](../../simulation_engine/utils/pulse_variable_forecaster.py:40) is called to update the state.
    *   The value of the target `variable` is retrieved from `state.variables` and stored.
    *   All trajectories (list of lists) are collected.
3.  **Aggregation:** The average value for each step across all trajectories is calculated ([`simulation_engine/utils/pulse_variable_forecaster.py:50`](../../simulation_engine/utils/pulse_variable_forecaster.py:50)).
4.  **Output Generation:**
    *   **Plotting ([`plot_forecast()`](../../simulation_engine/utils/pulse_variable_forecaster.py:54)):** If requested (or by default if no export path given), trajectories and the mean are plotted using `matplotlib`. The plot can be saved to a file.
    *   **Data Saving ([`save_forecast_data()`](../../simulation_engine/utils/pulse_variable_forecaster.py:71)):** If an export path is provided, the trajectories and average data are saved to a JSON file.

## 10. Naming Conventions

- **Overall:** Adheres well to Python's PEP 8 naming conventions for functions (e.g., [`simulate_forward`](../../simulation_engine/utils/pulse_variable_forecaster.py:21)), variables (e.g., `var_name`, `all_runs`), and the module filename ([`pulse_variable_forecaster.py`](../../simulation_engine/utils/pulse_variable_forecaster.py)).
- **Clarity:** Names are generally clear and descriptive.
- **Consistency:** Naming is consistent within the module.
- **Potential Issues:** No significant issues related to AI-generated naming or deviations from standards were observed. The type check `isinstance(state.variables, dict)` ([`simulation_engine/utils/pulse_variable_forecaster.py:42`](../../simulation_engine/utils/pulse_variable_forecaster.py:42)) is a good defensive programming practice.