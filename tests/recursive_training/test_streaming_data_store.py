"""
Tests for StreamingDataStore

This module contains unit tests for the StreamingDataStore class,
focusing on the streaming data loading functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import pytest

from recursive_training.data.streaming_data_store import (
    StreamingDataStore,
    PYARROW_AVAILABLE,
)
from recursive_training.data.optimized_data_store import OptimizedDataStore


class TestStreamingDataStore(unittest.TestCase):
    """Tests for the StreamingDataStore class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temp directory for test data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Create mock config
        self.mock_config = {
            "storage_path": str(self.temp_path),
            "use_compression": False,
            "chunk_size": 100,
            "prefetch_chunks": 2,
            "max_worker_threads": 2,
        }

        # Create sample DataFrame for testing
        self.sample_df = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=500),
                "value": np.random.randn(500),
                "category": np.random.choice(["A", "B", "C"], size=500),
            }
        )

    def tearDown(self):
        """Clean up after tests."""
        # Close temp directory
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test initialization of StreamingDataStore."""
        store = StreamingDataStore(self.mock_config)

        # Verify key attributes
        self.assertEqual(store.chunk_size, 100)
        self.assertEqual(store.prefetch_chunks, 2)
        self.assertEqual(store.max_worker_threads, 2)

        # Verify paths
        self.assertTrue(os.path.exists(os.path.join(self.temp_path, "streaming")))

    def test_singleton_pattern(self):
        """Test singleton pattern implementation."""
        store1 = StreamingDataStore.get_instance(self.mock_config)
        store2 = StreamingDataStore.get_instance()

        # Both should be the same instance
        self.assertIs(store1, store2)

    @patch("recursive_training.data.streaming_data_store.PYARROW_AVAILABLE", False)
    def test_fallback_to_pandas_when_pyarrow_unavailable(self):
        """Test fallback to pandas-based streaming when PyArrow is unavailable."""
        # The outer patch decorator should cover PYARROW_AVAILABLE for the whole method.
        # If PYARROW_AVAILABLE is False, StreamingDataStore will use pandas fallback.
        store = StreamingDataStore(self.mock_config)
        try:
            # Patch the retrieve_dataset_optimized method to return our sample data
            # This ensures that the underlying OptimizedDataStore's file operations for
            # data retrieval are not actually hit, isolating the test to StreamingDataStore's
            # fallback logic and its interaction with the (mocked) parent.
            with patch.object(
                OptimizedDataStore,
                "retrieve_dataset_optimized",
                return_value=(self.sample_df, {}),
            ):
                # Test streaming - should yield chunks of the sample data
                chunks = list(store.stream_dataset("test_dataset"))

                # Verify correct chunking
                self.assertEqual(len(chunks), 5)  # 500 rows / 100 chunk_size = 5 chunks
                self.assertEqual(len(chunks[0]), 100)

                # Test the streaming_arrow method fallback
                store.logger = MagicMock()  # Add mock logger to catch warnings
                chunks_arrow = list(store.stream_dataset_arrow("test_dataset"))

                # Should still produce 5 chunks
                self.assertEqual(len(chunks_arrow), 5)

                # Verify warning was logged
                store.logger.warning.assert_called_once()
        finally:
            store.close()  # Ensure store resources are released

    @pytest.mark.skipif(not PYARROW_AVAILABLE, reason="PyArrow not available")
    def test_streaming_with_pyarrow(self):
        """Test streaming with PyArrow functionality (when available)."""
        if not PYARROW_AVAILABLE:
            self.skipTest("PyArrow not available")

        store = StreamingDataStore(self.mock_config)

        # Create a test dataset
        _dataset_id = store.store_dataset(
            "test_arrow_dataset",
            [
                {str(k): v for k, v in record.items()}
                for record in self.sample_df.to_dict("records")
            ],
        )

        # Test streaming
        chunks = list(store.stream_dataset("test_arrow_dataset"))

        # Verify correct chunking
        self.assertEqual(len(chunks), 5)  # 500 rows / 100 chunk_size = 5 chunks
        self.assertEqual(len(chunks[0]), 100)

        # Test callback-based streaming
        collected_rows = 0

        def callback(chunk):
            nonlocal collected_rows
            collected_rows += len(chunk)

        # Use the callback-based interface
        store.retrieve_dataset_streaming("test_arrow_dataset", callback)

        # Verify all rows were processed
        self.assertEqual(collected_rows, 500)

    def test_access_pattern_tracking(self):
        """Test access pattern tracking functionality."""
        store = StreamingDataStore(self.mock_config)

        # Simulate a few data accesses
        store._track_access_pattern(
            "test_dataset", "2023-01-01", "2023-01-31", ["value"]
        )
        store._track_access_pattern(
            "test_dataset", "2023-02-01", "2023-02-28", ["value", "category"]
        )

        # Test prediction
        prediction = store._predict_next_access("test_dataset")

        # Should predict the most recent access pattern
        self.assertEqual(prediction["start_time"], "2023-02-01")
        self.assertEqual(prediction["end_time"], "2023-02-28")
        self.assertEqual(prediction["columns"], ["value", "category"])

    def test_preloading(self):
        """Test dataset preloading functionality."""
        store = StreamingDataStore(self.mock_config)

        # Add some access patterns
        store._track_access_pattern("dataset1", "2023-01-01", "2023-01-31", ["value"])
        store._track_access_pattern(
            "dataset2", "2023-02-01", "2023-02-28", ["category"]
        )

        # Mock the prefetch method to track which datasets would be preloaded
        with patch.object(
            store, "_prefetch_data", return_value=pd.DataFrame()
        ) as mock_prefetch:
            # Test preloading
            store.preload_datasets(["dataset1", "dataset2"])

            # Verify prefetch was called with the right arguments
            self.assertEqual(mock_prefetch.call_count, 2)
            # Check the first call
            args1, _ = mock_prefetch.call_args_list[0]
            self.assertEqual(args1[0], "dataset1")
            self.assertEqual(args1[2], "2023-01-01")  # start_time

            # Check the second call
            args2, _ = mock_prefetch.call_args_list[1]
            self.assertEqual(args2[0], "dataset2")
            self.assertEqual(args2[2], "2023-02-01")  # start_time

    def test_streaming_with_filtering(self):
        """Test streaming with time and column filtering."""
        store = StreamingDataStore(self.mock_config)

        # Create a test dataset
        _dataset_id = store.store_dataset(
            "test_filter_dataset",
            [
                {str(k): v for k, v in record.items()}
                for record in self.sample_df.to_dict("records")
            ],
        )

        # Test with time filtering - should get only the data for January
        chunks = list(
            store.stream_dataset(
                "test_filter_dataset",
                start_time="2023-01-01",
                end_time="2023-01-16",  # This should capture first 15 days (15 rows)
            )
        )

        # Calculate total rows in the filtered chunks
        total_rows = sum(len(chunk) for chunk in chunks)
        self.assertEqual(total_rows, 16)  # 16 days from Jan 1 to Jan 16 (inclusive)

        # Test with column filtering
        chunks = list(
            store.stream_dataset(
                "test_filter_dataset",
                columns=["timestamp", "value"],  # Only these two columns
            )
        )

        # Each chunk should have only 2 columns
        self.assertEqual(len(chunks[0].columns), 2)
        self.assertIn("timestamp", chunks[0].columns)
        self.assertIn("value", chunks[0].columns)
        self.assertNotIn("category", chunks[0].columns)

    def test_streaming_store(self):
        """Test storing data from a stream."""
        store = StreamingDataStore(self.mock_config)

        # Create a data generator function
        def data_generator():
            for i in range(300):
                yield {
                    "timestamp": (
                        pd.Timestamp("2023-01-01") + pd.Timedelta(days=i)
                    ).isoformat(),
                    "value": float(np.random.randn()),
                    "category": np.random.choice(["A", "B", "C"]),
                }

        # Store the streaming data with a small batch size to test batching
        _dataset_id = store.store_dataset_streaming(
            "streaming_test_dataset",
            data_generator(),
            batch_size=50,  # Small batch size to ensure multiple batches
        )

        # Retrieve the data to check
        df, metadata = store.retrieve_dataset_optimized("streaming_test_dataset")

        # Should have all 300 records
        self.assertEqual(len(df), 300)

        # Metadata should reflect streaming storage
        self.assertEqual(metadata.get("storage_method"), "streaming")
        self.assertEqual(metadata.get("item_count"), 300)

    def test_close(self):
        """Test proper cleanup when closing the store."""
        store = StreamingDataStore(self.mock_config)

        # Add some test data to the stream buffers and futures
        store.stream_buffers["test"] = MagicMock()
        store.prefetch_futures["test"] = [(0, MagicMock())]

        # Test close method
        store.close()

        # Buffers and futures should be cleared
        self.assertEqual(len(store.stream_buffers), 0)
        self.assertEqual(len(store.prefetch_futures), 0)


if __name__ == "__main__":
    unittest.main()
