"""
AWS Batch Job Status Monitoring Script for Pulse Retrodiction Training

This script provides functionality to monitor the status of AWS Batch jobs
that have been submitted for retrodiction training. It can be used to check
on jobs that were previously submitted using aws_batch_submit.py.

Usage:
    python -m recursive_training.aws_batch_submit_status --job-id YOUR_JOB_ID
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any

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

logger = logging.getLogger("aws_batch_status")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Monitor AWS Batch job status for Pulse retrodiction training")
    
    # Required arguments
    parser.add_argument("--job-id", type=str, required=True,
                        help="AWS Batch job ID to monitor")
    
    # AWS configuration
    parser.add_argument("--aws-region", type=str, default=os.environ.get("AWS_REGION", "us-east-1"),
                        help="AWS region")
    
    # Monitoring configuration
    parser.add_argument("--monitor", action="store_true",
                        help="Continuously monitor job status until completion")
    parser.add_argument("--poll-interval", type=int, default=30,
                        help="Polling interval for job status in seconds")
    parser.add_argument("--show-logs", action="store_true",
                        help="Display CloudWatch log link if available")
    
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

def display_job_status(job_info: Dict[str, Any], show_logs: bool = False) -> None:
    """
    Display detailed job status information.
    
    Args:
        job_info: Job status dictionary from get_job_status
        show_logs: Whether to display CloudWatch logs link
    """
    status = job_info['status']
    job_id = job_info['job_id']
    job_name = job_info.get('job_name', 'N/A')
    
    # Format timestamps if available
    created_at = job_info.get('created_at', 0)
    started_at = job_info.get('started_at', 0)
    stopped_at = job_info.get('stopped_at', 0)
    
    created_str = datetime.fromtimestamp(created_at/1000).strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A'
    started_str = datetime.fromtimestamp(started_at/1000).strftime('%Y-%m-%d %H:%M:%S') if started_at else 'N/A'
    stopped_str = datetime.fromtimestamp(stopped_at/1000).strftime('%Y-%m-%d %H:%M:%S') if stopped_at else 'N/A'
    
    runtime_str = 'N/A'
    if started_at and stopped_at:
        runtime_seconds = (stopped_at - started_at) / 1000
        runtime_str = f"{runtime_seconds:.2f} seconds"
    elif started_at:
        runtime_seconds = (time.time() - started_at/1000)
        runtime_str = f"{runtime_seconds:.2f} seconds (running)"
    
    # Display job information
    print("\n===== AWS Batch Job Status =====")
    print(f"Job ID:         {job_id}")
    print(f"Job Name:       {job_name}")
    print(f"Status:         {status}")
    
    if 'status_reason' in job_info and job_info['status_reason']:
        print(f"Status Reason:  {job_info['status_reason']}")
    
    print(f"Created:        {created_str}")
    print(f"Started:        {started_str}")
    print(f"Stopped:        {stopped_str}")
    print(f"Runtime:        {runtime_str}")
    
    # Display container details if available
    if 'container' in job_info:
        container = job_info['container']
        print("\n----- Container Details -----")
        
        exit_code = container.get('exit_code')
        if exit_code is not None:
            print(f"Exit Code:      {exit_code}")
        
        if 'reason' in container and container['reason']:
            print(f"Reason:         {container['reason']}")
        
        log_stream = container.get('log_stream_name', '')
        if log_stream and show_logs:
            region = boto3.session.Session().region_name
            log_url = f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/aws/batch/job/log-events/stream/{log_stream}"
            print(f"\nCloudWatch Logs: {log_url}")
    
    print("\n================================")

def monitor_job(batch_client: boto3.client, job_id: str, poll_interval: int = 30, show_logs: bool = False) -> Dict[str, Any]:
    """
    Monitor an AWS Batch job until it completes or fails.
    
    Args:
        batch_client: Boto3 AWS Batch client
        job_id: AWS Batch job ID
        poll_interval: Polling interval in seconds
        show_logs: Whether to display CloudWatch logs link
        
    Returns:
        Dictionary containing final job status
    """
    logger.info(f"Monitoring job {job_id}")
    
    terminal_states = ['SUCCEEDED', 'FAILED']
    status = None
    
    while status not in terminal_states:
        job_info = get_job_status(batch_client, job_id)
        status = job_info['status']
        
        # Display job status
        display_job_status(job_info, show_logs)
        
        if status in terminal_states:
            break
        
        print(f"\nRefreshing in {poll_interval} seconds... (Press Ctrl+C to stop monitoring)")
        try:
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            break
    
    return job_info

def main():
    """Main entry point for the AWS Batch status monitoring script."""
    args = parse_args()
    logger.info(f"Checking status for AWS Batch job: {args.job_id}")
    
    try:
        # Create AWS Batch client
        batch_client = get_batch_client(args.aws_region)
        
        # Get job status
        job_info = get_job_status(batch_client, args.job_id)
        
        if args.monitor and job_info['status'] not in ['SUCCEEDED', 'FAILED']:
            # Continuously monitor job
            monitor_job(
                batch_client=batch_client,
                job_id=args.job_id,
                poll_interval=args.poll_interval,
                show_logs=args.show_logs
            )
        else:
            # Just display current status
            display_job_status(job_info, args.show_logs)
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error monitoring AWS Batch job: {e}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())