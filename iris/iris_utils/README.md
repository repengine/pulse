# Historical Data Processing for Iris Timeline Project

This directory contains modules for retrieving, transforming, verifying, and repairing historical time series data.

## Overview

The historical data processing modules provide a comprehensive system for working with time series data:

1. **Retrieval**: Fetching data from various sources (APIs, databases, files)
2. **Transformation**: Converting raw data into standardized format
3. **Verification**: Quality checks and anomaly detection
4. **Repair**: Fixing missing data and inconsistencies

## Modules

- `historical_data_retriever.py`: Fetches historical data from various sources
- `historical_data_transformer.py`: Transforms raw data into standardized format
- `historical_data_verification.py`: Performs quality checks and anomaly detection
- `historical_data_repair.py`: Implements strategies for fixing data quality issues
- `cli_historical_data.py`: Command-line interface for all functionality

## Requirements

The full functionality requires the following Python packages:

```
pandas>=1.3.0
numpy>=1.20.0
scipy>=1.7.0
statsmodels>=0.13.0  # For ARIMA, SARIMAX, seasonal decomposition
scikit-learn>=1.0.0  # For isolation forest anomaly detection
matplotlib>=3.4.0    # For visualization
seaborn>=0.11.0      # For enhanced visualization
```

## Usage Examples

### Command Line Interface

```bash
# Retrieve raw historical data
python -m iris.iris_utils.cli_historical_data retrieve --variable spx_close

# Transform and store data
python -m iris.iris_utils.cli_historical_data transform --variable spx_close

# Verify data consistency
python -m iris.iris_utils.cli_historical_data verify --variable spx_close

# Repair data quality issues
python -m iris.iris_utils.cli_historical_data repair --variable spx_close

# Simulate repairs without applying them
python -m iris.iris_utils.cli_historical_data simulate-repair --variable spx_close

# Generate a report of repairs made
python -m iris.iris_utils.cli_historical_data repair-report --variable spx_close
```

### Programmatic Usage

```python
from iris.iris_utils.historical_data_repair import (
    repair_variable_data,
    simulate_repair,
    get_repair_report
)

# Repair data quality issues
result = repair_variable_data("spx_close", variable_type="price")
print(f"Made {result.total_repairs} repairs, quality improved by {result.quality_improvement:.2f}")

# Simulate repairs without applying them
simulation = simulate_repair("unemployment_rate", variable_type="percentage")
print(f"Potential improvements: {simulation.quality_improvement:.2f}")

# Get a report of repairs made
report = get_repair_report("gdp_quarterly")
```

## Data Repair Strategies

The `historical_data_repair.py` module provides multiple strategies for addressing data quality issues:

### Gap Filling Strategies

- **Forward Fill**: Propagate the last valid value forward
- **Backward Fill**: Propagate the next valid value backward
- **Linear Interpolation**: Draw a straight line between valid points
- **Polynomial Interpolation**: Fit a polynomial curve to surrounding data
- **Moving Average**: Use average of surrounding values
- **Seasonal Interpolation**: Use values from similar seasonal positions
- **ARIMA-based**: Use time series forecasting models

### Anomaly Correction Strategies

- **Median Filter**: Replace outliers with the median of surrounding values
- **Winsorizing**: Cap extreme values at specific percentiles
- **Moving Average**: Replace outliers with average of surrounding values
- **Bounded Correction**: Enforce min/max bounds on values

### Smoothing Strategies

- **Rolling Mean**: Replace each value with the mean of a window
- **Exponential Smoothing**: Weight recent values more heavily
- **Savitzky-Golay Filter**: Smooth using polynomial fitting
- **LOESS**: Locally estimated scatterplot smoothing

### Cross-Source Reconciliation Strategies

- **Prioritized Sources**: Use data from higher-priority sources
- **Weighted Average**: Combine sources using weights
- **Voting**: Use the value with the most support across sources