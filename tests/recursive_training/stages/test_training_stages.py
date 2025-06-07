"""
Tests for Training Pipeline Stages

This module tests the Command pattern implementation for training pipeline stages.
"""

import os
import pytest
import logging
from unittest.mock import Mock, patch

# Removed memory_profiler import to prevent memory balloon during test execution
from typing import Dict, Any

from recursive_training.config.training_config import TrainingConfig
from recursive_training.stages.training_stages import (
    TrainingStage,
    EnvironmentSetupStage,
    DataStoreSetupStage,
    DaskSetupStage,
    TrainingExecutionStage,
    ResultsUploadStage,
    TrainingPipeline,
)


class TestTrainingStage:
    """Test cases for abstract TrainingStage."""

    def test_abstract_methods(self):
        """Test that TrainingStage cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            # Attempt to instantiate the abstract base class directly
            TrainingStage()

    def test_rollback_default_implementation(self, caplog):
        """Test the default rollback implementation logs a warning."""

        # Create a concrete mock class that implements the abstract methods
        # to allow instantiation for testing the default rollback behavior.
        class ConcreteStage(TrainingStage):
            def execute(
                self, config: TrainingConfig, context: Dict[str, Any]
            ) -> Dict[str, Any]:
                return {}  # Not relevant for this test, but must return Dict[str, Any]

            def can_rollback(self) -> bool:
                return True  # Enable rollback for this test

        stage = ConcreteStage()  # Instantiate the concrete mock
        config = Mock(spec=TrainingConfig)
        context = {}

        with caplog.at_level(logging.WARNING):
            stage.rollback(config, context)
            assert "Rollback not implemented" in caplog.text


class TestEnvironmentSetupStage:
    """Test cases for EnvironmentSetupStage."""

    def test_execute_basic(self):
        """Test basic environment setup."""
        stage = EnvironmentSetupStage()
        config = TrainingConfig()
        context = {}

        result = stage.execute(config, context)

        assert "environment_config" in result
        assert "project_root" in result
        assert "is_aws_batch" in result
        assert result["is_aws_batch"] is False

    @patch.dict(
        os.environ, {"AWS_BATCH_JOB_ID": "test-job-123", "AWS_REGION": "us-west-2"}
    )
    def test_execute_aws_batch(self):
        """Test environment setup in AWS Batch environment."""
        stage = EnvironmentSetupStage()
        config = TrainingConfig()
        context = {}

        result = stage.execute(config, context)

        assert result["is_aws_batch"] is True
        assert result["environment_config"]["aws_region"] == "us-west-2"
        assert "batch_jobs/test-job-123/" in result["environment_config"]["output_path"]

    @patch("pathlib.Path.mkdir")
    def test_execute_creates_log_dir(self, mock_mkdir):
        """Test that log directory is created."""
        stage = EnvironmentSetupStage()
        config = TrainingConfig(log_dir="/tmp/test_logs")
        context = {}

        stage.execute(config, context)

        mock_mkdir.assert_called_once_with(exist_ok=True)

    def test_can_rollback(self):
        """Test that environment setup cannot be rolled back."""
        stage = EnvironmentSetupStage()
        assert stage.can_rollback() is False


class TestDataStoreSetupStage:
    """Test cases for DataStoreSetupStage."""

    def test_execute_no_s3_bucket(self):
        """Test data store setup when no S3 bucket is configured."""
        stage = DataStoreSetupStage()
        config = TrainingConfig()
        context = {}

        result = stage.execute(config, context)

        assert result["data_store"] is None
        assert result["data_store_config"] == {}

    @patch("recursive_training.data.s3_data_store.S3DataStore")
    def test_execute_with_s3_bucket(self, mock_s3_data_store):
        """Test data store setup with S3 bucket configured."""
        mock_instance = Mock()
        mock_s3_data_store.get_instance.return_value = mock_instance

        stage = DataStoreSetupStage()
        config = TrainingConfig(
            s3_data_bucket="test-bucket",
            s3_results_bucket="test-results",
            aws_region="us-east-1",
        )
        context = {}

        result = stage.execute(config, context)

        assert result["data_store"] == mock_instance
        assert "s3_data_bucket" in result["data_store_config"]
        assert result["data_store_config"]["s3_data_bucket"] == "test-bucket"
        mock_s3_data_store.get_instance.assert_called_once()

    @patch("builtins.__import__")
    def test_execute_import_error(self, mock_import):
        """Test data store setup when S3DataStore import fails."""

        def side_effect(name, *args, **kwargs):
            if name == "recursive_training.data.s3_data_store":
                raise ImportError("S3DataStore not available")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        stage = DataStoreSetupStage()
        config = TrainingConfig(s3_data_bucket="test-bucket")
        context = {}

        result = stage.execute(config, context)

        assert result["data_store"] is None
        assert result["data_store_config"] == {}

    def test_can_rollback(self):
        """Test that data store setup supports rollback."""
        stage = DataStoreSetupStage()
        assert stage.can_rollback() is True

    def test_rollback_with_data_store(self):
        """Test rollback when data store has close method."""
        stage = DataStoreSetupStage()
        config = TrainingConfig()

        mock_data_store = Mock()
        mock_data_store.close = Mock()
        context = {"data_store": mock_data_store}

        stage.rollback(config, context)

        mock_data_store.close.assert_called_once()

    def test_rollback_without_close_method(self):
        """Test rollback when data store doesn't have close method."""
        stage = DataStoreSetupStage()
        config = TrainingConfig()
        context = {"data_store": "not_a_mock_with_close"}

        # Should not raise an exception
        stage.rollback(config, context)


