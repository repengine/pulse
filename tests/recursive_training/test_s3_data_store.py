"""
Tests for S3DataStore

This module contains unit tests for the S3DataStore class,
focusing on S3 integration functionality.
"""

import pytest
import pandas as pd
import os
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, ANY

from recursive_training.data.s3_data_store import S3DataStore, BOTO3_AVAILABLE


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "storage_path": "./test_data/recursive_training",
        "use_compression": True,
        "compression_level": 6,
        "use_memory_mapping": True,
        "storage_format": "parquet",
        "cache_size": 10,
        "max_workers": 2,
        "s3_data_bucket": "pulse-retrodiction-data-poc",
        "s3_results_bucket": "pulse-retrodiction-results-poc",
        "s3_prefix": "datasets/",
        "s3_region": "us-east-1",
        "s3_cache_dir": "./test_data/s3_cache"
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
        data.append({
            "timestamp": date.isoformat(),
            "value": float(i),
            "label": f"day_{i}"
        })
    
    return data


@pytest.fixture
def mock_boto3():
    """Mock boto3 module."""
    with patch('recursive_training.data.s3_data_store.boto3') as mock_boto3:
        # Set up mock client and resource
        mock_client = MagicMock()
        mock_resource = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = mock_resource
        
        # Make BOTO3_AVAILABLE return True for testing
        with patch('recursive_training.data.s3_data_store.BOTO3_AVAILABLE', True):
            yield mock_boto3


@pytest.fixture
def s3_store(mock_config, mock_boto3):
    """Fixture for an S3 data store instance."""
    with patch('os.path.exists', return_value=False):
        with patch('recursive_training.data.data_store.Path.mkdir', return_value=None):
            with patch('builtins.open', MagicMock()):
                # Initialize store with mocked components
                store = S3DataStore(mock_config)
                
                # Mock base class indices to avoid file operations
                store.indices = {
                    "by_id": {},
                    "by_type": {},
                    "by_source": {},
                    "by_timestamp": {},
                    "by_tag": {}
                }
                
                store.storage_stats = {
                    "item_count": 0,
                    "total_size_bytes": 0,
                    "datasets": {}
                }
                
                # Mock cache operations
                store._is_in_cache = MagicMock(return_value=False)
                
                yield store


