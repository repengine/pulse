"""
Script to capture missing variables from Alpha Vantage:
- real_gdp
- inflation
- nonfarm_payroll

This script retrieves at least 5 years of historical data and applies
data cleaning and imputation strategies.
"""

from ingestion.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data,
    save_data_point_incremental,
)
from ingestion.iris_plugins_variable_ingestion.alpha_vantage_plugin import (
    AlphaVantagePlugin,
)
import os
import sys
import logging
import pandas as pd

# Add project root to path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
YEARS_OF_DATA = 5
TARGET_VARIABLES = ["real_gdp", "inflation", "nonfarm_payroll"]


def process_variable_data(variable_name, data):
    """
    Process and clean retrieved data:
    - Convert to pandas DataFrame
    - Sort by date
    - Apply linear interpolation for missing values
    - Apply forward/backward fill for remaining missing values

    Args:
        variable_name: Name of the variable
        data: Raw data from Alpha Vantage API

    Returns:
        Processed pandas DataFrame
    """
    logger.info(f"Processing data for {variable_name}")

    # Extract data from Alpha Vantage response
    if "data" not in data:
        logger.error(f"No data field found in response for {variable_name}")
        return None

    # Create DataFrame from the data
    df = pd.DataFrame(data["data"])

    # Convert date strings to datetime objects
    df["date"] = pd.to_datetime(df["date"])

    # Set date as index
    df = df.set_index("date")

    # Sort by date
    df = df.sort_index()

    # Convert values to float
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Apply linear interpolation
    df["value"] = df["value"].interpolate(method="linear")

    # Apply forward fill followed by backward fill for any remaining NaN values
    df["value"] = df["value"].fillna(method="ffill").fillna(method="bfill")

    logger.info(f"Processed {len(df)} data points for {variable_name}")

    return df


def fetch_and_store_variable(plugin, variable_name, interval="quarterly"):
    """
    Fetch variable data from Alpha Vantage and store it

    Args:
        plugin: Alpha Vantage plugin instance
        variable_name: Name of the variable to fetch
        interval: Data interval (default: quarterly)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Fetching {variable_name} data from Alpha Vantage")

    # Get API endpoint from variable name
    if variable_name == "real_gdp":
        function = "REAL_GDP"
    elif variable_name == "inflation":
        function = "INFLATION"
    elif variable_name == "nonfarm_payroll":
        function = "NONFARM_PAYROLL"
    else:
        logger.error(f"Unknown variable: {variable_name}")
        return False

    # Ensure data directory exists
    ensure_data_directory(f"historical_timeline/{variable_name}", base_dir="data")

    # Create dataset ID
    dataset_id = f"economic_{variable_name}"

    # Set up parameters
    params = {
        "function": function,
        "interval": "quarterly" if function == "REAL_GDP" else "monthly",
    }

    # Save request metadata
    save_request_metadata(
        dataset_id,
        params,
        source_name="alpha_vantage",
        base_dir="data/historical_timeline",
    )

    try:
        # Fetch data from Alpha Vantage
        data = plugin._safe_get(params, dataset_id)

        if not data or "data" not in data:
            logger.error(f"Failed to retrieve data for {variable_name}")
            return False

        # Save raw API response
        save_api_response(
            dataset_id,
            data,
            source_name="alpha_vantage",
            base_dir="data/historical_timeline",
        )

        # Process the data
        processed_df = process_variable_data(variable_name, data)

        if processed_df is None:
            return False

        # Create processed data structure
        processed_data = {
            "variable_name": variable_name,
            "source": "alpha_vantage",
            "values": [],
        }

        # Add values to processed data
        for date_idx, row in processed_df.iterrows():
            date_str = date_idx.isoformat()
            value = float(row["value"])

            # Save individual data point
            save_data_point_incremental(
                dataset_id,
                date_str,
                value,
                variable_name=variable_name,
                source_name="alpha_vantage",
                base_dir="data/historical_timeline",
            )

            # Add to processed data structure
            processed_data["values"].append({"date": date_str, "value": value})

        # Save processed data
        save_processed_data(
            variable_name,
            processed_data,
            source_name="alpha_vantage",
            base_dir="data/historical_timeline",
        )

        logger.info(
            f"Successfully processed and stored {
                len(processed_df)} data points for {variable_name}")
        return True

    except Exception as e:
        logger.error(f"Error processing {variable_name}: {e}")
        return False


def main():
    """Main function to capture the missing variables"""
    logger.info("Starting capture of missing variables")

    # Check for API key
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        logger.error("ALPHA_VANTAGE_KEY environment variable not set")
        return 1

    # Initialize the Alpha Vantage plugin
    plugin = AlphaVantagePlugin()

    # Verify plugin initialization
    if not plugin.enabled:
        logger.error("Alpha Vantage plugin is not enabled")
        return 1

    # Process each target variable
    results = {}
    for variable in TARGET_VARIABLES:
        logger.info(f"Processing {variable}")
        success = fetch_and_store_variable(plugin, variable)
        results[variable] = "Success" if success else "Failed"

    # Print summary
    logger.info("Processing complete. Summary:")
    for variable, status in results.items():
        logger.info(f"  - {variable}: {status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