class TestDaskSetupStage:
    """Test cases for DaskSetupStage."""

    def test_execute_dask_disabled(self):
        """Test Dask setup when Dask is disabled."""
        stage = DaskSetupStage()
        config = TrainingConfig(use_dask=False)
        context = {}

        result = stage.execute(config, context)

        assert result["dask_client"] is None

    @patch("dask.distributed.Client")
    def test_execute_dask_enabled_success(self, MockDaskClient):
        """Test successful Dask setup when enabled."""
        mock_client_instance = Mock()
        mock_client_instance.scheduler_info.return_value = {
            "workers": {"worker1": {}, "worker2": {}}
        }
        mock_client_instance.dashboard_link = "http://localhost:8787"
        MockDaskClient.return_value = mock_client_instance

        stage = DaskSetupStage()
        config = TrainingConfig(
            use_dask=True,
            dask_scheduler_address="127.0.0.1:8786",
            dask_dashboard_port=8787,
        )
        context = {}

        result = stage.execute(config, context)

        assert result["dask_client"] == mock_client_instance
        MockDaskClient.assert_called_once_with("127.0.0.1:8786")

    @patch("dask.distributed.Client")
    def test_execute_dask_connection_failure(self, MockDaskClient, caplog):
        """Test Dask setup when connection fails."""
        MockDaskClient.side_effect = Exception("Connection failed")
        stage = DaskSetupStage()
        config = TrainingConfig(use_dask=True)
        context = {}

        result = stage.execute(config, context)

        assert result["dask_client"] is None

        # Check for specific log messages
        error_logged = False
        warning_logged = False
        for record in caplog.records:
            if (
                record.levelname == "ERROR"
                and "Failed to connect to Dask scheduler: Connection failed"
                in record.message
            ):
                error_logged = True
            if (
                record.levelname == "WARNING"
                and "Continuing without Dask support" in record.message
            ):
                warning_logged = True

        assert error_logged, "Error message not logged"
        assert warning_logged, "Warning message not logged"
        MockDaskClient.assert_called_once()

    def test_can_rollback(self):
        """Test that Dask setup supports rollback."""
        stage = DaskSetupStage()
        assert stage.can_rollback() is True

    def test_rollback_with_client(self):
        """Test rollback when Dask client exists."""
        stage = DaskSetupStage()
        config = TrainingConfig()

        mock_client = Mock()
        mock_client.close = Mock()
        context = {"dask_client": mock_client}

        stage.rollback(config, context)

        mock_client.close.assert_called_once()

    def test_rollback_without_client(self):
        """Test rollback when no Dask client exists."""
        stage = DaskSetupStage()
        config = TrainingConfig()
        context = {}

        # Should not raise an exception
        stage.rollback(config, context)


