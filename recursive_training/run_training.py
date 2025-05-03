"""
Retrodiction Training Runner

This script provides the main entry point for running the Pulse retrodiction training
process in a containerized environment. It configures the ParallelTrainingCoordinator
and handles AWS-specific setup when running in AWS Batch.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import json
import boto3
import pandas as pd

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.environ.get("LOG_DIR", "logs"), "retrodiction_training.log"))
    ]
)

logger = logging.getLogger("retrodiction_training")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Pulse retrodiction training in AWS Batch")
    
    # Basic configuration
    parser.add_argument("--variables", type=str, nargs="+", default=["spx_close", "us_10y_yield"],
                        help="Variables to use for training")
    parser.add_argument("--batch-size-days", type=int, default=30,
                        help="Size of each training batch in days")
    parser.add_argument("--start-date", type=str, default="2022-01-01",
                        help="Start date for training period (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None,
                        help="End date for training period (YYYY-MM-DD), defaults to today")
    parser.add_argument("--max-workers", type=int, default=None,
                        help="Maximum number of worker processes to use")
    
    # AWS configuration
    parser.add_argument("--aws-region", type=str, default=os.environ.get("AWS_REGION", "us-east-1"),
                        help="AWS region")
    parser.add_argument("--s3-data-bucket", type=str, 
                        default=os.environ.get("S3_DATA_BUCKET", "pulse-retrodiction-data-poc"),
                        help="S3 bucket containing training data")
    parser.add_argument("--s3-results-bucket", type=str,
                        default=os.environ.get("S3_RESULTS_BUCKET", "pulse-retrodiction-results-poc"),
                        help="S3 bucket for saving results")
    parser.add_argument("--s3-data-prefix", type=str, default="datasets/",
                        help="Prefix for data objects in S3 data bucket")
    parser.add_argument("--s3-results-prefix", type=str, default="results/",
                        help="Prefix for results objects in S3 results bucket")
    
    # Dask configuration
    parser.add_argument("--use-dask", action="store_true",
                        help="Use Dask for distributed computing")
    parser.add_argument("--dask-scheduler-address", type=str, default="127.0.0.1:8786",
                        help="Address of the Dask scheduler")
    parser.add_argument("--dask-dashboard-port", type=int, default=8787,
                        help="Port for the Dask dashboard")
    parser.add_argument("--dask-threads-per-worker", type=int, default=1,
                        help="Number of threads per Dask worker")
    
    # Output configuration
    parser.add_argument("--output-file", type=str, default=None,
                        help="Path to save training results JSON (local path)")
    parser.add_argument("--s3-output-file", type=str, default=None,
                        help="S3 path to save training results JSON (s3://bucket/key)")
    
    return parser.parse_args()

def setup_s3_data_store(args):
    """
    Set up the S3DataStore with appropriate configuration for AWS.
    
    Args:
        args: Command line arguments
        
    Returns:
        An instance of S3DataStore configured for AWS
    """
    from recursive_training.data.s3_data_store import S3DataStore
    
    # Configure S3 data store
    config = {
        "s3_data_bucket": args.s3_data_bucket,
        "s3_results_bucket": args.s3_results_bucket,
        "s3_prefix": args.s3_data_prefix,
        "s3_region": args.aws_region,
        "max_s3_workers": 4,
        "s3_retry_attempts": 3,
        "cache_expiration_hours": 1  # Short cache for container environment
    }
    
    # Initialize and return the S3DataStore
    return S3DataStore.get_instance(config)

def setup_dask_client(args):
    """
    Set up a Dask client for distributed computing if enabled.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dask client or None if not enabled
    """
    if not args.use_dask:
        return None
    
    try:
        from dask.distributed import Client
        logger.info(f"Connecting to Dask scheduler at {args.dask_scheduler_address}")
        client = Client(args.dask_scheduler_address)
        logger.info(f"Connected to Dask cluster with {len(client.scheduler_info()['workers'])} workers")
        logger.info(f"Dask dashboard available at {client.dashboard_link}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Dask scheduler: {e}")
        logger.warning("Continuing without Dask support")
        return None

def is_running_in_aws_batch():
    """Check if we're running in AWS Batch environment."""
    return bool(os.environ.get("AWS_BATCH_JOB_ID"))

