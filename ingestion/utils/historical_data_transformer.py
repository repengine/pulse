"""ingestion.iris_utils.historical_data_transformer
============================================

A module for transforming and storing historical data in a standardized format using RecursiveDataStore.

This module provides functionality to:
1. Read raw historical data retrieved in Phase 2
2. Transform it into a standardized schema for time series data
3. Store the transformed data in RecursiveDataStore with appropriate indexing
4. Verify data consistency and correctness
5. Generate summary reports of the transformation and storage process

Usage:
------
```python
from ingestion.iris_utils.historical_data_transformer import (
    transform_and_store_variable,
    transform_and_store_priority_variables,
    verify_transformed_data,
    generate_data_coverage_report
)

# Transform and store data for a specific variable
result = transform_and_store_variable("spx_close")

# Transform and store data for all priority 1 variables
priority_results = transform_and_store_priority_variables(priority=1)

# Verify the consistency of stored data
verification_report = verify_transformed_data("spx_close")

# Generate a coverage report
coverage_report = generate_data_coverage_report()
```

The module also provides a command-line interface:
```
python -m ingestion.iris_utils.historical_data_transformer --variable spx_close
python -m ingestion.iris_utils.historical_data_transformer --priority 1
python -m ingestion.iris_utils.historical_data_transformer --verify spx_close
python -m ingestion.iris_utils.historical_data_transformer --coverage-report
```
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dateutil.parser import parse as parse_date

from ingestion.iris_utils.historical_data_retriever import (
    load_variable_catalog,
    get_priority_variables,
)

# Import RecursiveDataStore
from recursive_training.data.data_store import RecursiveDataStore

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default settings
HISTORICAL_DATA_BASE_DIR = "data/historical_timeline/historical_data"


class DataType(Enum):
    """Enum for data types in the standardized schema."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TIMESTAMP = "timestamp"
    TEXT = "text"
    BOOLEAN = "boolean"