class TestTrainingExecutionStage:
    """Test cases for TrainingExecutionStage."""

    @patch(
        "recursive_training.stages.training_stages.run_parallel_retrodiction_training"
    )
    @patch("recursive_training.stages.training_stages.TrainingConfig")
    def test_execute_success(self, MockTrainingConfig, mock_training_func):
        """Test successful training execution."""
        mock_training_func.return_value = "/tmp/results.json"
        mock_config_instance = MockTrainingConfig.return_value
        mock_config_instance.start_date = "2023-01-01"
        mock_config_instance.end_date = "2023-01-31"
        mock_config_instance.variables = ["var1", "var2"]
        mock_config_instance.batch_size_days = 30
        mock_config_instance.overlap_days = 5
        mock_config_instance.batch_limit = None
        mock_config_instance.max_workers = None
        mock_config_instance.output_file = None
        mock_config_instance.dask_dashboard_port = None
        mock_config_instance.dask_threads_per_worker = 1

        stage = TrainingExecutionStage()
        context = {}

        result = stage.execute(mock_config_instance, context)

        assert result["training_success"] is True
        # The output file should be a generated timestamped filename since config.output_file is None
        assert result["output_file"].startswith("results/training_results_")
        assert result["output_file"].endswith(".json")
        # Verify the function was called with correct individual parameters
        mock_training_func.assert_called_once()
        call_args = mock_training_func.call_args
        assert call_args[1]["variables"] == ["var1", "var2"]
        assert call_args[1]["batch_size_days"] == 30
        # Verify the output_file parameter was passed with the generated filename
        assert call_args[1]["output_file"].startswith("results/training_results_")

    @patch(
        "recursive_training.stages.training_stages.run_parallel_retrodiction_training"
    )
    @patch("recursive_training.stages.training_stages.TrainingConfig")
    def test_execute_failure(self, MockTrainingConfig, mock_training_func):
        """Test training execution failure."""
        mock_training_func.side_effect = Exception("Training failed")
        mock_config_instance = MockTrainingConfig.return_value
        mock_config_instance.start_date = "2023-01-01"
        mock_config_instance.end_date = "2023-01-31"
        mock_config_instance.variables = ["var1", "var2"]
        mock_config_instance.batch_size_days = 30
        mock_config_instance.overlap_days = 5
        mock_config_instance.batch_limit = None
        mock_config_instance.max_workers = None
        mock_config_instance.output_file = None
        mock_config_instance.dask_dashboard_port = None
        mock_config_instance.dask_threads_per_worker = 1

        stage = TrainingExecutionStage()
        context = {}

        with pytest.raises(Exception, match="Training failed"):
            stage.execute(mock_config_instance, context)

    @patch(
        "recursive_training.stages.training_stages.run_parallel_retrodiction_training"
    )
    @patch(
        "recursive_training.stages.training_stages.TrainingConfig"
    )  # Also mock TrainingConfig here
    def test_execute_aws_batch_output_path(
        self, MockTrainingConfig, mock_training_func
    ):
        """Test training execution with AWS Batch output path."""
        mock_training_func.return_value = "/tmp/results.json"
        mock_config_instance = MockTrainingConfig.return_value
        # Configure the specific method call needed on the config mock
        mock_config_instance.get_aws_batch_output_path.return_value = (
            "s3://batch-bucket/results.json"
        )
        mock_config_instance.start_date = "2023-01-01"
        mock_config_instance.end_date = "2023-01-31"
        mock_config_instance.variables = ["var1", "var2"]
        mock_config_instance.batch_size_days = 30
        mock_config_instance.overlap_days = 5
        mock_config_instance.batch_limit = None
        mock_config_instance.max_workers = None
        mock_config_instance.output_file = None
        mock_config_instance.dask_dashboard_port = None
        mock_config_instance.dask_threads_per_worker = 1

        stage = TrainingExecutionStage()
        context = {"is_aws_batch": True}

        result = stage.execute(mock_config_instance, context)

        assert result["training_success"] is True
        # In AWS Batch mode with a configured output path, it should use the AWS batch output path
        assert result["output_file"] == "s3://batch-bucket/results.json"
        # Verify the function was called with correct parameters
        mock_training_func.assert_called_once()
        call_args = mock_training_func.call_args
        assert call_args[1]["output_file"] == "s3://batch-bucket/results.json"

    def test_can_rollback(self):
        """Test that training execution cannot be rolled back."""
        stage = TrainingExecutionStage()
        assert stage.can_rollback() is False


