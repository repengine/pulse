# Historical Data Repair

This document describes the historical data repair module (`ingestion.iris_utils.historical_data_repair`) and its capabilities for addressing missing data and inconsistencies in historical time series data.

## Introduction

The `historical_data_repair` module provides a systematic approach to improving the quality of historical time series data. It implements various strategies for imputing missing values, correcting anomalies, reconciling data from multiple sources, and smoothing noisy data. A rule-based system automatically selects the most appropriate strategy based on the characteristics of the data and the identified quality issues. The module also includes a data versioning system to track changes and allow for reverting to previous states.

## Missing Data Imputation Strategies

The module supports several strategies for filling gaps in time series data:

-   **Forward Fill (`forward_fill`)**: Propagates the last valid observation forward to fill missing values. Suitable for categorical or slowly changing data.
-   **Backward Fill (`backward_fill`)**: Propagates the next valid observation backward to fill missing values. Useful when the future value is more representative than the past value.
-   **Linear Interpolation (`linear`)**: Fills missing values by drawing a straight line between the nearest valid data points. Appropriate for data with linear trends.
-   **Linear Bounded Interpolation (`linear_bounded`)**: Similar to linear interpolation, but the interpolated values are bounded within a specified range. Useful for variables with natural limits (e.g., percentages).
-   **Polynomial Interpolation (`polynomial`)**: Fits a polynomial of a specified degree to the surrounding data points and uses the polynomial to estimate missing values. Can capture non-linear patterns but may be sensitive to outliers.
-   **Moving Average Imputation (`moving_average`)**: Replaces missing values with the mean of a rolling window of surrounding valid data points. Effective for smoothing noisy data.
-   **Seasonal Interpolation (`seasonal_interpolation`)**: Uses detected seasonal patterns in the data to estimate missing values. Suitable for data with strong seasonality.
-   **ARIMA-based Imputation (`arima`)**: Fits an ARIMA (AutoRegressive Integrated Moving Average) model to the time series and uses the model to predict missing values. Powerful for data with complex temporal dependencies and seasonality (requires `statsmodels`).
-   **Interpolate Round (`interpolate_round`)**: Applies moving average imputation and then rounds the result to the nearest integer. Useful for count data.

## Inconsistency Resolution Strategies

The module provides strategies to address various inconsistencies in the data:

-   **Anomaly Correction**: Identifies and corrects outlier values.
    -   **Median Filter (`median_filter`)**: Replaces anomalous values with the median of a surrounding window. Robust to extreme outliers.
    -   **Winsorize (`winsorize`)**: Caps extreme values at a specified percentile. Limits the impact of outliers without removing them entirely.
    -   **Moving Average Correction (`moving_average_correction`)**: Replaces anomalous values with the moving average of a surrounding window.
    -   **Bounded Correction (`bounded_correction`)**: Enforces predefined minimum and maximum bounds on the data. Corrects values that fall outside the acceptable range.
    -   **Moving Average Round (`moving_average_round`)**: Applies moving average correction and rounds the result to the nearest integer. Useful for correcting anomalous counts.
-   **Cross-Source Reconciliation**: Combines data from multiple sources to produce a more reliable series.
    -   **Prioritized (`prioritized`)**: Selects data points from sources based on a predefined priority order.
    -   **Weighted Average (`weighted_average`)**: Calculates a weighted average of values from available sources, where weights can be based on source quality or correlation.
    -   **Voting (`voting`)**: Uses a voting mechanism where the value with the most agreement among sources (within a tolerance) is selected.
-   **Smoothing Methods**: Reduces noise in the data.
    -   **Rolling Mean (`rolling_mean`)**: Applies a simple moving average filter.
    -   **Exponential Smoothing (`exponential`)**: Applies exponential weighting to past observations.
    -   **Savitzky-Golay Filter (`savitzky_golay`)**: Fits a polynomial to a moving window of data and uses the polynomial to smooth the data. Can preserve features better than simple moving averages.
    -   **LOESS (`loess`)**: Locally Estimated Scatterplot Smoothing. Fits local polynomial regressions to smooth the data (requires `statsmodels`).
    -   **None (`none`)**: No smoothing is applied.
