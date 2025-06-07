"""
Tests for recursive_training.config.training_config module.
"""

import os
import pytest
from datetime import datetime
from unittest.mock import patch

from recursive_training.config.training_config import TrainingConfig


class TestTrainingConfig:
    """Test cases for TrainingConfig dataclass."""

    def test_default_initialization(self):
        """Test TrainingConfig with default values."""
        config = TrainingConfig()
        
        assert config.variables == ["spx_close", "us_10y_yield"]
        assert config.start_date == "2022-01-01"
        assert config.end_date is None
        assert config.batch_size_days == 30
        assert config.max_workers is None
        assert config.batch_limit is None
        
        assert config.aws_region == "us-east-1"
        assert config.s3_data_bucket is None
        assert config.s3_results_bucket is None
        assert config.s3_data_prefix == "datasets/"
        assert config.s3_results_prefix == "results/"
        
        assert config.use_dask is False
        assert config.dask_scheduler_address == "127.0.0.1:8786"
        assert config.dask_dashboard_port == 8787
        assert config.dask_threads_per_worker == 1
        
        assert config.output_file is None
        assert config.s3_output_file is None
        
        assert config.log_level == "INFO"
        assert config.log_dir == "logs"

    def test_custom_initialization(self):
        """Test TrainingConfig with custom values."""
        config = TrainingConfig(
            variables=["custom_var1", "custom_var2"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            batch_size_days=60,
            max_workers=8,
            batch_limit=10,
            aws_region="us-west-2",
            s3_data_bucket="custom-data-bucket",
            s3_results_bucket="custom-results-bucket",
            use_dask=True,
            dask_scheduler_address="192.168.1.100:8786",
            output_file="/tmp/results.json",
            log_level="DEBUG",
        )
        
        assert config.variables == ["custom_var1", "custom_var2"]
        assert config.start_date == "2023-01-01"
        assert config.end_date == "2023-12-31"
        assert config.batch_size_days == 60
        assert config.max_workers == 8
        assert config.batch_limit == 10
        assert config.aws_region == "us-west-2"
        assert config.s3_data_bucket == "custom-data-bucket"
        assert config.s3_results_bucket == "custom-results-bucket"
        assert config.use_dask is True
        assert config.dask_scheduler_address == "192.168.1.100:8786"
        assert config.output_file == "/tmp/results.json"
        assert config.log_level == "DEBUG"

    @patch.dict(os.environ, {
        "AWS_REGION": "eu-west-1",
        "S3_DATA_BUCKET": "env-data-bucket",
        "S3_RESULTS_BUCKET": "env-results-bucket",
        "LOG_LEVEL": "WARNING",
        "LOG_DIR": "/var/log/pulse",
    })
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        config = TrainingConfig()
        
        assert config.aws_region == "eu-west-1"
        assert config.s3_data_bucket == "env-data-bucket"
        assert config.s3_results_bucket == "env-results-bucket"
        assert config.log_level == "WARNING"
        assert config.log_dir == "/var/log/pulse"

    @patch.dict(os.environ, {
        "AWS_BATCH_JOB_ID": "test-job-123",
        "AWS_REGION": "us-east-1",
    })
    def test_get_aws_batch_output_path(self):
        """Test AWS Batch output path generation."""
        config = TrainingConfig(s3_results_bucket="test-bucket")
        
        output_path = config.get_aws_batch_output_path()
        
        assert output_path is not None
        assert "test-job-123" in output_path
        assert output_path.startswith("results/batch_jobs/test-job-123/")
        assert output_path.endswith(".json")

    def test_get_aws_batch_output_path_no_job_id(self):
        """Test AWS Batch output path when no job ID is set."""
        config = TrainingConfig(s3_results_bucket="test-bucket")
        
        output_path = config.get_aws_batch_output_path()
        
        assert output_path is None

    def test_get_aws_batch_output_path_no_bucket(self):
        """Test AWS Batch output path when no S3 bucket is configured."""
        with patch.dict(os.environ, {"AWS_BATCH_JOB_ID": "test-job-123"}):
            config = TrainingConfig()
            
            output_path = config.get_aws_batch_output_path()
            
            assert output_path is None

    def test_get_s3_output_path_explicit(self):
        """Test S3 output path when explicitly set."""
        config = TrainingConfig(s3_output_file="s3://custom-bucket/custom/path.json")
        
        s3_path = config.get_s3_output_path()
        
        assert s3_path == "s3://custom-bucket/custom/path.json"

    @patch.dict(os.environ, {"AWS_BATCH_JOB_ID": "test-job-456"})
    def test_get_s3_output_path_aws_batch(self):
        """Test S3 output path generation for AWS Batch."""
        config = TrainingConfig(s3_results_bucket="batch-bucket")
        
        s3_path = config.get_s3_output_path()
        
        assert s3_path is not None
        assert s3_path.startswith("s3://batch-bucket/results/batch_jobs/test-job-456/")
        assert s3_path.endswith(".json")

    def test_get_s3_output_path_none(self):
        """Test S3 output path when not configured."""
        config = TrainingConfig()
        
        s3_path = config.get_s3_output_path()
        
        assert s3_path is None

    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        config = TrainingConfig(
            variables=["var1", "var2"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            batch_size_days=30,
        )
        
        # Should not raise any exception
        config.validate()

    def test_validate_empty_variables(self):
        """Test validation fails with empty variables list."""
        config = TrainingConfig(variables=[])
        
        with pytest.raises(ValueError, match="Variables list cannot be empty"):
            config.validate()

    def test_validate_invalid_start_date(self):
        """Test validation fails with invalid start date format."""
        config = TrainingConfig(start_date="invalid-date")
        
        with pytest.raises(ValueError, match="Invalid start_date format"):
            config.validate()

    def test_validate_invalid_end_date(self):
        """Test validation fails with invalid end date format."""
        config = TrainingConfig(end_date="invalid-date")
        
        with pytest.raises(ValueError, match="Invalid end_date format"):
            config.validate()

    def test_validate_end_before_start(self):
        """Test validation fails when end date is before start date."""
        config = TrainingConfig(
            start_date="2023-12-31",
            end_date="2023-01-01"
        )
        
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            config.validate()

    def test_validate_negative_batch_size(self):
        """Test validation fails with negative batch size."""
        config = TrainingConfig(batch_size_days=-1)
        
        with pytest.raises(ValueError, match="batch_size_days must be positive"):
            config.validate()

    def test_validate_zero_max_workers(self):
        """Test validation fails with zero max workers."""
        config = TrainingConfig(max_workers=0)
        
        with pytest.raises(ValueError, match="max_workers must be positive"):
            config.validate()

    def test_validate_negative_batch_limit(self):
        """Test validation fails with negative batch limit."""
        config = TrainingConfig(batch_limit=-1)
        
        with pytest.raises(ValueError, match="batch_limit must be positive"):
            config.validate()

    def test_validate_invalid_log_level(self):
        """Test validation fails with invalid log level."""
        config = TrainingConfig(log_level="INVALID")
        
        with pytest.raises(ValueError, match="Invalid log_level"):
            config.validate()

    def test_str_representation(self):
        """Test string representation of TrainingConfig."""
        config = TrainingConfig(
            variables=["test_var"],
            start_date="2023-01-01",
            batch_size_days=15,
        )
        
        str_repr = str(config)
        
        assert "TrainingConfig" in str_repr
        assert "test_var" in str_repr
        assert "2023-01-01" in str_repr
        assert "15" in str_repr

    def test_equality(self):
        """Test equality comparison of TrainingConfig instances."""
        config1 = TrainingConfig(variables=["var1"], start_date="2023-01-01")
        config2 = TrainingConfig(variables=["var1"], start_date="2023-01-01")
        config3 = TrainingConfig(variables=["var2"], start_date="2023-01-01")
        
        assert config1 == config2
        assert config1 != config3

    def test_immutability_attempt(self):
        """Test that TrainingConfig is frozen (immutable)."""
        config = TrainingConfig()
        
        with pytest.raises(AttributeError):
            config.variables = ["new_var"]