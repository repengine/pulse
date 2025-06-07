"""
Training Configuration Management for Recursive Learning System

This module provides centralized configuration management for the recursive training
pipeline, supporting environment variables, file-based configuration, and validation.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

__all__ = ["TrainingConfig", "create_training_config"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainingConfig:
    """Configuration container for recursive training parameters.

    This class encapsulates all configuration parameters needed for training,
    providing validation and environment variable support.

    Example:
        >>> # Create a basic configuration
        >>> config = TrainingConfig(
        ...     variables=["spx_close", "us_10y_yield"],
        ...     batch_size_days=15,
        ...     start_date="2023-01-01",
        ...     end_date="2023-12-31"
        ... )
        >>> config.validate()
        >>> print(f"Training {len(config.variables)} variables")
        Training 2 variables
    """

    # Basic training parameters
    variables: List[str] = field(default_factory=lambda: ["spx_close", "us_10y_yield"])
    batch_size_days: int = 30
    start_date: str = "2022-01-01"
    end_date: Optional[str] = None
    max_workers: Optional[int] = None
    batch_limit: Optional[int] = None

    # AWS configuration
    aws_region: str = "us-east-1"
    s3_data_bucket: Optional[str] = None
    s3_results_bucket: Optional[str] = None
    s3_data_prefix: str = "datasets/"
    s3_results_prefix: str = "results/"

    # Dask configuration
    use_dask: bool = False
    dask_scheduler_address: str = "127.0.0.1:8786"
    dask_dashboard_port: int = 8787
    dask_threads_per_worker: int = 1

    # Output configuration
    output_file: Optional[str] = None
    s3_output_file: Optional[str] = None

    # Logging configuration
    log_level: str = "INFO"
    log_dir: str = "logs"

    def __post_init__(self) -> None:
        """Initialize configuration with environment variable overrides."""
        self._apply_environment_overrides()
        self._set_defaults()

    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            "AWS_REGION": "aws_region",
            "S3_DATA_BUCKET": "s3_data_bucket",
            "S3_RESULTS_BUCKET": "s3_results_bucket",
            "LOG_LEVEL": "log_level",
            "LOG_DIR": "log_dir",
        }

        for env_var, attr_name in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value:
                object.__setattr__(self, attr_name, env_value)
                logger.debug(f"Applied environment override: {attr_name}={env_value}")

    def _set_defaults(self) -> None:
        """Set computed defaults for configuration values."""
        # Only set max_workers if explicitly requested, keep None as default
        pass

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If configuration parameters are invalid.

        Example:
            >>> # Valid configuration
            >>> config = TrainingConfig(
            ...     variables=["spx_close"],
            ...     batch_size_days=30,
            ...     start_date="2023-01-01"
            ... )
            >>> config.validate()  # No exception raised
            >>>
            >>> # Invalid configuration - will raise ValueError
            >>> try:
            ...     bad_config = TrainingConfig(variables=[])
            ...     bad_config.validate()
            ... except ValueError as e:
            ...     print("Validation failed as expected")
            Validation failed as expected
        """
        if not self.variables:
            raise ValueError("Variables list cannot be empty")

        if self.batch_size_days <= 0:
            raise ValueError("batch_size_days must be positive")

        try:
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            if self.end_date:
                end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
                if start_dt >= end_dt:
                    raise ValueError("end_date must be after start_date")
        except ValueError as e:
            if "does not match format" in str(e):
                if "start_date" in str(e) or self.start_date in str(e):
                    raise ValueError("Invalid start_date format")
                else:
                    raise ValueError("Invalid end_date format")
            raise

        if self.max_workers is not None and self.max_workers <= 0:
            raise ValueError("max_workers must be positive")

        if self.batch_limit is not None and self.batch_limit <= 0:
            raise ValueError("batch_limit must be positive")

        # Add log level validation
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError("Invalid log_level")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration.
        """
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }

    def get_aws_batch_output_path(self) -> Optional[str]:
        """Generate AWS Batch-specific output path if running in AWS Batch.

        Returns:
            Output path string if in AWS Batch environment, None otherwise.
        """
        job_id = os.environ.get("AWS_BATCH_JOB_ID")
        if job_id and self.s3_results_bucket:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"results/batch_jobs/{job_id}/results_{timestamp}.json"
        return None

    def get_s3_output_path(self) -> Optional[str]:
        """Generate S3 output path for results.

        Returns:
            S3 path string if S3 output is configured.
        """
        if self.s3_output_file:
            return self.s3_output_file

        if not self.s3_results_bucket:
            return None

        job_id = os.environ.get("AWS_BATCH_JOB_ID")
        if job_id:
            # AWS Batch format: s3://bucket/results/batch_jobs/job-id/filename.json
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            s3_key = (
                f"{self.s3_results_prefix}batch_jobs/{job_id}/results_{timestamp}.json"
            )
            return f"s3://{self.s3_results_bucket}/{s3_key}"
        else:
            # Local format: s3://bucket/results/training_local_timestamp.json
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            s3_key = f"{self.s3_results_prefix}training_local_{timestamp}.json"
            return f"s3://{self.s3_results_bucket}/{s3_key}"


def create_training_config(**kwargs) -> TrainingConfig:
    """Create and validate a training configuration.

    Args:
        **kwargs: Configuration parameters to override defaults.

    Returns:
        Validated TrainingConfig instance.

    Raises:
        ValueError: If configuration validation fails.

    Example:
        >>> # Create a validated training configuration
        >>> config = create_training_config(
        ...     variables=["spx_close", "us_10y_yield"],
        ...     batch_size_days=15,
        ...     start_date="2023-01-01",
        ...     end_date="2023-06-30",
        ...     max_workers=4
        ... )
        >>> print(f"Config created with {len(config.variables)} variables")
        Config created with 2 variables
        >>> print(f"Batch size: {config.batch_size_days} days")
        Batch size: 15 days
    """
    config = TrainingConfig(**kwargs)
    config.validate()
    return config