-   **Seasonality-Aware Correction**: Strategies that consider and preserve seasonal patterns during correction.

## Rule-Based Strategy Selection

The module employs a rule-based system to automatically determine the most appropriate repair strategy for a given variable and data issue. The selection is based on:

-   **Variable Characteristics**: The type of variable (e.g., economic, market, temperature) influences the default strategies.
-   **Gap Size and Pattern**: The duration and nature of missing data gaps inform the choice of imputation method.
-   **Surrounding Data Context**: The values and trends of data points around an issue are considered.
-   **Quality Assessment from Phase 4**: Results from the `historical_data_verification` module, such as anomaly severity and seasonality detection, guide the selection process.

The `get_optimal_repair_strategy` function implements this logic, recommending strategies for gap filling, anomaly correction, smoothing, and cross-source reconciliation.

## Configuration Capabilities

The module allows for configuration of repair strategies:

-   **Default Strategies per Variable Type**: The `DEFAULT_REPAIR_STRATEGIES` dictionary defines the default strategies for different variable types. This can be extended or modified.
-   **Configurable Thresholds**: The `STRATEGY_THRESHOLDS` dictionary allows adjusting thresholds used in the rule-based strategy selection (e.g., gap size classifications, correlation thresholds).
-   **Audit Trail**: All modifications made during the repair process are recorded as `RepairAction` objects, providing a detailed audit trail.

## Data Versioning System

A data versioning system is implemented to manage different states of the historical data:

-   **Tracking Versions**: The `save_repair_version` function saves the original data, the repaired data, and the list of applied repair actions as a new version. Each version is assigned a unique ID based on its type and a timestamp.
-   **Reverting to Original**: The `revert_to_original` function allows reverting a variable's processed data back to a previously saved original state.
-   **Comparison Tools**: The `compare_versions` function allows comparing two different versions of a variable to assess the impact of repairs.
-   **Listing Versions**: The `get_all_versions` function provides a list of all saved repair versions for a given variable.

## Command-Line Interface

The following commands have been added to the main Pulse CLI (`main.py`) to interact with the historical data repair module:

-   `python main.py repair <variable_name> [--variable-type <type>] [--skip-smoothing] [--skip-cross-source]`: Addresses identified data quality issues for the specified variable using the determined optimal strategies.
    -   `<variable_name>`: The name of the variable to repair.
    -   `--variable-type`: Optional. Specifies the type of the variable (default: `raw`).
    -   `--skip-smoothing`: Optional flag to skip the smoothing step.
    -   `--skip-cross-source`: Optional flag to skip cross-source reconciliation.
-   `python main.py simulate-repair <variable_name> [--variable-type <type>]`: Previews the repairs that would be made for the specified variable without applying them.
    -   `<variable_name>`: The name of the variable to simulate repairs for.
    -   `--variable-type`: Optional. Specifies the type of the variable (default: `raw`).
-   `python main.py repair-report <variable_name> [--version <version_id>]`: Generates a report of all repairs made for a variable.
    -   `<variable_name>`: The name of the variable.
    -   `--version`: Optional. Specifies a specific version ID for the report (if not provided, the latest repair version is used).
-   `python main.py revert <variable_name> [--version <version_id>]`: Reverts a variable to a previous version.
    -   `<variable_name>`: The name of the variable.
    -   `--version`: Optional. Specifies the version ID to revert to (if not provided, reverts to the original state).
-   `python main.py compare-versions <variable_name> <version_id1> [--version2 <version_id2>]`: Compares two versions of a variable.
    -   `<variable_name>`: The name of the variable.
    -   `<version_id1>`: The ID of the first version to compare.
    -   `--version2`: Optional. The ID of the second version to compare (if not provided, compares `version_id1` to the latest repair version).
-   `python main.py list-versions <variable_name>`: Lists all available repair versions for a variable.
    -   `<variable_name>`: The name of the variable.

## Examples

(Conceptual examples of before/after repairs would be included here, potentially with visualizations or sample data snippets demonstrating the effect of different strategies on various data issues.)

This documentation provides a comprehensive overview of the historical data repair module, enabling users to understand its capabilities and effectively utilize the provided tools and CLI commands.