"""
AWS Batch Job Submission Script for Pulse Retrodiction Training

This script provides functionality to submit retrodiction training jobs to AWS Batch,
allowing distributed training workloads to run on AWS infrastructure. It handles job
configuration, submission, monitoring, and supports parameterization.

Usage:
    python -m recursive_training.aws_batch_submit --variables spx_close us_10y_yield --start-date 2022-01-01
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import uuid

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("aws_batch_submit")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Submit Pulse retrodiction training jobs to AWS Batch")
    
    # Basic configuration
    parser.add_argument("--variables", type=str, nargs="+", default=["spx_close", "us_10y_yield"],
                        help="Variables to use for training")
    parser.add_argument("--batch-size-days", type=int, default=30,
                        help="Size of each training batch in days")
    parser.add_argument("--start-date", type=str, default="2022-01-01",
                        help="Start date for training period (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None,
                        help="End date for training period (YYYY-MM-DD), defaults to today")
    
    # AWS configuration
    parser.add_argument("--aws-region", type=str, default=os.environ.get("AWS_REGION", "us-east-1"),
                        help="AWS region")
    parser.add_argument("--s3-data-bucket", type=str, 
                        default=os.environ.get("S3_DATA_BUCKET", "pulse-retrodiction-data-poc"),
                        help="S3 bucket containing training data")
    parser.add_argument("--s3-results-bucket", type=str,
                        default=os.environ.get("S3_RESULTS_BUCKET", "pulse-retrodiction-results-poc"),
                        help="S3 bucket for saving results")
    parser.add_argument("--job-queue", type=str, default="pulse-retrodiction-job-queue",
                        help="AWS Batch job queue name")
    parser.add_argument("--job-definition", type=str, default="pulse-retrodiction-training",
                        help="AWS Batch job definition name")
    
    # Job configuration
    parser.add_argument("--job-name-prefix", type=str, default="pulse-retrodiction",
                        help="Prefix for AWS Batch job names")
    parser.add_argument("--vcpus", type=int, default=4,
                        help="Number of vCPUs to allocate to the job")
    parser.add_argument("--memory", type=int, default=16384,
                        help="Memory (in MiB) to allocate to the job")
    parser.add_argument("--use-dask", action="store_true",
                        help="Use Dask for distributed computing")
    parser.add_argument("--dask-threads", type=int, default=2,
                        help="Number of threads per Dask worker")
    parser.add_argument("--job-timeout", type=int, default=86400,
                        help="Job timeout in seconds (default: 24 hours)")
    
    # Monitoring configuration
    parser.add_argument("--monitor", action="store_true",
                        help="Monitor job status after submission")
    parser.add_argument("--poll-interval", type=int, default=30,
                        help="Polling interval for job status in seconds")
    
    return parser.parse_args()

def get_batch_client(region: str = "us-east-1") -> boto3.client:
    """
    Create an AWS Batch client for the specified region.
    
    Args:
        region: AWS region name
        
    Returns:
        Boto3 AWS Batch client
    """
    try:
        return boto3.client('batch', region_name=region)
    except Exception as e:
        logger.error(f"Failed to create AWS Batch client: {e}")
        raise

def submit_batch_job(
    batch_client: boto3.client,
    job_name: str,
    job_queue: str,
    job_definition: str,
    command: List[str],
    environment: List[Dict[str, str]],
    vcpus: int = 4,
    memory: int = 16384,
    timeout_seconds: int = 86400
) -> Dict[str, str]:
    """
    Submit a job to AWS Batch.
    
    Args:
        batch_client: Boto3 AWS Batch client
        job_name: Name for the job
        job_queue: AWS Batch job queue name
        job_definition: AWS Batch job definition name
        command: Command to execute in the container (list of strings)
        environment: List of environment variables as dictionaries with 'name' and 'value' keys
        vcpus: Number of vCPUs to allocate to the job
        memory: Memory (in MiB) to allocate to the job
        timeout_seconds: Job timeout in seconds
        
    Returns:
        Dictionary containing job details including the job ID
    """
    try:
        # Calculate timeout in minutes (required by AWS Batch)
        timeout_minutes = max(1, timeout_seconds // 60)
        
        # Submit the job
        response = batch_client.submit_job(
            jobName=job_name,
            jobQueue=job_queue,
            jobDefinition=job_definition,
            containerOverrides={
                'command': command,
                'environment': environment,
                'resourceRequirements': [
                    {
                        'type': 'VCPU',
                        'value': str(vcpus)
                    },
                    {
                        'type': 'MEMORY',
                        'value': str(memory)
                    }
                ]
            },
            timeout={
                'attemptDurationSeconds': timeout_seconds
            },
            tags={
                'Project': 'Pulse',
                'Component': 'Retrodiction-Training',
                'CreatedBy': 'aws_batch_submit'
            }
        )
        
        # Extract job ID
        job_id = response['jobId']
        logger.info(f"Successfully submitted AWS Batch job {job_name} with ID {job_id}")
        
        return {
            'job_id': job_id,
            'job_name': job_name,
            'submission_time': datetime.now().isoformat()
        }
        
    except ClientError as e:
        logger.error(f"Failed to submit AWS Batch job: {e}")
        if 'errorMessage' in e.response.get('Error', {}):
            logger.error(f"Error details: {e.response['Error']['errorMessage']}")
        raise

def get_job_status(batch_client: boto3.client, job_id: str) -> Dict[str, Any]:
    """
    Get the status of an AWS Batch job.
    
    Args:
        batch_client: Boto3 AWS Batch client
        job_id: AWS Batch job ID
        
    Returns:
        Dictionary containing job status details
    """
    try:
        response = batch_client.describe_jobs(jobs=[job_id])
        
        if not response['jobs']:
            logger.warning(f"No job found with ID {job_id}")
            return {'status': 'UNKNOWN'}
        
        job = response['jobs'][0]
        status = job['status']
        status_reason = job.get('statusReason', '')
        
        result = {
            'job_id': job_id,
            'status': status,
            'status_reason': status_reason,
            'job_name': job['jobName'],
            'created_at': job.get('createdAt', 0),
            'started_at': job.get('startedAt', 0),
            'stopped_at': job.get('stoppedAt', 0)
        }
        
        # Add container details if available
        if 'container' in job and job['container']:
            result['container'] = {
                'exit_code': job['container'].get('exitCode'),
                'reason': job['container'].get('reason', ''),
                'log_stream_name': job['container'].get('logStreamName', '')
            }
        
        return result
        
    except ClientError as e:
        logger.error(f"Failed to get job status for job {job_id}: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def monitor_job(batch_client: boto3.client, job_id: str, poll_interval: int = 30) -> Dict[str, Any]:
    """
    Monitor an AWS Batch job until it completes or fails.
    
    Args:
        batch_client: Boto3 AWS Batch client
        job_id: AWS Batch job ID
        poll_interval: Polling interval in seconds
        
    Returns:
        Dictionary containing final job status
    """
    logger.info(f"Monitoring job {job_id}")
    
    terminal_states = ['SUCCEEDED', 'FAILED']
    status = None
    
    while status not in terminal_states:
        job_info = get_job_status(batch_client, job_id)
        status = job_info['status']
        
        # Format timestamps if available
        created_at = job_info.get('created_at', 0)
        started_at = job_info.get('started_at', 0)
        stopped_at = job_info.get('stopped_at', 0)
        
        created_str = datetime.fromtimestamp(created_at/1000).strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A'
        started_str = datetime.fromtimestamp(started_at/1000).strftime('%Y-%m-%d %H:%M:%S') if started_at else 'N/A'
        runtime_str = 'N/A'
        
        if started_at and stopped_at:
            runtime_seconds = (stopped_at - started_at) / 1000
            runtime_str = f"{runtime_seconds:.2f} seconds"
        elif started_at:
            runtime_seconds = (time.time() - started_at/1000)
            runtime_str = f"{runtime_seconds:.2f} seconds (running)"
        
        logger.info(
            f"Job {job_id} status: {status}, "
            f"Created: {created_str}, Started: {started_str}, Runtime: {runtime_str}"
        )
        
        if status in terminal_states:
            break
        
        # Log CloudWatch logs link if available
        if 'container' in job_info and 'log_stream_name' in job_info['container'] and job_info['container']['log_stream_name']:
            log_stream = job_info['container']['log_stream_name']
            region = boto3.session.Session().region_name
            log_url = f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/aws/batch/job/log-events/stream/{log_stream}"
            logger.info(f"CloudWatch Logs: {log_url}")
        
        time.sleep(poll_interval)
    
    # Get final job status
    final_status = get_job_status(batch_client, job_id)
    
    if status == 'SUCCEEDED':
        logger.info(f"Job {job_id} completed successfully")
    else:
        logger.error(f"Job {job_id} failed: {final_status.get('status_reason', '')}")
        if 'container' in final_status and 'reason' in final_status['container']:
            logger.error(f"Container reason: {final_status['container']['reason']}")
    
    return final_status

def build_command(args) -> List[str]:
    """
    Build the command to run inside the container.
    
    Args:
        args: Command line arguments from argparse
        
    Returns:
        List of command parts
    """
    # Start with the basic command
    command = ["python", "-m", "recursive_training.run_training"]
    
    # Add variables
    if args.variables:
        command.extend(["--variables"])
        command.extend(args.variables)
    
    # Add other parameters
    if args.batch_size_days:
        command.extend(["--batch-size-days", str(args.batch_size_days)])
    
    if args.start_date:
        command.extend(["--start-date", args.start_date])
    
    if args.end_date:
        command.extend(["--end-date", args.end_date])
    
    # S3 configuration
    if args.s3_data_bucket:
        command.extend(["--s3-data-bucket", args.s3_data_bucket])
    
    if args.s3_results_bucket:
        command.extend(["--s3-results-bucket", args.s3_results_bucket])
    
    # Dask configuration
    if args.use_dask:
        command.append("--use-dask")
    
    return command

def build_environment(args) -> List[Dict[str, str]]:
    """
    Build environment variables for the container.
    
    Args:
        args: Command line arguments from argparse
        
    Returns:
        List of environment variable dictionaries
    """
    environment = [
        {
            "name": "S3_DATA_BUCKET",
            "value": args.s3_data_bucket
        },
        {
            "name": "S3_RESULTS_BUCKET",
            "value": args.s3_results_bucket
        },
        {
            "name": "LOG_LEVEL",
            "value": os.environ.get("LOG_LEVEL", "INFO")
        }
    ]
    
    # Dask configuration
    if args.use_dask:
        environment.extend([
            {
                "name": "USE_DASK",
                "value": "true"
            },
            {
                "name": "DASK_THREADS",
                "value": str(args.dask_threads)
            }
        ])
    
    # Add job ID as environment variable
    environment.append({
        "name": "PULSE_JOB_ID",
        "value": f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    })
    
    return environment

def main():
    """Main entry point for the AWS Batch submission script."""
    args = parse_args()
    logger.info("Starting AWS Batch job submission for Pulse retrodiction training")
    
    try:
        # Create AWS Batch client
        batch_client = get_batch_client(args.aws_region)
        
        # Generate unique job name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        job_name = f"{args.job_name_prefix}-{timestamp}"
        
        # Build command and environment
        command = build_command(args)
        environment = build_environment(args)
        
        # Log configuration
        logger.info(f"Job configuration:")
        logger.info(f"  Job name:       {job_name}")
        logger.info(f"  Job queue:      {args.job_queue}")
        logger.info(f"  Job definition: {args.job_definition}")
        logger.info(f"  Command:        {' '.join(command)}")
        logger.info(f"  vCPUs:          {args.vcpus}")
        logger.info(f"  Memory:         {args.memory} MiB")
        logger.info(f"  Use Dask:       {args.use_dask}")
        logger.info(f"  Timeout:        {args.job_timeout} seconds")
        
        # Submit job
        job_details = submit_batch_job(
            batch_client=batch_client,
            job_name=job_name,
            job_queue=args.job_queue,
            job_definition=args.job_definition,
            command=command,
            environment=environment,
            vcpus=args.vcpus,
            memory=args.memory,
            timeout_seconds=args.job_timeout
        )
        
        # Write job details to file
        output_file = f"batch_job_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(job_details, f, indent=2)
            
        logger.info(f"Job details saved to {output_file}")
        
        # Monitor job if requested
        if args.monitor:
            monitor_job(
                batch_client=batch_client,
                job_id=job_details['job_id'],
                poll_interval=args.poll_interval
            )
        else:
            logger.info(f"Job submitted with ID: {job_details['job_id']}")
            logger.info(f"Monitor the job status in the AWS Management Console or run:")
            logger.info(f"python -m recursive_training.aws_batch_submit_status --job-id {job_details['job_id']}")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error in AWS Batch job submission: {e}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())