def configure_aws_batch_environment():
    """
    Configure environment based on AWS Batch environment variables.
    
    Returns:
        Dict with environment configuration
    """
    env_config = {}
    
    # Check AWS Batch environment variables
    if os.environ.get("AWS_BATCH_JOB_ID"):
        logger.info(f"Running in AWS Batch job {os.environ.get('AWS_BATCH_JOB_ID')}")
        
        # Set AWS region from environment if available
        if os.environ.get("AWS_REGION"):
            env_config["aws_region"] = os.environ.get("AWS_REGION")
        
        # Configure job-specific output path using job ID
        job_id = os.environ.get("AWS_BATCH_JOB_ID")
        env_config["output_path"] = f"batch_jobs/{job_id}/"
    
    return env_config

def main():
    """Main entry point for the retrodiction training runner."""
    args = parse_args()
    logger.info("Starting Pulse retrodiction training")
    
    # Configure environment if running in AWS Batch
    env_config = configure_aws_batch_environment() if is_running_in_aws_batch() else {}
    
    # Set up S3 data store if we're using S3
    if args.s3_data_bucket:
        logger.info(f"Setting up S3 data store with bucket {args.s3_data_bucket}")
        s3_data_store = setup_s3_data_store(args)
    
    # Set up Dask client if enabled
    dask_client = setup_dask_client(args)
    
    # Setup for ParallelTrainingCoordinator
    from recursive_training.parallel_trainer import ParallelTrainingCoordinator, run_parallel_retrodiction_training
    
    # Determine training date range
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    logger.info(f"Training period: {start_date} to {end_date}")
    logger.info(f"Variables: {args.variables}")
    
    # Configure output file path
    output_file = args.output_file
    if not output_file and is_running_in_aws_batch():
        # In AWS Batch, use a predictable output location
        job_id = os.environ.get("AWS_BATCH_JOB_ID", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"results/batch_{job_id}_{timestamp}.json"
    
    logger.info(f"Training output will be saved to: {output_file}")
    
    try:
        # Run the parallel training
        results = run_parallel_retrodiction_training(
            variables=args.variables,
            start_time=start_date,
            end_time=end_date,
            max_workers=args.max_workers,
            batch_size_days=args.batch_size_days,
            output_file=output_file,
            dask_scheduler_port=args.dask_dashboard_port,
            dask_dashboard_port=args.dask_dashboard_port,
            dask_threads_per_worker=args.dask_threads_per_worker
        )
        
        logger.info("Training completed successfully")
        
        # Upload results to S3 if requested
        if args.s3_output_file or (is_running_in_aws_batch() and args.s3_results_bucket):
            s3_path = args.s3_output_file
            if not s3_path:
                # Generate S3 path if not provided
                job_id = os.environ.get("AWS_BATCH_JOB_ID", "unknown")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                s3_key = f"{args.s3_results_prefix}batch_{job_id}_{timestamp}.json"
                s3_path = f"s3://{args.s3_results_bucket}/{s3_key}"
            
            # Extract bucket and key from S3 path
            s3_path = s3_path.replace("s3://", "")
            bucket_name = s3_path.split("/")[0]
            s3_key = "/".join(s3_path.split("/")[1:])
            
            logger.info(f"Uploading results to S3: {s3_path}")
            
            # Initialize S3 client and upload results
            s3_client = boto3.client("s3", region_name=args.aws_region)
            s3_client.upload_file(output_file, bucket_name, s3_key)
            
            logger.info(f"Results uploaded to S3: s3://{bucket_name}/{s3_key}")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error in retrodiction training: {e}")
        return 1
    
    finally:
        # Clean up resources
        if dask_client:
            logger.info("Shutting down Dask client")
            dask_client.close()

if __name__ == "__main__":
    sys.exit(main())