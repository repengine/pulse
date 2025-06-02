"""
RecursiveDataStore

Responsible for storing and retrieving data for the recursive training system.
Provides a unified interface for data access with support for versioning,
compression, indexing, and efficient querying.
"""

import json
import logging
import os
import pickle
import gzip
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Tuple,
    Set,
    Iterator,
    Callable,
    cast,
)
from concurrent.futures import ThreadPoolExecutor

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import relevant Pulse components
from engine.pulse_config import PulseConfig


class RecursiveDataStore:
    """
    Unified data storage system for recursive training.

    Features:
    - Hybrid storage approach (optimized for different data types)
    - Versioning with data lineage tracking
    - Compression for efficient storage
    - Indexing for fast retrieval
    - Automatic cleanup based on retention policies
    - Dataset-level metadata

    Designed to work with RecursiveDataIngestionManager and RecursiveFeatureProcessor.
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> "RecursiveDataStore":
        """
        Get or create the singleton instance of RecursiveDataStore.

        Args:
            config: Optional configuration dictionary

        Returns:
            RecursiveDataStore instance
        """
        if cls._instance is None:
            cls._instance = RecursiveDataStore(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RecursiveDataStore.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("RecursiveDataStore")

        self.config = config or {}  # Initialize self.config first

        # Attempt to initialize PulseConfig (Pydantic model from engine.pulse_config)
        # This instance is currently local to __init__ and not stored on self.
        # If it's meant to configure DataStore settings, further integration logic
        # would be needed to extract values from _pulse_config_instance and apply them
        # to self.config or other attributes.
        try:
            _pulse_config_instance = PulseConfig()
            self.logger.info(
                "Successfully instantiated PulseConfig from engine.pulse_config. "
                "Note: This instance is not currently used to override DataStore's own config.")
        except Exception as e:
            self.logger.warning(
                f"Could not initialize PulseConfig from engine.pulse_config: {e}. "
                "DataStore will use its default/provided configuration."
            )
        # self.config (from argument or default {}) is used below for storage_path etc.

        # Set up storage paths
        base_path = self.config.get("storage_path", "./data/recursive_training")
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.index_path = self.base_path / "indices"
        self.meta_path = self.base_path / "metadata"

        # Create directories if they don't exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.meta_path.mkdir(parents=True, exist_ok=True)

        # Load or create indices
        self.indices = self._load_indices()

        # Initialize storage stats
        self.storage_stats: Dict[str, Any] = {
            "item_count": 0,
            "total_size_bytes": 0,
            "datasets": {},
        }

        # Load storage stats
        self._load_storage_stats()

        # Configure storage options
        self.use_compression = self.config.get("use_compression", True)
        self.compression_level = self.config.get("compression_level", 6)
        self.enable_indexing = self.config.get("enable_indexing", True)
        self.enable_versioning = self.config.get("enable_versioning", True)
        self.max_versions = self.config.get("max_versions_per_item", 5)

        # Set up thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _load_indices(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load indices from disk or create new ones.

        Returns:
            Dictionary of index dictionaries
        """
        indices_file = self.index_path / "main_indices.json"
        if os.path.exists(indices_file):
            try:
                with open(indices_file, "r") as f:
                    return cast(Dict[str, Dict[str, List[str]]], json.load(f))
            except Exception as e:
                self.logger.error(f"Failed to load indices, creating new ones: {e}")

        # Default indices
        return {
            "by_id": {},
            "by_type": {},
            "by_source": {},
            "by_timestamp": {},
            "by_tag": {},
        }

    def _save_indices(self) -> None:
        """Save indices to disk."""
        indices_file = self.index_path / "main_indices.json"
        try:
            with open(indices_file, "w") as f:
                json.dump(self.indices, f)
        except Exception as e:
            self.logger.error(f"Failed to save indices: {e}")

    def _load_storage_stats(self) -> None:
        """Load storage statistics from disk."""
        stats_file = self.meta_path / "storage_stats.json"
        if os.path.exists(stats_file):
            try:
                with open(stats_file, "r") as f:
                    self.storage_stats = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load storage stats: {e}")

    def _save_storage_stats(self) -> None:
        """Save storage statistics to disk."""
        stats_file = self.meta_path / "storage_stats.json"
        try:
            with open(stats_file, "w") as f:
                json.dump(self.storage_stats, f)
        except Exception as e:
            self.logger.error(f"Failed to save storage stats: {e}")

    def _generate_item_id(self, data: Any, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a data item.

        Args:
            data: The data to store
            metadata: Metadata for the data

        Returns:
            Unique item ID
        """
        # Create a string representation of the data and metadata
        data_str = str(data)
        metadata_str = json.dumps(metadata, sort_keys=True)
        combined = data_str + metadata_str

        # Hash the combined string
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_storage_path(self, item_id: str, version: Optional[int] = None) -> Path:
        """
        Get the path for storing a data item.

        Args:
            item_id: The item ID
            version: Optional version number

        Returns:
            Path object for the storage location
        """
        # Use first few chars of the ID for directory structure to avoid too many
        # files in one directory
        prefix = item_id[:2]
        item_dir = self.data_path / prefix / item_id
        item_dir.mkdir(parents=True, exist_ok=True)

        if version is not None and self.enable_versioning:
            return item_dir / f"v{version}.data"

        return item_dir / "latest.data"

    def _get_metadata_path(self, item_id: str) -> Path:
        """
        Get the path for storing metadata for a data item.

        Args:
            item_id: The item ID

        Returns:
            Path object for the metadata location
        """
        prefix = item_id[:2]
        item_dir = self.data_path / prefix / item_id
        item_dir.mkdir(parents=True, exist_ok=True)
        return item_dir / "metadata.json"

    def _get_dataset_path(self, dataset_name: str) -> Path:
        """
        Get the path for a named dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Path object for the dataset location
        """
        dataset_dir = self.data_path / "datasets" / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir

    def _update_indices(self, item_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update indices with a new or updated item.

        Args:
            item_id: The item ID
            metadata: Metadata for the item
        """
        if not self.enable_indexing:
            return

        # Update ID index
        if item_id not in self.indices["by_id"]:
            self.indices["by_id"][item_id] = []
        if item_id not in self.indices["by_id"][item_id]:
            self.indices["by_id"][item_id].append(item_id)

        # Update type index
        item_type = metadata.get("type", "unknown")
        if item_type not in self.indices["by_type"]:
            self.indices["by_type"][item_type] = []
        if item_id not in self.indices["by_type"][item_type]:
            self.indices["by_type"][item_type].append(item_id)

        # Update source index
        source = metadata.get("source_id", "unknown")
        if source not in self.indices["by_source"]:
            self.indices["by_source"][source] = []
        if item_id not in self.indices["by_source"][source]:
            self.indices["by_source"][source].append(item_id)

        # Update timestamp index
        timestamp = metadata.get(
            "ingestion_timestamp", datetime.now(timezone.utc).isoformat()
        )
        date_part = timestamp.split("T")[0]
        if date_part not in self.indices["by_timestamp"]:
            self.indices["by_timestamp"][date_part] = []
        if item_id not in self.indices["by_timestamp"][date_part]:
            self.indices["by_timestamp"][date_part].append(item_id)

        # Update tag index
        tags = metadata.get("tags", [])
        for tag in tags:
            if tag not in self.indices["by_tag"]:
                self.indices["by_tag"][tag] = []
            if item_id not in self.indices["by_tag"][tag]:
                self.indices["by_tag"][tag].append(item_id)

        # Save indices
        self._save_indices()

    def _get_current_version(self, item_id: str) -> int:
        """
        Get the current version number for an item.

        Args:
            item_id: The item ID

        Returns:
            Current version number or 0 if item doesn't exist
        """
        prefix = item_id[:2]
        item_dir = self.data_path / prefix / item_id

        if not item_dir.exists():
            return 0

        versions = [
            int(f.name[1:-5])
            for f in item_dir.glob("v*.data")
            if f.name.startswith("v") and f.name.endswith(".data")
        ]

        return max(versions) if versions else 0

    def _compress_data(self, data: bytes) -> bytes:
        """
        Compress binary data.

        Args:
            data: Binary data to compress

        Returns:
            Compressed binary data
        """
        if not self.use_compression:
            return data

        return gzip.compress(data, compresslevel=self.compression_level)

    def _decompress_data(self, data: bytes) -> bytes:
        """
        Decompress binary data.

        Args:
            data: Compressed binary data

        Returns:
            Decompressed binary data
        """
        if not self.use_compression:
            return data

        try:
            return gzip.decompress(data)
        except Exception:
            # If decompression fails, assume data is not compressed
            return data

    def _serialize_data(self, data: Any) -> bytes:
        """
        Serialize data to binary format.

        Args:
            data: Data to serialize

        Returns:
            Serialized binary data
        """
        try:
            return pickle.dumps(data)
        except Exception as e:
            self.logger.error(f"Failed to serialize data: {e}")
            # Fallback to JSON for serialization
            return json.dumps(data).encode()

    def _deserialize_data(self, data: bytes) -> Any:
        """
        Deserialize binary data.

        Args:
            data: Binary data to deserialize

        Returns:
            Deserialized data
        """
        try:
            return pickle.loads(data)
        except Exception:
            # Fallback to JSON for deserialization
            try:
                return json.loads(data.decode())
            except Exception as e:
                self.logger.error(f"Failed to deserialize data: {e}")
                return None

    def store(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store data with metadata.

        Args:
            data: The data to store
            metadata: Optional metadata dictionary

        Returns:
            Item ID of the stored data
        """
        metadata = metadata or {}

        # Add default metadata
        if "ingestion_timestamp" not in metadata:
            metadata["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

        # Generate an ID if not provided
        item_id = metadata.get("id")
        if item_id is None:
            item_id = self._generate_item_id(data, metadata)
            metadata["id"] = item_id

        # Handle versioning
        if self.enable_versioning:
            current_version = self._get_current_version(item_id)
            new_version = current_version + 1
            metadata["version"] = new_version

            # Store the data with version
            data_path = self._get_storage_path(item_id, new_version)
        else:
            # Store the data without version
            data_path = self._get_storage_path(item_id)

        # Serialize and compress the data
        try:
            serialized_data = self._serialize_data(data)
            compressed_data = self._compress_data(serialized_data)

            # Write the data
            with open(data_path, "wb") as f:
                f.write(compressed_data)

            # Write the metadata
            metadata_path = self._get_metadata_path(item_id)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)

            # Update indices
            self._update_indices(item_id, metadata)

            # Store latest version
            if self.enable_versioning:
                latest_path = self._get_storage_path(item_id)
                with open(latest_path, "wb") as f:
                    f.write(compressed_data)

                # Clean up old versions if needed
                if self.max_versions > 0:
                    self._cleanup_old_versions(item_id)

            # Update storage stats
            self._update_storage_stats(item_id, len(compressed_data), metadata)

            return item_id

        except Exception as e:
            self.logger.error(f"Failed to store data: {e}")
            raise

    def _update_storage_stats(
        self, item_id: str, size: int, metadata: Dict[str, Any]
    ) -> None:
        """
        Update storage statistics after storing an item.

        Args:
            item_id: The item ID
            size: Size of the stored item in bytes
            metadata: Metadata for the item
        """
        dataset = metadata.get("dataset", "default")

        if dataset not in self.storage_stats["datasets"]:
            self.storage_stats["datasets"][dataset] = {
                "item_count": 0,
                "total_size_bytes": 0,
            }

        # Update stats
        self.storage_stats["item_count"] += 1
        self.storage_stats["total_size_bytes"] += size
        self.storage_stats["datasets"][dataset]["item_count"] += 1
        self.storage_stats["datasets"][dataset]["total_size_bytes"] += size

        # Save stats
        self._save_storage_stats()

    def _cleanup_old_versions(self, item_id: str) -> None:
        """
        Clean up old versions of an item.

        Args:
            item_id: The item ID
        """
        prefix = item_id[:2]
        item_dir = self.data_path / prefix / item_id

        if not item_dir.exists():
            return

        version_files = [
            (int(f.name[1:-5]), f)
            for f in item_dir.glob("v*.data")
            if f.name.startswith("v") and f.name.endswith(".data")
        ]

        version_files.sort(reverse=True)

        # Keep only the most recent versions
        for version, file_path in version_files[self.max_versions:]:
            try:
                os.remove(file_path)
            except Exception as e:
                self.logger.error(
                    f"Failed to remove old version {version} of {item_id}: {e}"
                )

    def retrieve(self, item_id: str, version: Optional[int] = None) -> Optional[Any]:
        """
        Retrieve data by item ID.

        Args:
            item_id: The item ID
            version: Optional version number

        Returns:
            The retrieved data or None if not found
        """
        try:
            if version is not None and self.enable_versioning:
                data_path = self._get_storage_path(item_id, version)
            else:
                data_path = self._get_storage_path(item_id)

            if not os.path.exists(data_path):
                return None

            with open(data_path, "rb") as f:
                compressed_data = f.read()

            decompressed_data = self._decompress_data(compressed_data)
            return self._deserialize_data(decompressed_data)

        except Exception as e:
            self.logger.error(f"Failed to retrieve data for {item_id}: {e}")
            return None

    def retrieve_metadata(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for an item.

        Args:
            item_id: The item ID

        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self._get_metadata_path(item_id)

        if not os.path.exists(metadata_path):
            return None

        try:
            with open(metadata_path, "r") as f:
                return cast(Dict[str, Any], json.load(f))
        except Exception as e:
            self.logger.error(f"Failed to retrieve metadata for {item_id}: {e}")
            return None

    def retrieve_by_query(self, query: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """
        Retrieve data items matching a query.

        Args:
            query: Dictionary of query parameters

        Returns:
            List of (item_id, data) tuples
        """
        # Use indices to find matching items
        matching_ids = self._find_matching_ids(query)

        # Retrieve the data for each matching ID
        results = []
        for item_id in matching_ids:
            data = self.retrieve(item_id)
            if data is not None:
                results.append((item_id, data))

        return results

    def _find_matching_ids(self, query: Dict[str, Any]) -> List[str]:
        """
        Find item IDs matching a query.

        Args:
            query: Dictionary of query parameters

        Returns:
            List of matching item IDs
        """
        matching_sets = []

        # Process each query parameter
        for key, value in query.items():
            if key == "id" and value in self.indices["by_id"]:
                matching_sets.append(set(self.indices["by_id"][value]))
            elif key == "type" and value in self.indices["by_type"]:
                matching_sets.append(set(self.indices["by_type"][value]))
            elif key == "source_id" and value in self.indices["by_source"]:
                matching_sets.append(set(self.indices["by_source"][value]))
            elif key == "date" and value in self.indices["by_timestamp"]:
                matching_sets.append(set(self.indices["by_timestamp"][value]))
            elif key == "tag" and value in self.indices["by_tag"]:
                matching_sets.append(set(self.indices["by_tag"][value]))

        # Find the intersection of all matching sets
        if not matching_sets:
            return []

        result_set = matching_sets[0]
        for s in matching_sets[1:]:
            result_set = result_set.intersection(s)

        return list(result_set)

    def store_dataset(
        self,
        dataset_name: str,
        data_items: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a named dataset.

        Args:
            dataset_name: Name of the dataset
            data_items: List of data items to store
            metadata: Optional metadata for the dataset

        Returns:
            Dataset ID
        """
        dataset_id = f"dataset_{dataset_name}_{
            datetime.now(
                timezone.utc).strftime('%Y%m%d%H%M%S')}"
        dataset_path = self._get_dataset_path(dataset_name)
        dataset_metadata = metadata or {}
        dataset_metadata.update(
            {
                "dataset_name": dataset_name,
                "dataset_id": dataset_id,
                "item_count": len(data_items),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Store metadata
        metadata_path = dataset_path / f"{dataset_id}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(dataset_metadata, f)

        # Store items with dataset reference
        item_ids = []
        for item in data_items:
            item_metadata = item.get("metadata", {})
            item_metadata["dataset"] = dataset_name
            item_metadata["dataset_id"] = dataset_id

            item_id = self.store(item.get("data"), item_metadata)
            item_ids.append(item_id)

        # Store item IDs
        ids_path = dataset_path / f"{dataset_id}_items.json"
        with open(ids_path, "w") as f:
            json.dump(item_ids, f)

        return dataset_id

    def retrieve_dataset(
        self, dataset_name: str, dataset_id: Optional[str] = None
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Retrieve a dataset.

        Args:
            dataset_name: Name of the dataset
            dataset_id: Optional specific dataset ID

        Returns:
            Tuple of (data_items, metadata)
        """
        dataset_path = self._get_dataset_path(dataset_name)

        if dataset_id is None:
            # Find the latest dataset
            metadata_files = list(dataset_path.glob("*_metadata.json"))
            if not metadata_files:
                return [], {}

            # Sort by modification time (newest first)
            metadata_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            metadata_path = metadata_files[0]
            dataset_id = metadata_path.name.split("_metadata.json")[0]
        else:
            metadata_path = dataset_path / f"{dataset_id}_metadata.json"

        # Load metadata
        if not metadata_path.exists():
            return [], {}

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Load item IDs
        ids_path = dataset_path / f"{dataset_id}_items.json"
        if not ids_path.exists():
            return [], metadata

        with open(ids_path, "r") as f:
            item_ids = json.load(f)

        # Retrieve items
        items = []
        for item_id in item_ids:
            item = self.retrieve(item_id)
            if item is not None:
                items.append(item)

        return items, metadata

    def get_all_datasets(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all datasets.

        Returns:
            List of dataset metadata dictionaries
        """
        datasets_dir = self.data_path / "datasets"
        if not datasets_dir.exists():
            return []

        datasets = []
        for dataset_dir in datasets_dir.iterdir():
            if dataset_dir.is_dir():
                metadata_files = list(dataset_dir.glob("*_metadata.json"))
                for metadata_file in metadata_files:
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                            datasets.append(metadata)
                    except Exception as e:
                        self.logger.error(f"Failed to load dataset metadata: {e}")

        return datasets

    def export_to_dataframe(
        self, query: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Export data to a pandas DataFrame.

        Args:
            query: Optional query dictionary to filter data

        Returns:
            DataFrame containing the data or None if pandas is not available
        """
        if not PANDAS_AVAILABLE:
            self.logger.warning("pandas is not available, cannot export to DataFrame")
            return None

        # Import pandas locally to avoid issues
        import pandas as pd

        data_items = []

        if query:
            results = self.retrieve_by_query(query)
            for item_id, data in results:
                metadata = self.retrieve_metadata(item_id) or {}
                data_items.append({**data, **metadata})
        else:
            # Export all data (be careful with large datasets)
            for prefix_dir in self.data_path.iterdir():
                if prefix_dir.is_dir() and len(prefix_dir.name) == 2:
                    for item_dir in prefix_dir.iterdir():
                        if item_dir.is_dir():
                            item_id = item_dir.name
                            data = self.retrieve(item_id)
                            metadata = self.retrieve_metadata(item_id) or {}

                            if data is not None:
                                data_items.append({**data, **metadata})

        if not data_items:
            return pd.DataFrame()

        return pd.DataFrame(data_items)

    def cleanup(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up old data based on retention policy.

        Args:
            retention_days: Optional override for retention policy

        Returns:
            Number of items removed
        """
        retention = retention_days or self.config.get("retention_days", 30)

        # Handle pandas dependency safely
        if PANDAS_AVAILABLE:
            import pandas as pd

            cutoff_date = datetime.now(timezone.utc) - pd.Timedelta(days=retention)
        else:
            # Fallback without pandas
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention)
        cutoff_str = cutoff_date.isoformat()

        removed_count = 0

        # Iterate through timestamps in the index
        for date_str, item_ids in list(self.indices["by_timestamp"].items()):
            if date_str < cutoff_str.split("T")[0]:
                for item_id in item_ids:
                    try:
                        # Get the item path
                        prefix = item_id[:2]
                        item_dir = self.data_path / prefix / item_id

                        if item_dir.exists():
                            # Remove all files in the directory
                            for file_path in item_dir.glob("*"):
                                os.remove(file_path)

                            # Remove the directory
                            item_dir.rmdir()

                            # Remove from indices
                            for index_name, index_dict in self.indices.items():
                                for key, ids in list(index_dict.items()):
                                    if item_id in ids:
                                        ids.remove(item_id)
                                    if not ids:
                                        del index_dict[key]

                            removed_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to remove item {item_id}: {e}")

        # Save indices after cleanup
        self._save_indices()

        # Update storage stats
        self._update_storage_stats_after_cleanup()

        return removed_count

    def _update_storage_stats_after_cleanup(self) -> None:
        """Update storage statistics after cleanup."""
        # Reset stats
        self.storage_stats = {"item_count": 0, "total_size_bytes": 0, "datasets": {}}

        # Recalculate stats by scanning the data directory
        for prefix_dir in self.data_path.iterdir():
            if prefix_dir.is_dir() and len(prefix_dir.name) == 2:
                for item_dir in prefix_dir.iterdir():
                    if item_dir.is_dir():
                        # Get the metadata
                        metadata_path = item_dir / "metadata.json"
                        if metadata_path.exists():
                            try:
                                with open(metadata_path, "r") as f:
                                    metadata = json.load(f)

                                # Get size of latest data file
                                latest_path = item_dir / "latest.data"
                                if latest_path.exists():
                                    size = latest_path.stat().st_size
                                else:
                                    size = 0

                                # Update stats
                                self.storage_stats["item_count"] += 1
                                self.storage_stats["total_size_bytes"] += size

                                # Update dataset stats
                                dataset = metadata.get("dataset", "default")
                                if dataset not in self.storage_stats["datasets"]:
                                    self.storage_stats["datasets"][dataset] = {
                                        "item_count": 0,
                                        "total_size_bytes": 0,
                                    }
                                self.storage_stats["datasets"][dataset][
                                    "item_count"
                                ] += 1
                                self.storage_stats["datasets"][dataset][
                                    "total_size_bytes"
                                ] += size
                            except Exception as e:
                                self.logger.error(
                                    f"Failed to update storage stats for {item_dir}: {e}")

        # Save updated stats
        self._save_storage_stats()

    def get_storage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of storage usage.

        Returns:
            Dictionary with storage summary information
        """
        return {
            "total_items": self.storage_stats["item_count"],
            "total_size_mb": round(
                self.storage_stats["total_size_bytes"] / (1024 * 1024), 2
            ),
            "datasets": {
                name: {
                    "items": stats["item_count"],
                    "size_mb": round(stats["total_size_bytes"] / (1024 * 1024), 2),
                }
                for name, stats in self.storage_stats["datasets"].items()
            },
            "indices": {name: len(index) for name, index in self.indices.items()},
        }

    def close(self) -> None:
        """Clean up resources when closing the data store."""
        self._save_indices()
        self._save_storage_stats()
        self.executor.shutdown()
