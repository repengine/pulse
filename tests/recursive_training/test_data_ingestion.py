"""
Tests for RecursiveDataIngestionManager

This module contains unit tests for the RecursiveDataIngestionManager class,
focusing on data collection, validation, transformation, and preprocessing.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
from pathlib import Path

from recursive_training.data.ingestion_manager import (
    RecursiveDataIngestionManager,
    DataSource,
    APISource,
    FileSource,
    DatabaseSource,
    get_ingestion_manager
)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "data_sources": [],
        "batch_size": 16,
        "parallel_ingestion": True,
        "max_workers": 2,
        "validate_schema": True,
        "filter_invalid_data": True,
        "enable_cache": True,
        "cache_ttl_seconds": 1800,
        "max_tokens_per_request": 4000,
        "max_total_tokens_per_day": 50000,
        "max_requests_per_minute": 5,
        "max_requests_per_hour": 50,
        "max_requests_per_day": 500,
        "daily_cost_threshold_usd": 5.0,
        "emergency_shutdown_threshold_usd": 25.0,
    }


@pytest.fixture
def sample_data_items():
    """Fixture for sample data items."""
    return [
        {"id": "item1", "value": 42, "category": "test"},
        {"id": "item2", "value": 73, "category": "test"},
    ]


@pytest.fixture
def ingestion_manager(mock_config):
    """Fixture for ingestion manager."""
    with patch('recursive_training.data.ingestion_manager.get_config') as mock_get_config:
        mock_pulse_config = MagicMock()
        mock_pulse_config.get.return_value = "./test_data"
        mock_get_config.return_value = mock_pulse_config
        
        with patch('recursive_training.data.ingestion_manager.RecursiveDataStore') as mock_data_store:
            mock_instance = MagicMock()
            mock_data_store.get_instance.return_value = mock_instance
            
            manager = RecursiveDataIngestionManager(config_path=None)
            manager.config = mock_config
            manager._init_data_sources = MagicMock()
            manager.processed_data_hashes = set()
            # Add a mock source for 'test_source' to prevent KeyError
            manager.sources["test_source"] = FileSource(
                source_id="test_source",
                source_type="file", # This is accessed in _process_data
                path="./test_data", # Placeholder, not critical for this fix
                file_pattern="*.json" # Placeholder
            )
            
            return manager


class TestRecursiveDataIngestionManager:
    """Tests for the RecursiveDataIngestionManager class."""

    def test_initialization(self, mock_config):
        """Test correct initialization of the manager."""
        with patch('recursive_training.data.ingestion_manager.get_config') as mock_get_config:
            mock_pulse_config = MagicMock()
            mock_pulse_config.get.return_value = "./test_data"
            mock_get_config.return_value = mock_pulse_config
            
            with patch('recursive_training.data.ingestion_manager.RecursiveDataStore'):
                manager = RecursiveDataIngestionManager(config_path=None)
                
                assert isinstance(manager.logger, object)
                assert isinstance(manager.base_data_path, Path)
                assert isinstance(manager.sources, dict)
                assert isinstance(manager.api_call_count, dict)
                assert isinstance(manager.token_usage, dict)
                assert isinstance(manager.cost_tracker, dict)
                assert isinstance(manager.processed_data_hashes, set)

    def test_load_config_from_dict(self, mock_config):
        """Test loading configuration from dictionary."""
        with patch('recursive_training.data.ingestion_manager.get_config') as mock_get_config:
            mock_pulse_config = MagicMock()
            mock_pulse_config.get.return_value = "./test_data"
            mock_get_config.return_value = mock_pulse_config
            
            with patch('recursive_training.data.ingestion_manager.RecursiveDataStore'):
                with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                    # Mock the os.path.exists call to return True for the config path
                    with patch('os.path.exists', return_value=True):
                        manager = RecursiveDataIngestionManager(config_path="fake_path.json")
                        
                        # Verify config loaded correctly
                        assert manager.config["batch_size"] == 16
                        assert manager.config["max_workers"] == 2

    def test_ingest_from_file(self, ingestion_manager, sample_data_items):
        """Test ingesting data from file sources."""
        mock_source = FileSource(
            source_id="test_source",
            source_type="file",
            path="./test_data",
            file_pattern="*.json"
        )
        
        # Mock glob to return a single test file
        with patch('glob.glob', return_value=["./test_data/test_file.json"]):
            # Mock open to return sample data
            m = mock_open(read_data=json.dumps(sample_data_items))
            with patch('builtins.open', m):
                # Mock the process_data method
                ingestion_manager._process_data = MagicMock(return_value=(2, 2))
                
                result = ingestion_manager._ingest_from_file("test_source", mock_source)
                
                # Verify correct processing
                assert result == (2, 2)
                ingestion_manager._process_data.assert_called_once()

    def test_ingest_empty_file_list(self, ingestion_manager):
        """Test behavior when no files match the pattern."""
        mock_source = FileSource(
            source_id="test_source",
            source_type="file",
            path="./test_data",
            file_pattern="*.json"
        )
        
        # Mock glob to return empty list (no matching files)
        with patch('glob.glob', return_value=[]):
            result = ingestion_manager._ingest_from_file("test_source", mock_source)
            
            # Should return zero counts and not process anything
            assert result == (0, 0)

    def test_process_data(self, ingestion_manager, sample_data_items):
        """Test processing and storing data items."""
        # Setup mock data store
        mock_store = MagicMock()
        with patch('recursive_training.data.data_store.RecursiveDataStore.get_instance', return_value=mock_store):
            # Call the method
            result = ingestion_manager._process_data("test_source", sample_data_items)
            
            # Verify results
            assert result[0] == 2  # Processed count
            assert result[1] == 2  # Ingested count
            assert mock_store.store.call_count == 2
            
            # Verify hash tracking
            assert len(ingestion_manager.processed_data_hashes) == 2

    def test_singleton_pattern(self):
        """Test the singleton pattern implementation."""
        with patch('recursive_training.data.ingestion_manager.RecursiveDataIngestionManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            # First call should create a new instance
            get_ingestion_manager()
            mock_class.assert_called_once()
            
            # Reset mock to check second call
            mock_class.reset_mock()
            
            # Second call should reuse existing instance
            get_ingestion_manager()
            mock_class.assert_not_called()

    def test_get_cost_summary(self, ingestion_manager):
        """Test getting cost summary information."""
        # Setup test data
        ingestion_manager.api_call_count = {"source1": 10, "source2": 20}
        ingestion_manager.token_usage = {"source1": 1000, "source2": 2000}
        ingestion_manager.cost_tracker = {"source1": 0.1, "source2": 0.2}
        ingestion_manager.sources = {"source1": MagicMock(), "source2": MagicMock()}
        
        # Get cost summary
        summary = ingestion_manager.get_cost_summary()
        
        # Verify summary contains expected data
        assert summary["total_api_calls"] == 30
        assert summary["total_tokens"] == 3000
        assert summary["estimated_cost_usd"] == pytest.approx(0.3)
        assert "source1" in summary["by_source"]
        assert "source2" in summary["by_source"]
        assert summary["by_source"]["source1"]["api_calls"] == 10
        assert summary["by_source"]["source2"]["token_usage"] == 2000


if __name__ == "__main__":
    pytest.main()