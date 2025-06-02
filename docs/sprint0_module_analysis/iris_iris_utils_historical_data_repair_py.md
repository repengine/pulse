# Analysis of iris/iris_utils/historical_data_repair.py

## Module Intent/Purpose

The primary role of this module is to repair data quality issues in historical time series data. This includes handling missing data through various imputation strategies, correcting anomalies (outliers and errors), reconciling data from multiple sources, and smoothing noisy data. It aims to improve the reliability and usability of historical data for downstream processes.
## Operational Status/Completeness

The module appears to be quite complete in terms of implementing the described data repair functionalities. It provides a comprehensive set of strategies for different data quality issues and includes functions for applying, simulating, reporting on, and managing different versions of repaired data. There are no explicit `TODO` comments or obvious placeholders indicating significant missing features within the provided code.
## Implementation Gaps / Unfinished Next Steps

While the module is functionally rich, one potential implementation gap is noted in comments (lines 2332, 2495 of the original Python file) regarding the `perform_quality_check` function in `historical_data_verification.py`. It suggests that this function needs to be updated to accept a time series directly (`_series` parameter) for evaluating repaired data, implying a dependency on a planned or incomplete modification in the `historical_data_verification` module. The modular design with abstract strategy classes allows for easy addition of new repair strategies in the future.
## Implementation Gaps / Unfinished Next Steps

While the module is functionally rich, one potential implementation gap is noted in comments (lines 2332, 2495 of the original Python file) regarding the `perform_quality_check` function in `historical_data_verification.py`. It suggests that this function needs to be updated to accept a time series directly (`_series` parameter) for evaluating repaired data, implying a dependency on a planned or incomplete modification in the `historical_data_verification` module. The modular design with abstract strategy classes allows for easy addition of new repair strategies in the future.
## Connections & Dependencies

*   **Direct imports from other project modules:**
    *   [`ingestion.iris_utils.historical_data_verification`](iris/iris_utils/historical_data_verification.py) (lines 84-97): Used for loading data, detecting gaps and anomalies, performing quality checks, cross-validating sources, and detecting seasonality.
*   **External library dependencies:**
    *   `copy`
    *   `datetime`
    *   `json`
    *   `logging`
    *   `os`
    *   `uuid`
    *   `abc`
    *   `dataclasses`
    *   `enum`
    *   `pathlib`
    *   `typing`
    *   `numpy`
    *   `pandas`
    *   `scipy.stats`
    *   `scipy.signal`
    *   `scipy.interpolate`
    *   `statsmodels.tsa.arima.model` (optional)
    *   `statsmodels.tsa.statespace.sarimax` (optional)
    *   `statsmodels.nonparametric.smoothers_lowess` (optional)
*   **Interaction with other modules via shared data:**
    *   Interacts heavily with the data storage mechanism managed by `historical_data_verification`, reading processed and multi-source data and writing back repaired data and repair version metadata.
*   **Input/output files:**
    *   Reads JSON data files from the historical data base directory (`HISTORICAL_DATA_BASE_DIR`).
    *   Writes JSON files for repair versions and updated processed data to the historical data base directory.
## Connections & Dependencies

*   **Direct imports from other project modules:**
    *   [`ingestion.iris_utils.historical_data_verification`](iris/iris_utils/historical_data_verification.py) (lines 84-97): Used for loading data, detecting gaps and anomalies, performing quality checks, cross-validating sources, and detecting seasonality.
*   **External library dependencies:**
    *   `copy`
    *   `datetime`
    *   `json`
    *   `logging`
    *   `os`
    *   `uuid`
    *   `abc`
    *   `dataclasses`
    *   `enum`
    *   `pathlib`
    *   `typing`
    *   `numpy`
    *   `pandas`
    *   `scipy.stats`
    *   `scipy.signal`
    *   `scipy.interpolate`
    *   `statsmodels.tsa.arima.model` (optional)
    *   `statsmodels.tsa.statespace.sarimax` (optional)
    *   `statsmodels.nonparametric.smoothers_lowess` (optional)
*   **Interaction with other modules via shared data:**
    *   Interacts heavily with the data storage mechanism managed by `historical_data_verification`, reading processed and multi-source data and writing back repaired data and repair version metadata.
*   **Input/output files:**
    *   Reads JSON data files from the historical data base directory (`HISTORICAL_DATA_BASE_DIR`).
    *   Writes JSON files for repair versions and updated processed data to the historical data base directory.
## Function and Class Example Usages

The module's docstring provides clear examples for key functions:

*   `repair_variable_data("spx_close")`: Repairs data for a specified variable.
*   `simulate_repair("unemployment_rate")`: Simulates repairs without applying them.
*   `get_repair_report("gdp_quarterly")`: Retrieves a report of repairs for a variable.
*   `compare_versions("inflation_rate", "original", "v20230515")`: Compares different versions of a variable's data.

The module defines several classes implementing specific repair strategies, such as:

*   [`ForwardFillStrategy`](iris/iris_utils/historical_data_repair.py:360): Fills gaps with the last valid value.
*   [`LinearInterpolationStrategy`](iris/iris_utils/historical_data_repair.py:460): Fills gaps using linear interpolation.
*   [`MedianFilterStrategy`](iris/iris_utils/historical_data_repair.py:988): Corrects anomalies using a median filter.
*   [`RollingMeanStrategy`](iris/iris_utils/historical_data_repair.py:1260): Smooths data using a rolling mean.
*   [`PrioritizedSourceStrategy`](iris/iris_utils/historical_data_repair.py:1544): Reconciles data by prioritizing sources.

