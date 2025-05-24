"""iris.iris_utils.ingestion_persistence
================================================
A reusable persistence module for API data ingestion plugins.

This module provides standardized functions for:
1. Creating and managing data directories
2. Saving request metadata and API responses
3. Storing processed data
4. Supporting different data formats (JSON, CSV, etc.)
5. Masking sensitive information

Usage:
------
```python
from iris.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_to_file,
    save_request_metadata,
    mask_sensitive_data
)

# Create data directory
data_dir = ensure_data_directory("my_api_source")

# Save API request metadata
metadata_file = save_request_metadata(
    "my_dataset",
    {"api_key": "secret", "param1": "value1"}
)

# Save API response
response_file = save_to_file("my_dataset", response_data)

# Save processed data
processed_file = save_to_file(
    "my_dataset_processed",
    processed_data,
    timestamp="2025-01-01T12:00:00"
)
```
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import pathlib
import csv
from typing import Dict, List, Any, Optional, Union, Set

logger = logging.getLogger(__name__)

# Default base directory for API data storage
DEFAULT_BASE_DIR = "data/api_ingestion"

# Common sensitive parameter names to mask
DEFAULT_SENSITIVE_PARAMS: Set[str] = {
    "api_key",
    "key",
    "secret",
    "token",
    "password",
    "auth",
    "apikey",
    "access_token",
    "client_secret",
    "app_secret",
    "private_key",
}


def ensure_data_directory(
    source_name: str, base_dir: Optional[str] = None
) -> pathlib.Path:
    """Ensure the data directory structure exists for storing API data.

    Args:
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
                                  Defaults to 'data/api_ingestion'.

    Returns:
        pathlib.Path: Path to the data directory for this source
    """
    # Create base data directory path
    if not base_dir:
        base_dir = DEFAULT_BASE_DIR

    data_dir = pathlib.Path(base_dir) / source_name

    # Create the directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)

    # Return path to the directory
    return data_dir


def save_to_file(
    dataset_id: str,
    data: Union[Dict, List],
    source_name: str = "default",
    base_dir: Optional[str] = None,
    timestamp: Optional[str] = None,
    file_format: str = "json",
) -> pathlib.Path:
    """Save the data to a file with appropriate naming.

    Args:
        dataset_id (str): The dataset identifier (e.g., 'LBMA/GOLD')
        data (Union[Dict, List]): The data to save
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
        timestamp (str, optional): Timestamp to use in filename. Defaults to current time.
        file_format (str, optional): Format to save the data in. Default is "json".
                                    Supported: "json", "csv".

    Returns:
        pathlib.Path: Path to the saved file
    """
    # Ensure data directory exists
    data_dir = ensure_data_directory(source_name, base_dir)

    # Create dataset-specific directory
    safe_dataset_id = dataset_id.replace("/", "_").replace("\\", "_")
    dataset_dir = data_dir / safe_dataset_id
    dataset_dir.mkdir(exist_ok=True)

    # Generate timestamp if not provided
    if not timestamp:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        # Convert ISO format to filename-friendly format if it's in ISO format
        try:
            timestamp_dt = dt.datetime.fromisoformat(timestamp)
            timestamp = timestamp_dt.strftime("%Y%m%d_%H%M%S")
        except (ValueError, TypeError):
            # Keep the timestamp as is if it's not in ISO format
            pass

    # Determine file extension based on format
    file_ext = f".{file_format}"

    # Create filename
    filename = f"{safe_dataset_id}_{timestamp}{file_ext}"
    file_path = dataset_dir / filename

    # Write data to file
    if file_format == "json":
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    elif file_format == "csv":
        # Handle CSV format - assumes data is a list of dictionaries or a dictionary
        with open(file_path, "w", newline="") as f:
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                # List of dictionaries - use column headers from first item
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            elif isinstance(data, dict):
                # Single dictionary - each key becomes a row
                writer = csv.writer(f)
                writer.writerow(["key", "value"])
                for key, value in data.items():
                    writer.writerow([key, value])
            else:
                # Fallback for other types - convert to string representation
                with open(file_path, "w") as f:
                    f.write(str(data))
    else:
        # For unsupported formats, write as plain text
        with open(file_path, "w") as f:
            f.write(str(data))

    logger.info(f"[{source_name}] Saved data to {file_path}")

    return file_path


def mask_sensitive_data(
    params: Dict[str, Any],
    sensitive_params: Optional[Set[str]] = None,
    mask_char: str = "*",
) -> Dict[str, Any]:
    """Mask sensitive data like API keys in parameter dictionaries.

    Args:
        params (Dict[str, Any]): Parameters dictionary that may contain sensitive info
        sensitive_params (Set[str], optional): Set of parameter names to mask.
                                              Defaults to common sensitive names.
        mask_char (str, optional): Character to use for masking. Defaults to "*".

    Returns:
        Dict[str, Any]: Copy of params with sensitive data masked
    """
    if sensitive_params is None:
        sensitive_params = DEFAULT_SENSITIVE_PARAMS

    # Create a copy to avoid modifying the original
    masked_params = params.copy()

    # Mask any sensitive parameters
    for param_name in sensitive_params:
        if param_name in masked_params and masked_params[param_name]:
            # Preserve first and last character if long enough
            value = str(masked_params[param_name])
            if len(value) > 4:
                masked_params[param_name] = (
                    value[0] + mask_char * (len(value) - 2) + value[-1]
                )
            else:
                masked_params[param_name] = mask_char * 4

    return masked_params


def save_request_metadata(
    dataset_id: str,
    params: Dict[str, Any],
    source_name: str = "default",
    base_dir: Optional[str] = None,
    url: Optional[str] = None,
    additional_metadata: Optional[Dict[str, Any]] = None,
    sensitive_params: Optional[Set[str]] = None,
) -> pathlib.Path:
    """Save the request metadata/configuration to allow resumption if scripts restart.

    Args:
        dataset_id (str): The dataset identifier
        params (Dict[str, Any]): The request parameters (sensitive data will be masked)
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
        url (str, optional): The request URL
        additional_metadata (Dict[str, Any], optional): Additional metadata to include
        sensitive_params (Set[str], optional): Set of parameter names to mask.
                                              Default includes common sensitive params.

    Returns:
        pathlib.Path: Path to the saved metadata file
    """
    # Mask sensitive parameters
    safe_params = mask_sensitive_data(params, sensitive_params)

    # Create metadata object
    metadata = {
        "dataset_id": dataset_id,
        "request_timestamp": dt.datetime.now().isoformat(),
        "params": safe_params,
    }

    # Add URL if provided
    if url:
        metadata["request_url"] = url

    # Add any additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    # Save with standardized name for easy identification
    return save_to_file(
        f"{dataset_id}_request_metadata",
        metadata,
        source_name=source_name,
        base_dir=base_dir,
    )


def save_api_response(
    dataset_id: str,
    response_data: Union[Dict, List, str],
    source_name: str = "default",
    base_dir: Optional[str] = None,
    timestamp: Optional[str] = None,
    file_format: str = "json",
    status_code: Optional[int] = None,
    headers: Optional[Dict] = None,
) -> pathlib.Path:
    """Save the raw API response data.

    Args:
        dataset_id (str): The dataset identifier
        response_data (Union[Dict, List, str]): The raw API response data
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
        timestamp (str, optional): Timestamp to use in filename.
        file_format (str, optional): Format to save the data in. Default is "json".
        status_code (int, optional): HTTP status code from the response
        headers (Dict, optional): HTTP headers from the response

    Returns:
        pathlib.Path: Path to the saved file
    """
    # If response_data is a string (non-JSON), convert it to a dict
    if isinstance(response_data, str):
        response_data = {"raw_content": response_data}

    # Add response metadata if provided
    actual_data = response_data
    if status_code is not None or headers is not None:
        if isinstance(response_data, (dict, list)):
            # Create a new container with metadata
            actual_data = {
                "data": response_data,
                "metadata": {"timestamp": timestamp or dt.datetime.now().isoformat()},
            }

            if status_code is not None:
                actual_data["metadata"]["status_code"] = status_code

            if headers is not None:
                actual_data["metadata"]["headers"] = headers

    # Save the data
    return save_to_file(
        dataset_id,
        actual_data,
        source_name=source_name,
        base_dir=base_dir,
        timestamp=timestamp,
        file_format=file_format,
    )


def save_processed_data(
    dataset_id: str,
    processed_data: Union[Dict, List],
    source_name: str = "default",
    base_dir: Optional[str] = None,
    timestamp: Optional[str] = None,
    file_format: str = "json",
    metadata: Optional[Dict] = None,
) -> pathlib.Path:
    """Save processed data with optional metadata.

    Args:
        dataset_id (str): The dataset identifier
        processed_data (Union[Dict, List]): The processed data
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
        timestamp (str, optional): Timestamp to use in filename.
        file_format (str, optional): Format to save the data in. Default is "json".
        metadata (Dict, optional): Additional metadata to include with the data

    Returns:
        pathlib.Path: Path to the saved file
    """
    # Add the processed suffix to dataset_id if not already present
    if not dataset_id.endswith("_processed"):
        dataset_id = f"{dataset_id}_processed"

    # Add metadata if provided
    if metadata and isinstance(processed_data, dict):
        # Create a copy to avoid modifying the original
        data_to_save = processed_data.copy()
        data_to_save["metadata"] = metadata
    else:
        data_to_save = processed_data

    # Save the data
    return save_to_file(
        dataset_id,
        data_to_save,
        source_name=source_name,
        base_dir=base_dir,
        timestamp=timestamp,
        file_format=file_format,
    )


def find_latest_file(
    dataset_id: str,
    source_name: str = "default",
    base_dir: Optional[str] = None,
    suffix: str = "",
    file_format: str = "json",
) -> Optional[pathlib.Path]:
    """Find the most recent file for a given dataset and source.

    Args:
        dataset_id (str): The dataset identifier
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
        suffix (str, optional): Suffix to filter by (e.g., '_processed')
        file_format (str, optional): File extension to filter by. Default is "json".

    Returns:
        Optional[pathlib.Path]: Path to the most recent file, or None if no files found
    """
    # Ensure data directory exists
    data_dir = ensure_data_directory(source_name, base_dir)

    # Create dataset-specific directory
    safe_dataset_id = dataset_id.replace("/", "_").replace("\\", "_")

    # Add suffix if provided
    if suffix and not safe_dataset_id.endswith(suffix):
        safe_dataset_id = f"{safe_dataset_id}{suffix}"

    dataset_dir = data_dir / safe_dataset_id

    # Return None if directory doesn't exist
    if not dataset_dir.exists():
        return None

    # Find all matching files
    pattern = f"*.{file_format}"
    files = list(dataset_dir.glob(pattern))

    # Return None if no files found
    if not files:
        return None

    # Sort by modification time (newest first)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Return the newest file
    return files[0]


def save_data_point_incremental(
    dataset_id: str,
    timestamp: str,
    value: Any,
    variable_name: Optional[str] = None,
    source_name: str = "default",
    base_dir: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> pathlib.Path:
    """Save a single data point incrementally to a JSONL file as soon as it's ingested.

    This function follows the approach used by HighFrequencyDataStore.store_data_point()
    but is integrated with the ingestion_persistence module's conventions.

    Args:
        dataset_id (str): The dataset identifier
        timestamp (str): The ISO-formatted timestamp for this data point
        value (Any): The value of the data point
        variable_name (str, optional): Optional variable name if different from dataset_id
        source_name (str): Name of the API source (e.g., 'nasdaq', 'alpha_vantage')
        base_dir (str, optional): Base directory for data storage.
        metadata (Dict, optional): Additional metadata to include with the data point

    Returns:
        pathlib.Path: Path to the saved file
    """
    # Ensure data directory exists
    data_dir = ensure_data_directory(source_name, base_dir)

    # Create dataset-specific directory
    safe_dataset_id = dataset_id.replace("/", "_").replace("\\", "_")
    dataset_dir = data_dir / safe_dataset_id
    dataset_dir.mkdir(exist_ok=True)

    # Use the variable_name if provided, otherwise use dataset_id
    actual_var_name = variable_name if variable_name else safe_dataset_id

    # Create a JSONL file path (one file per variable)
    file_path = dataset_dir / f"{actual_var_name}.jsonl"

    # Create the data point
    data_point = {
        "timestamp": timestamp,
        "value": value,
        "metadata": metadata if metadata is not None else {},
    }

    # Append the data point to the JSONL file
    with open(file_path, "a") as f:
        f.write(json.dumps(data_point) + "\n")

    logger.info(f"[{source_name}] Saved incremental data point to {file_path}")

    return file_path
