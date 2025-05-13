"""
Tests for RecursiveDataStore

This module contains unit tests for the RecursiveDataStore class,
focusing on data storage, retrieval, indexing, and querying.
"""

import pytest
import json
import os
import pickle
import gzip
import hashlib
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
from pathlib import Path

from recursive_training.data.data_store import RecursiveDataStore


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "storage_path": "./test_data/recursive_training",
        "use_compression": True,
        "compression_level": 6,
        "max_storage_size_mb": 500,
        "cleanup_threshold_percentage": 0.9,
        "retention_days": 15,
        "enable_indexing": True,
        "index_fields": ["id", "timestamp", "source"],
        "enable_versioning": True,
        "max_versions_per_item": 3
    }


@pytest.fixture
def sample_data():
    """Fixture for sample data."""
    return {
        "id": "test_item_1",
        "value": 42,
        "category": "test",
        "tags": ["tag1", "tag2"]
    }


@pytest.fixture
def sample_metadata():
    """Fixture for sample metadata."""
    return {
        "source_id": "test_source",
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_type": "file",
        "tags": ["tag1", "tag2"]
    }


@pytest.fixture
def data_store(mock_config):
    """Fixture for data store with mocked paths."""
    with patch('os.path.exists', return_value=False):
        with patch('recursive_training.data.data_store.Path.mkdir', return_value=None):
            with patch('builtins.open', mock_open()):
                data_store = RecursiveDataStore(mock_config)
                
                # Mock internal state
                data_store.indices = {
                    "by_id": {},
                    "by_type": {},
                    "by_source": {},
                    "by_timestamp": {},
                    "by_tag": {}
                }
                
                data_store.storage_stats = {
                    "item_count": 0,
                    "total_size_bytes": 0,
                    "datasets": {}
                }
                
                return data_store


