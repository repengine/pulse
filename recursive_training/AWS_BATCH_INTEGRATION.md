# AWS Batch Integration for Pulse Retrodiction Training

This document describes how to use AWS Batch to run Pulse retrodiction training jobs in a cloud environment. The integration allows you to offload computationally intensive training tasks to AWS infrastructure, providing scalability and resource efficiency.

## Overview

The AWS Batch integration consists of:

1. **Containerized Training Process**: Containerized version of the retrodiction training that runs in AWS Batch environments
2. **Job Submission Script**: Python script to submit training jobs to AWS Batch (`aws_batch_submit.py`)
3. **Status Monitoring Script**: Python script to monitor running AWS Batch jobs (`aws_batch_submit_status.py`)
4. **AWS S3 Integration**: Built-in support for data storage and retrieval using S3

This implementation leverages existing infrastructure including Terraform configurations for AWS Batch, S3, and VPC resources.

## Prerequisites

Before using the AWS Batch integration, ensure you have:

1. AWS CLI configured with appropriate credentials and permissions
2. Access to the AWS Batch job queue and job definition
3. Access to S3 buckets for data and results storage
4. Python 3.9+ with boto3 installed (`pip install boto3`)

## Usage

### Submitting a Training Job

To submit a retrodiction training job to AWS Batch, use the `aws_batch_submit.py` script:

```bash
python -m recursive_training.aws_batch_submit \
  --variables spx_close us_10y_yield \
  --start-date 2022-01-01 \
  --end-date 2023-01-01 \
  --job-queue pulse-retrodiction-job-queue \
  --monitor
```

#### Key Parameters

- `--variables`: List of variables to use for training
- `--start-date`: Start date for training period (YYYY-MM-DD)
- `--end-date`: End date for training period (YYYY-MM-DD) - defaults to today
- `--batch-size-days`: Size of each training batch in days (default: 30)
- `--job-queue`: AWS Batch job queue name (default: pulse-retrodiction-job-queue)
- `--job-definition`: AWS Batch job definition name (default: pulse-retrodiction-training)
- `--vcpus`: Number of vCPUs to allocate to the job (default: 4)
- `--memory`: Memory in MiB to allocate to the job (default: 16384)
- `--use-dask`: Use Dask for distributed computing
- `--monitor`: Monitor job status after submission

Run `python -m recursive_training.aws_batch_submit --help` for a complete list of options.

### Monitoring Job Status

To monitor the status of a previously submitted job:

```bash
python -m recursive_training.aws_batch_submit_status \
  --job-id YOUR_JOB_ID \
  --monitor \
  --show-logs
```

#### Key Parameters

- `--job-id`: AWS Batch job ID to monitor (required)
- `--monitor`: Continuously monitor job status until completion
- `--poll-interval`: Polling interval in seconds (default: 30)
- `--show-logs`: Display CloudWatch log link if available

Run `python -m recursive_training.aws_batch_submit_status --help` for a complete list of options.

## AWS Batch Job Configuration

The retrodiction training job is configured with:

1. Container image: Based on Python 3.11 with all required dependencies
2. Command: Python command to run the training script with parameters
3. Environment variables: S3 bucket names, Dask configuration, etc.
4. Resource requirements: CPU, memory, timeout

The job definition is stored in Terraform configuration at `cloud/aws/batch/batch_job_definition.json`.

## Data Flow

1. **Input Data**: Training data is read from the specified S3 data bucket
2. **Processing**: The containerized training process runs in AWS Batch
3. **Output Data**: Results are stored in the specified S3 results bucket
4. **Logs**: Logs are captured in CloudWatch Logs

## S3 Data Integration

The S3 integration is handled by the `S3DataStore` class which extends `StreamingDataStore`. This provides:

1. Efficient loading of data from S3 buckets
2. Caching to reduce S3 API calls
3. Streaming data directly from S3 without full downloads
4. Support for various data formats (Parquet, HDF5, Pickle)

## Advanced Features

### Dask Integration

The AWS Batch integration supports Dask for distributed computing within a single container:

```bash
python -m recursive_training.aws_batch_submit \
  --variables spx_close us_10y_yield \
  --use-dask \
  --dask-threads 2
```

This creates a local Dask cluster inside the container, improving parallelism.

### Resource Configuration

You can configure the resources allocated to your training job:

```bash
python -m recursive_training.aws_batch_submit \
  --variables spx_close us_10y_yield \
  --vcpus 8 \
  --memory 32768
```

### Job Timeouts

Set custom timeouts for long-running jobs:

```bash
python -m recursive_training.aws_batch_submit \
  --variables spx_close us_10y_yield \
  --job-timeout 172800  # 48 hours
```

## Troubleshooting

1. **Job Failures**: Check job status with `aws_batch_submit_status.py` and review CloudWatch logs
2. **S3 Access Issues**: Ensure the AWS Batch job has proper IAM permissions to access S3 buckets
3. **Resource Constraints**: If jobs are stuck in RUNNABLE state, the AWS Batch compute environment may not have sufficient resources

## Future Improvements

1. **Multi-node training**: Extend to use multiple containers for larger distributed training
2. **Parameter tuning**: Add support for hyperparameter tuning using AWS Batch array jobs
3. **Job dependencies**: Create workflows with dependent jobs for preprocessing, training, and evaluation