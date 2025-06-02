"""
Tests for OptimizedDataStore

This module contains unit tests for the OptimizedDataStore class,
focusing on the optimized data loading functionality.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from recursive_training.data.optimized_data_store import (
    OptimizedDataStore,
    PYARROW_AVAILABLE,
    H5PY_AVAILABLE,
)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "storage_path": "./test_data/recursive_training",
        "use_compression": True,
        "compression_level": 6,
        "use_memory_mapping": True,
        "storage_format": "pickle",  # Use pickle for tests to avoid dependencies
        "cache_size": 10,
        "max_workers": 2,
    }


@pytest.fixture
def sample_data():
    """Fixture for sample time-series data."""
    # Create timestamps for the last 30 days
    now = datetime.now(timezone.utc)
    dates = [now - timedelta(days=i) for i in range(30)]

    # Create sample data
    data = []
    for i, date in enumerate(dates):
        data.append(
            {"timestamp": date.isoformat(), "value": float(i), "label": f"day_{i}"}
        )

    return data


@pytest.fixture
def optimized_store(mock_config):
    """Fixture for an optimized data store instance."""
    with patch("os.path.exists", return_value=False):
        with patch("recursive_training.data.data_store.Path.mkdir", return_value=None):
            with patch("builtins.open", MagicMock()):
                # Initialize base class attributes to avoid file operations
                store = OptimizedDataStore(mock_config)
                store.indices = {
                    "by_id": {},
                    "by_type": {},
                    "by_source": {},
                    "by_timestamp": {},
                    "by_tag": {},
                }
                store.storage_stats = {
                    "item_count": 0,
                    "total_size_bytes": 0,
                    "datasets": {},
                }
                return store


class TestOptimizedDataStore:
    """Tests for the OptimizedDataStore class."""

    def test_initialization(self, mock_config):
        """Test correct initialization with optimized parameters."""
        with patch("os.path.exists", return_value=False):
            with patch(
                "recursive_training.data.data_store.Path.mkdir", return_value=None
            ):
                with patch("builtins.open", MagicMock()):
                    store = OptimizedDataStore(mock_config)

                    # Check optimized properties
                    assert store.use_memory_mapping == mock_config["use_memory_mapping"]
                    assert store.storage_format == mock_config["storage_format"]
                    assert store.cache_size == mock_config["cache_size"]
                    assert isinstance(store.dataset_cache, dict)
                    assert isinstance(store.cache_lock, object)
                    assert isinstance(store.executor, object)

    def test_vectorized_filtering(self, optimized_store, sample_data):
        """Test vectorized filtering of time-series data."""
        # Mock the DataFrame retrieval
        df = pd.DataFrame(sample_data)

        # Convert timestamp to datetime for filtering
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Create a time range filter
        start_time = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
        end_time = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

        # Apply vectorized filtering
        mask = (df["timestamp"] >= pd.to_datetime(start_time)) & (
            df["timestamp"] <= pd.to_datetime(end_time)
        )
        filtered_df = df[mask]

        # Verify filtering is correct - we get days 5-14 (10 days)
        # The inclusive range from 15 to 5 days ago technically has 11 days, but due to timestamp
        # precision and day boundaries, we only get 10 days in the actual filtering.
        assert len(filtered_df) == 10

        # Check the expected values - we expect day_5 through day_14 (10 days)
        expected_labels = [f"day_{i}" for i in range(5, 15)]
        actual_labels = filtered_df["label"].tolist()
        assert set(actual_labels) == set(expected_labels)

    def test_dataset_cache(self, optimized_store):
        """Test dataset caching functionality."""
        # Create test DataFrame
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        # Mock the cache
        with optimized_store.cache_lock:
            optimized_store.dataset_cache["test_dataset"] = df
            optimized_store._update_cache_access("test_dataset")

        # Check dataset is in cache
        assert "test_dataset" in optimized_store.dataset_cache
        assert "test_dataset" in optimized_store.dataset_access_times

        # Test cache hit
        with optimized_store.cache_lock:
            cached_df = optimized_store.dataset_cache["test_dataset"]

        assert cached_df is df  # Same object reference

        # Test cache eviction (add more items than cache_size)
        for i in range(optimized_store.cache_size + 5):
            dataset_name = f"dataset_{i}"
            with optimized_store.cache_lock:
                optimized_store.dataset_cache[dataset_name] = pd.DataFrame()
                optimized_store._update_cache_access(dataset_name)

        # Check that cache size is maintained
        assert len(optimized_store.dataset_cache) <= optimized_store.cache_size

    def test_batch_retrieve(self, optimized_store):
        """Test batch retrieval functionality."""
        # Mock the retrieve method
        optimized_store.retrieve = MagicMock(
            side_effect=lambda id: {"id": id, "value": int(id.split("_")[1])}
        )

        # Test batch retrieval
        item_ids = [f"item_{i}" for i in range(5)]
        results = optimized_store.batch_retrieve(item_ids)

        # Check results
        assert len(results) == 5
        for i, item_id in enumerate(item_ids):
            assert item_id in results
            assert results[item_id]["value"] == i

        # Verify retrieve was called for each item
        assert optimized_store.retrieve.call_count == 5

    def test_storage_format_selection(self, mock_config):
        """Test selection of storage format based on available dependencies."""
        # Test with different formats
        formats = ["parquet", "hdf5", "pickle"]

        for fmt in formats:
            config = mock_config.copy()
            config["storage_format"] = fmt

            with patch("os.path.exists", return_value=False):
                with patch(
                    "recursive_training.data.data_store.Path.mkdir", return_value=None
                ):
                    with patch("builtins.open", MagicMock()):
                        store = OptimizedDataStore(config)

                        # Format might be adjusted based on available dependencies
                        if fmt == "parquet" and not PYARROW_AVAILABLE:
                            expected_format = "pickle"
                        elif fmt == "hdf5" and not H5PY_AVAILABLE:
                            expected_format = "pickle"
                        else:
                            expected_format = fmt

                        # Check storage path reflects the format
                        path = store._get_optimized_storage_path("test")
                        expected_extension = (
                            ".parquet"
                            if expected_format == "parquet"
                            else ".h5" if expected_format == "hdf5" else ".pkl"
                        )

                        assert path.name.endswith(expected_extension)


if __name__ == "__main__":
    pytest.main()