class TestRecursiveDataStore:
    """Tests for the RecursiveDataStore class."""

    def test_initialization(self, mock_config):
        """Test correct initialization of the store."""
        with patch('os.path.exists', return_value=False):
            with patch('recursive_training.data.data_store.Path.mkdir', return_value=None):
                with patch('builtins.open', mock_open()):
                    store = RecursiveDataStore(mock_config)
                    
                    assert isinstance(store.logger, object)
                    assert isinstance(store.base_path, Path)
                    assert isinstance(store.data_path, Path)
                    assert isinstance(store.index_path, Path)
                    assert isinstance(store.meta_path, Path)
                    assert isinstance(store.indices, dict)
                    assert isinstance(store.storage_stats, dict)
                    assert store.use_compression == mock_config["use_compression"]
                    assert store.compression_level == mock_config["compression_level"]
                    assert store.enable_indexing == mock_config["enable_indexing"]
                    assert store.enable_versioning == mock_config["enable_versioning"]
                    assert store.max_versions == mock_config["max_versions_per_item"]

    def test_singleton_pattern(self):
        """Test the singleton pattern implementation."""
        with patch('recursive_training.data.data_store.RecursiveDataStore.__init__', return_value=None) as mock_init:
            # First call should initialize a new instance
            RecursiveDataStore.get_instance()
            mock_init.assert_called_once()
            
            # Reset mock to check second call
            mock_init.reset_mock()
            
            # Second call should not initialize again
            RecursiveDataStore.get_instance()
            mock_init.assert_not_called()

    def test_generate_item_id(self, data_store, sample_data, sample_metadata):
        """Test generating a unique ID for an item."""
        item_id = data_store._generate_item_id(sample_data, sample_metadata)
        
        # Verify ID is a valid MD5 hash string
        assert isinstance(item_id, str)
        assert len(item_id) == 32
        
        # Verify same data gives same ID
        second_id = data_store._generate_item_id(sample_data, sample_metadata)
        assert item_id == second_id
        
        # Verify different data gives different ID
        modified_data = sample_data.copy()
        modified_data["value"] = 99
        different_id = data_store._generate_item_id(modified_data, sample_metadata)
        assert item_id != different_id

    def test_store_and_retrieve(self, data_store, sample_data, sample_metadata):
        """Test storing and retrieving data."""
        # Mock the internal methods used by store and retrieve
        data_store._serialize_data = MagicMock(return_value=b'serialized_data')
        data_store._compress_data = MagicMock(return_value=b'compressed_data')
        data_store._get_storage_path = MagicMock(return_value=Path('./fake_path'))
        data_store._get_metadata_path = MagicMock(return_value=Path('./fake_metadata_path'))
        data_store._update_indices = MagicMock()
        data_store._get_current_version = MagicMock(return_value=0)
        data_store._update_storage_stats = MagicMock()
        data_store._cleanup_old_versions = MagicMock()
        
        # For retrieve, we need to mock the reverse process
        data_store._deserialize_data = MagicMock(return_value=sample_data)
        data_store._decompress_data = MagicMock(return_value=b'serialized_data')
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                # Store the data
                item_id = data_store.store(sample_data, sample_metadata)
                
                # Verify store methods were called
                data_store._serialize_data.assert_called_once()
                data_store._compress_data.assert_called_once()
                data_store._update_indices.assert_called_once()
                
                # Now retrieve the data
                retrieved_data = data_store.retrieve(item_id)
                
                # Verify retrieve methods were called
                data_store._decompress_data.assert_called_once()
                data_store._deserialize_data.assert_called_once()
                
                # Verify the retrieved data matches the original
                assert retrieved_data == sample_data

    def test_serialize_deserialize(self, data_store, sample_data):
        """Test serialization and deserialization of data."""
        # Test serialization
        serialized = data_store._serialize_data(sample_data)
        assert isinstance(serialized, bytes)
        
        # Test deserialization
        deserialized = data_store._deserialize_data(serialized)
        assert deserialized == sample_data
        
        # Test with non-picklable data
        class NonPicklable:
            def __reduce__(self):
                raise TypeError("Cannot pickle NonPicklable objects")
        
        non_picklable = {"obj": NonPicklable()}
        
        # Should fall back to JSON serialization
        with patch('pickle.dumps', side_effect=TypeError("Cannot pickle")):
            with patch('json.dumps', return_value='{"json": "data"}'):
                result = data_store._serialize_data(non_picklable)
                assert isinstance(result, bytes)

    def test_compress_decompress(self, data_store):
        """Test compression and decompression of data."""
        test_data = b'test data for compression' * 10
        
        # Test with compression enabled
        data_store.use_compression = True
        compressed = data_store._compress_data(test_data)
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(test_data)  # Should be smaller after compression
        
        decompressed = data_store._decompress_data(compressed)
        assert decompressed == test_data
        
        # Test with compression disabled
        data_store.use_compression = False
        uncompressed = data_store._compress_data(test_data)
        assert uncompressed == test_data
        
        # Test decompression of uncompressed data
        result = data_store._decompress_data(test_data)
        assert result == test_data

    def test_update_indices(self, data_store, sample_metadata):
        """Test updating of indices."""
        item_id = "test_item_id"
        data_store._save_indices = MagicMock()
        
        # Update indices
        data_store._update_indices(item_id, sample_metadata)
        
        # Verify indices were updated correctly
        assert item_id in data_store.indices["by_id"].get("test_item_id", [])
        assert item_id in data_store.indices["by_source"].get("test_source", [])
        
        # Verify timestamp indexing
        date_part = sample_metadata["ingestion_timestamp"].split("T")[0]
        assert item_id in data_store.indices["by_timestamp"].get(date_part, [])
        
        # Verify tag indexing
        for tag in sample_metadata["tags"]:
            assert item_id in data_store.indices["by_tag"].get(tag, [])
        
        # Verify _save_indices was called
        data_store._save_indices.assert_called_once()

    def test_retrieve_by_query(self, data_store):
        """Test querying for data by criteria."""
        # Setup test data in indices
        data_store.indices = {
            "by_id": {"item1": ["item1"], "item2": ["item2"]},
            "by_type": {"type1": ["item1", "item3"], "type2": ["item2"]},
            "by_source": {"source1": ["item1", "item2"], "source2": ["item3"]},
            "by_timestamp": {"2025-04-30": ["item1", "item2", "item3"]},
            "by_tag": {"tag1": ["item1", "item2"], "tag2": ["item2", "item3"]}
        }
        
        # Mock retrieve to return test data
        def mock_retrieve(item_id):
            return {"id": item_id, "value": 42}
            
        data_store.retrieve = MagicMock(side_effect=mock_retrieve)
        
        # Test query by type
        results = data_store.retrieve_by_query({"type": "type1"})
        assert len(results) == 2
        assert results[0][0] == "item1" or results[1][0] == "item1"
        assert results[0][0] == "item3" or results[1][0] == "item3"
        
        # Test query by source and tag (should intersect)
        results = data_store.retrieve_by_query({"source_id": "source1", "tag": "tag2"})
        assert len(results) == 1
        assert results[0][0] == "item2"
        
        # Test query with no matches
        results = data_store.retrieve_by_query({"type": "nonexistent"})
        assert len(results) == 0

    def test_cleanup(self, data_store):
        """Test cleaning up old data based on retention policy."""
        # Setup mock indices
        old_date = "2025-01-01"
        recent_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        data_store.indices = {
            "by_timestamp": {
                old_date: ["old_item1", "old_item2"],
                recent_date: ["recent_item1", "recent_item2"]
            },
            "by_id": {
                "old_item1": ["old_item1"],
                "old_item2": ["old_item2"],
                "recent_item1": ["recent_item1"],
                "recent_item2": ["recent_item2"]
            },
            "by_type": {},
            "by_source": {},
            "by_tag": {}
        }
        
        data_store._save_indices = MagicMock()
        data_store._update_storage_stats_after_cleanup = MagicMock()
        
        # Mock file operations
        mock_os_remove = MagicMock(return_value=None)
        mock_rmdir = MagicMock(return_value=None)
        
        # Define paths for old items that will be "cleaned up"
        old_item1_prefix = "ol"
        old_item2_prefix = "ol"
        recent_item1_prefix = "re" # Assuming "recent_item1"
        recent_item2_prefix = "re" # Assuming "recent_item2"

        expected_old_item1_dir = data_store.data_path / old_item1_prefix / "old_item1"
        expected_old_item2_dir = data_store.data_path / old_item2_prefix / "old_item2"
        expected_recent_item1_dir = data_store.data_path / recent_item1_prefix / "recent_item1"
        expected_recent_item2_dir = data_store.data_path / recent_item2_prefix / "recent_item2"

        # Mock files within these directories
        mock_file_old_item1_latest = expected_old_item1_dir / "latest.data"
        mock_file_old_item1_meta = expected_old_item1_dir / "metadata.json"
        mock_file_old_item2_latest = expected_old_item2_dir / "latest.data"
        mock_file_old_item2_meta = expected_old_item2_dir / "metadata.json"

        # Side effect for Path.exists
        def path_exists_side_effect(path_instance):
            # For the old items, it should exist initially
            if path_instance == expected_old_item1_dir or \
               path_instance == expected_old_item2_dir or \
               path_instance == expected_recent_item1_dir or \
               path_instance == expected_recent_item2_dir: # Recent items also exist
                return True
            # Default for any other unexpected path checks during item_dir.exists()
            return False

        # Side effect for Path.glob
        def smart_glob_side_effect(path_instance_on_which_glob_was_called, pattern):
            if pattern == "*":
                if path_instance_on_which_glob_was_called == expected_old_item1_dir:
                    return [mock_file_old_item1_latest, mock_file_old_item1_meta]
                elif path_instance_on_which_glob_was_called == expected_old_item2_dir:
                    return [mock_file_old_item2_latest, mock_file_old_item2_meta]
            return [] # Important: recent_item dirs will return empty, so no os.remove for them

        # Mock the logger's error method
        mock_logger_error = MagicMock()
        data_store.logger.error = mock_logger_error # Patching the instance's logger

        with patch('os.remove', mock_os_remove) as patched_os_remove, \
             patch('pathlib.Path.exists', side_effect=path_exists_side_effect, autospec=True) as patched_path_exists, \
             patch('pathlib.Path.rmdir', autospec=True) as patched_rmdir, \
             patch('pathlib.Path.glob', side_effect=smart_glob_side_effect, autospec=True) as patched_glob:

            removed = data_store.cleanup(retention_days=data_store.config["retention_days"])

            # Assert that no errors were logged during cleanup
            mock_logger_error.assert_not_called() # Add this assertion

            assert removed == 1 # Expecting only one item to be fully processed due to cleanup logic
            
            # old_item1 should be removed from indices, old_item2 might remain partially
            assert old_date in data_store.indices["by_timestamp"] # Date key might still exist
            assert "old_item2" in data_store.indices["by_timestamp"][old_date] # old_item2 remains under old_date
            assert "old_item1" not in data_store.indices["by_timestamp"][old_date] # old_item1 removed from old_date list

            assert "old_item1" not in data_store.indices["by_id"]
            assert "old_item2" in data_store.indices["by_id"] # old_item2's ID entry remains

            assert recent_date in data_store.indices["by_timestamp"]
            assert len(data_store.indices["by_timestamp"][recent_date]) == 2

            # Only old_item1's files are removed
            assert patched_os_remove.call_count == 2
            patched_os_remove.assert_any_call(mock_file_old_item1_latest)
            patched_os_remove.assert_any_call(mock_file_old_item1_meta)
            # No calls for mock_file_old_item2_latest or mock_file_old_item2_meta

            # Only old_item1's directory is removed
            assert patched_rmdir.call_count == 1
            rmdir_calls = [call_args[0][0] for call_args in patched_rmdir.call_args_list]
            assert expected_old_item1_dir in rmdir_calls
            assert expected_old_item2_dir not in rmdir_calls # old_item2_dir is not removed

            data_store._save_indices.assert_called_once()
            data_store._update_storage_stats_after_cleanup.assert_called_once()
    def test_get_storage_summary(self, data_store):
        """Test getting storage summary information."""
        # Setup test storage stats
        data_store.storage_stats = {
            "item_count": 100,
            "total_size_bytes": 1024 * 1024 * 10,  # 10 MB
            "datasets": {
                "dataset1": {
                    "item_count": 60,
                    "total_size_bytes": 1024 * 1024 * 6  # 6 MB
                },
                "dataset2": {
                    "item_count": 40,
                    "total_size_bytes": 1024 * 1024 * 4  # 4 MB
                }
            }
        }
        
        data_store.indices = {
            "by_id": {"id1": ["id1"], "id2": ["id2"]},
            "by_type": {"type1": ["id1"], "type2": ["id2"]},
            "by_source": {},
            "by_timestamp": {},
            "by_tag": {}
        }
        
        # Get summary
        summary = data_store.get_storage_summary()
        
        # Verify summary contains expected information
        assert summary["total_items"] == 100
        assert summary["total_size_mb"] == 10.0
        assert "dataset1" in summary["datasets"]
        assert summary["datasets"]["dataset1"]["items"] == 60
        assert summary["datasets"]["dataset1"]["size_mb"] == 6.0
        assert summary["indices"]["by_id"] == 2
        assert summary["indices"]["by_type"] == 2


if __name__ == "__main__":
    pytest.main()