class TestResultsUploadStage:
    """Test cases for ResultsUploadStage."""

    def test_execute_training_failed(self):
        """Test results upload when training failed."""
        stage = ResultsUploadStage()
        config = TrainingConfig()
        context = {"training_success": False}

        result = stage.execute(config, context)

        assert result == context  # Should return unchanged context

    def test_execute_no_output_file(self):
        """Test results upload when no output file exists."""
        stage = ResultsUploadStage()
        config = TrainingConfig()
        context = {"training_success": True}

        result = stage.execute(config, context)

        assert result == context

    def test_execute_no_s3_config(self):
        """Test results upload when no S3 configuration exists."""
        stage = ResultsUploadStage()
        config = TrainingConfig()
        context = {"training_success": True, "output_file": "/tmp/results.json"}

        result = stage.execute(config, context)

        assert result == context

    @patch("boto3.client")
    @patch("os.path.exists")
    def test_execute_s3_upload_success(self, mock_exists, mock_boto3_client):
        """Test successful S3 upload."""
        mock_exists.return_value = True
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client

        stage = ResultsUploadStage()
        config = TrainingConfig(
            s3_output_file="s3://test-bucket/results.json", aws_region="us-east-1"
        )
        context = {"training_success": True, "output_file": "/tmp/results.json"}

        result = stage.execute(config, context)

        assert result["s3_upload_success"] is True
        mock_s3_client.upload_file.assert_called_once()

    @patch("boto3.client")
    @patch("os.path.exists")
    def test_execute_s3_upload_failure(self, mock_exists, mock_boto3_client):
        """Test S3 upload failure."""
        mock_exists.return_value = True
        mock_s3_client = Mock()
        mock_s3_client.upload_file.side_effect = Exception("Upload failed")
        mock_boto3_client.return_value = mock_s3_client

        stage = ResultsUploadStage()
        config = TrainingConfig(
            s3_output_file="s3://test-bucket/results.json",
            aws_region="us-east-1",  # Ensure aws_region is set
        )
        context = {"training_success": True, "output_file": "/tmp/results.json"}

        result = stage.execute(config, context)

        assert result["s3_upload_success"] is False
        assert "Upload failed" in result["s3_upload_error"]

    def test_can_rollback(self):
        """Test that results upload cannot be rolled back."""
        stage = ResultsUploadStage()
        assert stage.can_rollback() is False


class TestTrainingPipeline:
    """Test cases for TrainingPipeline."""

    def test_initialization(self):
        """Test pipeline initialization."""
        pipeline = TrainingPipeline()

        assert len(pipeline.stages) == 5
        assert isinstance(pipeline.stages[0], EnvironmentSetupStage)
        assert isinstance(pipeline.stages[1], DataStoreSetupStage)
        assert isinstance(pipeline.stages[2], DaskSetupStage)
        assert isinstance(pipeline.stages[3], TrainingExecutionStage)
        assert isinstance(pipeline.stages[4], ResultsUploadStage)

    @patch("recursive_training.stages.training_stages.TrainingConfig")  # Add this
    def test_execute_success(self, MockTrainingConfig):  # Add MockTrainingConfig
        """Test successful pipeline execution."""
        pipeline = TrainingPipeline()
        mock_config_instance = MockTrainingConfig.return_value  # Use mocked config

        # Mock all stages to succeed
        for stage in pipeline.stages:
            stage.execute = Mock(return_value={})

        pipeline.execute(mock_config_instance)

        assert len(pipeline.executed_stages) == 5
        for stage in pipeline.stages:
            stage.execute.assert_called_once()

    @patch("recursive_training.stages.training_stages.TrainingConfig")  # Add this
    def test_execute_stage_failure(self, MockTrainingConfig):  # Add MockTrainingConfig
        """Test pipeline execution when a stage fails."""
        pipeline = TrainingPipeline()
        mock_config_instance = MockTrainingConfig.return_value  # Use mocked config

        # Mock first stage to succeed, second to fail
        pipeline.stages[0].execute = Mock(return_value={})
        pipeline.stages[1].execute = Mock(side_effect=Exception("Stage failed"))

        # Mock rollback methods
        for stage in pipeline.stages:
            stage.can_rollback = Mock(return_value=True)
            stage.rollback = Mock()

        with pytest.raises(Exception, match="Stage failed"):
            pipeline.execute(mock_config_instance)

        # Should have executed first stage and attempted rollback
        assert len(pipeline.executed_stages) == 1
        # First stage should be rolled back twice - once during normal rollback, once during cleanup
        assert pipeline.stages[0].rollback.call_count == 2

    def test_rollback_stages_private_method(self):
        """Test private rollback method functionality."""
        pipeline = TrainingPipeline()
        config = TrainingConfig()

        # Add some executed stages
        pipeline.executed_stages = [pipeline.stages[0], pipeline.stages[1]]

        # Mock rollback methods
        for stage in pipeline.executed_stages:
            stage.can_rollback = Mock(return_value=True)
            stage.rollback = Mock()

        pipeline._rollback_stages(config)

        # Should rollback in reverse order
        for stage in pipeline.executed_stages:
            stage.rollback.assert_called_once()

    def test_cleanup_stages_private_method(self):
        """Test private cleanup method functionality."""
        pipeline = TrainingPipeline()
        config = TrainingConfig()

        # Add some executed stages
        pipeline.executed_stages = [pipeline.stages[0], pipeline.stages[1]]

        # Mock rollback methods for executed stages
        for stage in pipeline.executed_stages:
            stage.can_rollback = Mock(return_value=True)
            stage.rollback = Mock()

        pipeline._cleanup_stages(config)

        # Should cleanup executed stages
        for stage in pipeline.executed_stages:
            stage.rollback.assert_called_once()
