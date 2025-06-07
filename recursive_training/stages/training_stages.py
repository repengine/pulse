"""
Training Pipeline Stages for Recursive Learning System

This module implements the Command pattern to separate training pipeline stages,
providing clear separation of concerns and improved testability.
"""

import os
import sys
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
import boto3
from pathlib import Path

from recursive_training.config.training_config import TrainingConfig
from recursive_training.parallel_trainer import run_parallel_retrodiction_training

__all__ = [
    "TrainingStage",
    "EnvironmentSetupStage",
    "DataStoreSetupStage",
    "DaskSetupStage",
    "TrainingExecutionStage",
    "ResultsUploadStage",
    "TrainingPipeline",
]

logger = logging.getLogger(__name__)


class TrainingStage(ABC):
    """Abstract base class for training pipeline stages.

    Implements the Command pattern for pipeline stage execution.
    """

    @abstractmethod
    def execute(
        self, config: TrainingConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the training stage.

        Args:
            config: Training configuration.
            context: Shared context between stages.

        Returns:
            Updated context dictionary.

        Raises:
            Exception: If stage execution fails.
        """
        pass

    @abstractmethod
    def can_rollback(self) -> bool:
        """Check if this stage supports rollback operations.

        Returns:
            True if rollback is supported, False otherwise.
        """
        pass

    def rollback(self, config: TrainingConfig, context: Dict[str, Any]) -> None:
        """Rollback changes made by this stage.

        Args:
            config: Training configuration.
            context: Shared context between stages.
        """
        if self.can_rollback():
            logger.warning(f"Rollback not implemented for {self.__class__.__name__}")


class EnvironmentSetupStage(TrainingStage):
    """Stage for setting up the training environment and paths."""

    def execute(
        self, config: TrainingConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up environment configuration and paths.

        Args:
            config: Training configuration.
            context: Shared context between stages.

        Returns:
            Updated context with environment setup.
        """
        logger.info("Setting up training environment")

        # Add project root to Python path
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logger.debug(f"Added project root to Python path: {project_root}")

        # Configure logging
        log_dir = Path(config.log_dir)
        log_dir.mkdir(exist_ok=True)

        # Set up AWS Batch environment if applicable
        env_config = {}
        if os.environ.get("AWS_BATCH_JOB_ID"):
            job_id = os.environ.get("AWS_BATCH_JOB_ID")
            logger.info(f"Running in AWS Batch job {job_id}")

            if os.environ.get("AWS_REGION"):
                env_config["aws_region"] = os.environ.get("AWS_REGION")

            env_config["output_path"] = f"batch_jobs/{job_id}/"

        context.update(
            {
                "environment_config": env_config,
                "project_root": project_root,
                "is_aws_batch": bool(os.environ.get("AWS_BATCH_JOB_ID")),
            }
        )

        logger.info("Environment setup completed")
        return context

    def can_rollback(self) -> bool:
        """Environment setup cannot be rolled back."""
        return False


class DataStoreSetupStage(TrainingStage):
    """Stage for setting up data store connections."""

    def execute(
        self, config: TrainingConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up data store configuration.

        Args:
            config: Training configuration.
            context: Shared context between stages.

        Returns:
            Updated context with data store setup.
        """
        logger.info("Setting up data store")

        if config.s3_data_bucket:
            logger.info(
                f"Configuring S3 data store with bucket {config.s3_data_bucket}"
            )

            try:
                from recursive_training.data.s3_data_store import S3DataStore

                s3_config = {
                    "s3_data_bucket": config.s3_data_bucket,
                    "s3_results_bucket": config.s3_results_bucket,
                    "s3_prefix": config.s3_data_prefix,
                    "s3_region": config.aws_region,
                    "max_s3_workers": 4,
                    "s3_retry_attempts": 3,
                    "cache_expiration_hours": 1,
                }

                data_store = S3DataStore.get_instance(s3_config)
                context["data_store"] = data_store
                context["data_store_config"] = s3_config

                logger.info("S3 data store configured successfully")

            except ImportError as e:
                logger.warning(f"S3DataStore not available: {e}")
                context["data_store"] = None
                context["data_store_config"] = {}
        else:
            logger.info("No S3 data bucket configured, using default data store")
            context["data_store"] = None
            context["data_store_config"] = {}

        return context

    def can_rollback(self) -> bool:
        """Data store setup supports cleanup."""
        return True

    def rollback(self, config: TrainingConfig, context: Dict[str, Any]) -> None:
        """Clean up data store connections."""
        data_store = context.get("data_store")
        if data_store and hasattr(data_store, "close"):
            try:
                data_store.close()
                logger.info("Data store connection closed")
            except Exception as e:
                logger.warning(f"Error closing data store: {e}")


class DaskSetupStage(TrainingStage):
    """Stage for setting up Dask distributed computing."""

    def execute(
        self, config: TrainingConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up Dask client if enabled.

        Args:
            config: Training configuration.
            context: Shared context between stages.

        Returns:
            Updated context with Dask setup.
        """
        if not config.use_dask:
            logger.info("Dask not enabled, skipping setup")
            context["dask_client"] = None
            return context

        logger.info("Setting up Dask client")

        try:
            from dask.distributed import Client

            logger.info(
                f"Connecting to Dask scheduler at {config.dask_scheduler_address}"
            )
            client = Client(config.dask_scheduler_address)

            worker_count = len(client.scheduler_info().get("workers", {}))
            logger.info(f"Connected to Dask cluster with {worker_count} workers")
            logger.info(f"Dask dashboard available at {client.dashboard_link}")

            context["dask_client"] = client

        except Exception as e:
            logger.error(f"Failed to connect to Dask scheduler: {e}")
            logger.warning("Continuing without Dask support")
            context["dask_client"] = None

        return context

    def can_rollback(self) -> bool:
        """Dask setup supports cleanup."""
        return True

    def rollback(self, config: TrainingConfig, context: Dict[str, Any]) -> None:
        """Clean up Dask client connection."""
        dask_client = context.get("dask_client")
        if dask_client:
            try:
                logger.info("Shutting down Dask client")
                dask_client.close()
            except Exception as e:
                logger.warning(f"Error closing Dask client: {e}")


class TrainingExecutionStage(TrainingStage):
    """Stage for executing the main training process."""

    def execute(
        self, config: TrainingConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the parallel training process.

        Args:
            config: Training configuration.
            context: Shared context between stages.

        Returns:
            Updated context with training results.
        """
        logger.info("Starting training execution")

        # Determine training date range
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
        if config.end_date:
            end_date = datetime.strptime(config.end_date, "%Y-%m-%d")
        else:
            end_date = datetime.now()

        logger.info(f"Training period: {start_date} to {end_date}")
        logger.info(f"Variables: {config.variables}")

        # Configure output file path
        output_file = config.output_file
        if not output_file and context.get("is_aws_batch"):
            batch_output_path = config.get_aws_batch_output_path()
            if batch_output_path:
                output_file = batch_output_path

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = f"results/training_results_{timestamp}.json"

        logger.info(f"Training output will be saved to: {output_file}")

        # Run the parallel training
        try:
            results = run_parallel_retrodiction_training(
                variables=config.variables,
                start_time=start_date,
                end_time=end_date,
                max_workers=config.max_workers,
                batch_size_days=config.batch_size_days,
                output_file=output_file,
                dask_scheduler_port=config.dask_dashboard_port,
                dask_dashboard_port=config.dask_dashboard_port,
                dask_threads_per_worker=config.dask_threads_per_worker,
                batch_limit=config.batch_limit,
            )

            context.update(
                {
                    "training_results": results,
                    "output_file": output_file,
                    "training_success": True,
                }
            )

            logger.info("Training execution completed successfully")

        except Exception as e:
            logger.error(f"Training execution failed: {e}")
            context.update(
                {
                    "training_results": None,
                    "output_file": output_file,
                    "training_success": False,
                    "training_error": str(e),
                }
            )
            raise

        return context

    def can_rollback(self) -> bool:
        """Training execution cannot be rolled back."""
        return False


class ResultsUploadStage(TrainingStage):
    """Stage for uploading training results to S3."""

    def execute(
        self, config: TrainingConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload training results to S3 if configured.

        Args:
            config: Training configuration.
            context: Shared context between stages.

        Returns:
            Updated context with upload status.
        """
        if not context.get("training_success"):
            logger.warning("Skipping results upload due to training failure")
            return context

        output_file = context.get("output_file")
        if not output_file or not os.path.exists(output_file):
            logger.warning("No output file to upload")
            return context

        # Determine if S3 upload is needed
        logger.info(
            f"[DEBUG] ResultsUploadStage: config.s3_output_file = {config.s3_output_file!r}"
        )
        logger.info(
            f"[DEBUG] ResultsUploadStage: context.get('is_aws_batch') = {context.get('is_aws_batch')!r}"
        )
        logger.info(
            f"[DEBUG] ResultsUploadStage: config.s3_results_bucket = {config.s3_results_bucket!r}"
        )
        should_upload = config.s3_output_file or (
            context.get("is_aws_batch") and config.s3_results_bucket
        )
        logger.info(
            f"[DEBUG] ResultsUploadStage: calculated should_upload = {should_upload!r}"
        )

        if not should_upload:
            logger.info("S3 upload not configured, skipping")
            return context

        logger.info("Starting S3 results upload")

        try:
            s3_path = config.get_s3_output_path()
            logger.info(
                f"[DEBUG] ResultsUploadStage: config.get_s3_output_path() returned = {s3_path!r}"
            )
            if not s3_path:
                logger.warning("Could not determine S3 output path")
                return context

            # Parse S3 path
            s3_path_clean = s3_path.replace("s3://", "")
            bucket_name = s3_path_clean.split("/")[0]
            s3_key = "/".join(s3_path_clean.split("/")[1:])

            logger.info(f"Uploading results to S3: s3://{bucket_name}/{s3_key}")

            # Initialize S3 client and upload
            s3_client = boto3.client("s3", region_name=config.aws_region)
            s3_client.upload_file(output_file, bucket_name, s3_key)

            context.update(
                {
                    "s3_upload_success": True,
                    "s3_upload_path": f"s3://{bucket_name}/{s3_key}",
                }
            )

            logger.info(
                f"Results uploaded successfully to S3: s3://{bucket_name}/{s3_key}"
            )

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            context.update({"s3_upload_success": False, "s3_upload_error": str(e)})
            # Don't raise - upload failure shouldn't fail the entire pipeline

        return context

    def can_rollback(self) -> bool:
        """Results upload cannot be meaningfully rolled back in this context."""
        return False

    def rollback(self, config: TrainingConfig, context: Dict[str, Any]) -> None:
        """Clean up uploaded results if needed."""
        if context.get("s3_upload_success") and context.get("s3_upload_path"):
            logger.info(
                "S3 upload rollback not implemented - manual cleanup may be required"
            )


class TrainingPipeline:
    """Orchestrates the execution of training pipeline stages.

    Implements the Command pattern for stage execution with error handling
    and rollback capabilities.

    Example:
        >>> # Create a training configuration
        >>> config = TrainingConfig(
        ...     variables=["spx_close", "us_10y_yield"],
        ...     batch_size_days=30,
        ...     start_date="2023-01-01",
        ...     end_date="2023-03-31"
        ... )
        >>>
        >>> # Execute the complete training pipeline
        >>> pipeline = TrainingPipeline()
        >>> results = pipeline.execute(config)
        >>>
        >>> # Check if training was successful
        >>> if results.get("training_success"):
        ...     print("Training completed successfully")
        ... else:
        ...     print("Training failed")
        Training completed successfully
    """

    def __init__(self):
        """Initialize the training pipeline with default stages."""
        self.stages = [
            EnvironmentSetupStage(),
            DataStoreSetupStage(),
            DaskSetupStage(),
            TrainingExecutionStage(),
            ResultsUploadStage(),
        ]
        self.executed_stages = []
        self.context = {}

    def execute(self, config: TrainingConfig) -> Dict[str, Any]:
        """Execute the complete training pipeline.

        Args:
            config: Training configuration.

        Returns:
            Final context with execution results.

        Raises:
            Exception: If any critical stage fails.
        """
        logger.info("Starting training pipeline execution")

        try:
            for stage in self.stages:
                stage_name = stage.__class__.__name__
                logger.info(f"Executing stage: {stage_name}")

                try:
                    self.context = stage.execute(config, self.context)
                    self.executed_stages.append(stage)
                    logger.info(f"Stage {stage_name} completed successfully")

                except Exception as e:
                    logger.error(f"Stage {stage_name} failed: {e}")
                    self._rollback_stages(config)
                    raise

            logger.info("Training pipeline completed successfully")
            return self.context

        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            raise

        finally:
            self._cleanup_stages(config)

    def _rollback_stages(self, config: TrainingConfig) -> None:
        """Rollback executed stages in reverse order."""
        logger.info("Starting pipeline rollback")

        for stage in reversed(self.executed_stages):
            if stage.can_rollback():
                stage_name = stage.__class__.__name__
                try:
                    logger.info(f"Rolling back stage: {stage_name}")
                    stage.rollback(config, self.context)
                except Exception as e:
                    logger.warning(f"Rollback failed for {stage_name}: {e}")

    def _cleanup_stages(self, config: TrainingConfig) -> None:
        """Clean up resources from all executed stages."""
        logger.info("Cleaning up pipeline resources")

        for stage in self.executed_stages:
            if stage.can_rollback():
                try:
                    stage.rollback(config, self.context)
                except Exception as e:
                    stage_name = stage.__class__.__name__
                    logger.warning(f"Cleanup failed for {stage_name}: {e}")