class TestS3DataStore:
    """Tests for the S3DataStore class."""

    def test_initialization(self, mock_config, mock_boto3):
        """Test initialization of S3DataStore."""
        with patch('os.path.exists', return_value=False):
            with patch('recursive_training.data.data_store.Path.mkdir', return_value=None):
                with patch('os.makedirs', return_value=None):
                    with patch('builtins.open', MagicMock()):
                        store = S3DataStore(mock_config)
                        
                        # Check S3-specific properties
                        assert store.s3_data_bucket == mock_config["s3_data_bucket"]
                        assert store.s3_results_bucket == mock_config["s3_results_bucket"]
                        assert store.s3_prefix == mock_config["s3_prefix"]
                        assert store.s3_region == mock_config["s3_region"]
                        
                        # Check S3 client initialization
                        mock_boto3.client.assert_called_with('s3', region_name=mock_config["s3_region"])
                        mock_boto3.resource.assert_called_with('s3', region_name=mock_config["s3_region"])

    def test_get_s3_key_generation(self, s3_store):
        """Test S3 key generation for datasets."""
        # Test with normal dataset name
        assert s3_store._get_s3_key("test_dataset") == "datasets/test_dataset.parquet"
        
        # Test with problematic characters
        assert s3_store._get_s3_key("test/dataset") == "datasets/test_dataset.parquet"
        assert s3_store._get_s3_key("test\\dataset") == "datasets/test_dataset.parquet"
        
        # Test with different storage format
        s3_store.storage_format = "hdf5"
        assert s3_store._get_s3_key("test_dataset") == "datasets/test_dataset.h5"
        
        s3_store.storage_format = "pickle"
        assert s3_store._get_s3_key("test_dataset") == "datasets/test_dataset.pkl"

    def test_retrieve_dataset_s3_direct_read(self, s3_store, sample_data):
        """Test retrieving dataset directly from S3."""
        # Mock direct S3 reading
        with patch.object(s3_store, '_read_parquet_from_s3') as mock_read:
            df = pd.DataFrame(sample_data)
            mock_read.return_value = df
            
            # Test direct S3 read
            result_df, metadata = s3_store.retrieve_dataset_s3("test_dataset")
            
            # Verify we called the read method
            mock_read.assert_called_once()
            assert result_df is df
            assert "source" in metadata
            assert metadata["source"] == "s3"

    def test_retrieve_dataset_s3_with_cache(self, s3_store, sample_data):
        """Test retrieving dataset from S3 cache."""
        # Mock cache operations
        with patch.object(s3_store, '_ensure_dataset_in_cache') as mock_ensure:
            cache_path = "/tmp/cached_file.parquet"
            mock_ensure.return_value = cache_path
            
            # Set up mock read_parquet
            df = pd.DataFrame(sample_data)
            with patch('pandas.read_parquet', return_value=df):
                with patch('os.path.exists', return_value=True):
                    # Test cache read
                    result_df, metadata = s3_store.retrieve_dataset_s3("test_dataset")
                    
                    # Verify we used cache
                    mock_ensure.assert_called_once_with("test_dataset")
                    assert result_df is not None
                    assert "source" in metadata
                    assert metadata["source"] == "s3_cache"

    def test_store_dataset_s3(self, s3_store, sample_data):
        """Test storing dataset to S3."""
        # Mock parent class store method
        dataset_id = "dataset_test_123456"
        with patch.object(s3_store, 'store_dataset_optimized', return_value=dataset_id):
            # Mock optimized storage path
            local_path = "/tmp/test_dataset.parquet"
            with patch.object(s3_store, '_get_optimized_storage_path', return_value=local_path):
                # Mock file exists
                with patch('os.path.exists', return_value=True):
                    # Mock S3 upload
                    with patch.object(s3_store, '_upload_to_s3', return_value=True) as mock_upload:
                        # Test store to S3
                        result_id = s3_store.store_dataset_s3("test_dataset", sample_data)
                        
                        # Verify we called upload
                        mock_upload.assert_called_once()
                        assert result_id == dataset_id

    def test_copy_dataset_to_s3(self, s3_store):
        """Test copying a local dataset to S3."""
        # Mock optimized storage path
        local_path = "/tmp/test_dataset.parquet"
        with patch.object(s3_store, '_get_optimized_storage_path', return_value=local_path):
            # Mock file exists
            with patch('os.path.exists', return_value=True):
                # Mock S3 upload
                with patch.object(s3_store, '_upload_to_s3', return_value=True) as mock_upload:
                    # Test copy to S3
                    result = s3_store.copy_dataset_to_s3("test_dataset")
                    
                    # Verify we called upload
                    mock_upload.assert_called_once()
                    assert result is True

    @pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 is required")
    def test_download_from_s3(self, s3_store, mock_boto3):
        """Test downloading a file from S3."""
        # Set up mock client
        mock_client = mock_boto3.client.return_value
        
        # Test successful download
        result = s3_store._download_from_s3("test-bucket", "test-key", "/tmp/test-file")
        
        # Verify download_file was called
        mock_client.download_file.assert_called_with("test-bucket", "test-key", "/tmp/test-file")
        assert result is True
        
        # Test failed download
        mock_client.download_file.side_effect = Exception("NoSuchKey")
        result = s3_store._download_from_s3("test-bucket", "missing-key", "/tmp/test-file")
        assert result is False

    def test_stream_dataset_s3(self, s3_store, sample_data):
        """Test streaming dataset from S3."""
        # Mock metadata retrieval
        with patch.object(s3_store, '_get_s3_object_metadata', return_value={"ContentLength": 1000}):
            # Mock pyarrow dataset operations
            with patch('pyarrow.dataset.dataset') as mock_dataset:
                mock_scanner = MagicMock()
                mock_table = MagicMock()
                mock_batch = MagicMock()
                
                # Set up mock returns
                mock_dataset.return_value.schema.names = ["timestamp", "value", "label"]
                mock_dataset.return_value.scanner.return_value = mock_scanner
                mock_scanner.to_batches.return_value = [mock_batch]
                mock_batch.to_pandas.return_value = pd.DataFrame(sample_data[:10])
                
                # Mock field function
                mock_field = MagicMock()
                with patch('pyarrow.dataset.field', return_value=mock_field):
                    # Test streaming from S3
                    chunks = list(s3_store.stream_dataset_s3("test_dataset"))
                    
                    # Verify we got chunks
                    assert len(chunks) == 1
                    assert len(chunks[0]) == 10

    def test_fallback_to_parent_methods(self, s3_store, sample_data):
        """Test fallback to parent class methods when S3 fails."""
        # Mock failed S3 operations
        with patch.object(s3_store, '_read_parquet_from_s3', return_value=None):
            with patch.object(s3_store, '_ensure_dataset_in_cache', return_value=None):
                # Mock parent class method
                df = pd.DataFrame(sample_data)
                with patch.object(s3_store, 'retrieve_dataset_optimized', 
                                return_value=(df, {"source": "local"})) as mock_parent:
                    # Test fallback
                    result_df, metadata = s3_store.retrieve_dataset_s3("test_dataset")
                    
                    # Verify parent method was called
                    mock_parent.assert_called_once()
                    assert result_df is df
                    assert metadata["source"] == "local"


if __name__ == "__main__":
    pytest.main()