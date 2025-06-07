"""
Retrodiction Training Runner

This script provides the main entry point for running the Pulse retrodiction training
process in a containerized environment. It uses a modular pipeline architecture
with the Command pattern for improved maintainability and testability.
"""

import argparse
import logging
import os
import sys

from recursive_training.config.training_config import TrainingConfig
from recursive_training.stages import TrainingPipeline

# Add the project root to the Python path to allow importing recursive_training
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

__all__ = ["parse_args", "create_config_from_args", "main"]

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments.

    Example:
        >>> args = parse_args()
        >>> print(args.variables)
        ['spx_close', 'us_10y_yield']
    """
    parser = argparse.ArgumentParser(
        description="Run Pulse retrodiction training in AWS Batch"
    )

    # Basic configuration
    parser.add_argument(
        "--variables",
        type=str,
        nargs="+",
        default=["spx_close", "us_10y_yield"],
        help="Variables to use for training",
    )
    parser.add_argument(
        "--batch-size-days",
        type=int,
        default=30,
        help="Size of each training batch in days",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2022-01-01",
        help="Start date for training period (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date for training period (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Maximum number of worker processes to use",
    )
    parser.add_argument(
        "--batch-limit",
        type=int,
        default=None,
        help="Limit number of batches for debugging",
    )

    # AWS configuration
    parser.add_argument(
        "--aws-region",
        type=str,
        default=os.environ.get("AWS_REGION", "us-east-1"),
        help="AWS region",
    )
    parser.add_argument(
        "--s3-data-bucket",
        type=str,
        default=os.environ.get("S3_DATA_BUCKET", "pulse-retrodiction-data-poc"),
        help="S3 bucket containing training data",
    )
    parser.add_argument(
        "--s3-results-bucket",
        type=str,
        default=os.environ.get("S3_RESULTS_BUCKET", "pulse-retrodiction-results-poc"),
        help="S3 bucket for saving results",
    )
    parser.add_argument(
        "--s3-data-prefix",
        type=str,
        default="datasets/",
        help="Prefix for data objects in S3 data bucket",
    )
    parser.add_argument(
        "--s3-results-prefix",
        type=str,
        default="results/",
        help="Prefix for results objects in S3 results bucket",
    )

    # Dask configuration
    parser.add_argument(
        "--use-dask", action="store_true", help="Use Dask for distributed computing"
    )
    parser.add_argument(
        "--dask-scheduler-address",
        type=str,
        default="127.0.0.1:8786",
        help="Address of the Dask scheduler",
    )
    parser.add_argument(
        "--dask-dashboard-port",
        type=int,
        default=8787,
        help="Port for the Dask dashboard",
    )
    parser.add_argument(
        "--dask-threads-per-worker",
        type=int,
        default=1,
        help="Number of threads per Dask worker",
    )

    # Output configuration
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Path to save training results JSON (local path)",
    )
    parser.add_argument(
        "--s3-output-file",
        type=str,
        default=None,
        help="S3 path to save training results JSON (s3://bucket/key)",
    )

    # Logging configuration
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=os.environ.get("LOG_DIR", "logs"),
        help="Directory for log files",
    )

    return parser.parse_args()


def create_config_from_args(args: argparse.Namespace) -> TrainingConfig:
    """Create a TrainingConfig from command line arguments.

    Args:
        args: Parsed command line arguments.

    Returns:
        TrainingConfig instance with values from arguments.

    Example:
        >>> args = parse_args()
        >>> config = create_config_from_args(args)
        >>> print(config.variables)
        ['spx_close', 'us_10y_yield']
    """
    return TrainingConfig(
        # Basic configuration
        variables=args.variables,
        start_date=args.start_date,
        end_date=args.end_date,
        batch_size_days=args.batch_size_days,
        max_workers=args.max_workers,
        batch_limit=args.batch_limit,
        # AWS configuration
        aws_region=args.aws_region,
        s3_data_bucket=args.s3_data_bucket,
        s3_results_bucket=args.s3_results_bucket,
        s3_data_prefix=args.s3_data_prefix,
        s3_results_prefix=args.s3_results_prefix,
        # Dask configuration
        use_dask=args.use_dask,
        dask_scheduler_address=args.dask_scheduler_address,
        dask_dashboard_port=args.dask_dashboard_port,
        dask_threads_per_worker=args.dask_threads_per_worker,
        # Output configuration
        output_file=args.output_file,
        s3_output_file=args.s3_output_file,
        # Logging configuration
        log_level=args.log_level,
        log_dir=args.log_dir,
    )


def setup_logging(config: TrainingConfig) -> None:
    """Set up logging configuration for the training process.

    Configures both console and file logging with the specified log level
    and creates the log directory if it doesn't exist.

    Args:
        config: Training configuration with logging settings including
            log_level and log_dir.

    Returns:
        None.

    Example:
        >>> config = TrainingConfig(log_level="DEBUG", log_dir="logs")
        >>> setup_logging(config)
        >>> # Logging is now configured for both console and file output
    """
    # Create log directory if it doesn't exist
    os.makedirs(config.log_dir, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(config.log_dir, "retrodiction_training.log")
            ),
        ],
    )


def main() -> int:
    """Main entry point for the retrodiction training runner.

    Returns:
        Exit code (0 for success, 1 for failure).

    Example:
        >>> exit_code = main()
        >>> print(f"Training completed with exit code: {exit_code}")
    """
    try:
        # Parse command line arguments
        args = parse_args()

        # Create configuration from arguments
        config = create_config_from_args(args)

        # Set up logging
        setup_logging(config)

        logger.info("Starting Pulse retrodiction training")
        logger.info(f"Configuration: {config}")

        # Create and execute the training pipeline
        pipeline = TrainingPipeline()
        results = pipeline.execute(config)

        # Check if training was successful
        if results.get("training_success", False):
            logger.info("Training pipeline completed successfully")

            # Log S3 upload status if applicable
            if results.get("s3_upload_success"):
                s3_path = results.get("s3_upload_path")
                logger.info(f"Results uploaded to S3: {s3_path}")
            elif results.get("s3_upload_success") is False:
                logger.warning(f"S3 upload failed: {results.get('s3_upload_error')}")

            return 0
        else:
            error_msg = results.get("training_error", "Unknown error")
            logger.error(f"Training pipeline failed: {error_msg}")
            return 1

    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error in training pipeline: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
