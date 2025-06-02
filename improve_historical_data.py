"""
Script to improve historical timeline data for retrodiction training by:
1. Extending historical periods to 5 years
2. Focusing on priority variables
3. Implementing data cleaning and imputation strategies
4. Ensuring temporal alignment
"""

import os
import json
import numpy as np
import pandas as pd
import logging
import datetime as dt
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
import sys
from datetime import datetime, date


# Custom JSON encoder to handle pandas Timestamp and other non-serializable objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (pd.Timestamp, datetime, date)):
            return o.isoformat()
        if pd.isna(o):
            return None
        return super().default(o)


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("historical_data_improvement.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Constants
HISTORICAL_TIMELINE_DIR = "data/historical_timeline"
VARIABLE_CATALOG_PATH = f"{HISTORICAL_TIMELINE_DIR}/variable_catalog.json"
VERIFICATION_REPORT_PATH = f"{HISTORICAL_TIMELINE_DIR}/verification_report.json"
TARGET_YEARS = 5  # Target years of historical data

# Priority financial and economic indicators
PRIORITY_VARIABLES = [
    # Market indices
    "spx_close",  # S&P 500
    "vix_close",  # VIX volatility index
    "us_10y_yield",  # US 10-year Treasury yield
    # Economic indicators
    "gdp_growth_annual",  # GDP growth
    "real_gdp",  # Real GDP
    "cpi_yoy",  # CPI year-over-year
    "inflation",  # Inflation
    "unemployment_rate_fred",  # Unemployment rate
    # Commodities
    "gold_futures",  # Gold
    "crude_oil_futures_wti",  # Oil
    "wti_crude_oil_price",  # WTI Oil price
    "brent_crude_oil_price",  # Brent Oil price
    # Additional financial indicators
    "crypto_bitcoin_usd",  # Bitcoin price
    "vanguard_total_stock_market_etf",
    "personal_consumption_expenditures",
    "nonfarm_payroll",
    "total_nonfarm_payroll",
    "federal_debt_total",
]


def load_variable_catalog() -> dict:
    """Load the variable catalog."""
    with open(VARIABLE_CATALOG_PATH, "r") as f:
        return json.load(f)


def load_verification_report() -> dict:
    """Load the current verification report."""
    try:
        with open(VERIFICATION_REPORT_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Verification report not found. Creating a new one.")
        return {
            "verification_timestamp": dt.datetime.now().isoformat(),
            "variables_processed": 0,
            "successful_retrievals": 0,
            "failed_retrievals": 0,
            "variable_reports": {},
            "overall_metrics": {
                "average_completeness": 0,
                "variables_with_gaps": 0,
                "variables_with_anomalies": 0,
            },
        }


def modify_historical_ingestion_plugin():
    """Update the historical ingestion plugin to use 5 years of data."""
    plugin_path = "iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py"

    try:
        with open(plugin_path, "r") as f:
            content = f.read()

        # Replace the RETRODICTION_TIMELINE_YEARS parameter
        modified_content = content.replace(
            "RETRODICTION_TIMELINE_YEARS = 5", "RETRODICTION_TIMELINE_YEARS = 5"
        )

        # If the parameter was 1 year, change it to 5
        modified_content = modified_content.replace(
            "RETRODICTION_TIMELINE_YEARS = 1", "RETRODICTION_TIMELINE_YEARS = 5"
        )

        # Write the updated file
        with open(plugin_path, "w") as f:
            f.write(modified_content)

        logger.info("Updated historical_ingestion_plugin.py to use 5 years of data")
    except Exception as e:
        logger.error(f"Error modifying historical_ingestion_plugin.py: {e}")
        raise


def get_processed_data_path(variable_name: str) -> Optional[str]:
    """Get the most recent processed data file path for a variable."""
    processed_dir = f"{HISTORICAL_TIMELINE_DIR}/historical_ingestion_plugin/{variable_name}_processed"

    if not os.path.exists(processed_dir):
        logger.warning(f"No processed data directory found for {variable_name}")
        return None

    try:
        # Get the most recent processed file
        files = list(Path(processed_dir).glob(f"{variable_name}_processed_*.json"))
        if not files:
            logger.warning(f"No processed data files found for {variable_name}")
            return None

        # Sort by modification time, most recent first
        latest_file = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        return str(latest_file)
    except Exception as e:
        logger.error(f"Error getting processed data path for {variable_name}: {e}")
        return None


def load_processed_data(filepath: str) -> Optional[dict]:
    """Load the processed data from a file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading processed data from {filepath}: {e}")
        return None


def clean_and_impute_data(data: dict) -> dict:
    """
    Clean and impute missing values in the data.

    This function:
    1. Identifies NaN values in the data
    2. Applies imputation strategies
    3. Returns the cleaned data
    """
    if not data or "values" not in data:
        logger.error("Invalid data format for cleaning and imputation")
        return data

    try:
        # Convert to pandas DataFrame for easier manipulation
        df = pd.DataFrame(data["values"])

        # Convert date strings to datetime
        df["date"] = pd.to_datetime(df["date"])

        # Check for missing values
        missing_count = df["value"].isna().sum()
        logger.info(f"Found {missing_count} missing values out of {len(df)} records")

        if missing_count > 0:
            # Sort by date to ensure proper interpolation
            df = df.sort_values("date")

            # Set the date as index for proper time-based interpolation
            df_indexed = df.set_index("date")

            # Interpolate missing values using linear interpolation
            df_indexed["value"] = df_indexed["value"].interpolate(method="linear")

            # If there are still NaN values at the beginning or end, use forward/backward fill
            if df_indexed["value"].isna().any():
                df_indexed["value"] = df_indexed["value"].ffill().bfill()

            # Reset index to get back the date column
            df = df_indexed.reset_index()

            logger.info(
                f"After imputation: {df['value'].isna().sum()} missing values remain"
            )

        # Convert back to the original format
        data["values"] = df.to_dict(orient="records")

        # Update metadata
        if "metadata" not in data:
            data["metadata"] = {}

        if "retrieval_stats" not in data["metadata"]:
            data["metadata"]["retrieval_stats"] = {}

        # Update statistics
        non_nan_values = [
            item["value"] for item in data["values"] if not pd.isna(item["value"])
        ]
        if non_nan_values:
            data["metadata"]["retrieval_stats"].update(
                {
                    "data_point_count": len(data["values"]),
                    "min_value": min(non_nan_values),
                    "max_value": max(non_nan_values),
                    "mean_value": sum(non_nan_values) / len(non_nan_values),
                    "median_value": sorted(non_nan_values)[len(non_nan_values) // 2],
                    "completeness_pct": 100.0
                    * len(non_nan_values)
                    / len(data["values"]),
                    "gaps_count": 0,  # We've filled all gaps
                    "anomalies_count": 0,  # Anomaly detection would go here
                }
            )

        return data
    except Exception as e:
        logger.error(f"Error cleaning and imputing data: {e}")
        return data


def save_processed_data(data: dict, variable_name: str) -> str:
    """Save the processed data to a new file."""
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{HISTORICAL_TIMELINE_DIR}/{variable_name}/transformations"

    # Ensure the directory exists
    os.makedirs(output_dir, exist_ok=True)

    output_path = f"{output_dir}/{timestamp}_transform_result.json"

    try:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, cls=CustomJSONEncoder)

        logger.info(f"Saved transformed data to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving processed data: {e}")
        raise


def visualize_data(data: dict, variable_name: str) -> str:
    """Create a visualization of the data and save it to a file."""
    if not data or "values" not in data:
        logger.error("Invalid data format for visualization")
        return ""

    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(data["values"])
        df["date"] = pd.to_datetime(df["date"])

        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(df["date"], df["value"])
        plt.title(f"{variable_name} - Historical Data")
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.grid(True)

        # Save the plot
        output_dir = f"{HISTORICAL_TIMELINE_DIR}/{variable_name}/visualizations"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{output_dir}/{timestamp}_visualization.png"
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Saved visualization to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error visualizing data: {e}")
        return ""


def update_verification_report(variable_results: Dict[str, Dict[str, Any]]):
    """Update the verification report with the new data."""
    try:
        report = load_verification_report()

        # Update the report with new results
        report["verification_timestamp"] = dt.datetime.now().isoformat()
        report["variables_processed"] = len(variable_results)
        report["successful_retrievals"] = sum(
            1 for v in variable_results.values() if v.get("success", False)
        )
        report["failed_retrievals"] = sum(
            1 for v in variable_results.values() if not v.get("success", False)
        )

        # Update variable reports
        for var_name, var_report in variable_results.items():
            if var_report.get("success", False) and var_report.get("stats"):
                report["variable_reports"][var_name] = {
                    "source": "historical_ingestion_plugin",
                    "data_point_count": var_report["stats"].get("data_point_count", 0),
                    "completeness_pct": var_report["stats"].get("completeness_pct", 0),
                    "min_value": var_report["stats"].get("min_value", 0),
                    "max_value": var_report["stats"].get("max_value", 0),
                    "mean_value": var_report["stats"].get("mean_value", 0),
                    "gaps_detected": var_report["stats"].get("gaps_count", 0) > 0,
                    "anomalies_detected": var_report["stats"].get("anomalies_count", 0)
                    > 0,
                }

        # Update overall metrics
        completeness_values = [
            v.get("completeness_pct", 0) for v in report["variable_reports"].values()
        ]
        report["overall_metrics"]["average_completeness"] = (
            sum(completeness_values) / len(completeness_values)
            if completeness_values
            else 0
        )
        report["overall_metrics"]["variables_with_gaps"] = sum(
            1
            for v in report["variable_reports"].values()
            if v.get("gaps_detected", False)
        )
        report["overall_metrics"]["variables_with_anomalies"] = sum(
            1
            for v in report["variable_reports"].values()
            if v.get("anomalies_detected", False)
        )

        # Save the updated report
        with open(VERIFICATION_REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2, cls=CustomJSONEncoder)

        logger.info(f"Updated verification report at {VERIFICATION_REPORT_PATH}")
    except Exception as e:
        logger.error(f"Error updating verification report: {e}")


def execute_data_ingestion():
    """Execute the historical data ingestion plugin."""
    try:
        # Add the project root to the path
        sys.path.insert(0, os.path.abspath("."))

        # Import the plugin
        from ingestion.iris_plugins_variable_ingestion.historical_ingestion_plugin import (
            historical_ingestion_plugin,
        )

        # Run the plugin
        logger.info("Running historical_ingestion_plugin...")
        historical_data_by_date = historical_ingestion_plugin()

        logger.info(f"Plugin returned data for {len(historical_data_by_date)} dates.")

        # Create raw and processed directories for variables that don't have them
        for variable_name in PRIORITY_VARIABLES:
            # Create directories for this variable
            raw_dir = f"{HISTORICAL_TIMELINE_DIR}/historical_ingestion_plugin/{variable_name}_raw"
            processed_dir = f"{HISTORICAL_TIMELINE_DIR}/historical_ingestion_plugin/{variable_name}_processed"

            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)

            # Create a variable directory if it doesn't exist
            var_dir = f"{HISTORICAL_TIMELINE_DIR}/{variable_name}"
            os.makedirs(var_dir, exist_ok=True)
            os.makedirs(f"{var_dir}/transformations", exist_ok=True)
            os.makedirs(f"{var_dir}/visualizations", exist_ok=True)

            # Extract this variable's data from the historical data
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Check if the variable exists in the registry
            variable_data = []
            for date_signals in historical_data_by_date:
                for signal in date_signals:
                    # Check if we're dealing with a dictionary or a pandas Series or DataFrame
                    if isinstance(signal, dict):
                        signal_name = signal.get("name")
                        if signal_name == variable_name:
                            timestamp_val = signal.get("timestamp")
                            value_val = signal.get("value")

                            # Convert pandas objects to native Python types if needed
                            if isinstance(timestamp_val, pd.Timestamp):
                                timestamp_val = timestamp_val.isoformat()
                            if isinstance(value_val, (pd.Series, pd.DataFrame)):
                                if not value_val.empty:
                                    value_val = value_val.iloc[0]
                                else:
                                    value_val = None

                            variable_data.append(
                                {"date": timestamp_val, "value": value_val}
                            )
                    # Log if we encounter unexpected data formats
                    else:
                        logger.warning(f"Unexpected signal format: {type(signal)}")

            if variable_data:
                # Save raw data
                raw_file = f"{raw_dir}/{variable_name}_raw_{timestamp}.json"
                with open(raw_file, "w") as f:
                    json.dump(
                        {
                            "variable_name": variable_name,
                            "source": "historical_ingestion_plugin",
                            "values": variable_data,
                        },
                        f,
                        indent=2,
                        cls=CustomJSONEncoder,
                    )

                # Find valid dates (non-NaN, non-empty) for start/end date
                valid_dates = []
                for item in variable_data:
                    date_val = item.get("date")
                    if date_val is not None and date_val != "":
                        valid_dates.append(date_val)

                # Find valid values for completeness calculation
                valid_values = 0
                for item in variable_data:
                    value_val = item.get("value")
                    if value_val is not None and not (
                        isinstance(value_val, float) and np.isnan(value_val)
                    ):
                        valid_values += 1

                # Calculate completeness percentage
                total_points = len(variable_data)
                completeness = 0
                if total_points > 0:
                    completeness = 100.0 * valid_values / total_points

                # Save processed data with basic cleaning
                processed_data = {
                    "variable_name": variable_name,
                    "source": "historical_ingestion_plugin",
                    "start_date": min(valid_dates) if valid_dates else None,
                    "end_date": max(valid_dates) if valid_dates else None,
                    "values": variable_data,
                    "metadata": {
                        "retrieval_stats": {
                            "data_point_count": total_points,
                            "completeness_pct": completeness,
                        }
                    },
                }

                processed_file = (
                    f"{processed_dir}/{variable_name}_processed_{timestamp}.json"
                )
                with open(processed_file, "w") as f:
                    json.dump(processed_data, f, indent=2, cls=CustomJSONEncoder)

                logger.info(f"Created raw and processed data files for {variable_name}")

        return True
    except Exception as e:
        logger.error(f"Error executing historical_ingestion_plugin: {e}")
        return False


def process_priority_variables() -> Dict[str, Dict[str, Any]]:
    """Process priority variables and return results."""
    results = {}

    for variable_name in PRIORITY_VARIABLES:
        logger.info(f"Processing {variable_name}...")

        try:
            # Get the processed data path
            processed_path = get_processed_data_path(variable_name)

            if not processed_path:
                logger.warning(f"No processed data found for {variable_name}, skipping")
                results[variable_name] = {
                    "success": False,
                    "error": "No processed data found",
                }
                continue

            # Load the processed data
            data = load_processed_data(processed_path)

            if not data:
                logger.warning(
                    f"Failed to load processed data for {variable_name}, skipping"
                )
                results[variable_name] = {
                    "success": False,
                    "error": "Failed to load processed data",
                }
                continue

            # Clean and impute the data
            cleaned_data = clean_and_impute_data(data)

            # Save the transformed data
            transform_path = save_processed_data(cleaned_data, variable_name)

            # Visualize the data
            viz_path = visualize_data(cleaned_data, variable_name)

            # Record the results
            results[variable_name] = {
                "success": True,
                "processed_path": processed_path,
                "transform_path": transform_path,
                "visualization_path": viz_path,
                "stats": cleaned_data.get("metadata", {}).get("retrieval_stats", {}),
            }

            logger.info(f"Successfully processed {variable_name}")
        except Exception as e:
            logger.error(f"Error processing {variable_name}: {e}")
            results[variable_name] = {"success": False, "error": str(e)}

    return results


def main():
    """Main function to improve historical data."""
    logger.info("Starting historical data improvement process")

    try:
        # 1. Modify the historical ingestion plugin
        modify_historical_ingestion_plugin()

        # 2. Execute the data ingestion
        success = execute_data_ingestion()

        if not success:
            logger.error("Failed to execute data ingestion, aborting")
            return

        # 3. Process priority variables
        results = process_priority_variables()

        # 4. Update the verification report
        update_verification_report(results)

        # 5. Log a summary
        successful = sum(1 for v in results.values() if v.get("success", False))
        logger.info(
            f"Completed historical data improvement: {successful}/{len(results)} variables successfully processed"
        )

    except Exception as e:
        logger.error(f"Error in main process: {e}")


if __name__ == "__main__":
    main()