These classes are instantiated and used within the main repair functions based on the selected strategy.
## Function and Class Example Usages

The module's docstring provides clear examples for key functions:

*   `repair_variable_data("spx_close")`: Repairs data for a specified variable.
*   `simulate_repair("unemployment_rate")`: Simulates repairs without applying them.
*   `get_repair_report("gdp_quarterly")`: Retrieves a report of repairs for a variable.
*   `compare_versions("inflation_rate", "original", "v20230515")`: Compares different versions of a variable's data.

The module defines several classes implementing specific repair strategies, such as:

*   [`ForwardFillStrategy`](iris/iris_utils/historical_data_repair.py:360): Fills gaps with the last valid value.
*   [`LinearInterpolationStrategy`](iris/iris_utils/historical_data_repair.py:460): Fills gaps using linear interpolation.
*   [`MedianFilterStrategy`](iris/iris_utils/historical_data_repair.py:988): Corrects anomalies using a median filter.
*   [`RollingMeanStrategy`](iris/iris_utils/historical_data_repair.py:1260): Smooths data using a rolling mean.
*   [`PrioritizedSourceStrategy`](iris/iris_utils/historical_data_repair.py:1544): Reconciles data by prioritizing sources.

These classes are instantiated and used within the main repair functions based on the selected strategy.
## Hardcoding Issues

Several hardcoded values and configurations are present:

*   `REPAIR_VERSION_DIR = "repair_versions"` (line 107): The subdirectory name for storing repair versions.
*   `DEFAULT_REPAIR_STRATEGIES` (lines 110-153): Default repair strategies mapped to variable types.
*   `STRATEGY_THRESHOLDS` (lines 156-165): Thresholds for gap sizes, correlation, and anomaly severity used in strategy selection.
*   Arbitrary minimum data points for certain strategies (e.g., ARIMA, LOESS).
*   Default parameters for strategy classes (e.g., window sizes, polynomial degrees, alpha values, tolerance).
*   Hardcoded ranges for bounded strategies for specific variable types.
*   File naming conventions for saving repair versions and processed data.
## Hardcoding Issues

Several hardcoded values and configurations are present:

*   `REPAIR_VERSION_DIR = "repair_versions"` (line 107): The subdirectory name for storing repair versions.
*   `DEFAULT_REPAIR_STRATEGIES` (lines 110-153): Default repair strategies mapped to variable types.
*   `STRATEGY_THRESHOLDS` (lines 156-165): Thresholds for gap sizes, correlation, and anomaly severity used in strategy selection.
*   Arbitrary minimum data points for certain strategies (e.g., ARIMA, LOESS).
*   Default parameters for strategy classes (e.g., window sizes, polynomial degrees, alpha values, tolerance).
*   Hardcoded ranges for bounded strategies for specific variable types.
*   File naming conventions for saving repair versions and processed data.
## Coupling Points

The module exhibits significant coupling with the `ingestion.iris_utils.historical_data_verification` module, relying heavily on its functions for data loading, quality assessment, and issue detection. It is also coupled with the defined file system structure for storing and retrieving historical data and repair versions.
## Existing Tests

Based on the provided file list, the presence of [`iris/iris_utils/test_historical_data_pipeline.py`](iris/iris_utils/test_historical_data_pipeline.py) suggests that testing for this module and related historical data utilities exists. The extent of test coverage and the specific aspects tested would require examining the content of this test file.
## Module Architecture and Flow

The module is structured around a strategy pattern, with abstract base classes defining the interface for different repair types (gap filling, anomaly correction, smoothing, cross-source reconciliation) and concrete classes implementing specific algorithms. The main functions (`repair_variable_data`, `simulate_repair`) orchestrate the process:

1.  Load data using functions from `historical_data_verification`.
2.  Perform an initial quality check using `historical_data_verification`.
3.  Determine optimal repair strategies based on the quality assessment and variable type.
4.  Apply the selected strategies sequentially to the data.
5.  Perform a post-repair quality check (requires update in `historical_data_verification`).
6.  Save the repaired data and a record of the repair actions as a new version.

The `create_repair_strategy` function acts as a factory to instantiate the appropriate strategy class based on the chosen strategy type.
## Module Architecture and Flow

The module is structured around a strategy pattern, with abstract base classes defining the interface for different repair types (gap filling, anomaly correction, smoothing, cross-source reconciliation) and concrete classes implementing specific algorithms. The main functions (`repair_variable_data`, `simulate_repair`) orchestrate the process:

1.  Load data using functions from `historical_data_verification`.
2.  Perform an initial quality check using `historical_data_verification`.
3.  Determine optimal repair strategies based on the quality assessment and variable type.
4.  Apply the selected strategies sequentially to the data.
5.  Perform a post-repair quality check (requires update in `historical_data_verification`).
6.  Save the repaired data and a record of the repair actions as a new version.

The `create_repair_strategy` function acts as a factory to instantiate the appropriate strategy class based on the chosen strategy type.
## Naming Conventions

The module generally adheres to standard Python naming conventions (PEP 8), using snake_case for functions and variables and PascalCase for classes. Enum members are in uppercase. The naming is descriptive and consistent throughout the module. No obvious AI assumption errors or deviations from standard practices were noted in naming.
## Naming Conventions

The module generally adheres to standard Python naming conventions (PEP 8), using snake_case for functions and variables and PascalCase for classes. Enum members are in uppercase. The naming is descriptive and consistent throughout the module. No obvious AI assumption errors or deviations from standard practices were noted in naming.