class TransformationResult:
    """Result of a data transformation operation."""

    def __init__(
        self,
        variable_name: str,
        source: str,
        status: str,
        item_count: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        data_store_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.variable_name = variable_name
        self.source = source
        self.status = status
        self.item_count = item_count
        self.start_date = start_date
        self.end_date = end_date
        self.data_store_id = data_store_id
        self.error = error
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "variable_name": self.variable_name,
            "source": self.source,
            "status": self.status,
            "item_count": self.item_count,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "data_store_id": self.data_store_id,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


def get_data_type(value: Any) -> DataType:
    """
    Determine the data type of a value for the standardized schema.

    Args:
        value: The value to check

    Returns:
        DataType enum value
    """
    if isinstance(value, (int, float)) or (
        isinstance(value, str) and value.replace(".", "", 1).isdigit()
    ):
        return DataType.NUMERIC
    elif isinstance(value, (datetime, pd.Timestamp)) or (
        isinstance(value, str) and _is_parsable_date(value)
    ):
        return DataType.TIMESTAMP
    elif isinstance(value, bool) or (
        isinstance(value, str) and value.lower() in ("true", "false")
    ):
        return DataType.BOOLEAN
    elif isinstance(value, str):
        return DataType.TEXT
    else:
        # Default to categorical for other types
        return DataType.CATEGORICAL


def _is_parsable_date(date_string: str) -> bool:
    """
    Check if a string can be parsed as a date.

    Args:
        date_string: String to check

    Returns:
        True if parsable as a date, False otherwise
    """
    try:
        parse_date(date_string)
        return True
    except (ValueError, TypeError):
        return False


def _convert_value(value: Any, data_type: DataType) -> Any:
    """
    Convert a value to the appropriate Python type based on the data type.

    Args:
        value: The value to convert
        data_type: Target data type

    Returns:
        Converted value
    """
    if value is None:
        return None

    try:
        if data_type == DataType.NUMERIC:
            return float(value)
        elif data_type == DataType.TIMESTAMP:
            if isinstance(value, (datetime, pd.Timestamp)):
                return value.isoformat()
            return parse_date(value).isoformat()
        elif data_type == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() == "true"
            return bool(value)
        elif data_type == DataType.TEXT:
            return str(value)
        else:  # CATEGORICAL
            return str(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not convert value {value} to {data_type.name}: {e}")
        return None


def load_raw_historical_data(variable_name: str) -> Optional[Dict[str, Any]]:
    """
    Load raw historical data for a variable from the Phase 2 output.

    Args:
        variable_name: Name of the variable to load data for

    Returns:
        Dictionary containing the raw data or None if not found
    """
    # Load variable information from catalog to get the source name
    catalog = load_variable_catalog()
    variable_info = next(
        (var for var in catalog["variables"] if var["variable_name"] == variable_name),
        None,
    )

    if variable_info is None:
        logger.error(f"Variable {variable_name} not found in the catalog")
        return None

    source_name = variable_info.get("source", "unknown")

    # Construct the path to the processed data directory based on ingestion_persistence structure
    data_dir = Path(f"data/historical_timeline/{source_name}/{variable_name}_processed")

    if not data_dir.exists():
        logger.error(
            f"Processed data directory not found for variable {variable_name} at {data_dir}"
        )
        return None

    # Find the latest processed data file (assuming JSON format as per ingestion_persistence)
    processed_files = list(data_dir.glob("*.json"))

    if not processed_files:
        logger.error(f"No processed data files found in {data_dir}")
        return None

    # Get the most recent file based on modification time
    processed_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_file = processed_files[0]

    try:
        with open(latest_file, "r") as f:
            # ingestion_persistence saves processed data directly as the content
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load data from {latest_file}: {e}")
        return None


def transform_historical_data(
    raw_data: Dict[str, Any], variable_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Transform raw historical data into standardized format, writing to file as we process.

    Args:
        raw_data: Raw data from Phase 2
        variable_info: Variable information from the catalog

    Returns:
        List of dictionaries in standardized schema
    """
    transformed_data = []

    variable_name = variable_info["variable_name"]
    data_type = variable_info.get("data_type", "float")
    source = variable_info["source"]

    # Determine standardized data type
    std_data_type = DataType.NUMERIC if data_type == "float" else DataType.CATEGORICAL

    # Extract the values array from the raw data
    values = raw_data.get("values", [])

    if not values:
        logger.warning(f"No values found in raw data for {variable_name}")
        return transformed_data

    retrieval_timestamp = raw_data.get(
        "ingestion_timestamp", datetime.now(timezone.utc).isoformat()
    )

    # Keep track of how many records we've processed for incremental saving
    processed_count = 0
    save_interval = 50  # Save every 50 records

    # Create a batch directory for this transformation session
    transformation_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    incremental_path = Path(f"data/historical_timeline/{variable_name}/incremental")
    incremental_path.mkdir(parents=True, exist_ok=True)

    # Create standardized entries for each value
    for value_entry in values:
        try:
            # Extract date and value
            date_str = value_entry.get("date")
            value = value_entry.get("value")

            if date_str is None or value is None:
                continue

            # Ensure date is in ISO format
            timestamp = parse_date(date_str).isoformat()

            # Convert value to appropriate type
            converted_value = _convert_value(value, std_data_type)

            if converted_value is None:
                continue

            # Create standardized record
            standard_record = {
                "timestamp": timestamp,
                "variable_id": variable_name,
                "value": converted_value,
                "source_id": source,
                "retrieval_metadata": {
                    "retrieval_timestamp": retrieval_timestamp,
                    "original_units": variable_info.get("units", ""),
                    "original_data_type": data_type,
                    "transformation_timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            transformed_data.append(standard_record)

            # Incremental write to file during processing
            processed_count += 1
            if processed_count % save_interval == 0:
                # Save the current batch to a file
                incremental_file = (
                    incremental_path
                    / f"{variable_name}_incremental_{transformation_timestamp}_{processed_count}.json"
                )
                with open(incremental_file, "w") as f:
                    json.dump(
                        {
                            "variable_name": variable_name,
                            "source": source,
                            "batch_number": processed_count // save_interval,
                            "records_processed": processed_count,
                            "transformation_timestamp": transformation_timestamp,
                            "incremental_data": transformed_data[
                                -save_interval:
                            ],  # Save just the latest batch
                        },
                        f,
                        indent=2,
                    )
                logger.info(
                    f"Incremental transformation save: {processed_count} records processed for {variable_name}"
                )

        except Exception as e:
            logger.warning(f"Could not transform entry for {variable_name}: {e}")

    # Save final batch if there are remaining records
    remaining = processed_count % save_interval
    if remaining > 0:
        incremental_file = (
            incremental_path
            / f"{variable_name}_incremental_{transformation_timestamp}_final.json"
        )
        with open(incremental_file, "w") as f:
            json.dump(
                {
                    "variable_name": variable_name,
                    "source": source,
                    "batch_number": (processed_count // save_interval) + 1,
                    "records_processed": processed_count,
                    "transformation_timestamp": transformation_timestamp,
                    "incremental_data": transformed_data[
                        -remaining:
                    ],  # Save just the remaining batch
                },
                f,
                indent=2,
            )
        logger.info(
            f"Final incremental transformation save: {processed_count} records processed for {variable_name}"
        )

    return transformed_data


def store_transformed_data(
    transformed_data: List[Dict[str, Any]], variable_info: Dict[str, Any]
) -> TransformationResult:
    """
    Store transformed data in RecursiveDataStore.

    Args:
        transformed_data: List of transformed data records
        variable_info: Variable information from the catalog

    Returns:
        TransformationResult object with details of the operation
    """
    variable_name = variable_info["variable_name"]
    source = variable_info["source"]

    if not transformed_data:
        return TransformationResult(
            variable_name=variable_name,
            source=source,
            status="error",
            error="No data to store after transformation",
        )

    try:
        # Get RecursiveDataStore instance
        data_store = RecursiveDataStore.get_instance()

        # Prepare dataset metadata
        dataset_metadata = {
            "variable": variable_name,
            "source": source,
            "data_type": variable_info.get("data_type", "float"),
            "update_frequency": variable_info.get("update_frequency", "daily"),
            "limitations": variable_info.get("limitations", ""),
            "priority": variable_info.get("priority", 3),
            "transformed_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(transformed_data),
        }

        # Sort data by timestamp
        transformed_data.sort(key=lambda x: x["timestamp"])

        # Get start and end dates if data exists
        start_date = (
            parse_date(transformed_data[0]["timestamp"]) if transformed_data else None
        )
        end_date = (
            parse_date(transformed_data[-1]["timestamp"]) if transformed_data else None
        )

        # Prepare data items for storage
        data_items = [
            {
                "data": record,
                "metadata": {
                    "type": "historical_time_series",
                    "source_id": source,
                    "variable_id": variable_name,
                    "timestamp": record["timestamp"],
                    "tags": [
                        variable_name,
                        f"priority_{variable_info.get('priority', 3)}",
                        source,
                    ],
                },
            }
            for record in transformed_data
        ]

        # Store as a dataset
        dataset_id = data_store.store_dataset(
            f"historical_{variable_name}", data_items, dataset_metadata
        )

        logger.info(
            f"Successfully stored {len(transformed_data)} records for {variable_name} with dataset ID {dataset_id}"
        )

        return TransformationResult(
            variable_name=variable_name,
            source=source,
            status="success",
            item_count=len(transformed_data),
            start_date=start_date,
            end_date=end_date,
            data_store_id=dataset_id,
        )

    except Exception as e:
        logger.error(f"Failed to store transformed data for {variable_name}: {e}")
        return TransformationResult(
            variable_name=variable_name, source=source, status="error", error=str(e)
        )


def transform_and_store_variable(variable_name: str) -> TransformationResult:
    """
    Transform and store historical data for a specific variable.

    Args:
        variable_name: Name of the variable to process

    Returns:
        TransformationResult with details of the operation
    """
    logger.info(f"Transforming and storing data for variable {variable_name}")

    # Load variable information from catalog
    catalog = load_variable_catalog()
    variable_info = next(
        (var for var in catalog["variables"] if var["variable_name"] == variable_name),
        None,
    )

    if variable_info is None:
        logger.error(f"Variable {variable_name} not found in the catalog")
        return TransformationResult(
            variable_name=variable_name,
            source="unknown",
            status="error",
            error="Variable not found in catalog",
        )

    # Load raw data
    raw_data = load_raw_historical_data(variable_name)

    if raw_data is None:
        logger.error(f"No raw data found for variable {variable_name}")
        return TransformationResult(
            variable_name=variable_name,
            source=variable_info["source"],
            status="error",
            error="No raw data found",
        )

    # Transform data
    transformed_data = transform_historical_data(raw_data, variable_info)

    if not transformed_data:
        logger.error(f"Transformation produced no data for variable {variable_name}")
        return TransformationResult(
            variable_name=variable_name,
            source=variable_info["source"],
            status="error",
            error="Transformation produced no data",
        )

    # Store transformed data
    result = store_transformed_data(transformed_data, variable_info)

    # Save transformation result
    save_transformation_result(result)

    return result


def transform_and_store_priority_variables(
    priority: int = 1,
) -> Dict[str, TransformationResult]:
    """
    Transform and store historical data for all variables with the specified priority.

    Args:
        priority: Priority level to filter variables by

    Returns:
        Dictionary mapping variable names to their TransformationResult
    """
    priority_vars = get_priority_variables(priority)

    if not priority_vars:
        logger.warning(f"No variables found with priority {priority}")
        return {}

    results = {}

    for var_info in priority_vars:
        try:
            var_name = var_info["variable_name"]
            result = transform_and_store_variable(var_name)
            results[var_name] = result

        except Exception as e:
            logger.error(f"Failed to process variable {var_info['variable_name']}: {e}")
            results[var_info["variable_name"]] = TransformationResult(
                variable_name=var_info["variable_name"],
                source=var_info["source"],
                status="error",
                error=str(e),
            )

    return results


def save_transformation_result(result: TransformationResult) -> None:
    """
    Save transformation result to a file.

    Args:
        result: TransformationResult to save
    """
    result_dir = Path(
        f"data/historical_timeline/{result.variable_name}/transformations"
    )
    result_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    result_path = result_dir / f"{timestamp}_transform_result.json"

    with open(result_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    logger.info(f"Saved transformation result to {result_path}")


def verify_transformed_data(variable_name: str) -> Dict[str, Any]:
    """
    Verify the consistency and correctness of transformed data for a variable.

    Args:
        variable_name: Name of the variable to verify

    Returns:
        Dictionary with verification results
    """
    logger.info(f"Verifying transformed data for variable {variable_name}")

    # Get RecursiveDataStore instance
    data_store = RecursiveDataStore.get_instance()

    # Get the stored dataset
    items, metadata = data_store.retrieve_dataset(f"historical_{variable_name}")

    if not items:
        verification = {
            "variable_name": variable_name,
            "status": "error",
            "error": "No data found in RecursiveDataStore",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    else:
        # Check data types and consistency
        type_errors = []
        non_null_values = []
        timestamps = []

        for item in items:
            # Verify required fields exist
            for field in [
                "timestamp",
                "variable_id",
                "value",
                "source_id",
                "retrieval_metadata",
            ]:
                if field not in item:
                    type_errors.append(f"Missing required field: {field}")

            # Verify timestamp format
            try:
                timestamp = parse_date(item.get("timestamp", ""))
                timestamps.append(timestamp)
            except (ValueError, TypeError):
                type_errors.append(f"Invalid timestamp format: {item.get('timestamp')}")

            # Verify value type
            value = item.get("value")
            if value is not None:
                try:
                    float_value = float(value)
                    non_null_values.append(float_value)
                except (ValueError, TypeError):
                    type_errors.append(f"Non-numeric value: {value}")

        # Calculate verification metrics
        verification = {
            "variable_name": variable_name,
            "status": "success" if not type_errors else "warning",
            "record_count": len(items),
            "data_type_errors": type_errors,
            "error_count": len(type_errors),
            "non_null_count": len(non_null_values),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if non_null_values:
            verification.update(
                {
                    "min_value": min(non_null_values),
                    "max_value": max(non_null_values),
                    "mean_value": sum(non_null_values) / len(non_null_values),
                }
            )

        if timestamps:
            verification.update(
                {
                    "start_date": min(timestamps).isoformat(),
                    "end_date": max(timestamps).isoformat(),
                    "date_range_days": (max(timestamps) - min(timestamps)).days,
                }
            )

    # Save verification result
    result_dir = Path(f"data/historical_timeline/{variable_name}/verifications")
    result_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    result_path = result_dir / f"{timestamp}_verification.json"

    with open(result_path, "w") as f:
        json.dump(verification, f, indent=2)

    logger.info(f"Saved verification result to {result_path}")

    return verification


def generate_data_coverage_report() -> Dict[str, Any]:
    """
    Generate a report on data coverage and completeness across all variables.

    Returns:
        Dictionary with coverage report
    """
    logger.info("Generating data coverage report")

    # Get RecursiveDataStore instance
    data_store = RecursiveDataStore.get_instance()

    # Get all datasets
    datasets = data_store.get_all_datasets()

    # Filter for historical datasets
    historical_datasets = [
        ds for ds in datasets if ds.get("dataset_name", "").startswith("historical_")
    ]

    # Prepare report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_variables": len(historical_datasets),
        "variables_coverage": {},
    }

    for dataset in historical_datasets:
        variable = dataset.get("variable", "unknown")

        # Get the data for this dataset
        items, _ = data_store.retrieve_dataset(
            dataset.get("dataset_name", ""), dataset.get("dataset_id", None)
        )

        # Extract timestamps
        timestamps = []
        values = []
        for item in items:
            try:
                timestamp = parse_date(item.get("timestamp", ""))
                timestamps.append(timestamp)
                values.append(item.get("value"))
            except (ValueError, TypeError):
                continue

        # Calculate coverage metrics
        if timestamps:
            start_date = min(timestamps)
            end_date = max(timestamps)
            date_range = (end_date - start_date).days

            # Calculate days with data
            unique_dates = set(timestamp.date() for timestamp in timestamps)
            days_with_data = len(unique_dates)

            # Calculate completeness ratio
            completeness = (
                (days_with_data / (date_range + 1)) * 100 if date_range > 0 else 100
            )

            # Get non-null values count
            non_null_count = sum(1 for v in values if v is not None)

            report["variables_coverage"][variable] = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "date_range_days": date_range,
                "days_with_data": days_with_data,
                "completeness_pct": completeness,
                "record_count": len(items),
                "non_null_count": non_null_count,
                "source": dataset.get("source", "unknown"),
                "priority": dataset.get("priority", 3),
            }

    # Calculate overall metrics
    if report["variables_coverage"]:
        completeness_values = [
            var["completeness_pct"] for var in report["variables_coverage"].values()
        ]

        report["overall_metrics"] = {
            "average_completeness": sum(completeness_values) / len(completeness_values),
            "min_completeness": min(completeness_values),
            "max_completeness": max(completeness_values),
            "fully_complete_variables": sum(
                1 for v in completeness_values if v >= 99.0
            ),
            "partially_complete_variables": sum(
                1 for v in completeness_values if 80.0 <= v < 99.0
            ),
            "incomplete_variables": sum(1 for v in completeness_values if v < 80.0),
        }

    # Save report
    report_dir = Path("data/historical_timeline/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    report_path = report_dir / f"{timestamp}_coverage_report.json"

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved coverage report to {report_path}")

    return report


def main():
    """Command-line interface for historical data transformation and storage."""
    parser = argparse.ArgumentParser(
        description="Transform and store historical data in standardized format"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--variable", type=str, help="Transform and store a specific variable"
    )
    group.add_argument(
        "--priority",
        type=int,
        help="Transform and store all variables with this priority level",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Transform and store all variables in the catalog",
    )
    group.add_argument(
        "--verify", type=str, help="Verify transformed data for a specific variable"
    )
    group.add_argument(
        "--coverage-report", action="store_true", help="Generate a data coverage report"
    )

    args = parser.parse_args()

    try:
        if args.variable:
            # Transform and store a specific variable
            result = transform_and_store_variable(args.variable)

            if result.status == "success":
                logger.info(
                    f"Successfully transformed and stored {result.item_count} records for {args.variable}"
                )
                logger.info(f"Dataset ID: {result.data_store_id}")
                logger.info(
                    f"Date range: {result.start_date.date() if result.start_date else 'N/A'} to {result.end_date.date() if result.end_date else 'N/A'}"
                )
            else:
                logger.error(
                    f"Failed to transform and store data for {args.variable}: {result.error}"
                )
                return 1

        elif args.priority:
            # Transform and store all variables with specified priority
            results = transform_and_store_priority_variables(args.priority)

            successes = sum(1 for r in results.values() if r.status == "success")
            failures = sum(1 for r in results.values() if r.status != "success")

            logger.info(
                f"Processed {len(results)} variables with priority {args.priority}:"
            )
            logger.info(f"  - Successful: {successes}")
            logger.info(f"  - Failed: {failures}")

            if failures > 0:
                logger.warning(
                    "Some variables failed to process. Check logs for details."
                )

        elif args.all:
            # Transform and store all variables
            catalog = load_variable_catalog()
            results = {}

            for variable_info in catalog["variables"]:
                try:
                    var_name = variable_info["variable_name"]
                    result = transform_and_store_variable(var_name)
                    results[var_name] = result
                except Exception as e:
                    logger.error(
                        f"Failed to process {variable_info['variable_name']}: {e}"
                    )
                    results[variable_info["variable_name"]] = TransformationResult(
                        variable_name=variable_info["variable_name"],
                        source=variable_info["source"],
                        status="error",
                        error=str(e),
                    )

            successes = sum(1 for r in results.values() if r.status == "success")
            failures = sum(1 for r in results.values() if r.status != "success")

            logger.info(f"Processed {len(results)} variables:")
            logger.info(f"  - Successful: {successes}")
            logger.info(f"  - Failed: {failures}")

        elif args.verify:
            # Verify transformed data for a specific variable
            verification = verify_transformed_data(args.verify)

            if verification["status"] == "success":
                logger.info(f"Verification successful for {args.verify}")
                logger.info(f"Record count: {verification['record_count']}")
                if "start_date" in verification:
                    logger.info(
                        f"Date range: {verification['start_date']} to {verification['end_date']} ({verification['date_range_days']} days)"
                    )
            else:
                logger.error(
                    f"Verification failed for {args.verify}: {verification.get('error', '')}"
                )
                if verification.get("error_count", 0) > 0:
                    logger.error(
                        f"Found {verification['error_count']} data type errors"
                    )
                return 1

        elif args.coverage_report:
            # Generate coverage report
            report = generate_data_coverage_report()

            total_vars = report["total_variables"]
            logger.info(f"Generated coverage report for {total_vars} variables")

            if "overall_metrics" in report:
                metrics = report["overall_metrics"]
                logger.info(
                    f"Average completeness: {metrics['average_completeness']:.2f}%"
                )
                logger.info("Variables by completeness:")
                logger.info(
                    f"  - Fully complete (≥99%): {metrics['fully_complete_variables']}"
                )
                logger.info(
                    f"  - Partially complete (80-99%): {metrics['partially_complete_variables']}"
                )
                logger.info(f"  - Incomplete (<80%): {metrics['incomplete_variables']}")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
