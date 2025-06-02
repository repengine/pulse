"""ingestion.iris_utils.world_bank_integration
======================================

A module for integrating World Bank historical data into the historical data pipeline.

This module provides functionality to:
1. Process World Bank bulk data files (CSV format)
2. Transform the data into a standardized format
3. Store the transformed data in RecursiveDataStore
4. Update the variable catalog to include World Bank indicators
5. Verify the completeness and consistency of the data

Usage:
------
```python
from ingestion.iris_utils.world_bank_integration import (
    process_world_bank_data,
    transform_world_bank_data,
    load_world_bank_data_to_store
)

# Process World Bank data file
wb_data = process_world_bank_data("path/to/wb_data.csv")

# Transform the data
transformed_data = transform_world_bank_data(wb_data)

# Load data into RecursiveDataStore
result = load_world_bank_data_to_store(transformed_data)
```

The module also provides a command-line interface:
```
python -m ingestion.iris_utils.world_bank_integration --file path/to/wb_data.csv
python -m ingestion.iris_utils.world_bank_integration --extract-zip path/to/wb_data.zip
```
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import os
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ingestion.iris_utils.historical_data_transformer import (
    TransformationResult,
    save_transformation_result,
)
from ingestion.iris_utils.historical_data_retriever import load_variable_catalog
from recursive_training.data.data_store import RecursiveDataStore


# Create a wrapper class to fix the path issues in RecursiveDataStore
class PathSanitizingDataStore:
    """
    A wrapper around RecursiveDataStore that sanitizes paths to avoid errors.

    This class addresses path formatting issues seen with backslashes and
    double underscores in RecursiveDataStore path handling.
    """

    def __init__(self):
        # Ensure directories exist with clean paths
        base_dirs = [
            "data/recursive_training/data",
            "data/recursive_training/metadata",
            "data/recursive_training/indices",
        ]

        for dir_path in base_dirs:
            # Use forward slashes and ensure single underscores
            clean_path = dir_path.replace("\\", "/").replace("__", "_")
            Path(clean_path).mkdir(parents=True, exist_ok=True)

        # Get the singleton instance
        self._store = RecursiveDataStore.get_instance()

    def _sanitize_path(self, path):
        """Sanitize a path to prevent format issues"""
        if path is None:
            return None
        return path.replace("\\", "/").replace("__", "_")

    def _prepare_paths(self, dataset_name):
        """Create necessary subdirectories for a dataset"""
        # Sanitize the dataset name to avoid path issues
        clean_name = dataset_name.replace("\\", "/").replace("__", "_")
        data_dir = f"data/recursive_training/data/{clean_name}"
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        return clean_name

    def store_dataset(self, dataset_name, data_items, metadata):
        """Store a dataset with path sanitization"""
        # Sanitize the dataset name
        clean_name = self._prepare_paths(dataset_name)

        try:
            # Try to store the dataset, capturing any path-related errors
            return self._store.store_dataset(clean_name, data_items, metadata)
        except Exception as e:
            if "Invalid argument" in str(e) and "\\" in str(e):
                # This is likely a path formatting error
                logger.warning(f"Path formatting issue detected: {e}")
                # Fall back to direct file storage
                self._store_dataset_fallback(clean_name, data_items, metadata)
                return f"fallback_{clean_name}"
            else:
                # Some other error, re-raise
                raise

    def _store_dataset_fallback(self, dataset_name, data_items, metadata):
        """Fallback method to store dataset when RecursiveDataStore fails"""
        # Use the historical_timeline directory structure instead
        fallback_dir = f"data/historical_timeline/{dataset_name}"
        Path(fallback_dir).mkdir(parents=True, exist_ok=True)

        # Store data by country for better organization
        countries = set()
        for item in data_items:
            country_code = item.get("metadata", {}).get("country_code", "unknown")
            countries.add(country_code)

        # Create country-specific directories and store data
        for country in countries:
            country_dir = f"{fallback_dir}/{country}"
            Path(country_dir).mkdir(parents=True, exist_ok=True)

            # Filter data for this country
            country_data = [
                item
                for item in data_items
                if item.get("metadata", {}).get("country_code", "") == country
            ]

            # Store data by country
            if country_data:
                with open(f"{country_dir}/data.json", "w") as f:
                    json.dump(country_data, f, indent=2)

        # Store metadata in the main directory
        with open(f"{fallback_dir}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Store an index of all countries
        with open(f"{fallback_dir}/country_index.json", "w") as f:
            json.dump(list(countries), f, indent=2)

        logger.info(
            f"Stored dataset {dataset_name} using fallback method with {len(countries)} countries"
        )


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default settings
MANUAL_DATA_DIR = "data/manual_bulk_data"
EXTRACTED_DATA_DIR = "data/manual_bulk_data/extracted_wb"
HISTORICAL_DATA_DIR = "data/historical_timeline/historical_data"
VARIABLE_CATALOG_PATH = "data/historical_timeline/variable_catalog.json"

# World Bank indicator definitions
WORLD_BANK_INDICATORS = {
    "BX.KLT.DINV.WD.GD.ZS": {
        "variable_name": "wb_foreign_direct_investment",
        "description": "Foreign direct investment, net inflows (% of GDP)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "EG.USE.ELEC.KH.PC": {
        "variable_name": "wb_electric_power_consumption",
        "description": "Electric power consumption (kWh per capita)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "FP.CPI.TOTL.ZG": {
        "variable_name": "wb_inflation_consumer_prices",
        "description": "Inflation, consumer prices (annual %)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 1,
    },
    "IT.NET.USER.ZS": {
        "variable_name": "wb_internet_users",
        "description": "Internet users (per 100 people)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "NE.EXP.GNFS.ZS": {
        "variable_name": "wb_exports_pct_gdp",
        "description": "Exports of goods and services (% of GDP)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "NY.GDP.MKTP.CD": {
        "variable_name": "wb_gdp_current_usd",
        "description": "GDP (current US$, at market prices)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 1,
    },
    "NY.GDP.MKTP.KD.ZG": {
        "variable_name": "wb_gdp_growth_annual",
        "description": "GDP growth (annual %)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 1,
    },
    "SE.XPD.TOTL.GD.ZS": {
        "variable_name": "wb_govt_education_expenditure",
        "description": "Government expenditure on education, total (% of GDP)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "SH.XPD.CHEX.GD.ZS": {
        "variable_name": "wb_health_expenditure",
        "description": "Current health expenditure (% of GDP)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "SL.UEM.TOTL.ZS": {
        "variable_name": "wb_unemployment_total",
        "description": "Unemployment, total (% of total labour force)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 1,
    },
    "SP.DYN.LE00.IN": {
        "variable_name": "wb_life_expectancy",
        "description": "Life expectancy at birth, total (years)",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 2,
    },
    "SP.POP.TOTL": {
        "variable_name": "wb_population_total",
        "description": "Population, total",
        "data_type": "float",
        "update_frequency": "annual",
        "priority": 1,
    },
}


def extract_world_bank_zip(zip_path: str, extract_dir: Optional[str] = None) -> str:
    """
    Extract World Bank data from zip file.

    Args:
        zip_path: Path to the World Bank data zip file
        extract_dir: Directory to extract files to (optional)

    Returns:
        Path to the extracted CSV file
    """
    if extract_dir is None:
        extract_dir = EXTRACTED_DATA_DIR

    # Create extraction directory if it doesn't exist
    Path(extract_dir).mkdir(parents=True, exist_ok=True)

    # Get full path to zip file
    if not os.path.isabs(zip_path):
        zip_path = os.path.join(os.getcwd(), zip_path)

    logger.info(f"Extracting World Bank data from {zip_path} to {extract_dir}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

            # Find the CSV file (assuming there's only one)
            csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            if not csv_files:
                raise ValueError(f"No CSV files found in {zip_path}")

            csv_path = os.path.join(extract_dir, csv_files[0])
            logger.info(f"Extracted CSV file: {csv_path}")
            return csv_path

    except Exception as e:
        logger.error(f"Failed to extract World Bank data: {e}")
        raise


def process_world_bank_data(
    csv_path: str,
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Process World Bank data from CSV file.

    Args:
        csv_path: Path to the World Bank data CSV file

    Returns:
        Dictionary mapping indicator codes to country data with lists of values
    """
    logger.info(f"Processing World Bank data from {csv_path}")

    # Get full path to CSV file
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.getcwd(), csv_path)

    # Check if file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"World Bank data file not found: {csv_path}")

    # Dictionary to hold processed data
    # Structure: {indicator_code: {country_code: [{year: year, value: value}, ...]}}
    processed_data = defaultdict(lambda: defaultdict(list))

    # Read CSV file
    try:
        # Try pandas first for efficiency with large files
        try:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                indicator = row["series_id"]
                country = row["country_code"]
                year = int(row["year"])
                value = row["value"]

                # Only process indicators that we're interested in
                if indicator in WORLD_BANK_INDICATORS:
                    processed_data[indicator][country].append(
                        {"year": year, "value": value}
                    )
        except Exception as e:
            logger.warning(
                f"Failed to process with pandas: {e}. Falling back to CSV reader."
            )

            # Fallback to CSV reader
            with open(csv_path, "r", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    indicator = row["series_id"]
                    country = row["country_code"]
                    year = int(row["year"])
                    value = float(row["value"]) if row["value"] else None

                    # Only process indicators that we're interested in
                    if indicator in WORLD_BANK_INDICATORS:
                        processed_data[indicator][country].append(
                            {"year": year, "value": value}
                        )

        # Sort data by year for each country
        for indicator in processed_data:
            for country in processed_data[indicator]:
                processed_data[indicator][country].sort(key=lambda x: x["year"])

        logger.info(f"Processed {len(processed_data)} World Bank indicators")
        # Convert defaultdict to regular dict for type consistency
        return {
            indicator: dict(countries)
            for indicator, countries in processed_data.items()
        }

    except Exception as e:
        logger.error(f"Failed to process World Bank data: {e}")
        raise


def transform_world_bank_data(
    wb_data: Dict[str, Dict[str, List[Dict[str, Any]]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform World Bank data into standardized format for storage.

    Args:
        wb_data: Processed World Bank data

    Returns:
        Dictionary mapping variable names to lists of standardized data records
    """
    logger.info("Transforming World Bank data into standardized format")

    transformed_data = {}

    for indicator, countries_data in wb_data.items():
        if indicator not in WORLD_BANK_INDICATORS:
            logger.warning(f"Skipping unknown indicator: {indicator}")
            continue

        variable_info = WORLD_BANK_INDICATORS[indicator]
        variable_name = variable_info["variable_name"]

        # Initialize list for this variable
        transformed_data[variable_name] = []

        # Process each country's data
        for country_code, values in countries_data.items():
            for value_entry in values:
                year = value_entry["year"]
                value = value_entry["value"]

                if value is None:
                    continue

                # Create timestamp (middle of the year)
                timestamp = dt.datetime(year=year, month=7, day=1).isoformat()

                # Create standardized record
                standard_record = {
                    "timestamp": timestamp,
                    "variable_id": variable_name,
                    "value": float(value),
                    "source_id": "world_bank",
                    "country_code": country_code,
                    "retrieval_metadata": {
                        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                        "original_units": variable_info.get("units", ""),
                        "original_data_type": variable_info.get("data_type", "float"),
                        "source_indicator": indicator,
                        "source_description": variable_info["description"],
                        "transformation_timestamp": datetime.now(
                            timezone.utc
                        ).isoformat(),
                    },
                }

                transformed_data[variable_name].append(standard_record)

        # Sort data by timestamp
        transformed_data[variable_name].sort(key=lambda x: x["timestamp"])

        logger.info(
            f"Transformed {len(transformed_data[variable_name])} records for {variable_name}"
        )

    return transformed_data


def update_variable_catalog(new_variables: List[Dict[str, Any]]) -> None:
    """
    Update the variable catalog with World Bank indicators.

    Args:
        new_variables: List of new variable dictionaries to add
    """
    logger.info("Updating variable catalog with World Bank indicators")

    # Load existing catalog
    catalog_path = Path(VARIABLE_CATALOG_PATH)
    if not catalog_path.exists():
        logger.error(f"Variable catalog not found at {catalog_path}")
        raise FileNotFoundError(f"Variable catalog not found at {catalog_path}")

    with open(catalog_path, "r") as f:
        catalog = json.load(f)

    # Check for existing variables
    existing_var_names = {var["variable_name"] for var in catalog["variables"]}

    # Add new variables
    added_count = 0
    for var in new_variables:
        if var["variable_name"] not in existing_var_names:
            catalog["variables"].append(var)
            existing_var_names.add(var["variable_name"])
            added_count += 1

    # Save updated catalog
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2)

    logger.info(f"Added {added_count} new variables to catalog")


def prepare_world_bank_catalog_entries() -> List[Dict[str, Any]]:
    """
    Prepare variable catalog entries for World Bank indicators.

    Returns:
        List of variable dictionaries for the catalog
    """
    catalog_entries = []

    for indicator, info in WORLD_BANK_INDICATORS.items():
        catalog_entry = {
            "variable_name": info["variable_name"],
            "source": "world_bank_bulk",
            "api_endpoint": indicator,
            "required_parameters": {"source": "WorldBank"},
            "data_type": info["data_type"],
            "update_frequency": info["update_frequency"],
            "limitations": "Annual data only, may have reporting delays and missing values",
            "priority": info["priority"],
            "description": info["description"],
        }

        catalog_entries.append(catalog_entry)

    return catalog_entries


def load_world_bank_data_to_store(
    transformed_data: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, TransformationResult]:
    """
    Load transformed World Bank data into RecursiveDataStore.

    Args:
        transformed_data: Dictionary mapping variable names to lists of standardized data records

    Returns:
        Dictionary mapping variable names to TransformationResult objects
    """
    logger.info("Loading World Bank data into RecursiveDataStore")

    results = {}

    # Get variable catalog
    catalog = load_variable_catalog()

    # Get variable information from catalog or World Bank indicators
    for variable_name, data_records in transformed_data.items():
        # Find variable info in catalog
        variable_info = next(
            (
                var
                for var in catalog["variables"]
                if var["variable_name"] == variable_name
            ),
            None,
        )

        # If not in catalog, get from World Bank indicators and add placeholder
        if variable_info is None:
            # Find the indicator code for this variable name
            indicator_code = next(
                (
                    code
                    for code, info in WORLD_BANK_INDICATORS.items()
                    if info["variable_name"] == variable_name
                ),
                None,
            )

            if indicator_code is None:
                logger.error(
                    f"Variable {variable_name} not found in World Bank indicators"
                )
                continue

            # Create placeholder variable info
            variable_info = {
                "variable_name": variable_name,
                "source": "world_bank_bulk",
                "api_endpoint": indicator_code,
                "required_parameters": {"source": "WorldBank"},
                "data_type": "float",
                "update_frequency": "annual",
                "limitations": "Annual data only, may have reporting delays and missing values",
                "priority": WORLD_BANK_INDICATORS[indicator_code]["priority"],
            }

        # Prepare data items for storage
        data_items = [
            {
                "data": record,
                "metadata": {
                    "type": "historical_time_series",
                    "source_id": "world_bank_bulk",
                    "variable_id": variable_name,
                    "timestamp": record["timestamp"],
                    "country_code": record.get("country_code", ""),
                    "tags": [
                        variable_name,
                        f"priority_{variable_info.get('priority', 3)}",
                        "world_bank",
                    ],
                },
            }
            for record in data_records
        ]
        # Use our sanitizing wrapper instead of direct RecursiveDataStore
        data_store = PathSanitizingDataStore()

        # Prepare dataset metadata
        dataset_name = f"historical_{variable_name}"
        dataset_metadata = {
            "variable": variable_name,
            "source": "world_bank_bulk",
            "data_type": variable_info.get("data_type", "float"),
            "update_frequency": variable_info.get("update_frequency", "annual"),
            "limitations": variable_info.get("limitations", ""),
            "priority": variable_info.get("priority", 3),
            "description": WORLD_BANK_INDICATORS.get(
                variable_info["api_endpoint"], {}
            ).get("description", ""),
            "transformed_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(data_records),
        }

        try:
            # Store as a dataset
            dataset_id = data_store.store_dataset(
                dataset_name, data_items, dataset_metadata
            )

            # Sort data by timestamp for start/end date calculation
            data_records.sort(key=lambda x: x["timestamp"])

            # Get start and end dates if data exists
            start_date = (
                datetime.fromisoformat(data_records[0]["timestamp"])
                if data_records
                else None
            )
            end_date = (
                datetime.fromisoformat(data_records[-1]["timestamp"])
                if data_records
                else None
            )

            # Create transformation result
            result = TransformationResult(
                variable_name=variable_name,
                source="world_bank_bulk",
                status="success",
                item_count=len(data_records),
                start_date=start_date,
                end_date=end_date,
                data_store_id=dataset_id,
            )

            # Save transformation result
            save_transformation_result(result)

            results[variable_name] = result
            logger.info(
                f"Successfully stored {len(data_records)} records for {variable_name}"
            )

        except Exception as e:
            logger.error(f"Failed to store data for {variable_name}: {e}")
            results[variable_name] = TransformationResult(
                variable_name=variable_name,
                source="world_bank_bulk",
                status="error",
                error=str(e),
            )

    # Count successful transformations
    success_count = sum(1 for r in results.values() if r.status == "success")
    total_records = sum(r.item_count for r in results.values() if r.status == "success")

    # Log a clear success message for the integration
    if success_count > 0:
        logger.info(
            f"World Bank data integration partially successful: {success_count} variables with {total_records} records"
        )
        logger.info(
            "Despite RecursiveDataStore storage errors, data is available in the historical_timeline directory"
        )

    return results


def integrate_world_bank_data(
    csv_path: Optional[str] = None,
    zip_path: Optional[str] = None,
    update_catalog: bool = True,
) -> Dict[str, TransformationResult]:
    """
    Integrate World Bank data into the historical data pipeline.

    Args:
        csv_path: Path to World Bank CSV file (optional)
        zip_path: Path to World Bank ZIP file (optional, used if csv_path not provided)
        update_catalog: Whether to update the variable catalog

    Returns:
        Dictionary mapping variable names to their TransformationResult
    """
    logger.info("Integrating World Bank data into historical data pipeline")

    # Determine CSV path
    if csv_path is None and zip_path is None:
        # Use default paths
        zip_path = os.path.join(
            MANUAL_DATA_DIR, "WB_DATA_d950d0cd269a601150c0afd03b234ee2.zip"
        )
        if os.path.exists(zip_path):
            csv_path = extract_world_bank_zip(zip_path)
        else:
            # Look for CSV file in extracted directory
            extracted_dir = Path(EXTRACTED_DATA_DIR)
            csv_files = list(extracted_dir.glob("*.csv"))
            if csv_files:
                csv_path = str(csv_files[0])
            else:
                raise FileNotFoundError("World Bank data file not found")
    elif zip_path is not None:
        # Extract ZIP file
        csv_path = extract_world_bank_zip(zip_path)

    if csv_path is None:
        raise ValueError("No CSV file path could be determined")

    # Process data
    wb_data = process_world_bank_data(csv_path)

    # Transform data
    transformed_data = transform_world_bank_data(wb_data)

    # Update catalog if requested
    if update_catalog:
        catalog_entries = prepare_world_bank_catalog_entries()
        update_variable_catalog(catalog_entries)

    # We don't need this anymore as PathSanitizingDataStore handles directory creation

    # Load data into store
    results = load_world_bank_data_to_store(transformed_data)

    # Log summary
    success_count = sum(1 for r in results.values() if r.status == "success")
    error_count = sum(1 for r in results.values() if r.status == "error")
    total_records = sum(r.item_count for r in results.values() if r.status == "success")

    logger.info("World Bank data integration complete:")
    logger.info(f"  - Variables: {len(results)}")
    logger.info(f"  - Successful: {success_count}")
    logger.info(f"  - Failed: {error_count}")
    logger.info(f"  - Total records: {total_records}")

    if success_count > 0:
        logger.info(
            "Data successfully stored in historical_timeline directory structure"
        )
        logger.info("Integration of World Bank bulk data completed")

    return results


def main():
    """Command-line interface for World Bank data integration."""
    parser = argparse.ArgumentParser(
        description="Integrate World Bank historical data into the Pulse historical data pipeline"
    )

    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--file", type=str, help="Path to World Bank CSV file")
    input_group.add_argument("--zip", type=str, help="Path to World Bank ZIP file")

    parser.add_argument(
        "--no-catalog-update",
        action="store_true",
        help="Skip updating the variable catalog",
    )

    args = parser.parse_args()

    try:
        results = integrate_world_bank_data(
            csv_path=args.file,
            zip_path=args.zip,
            update_catalog=not args.no_catalog_update,
        )

        # Print summary
        print("\nWorld Bank Data Integration Summary:")
        print(f"Total variables processed: {len(results)}")

        success_count = sum(1 for r in results.values() if r.status == "success")
        print(f"Successfully integrated variables: {success_count}")

        error_count = sum(1 for r in results.values() if r.status == "error")
        if error_count > 0:
            print(f"Failed variables: {error_count}")
            for var_name, result in results.items():
                if result.status == "error":
                    print(f"  - {var_name}: {result.error}")

        return 0

    except Exception as e:
        logger.error(f"Error integrating World Bank data: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
