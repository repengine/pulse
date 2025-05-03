# Pulse Retrodiction Training Docker Containers

This directory contains Docker configurations for containerizing the Pulse retrodiction training system, focusing on the `ParallelTrainingCoordinator` and related components. These containers are designed to be run locally for development/testing and in AWS Batch for production workloads.

## Container Architecture

The Docker containers package the following components:

- **ParallelTrainingCoordinator**: Core component for distributed training
- **Data Storage Components**: Optimized data loading from local storage and S3
- **Dask Integration**: Support for distributed computing with Dask
- **AWS Integration**: Tools for interacting with S3 and other AWS services

## File Structure

- `Dockerfile`: Standard Docker configuration for local development and testing
- `Dockerfile.aws_batch`: Optimized Docker configuration for AWS Batch execution
- `docker-compose.yml`: Docker Compose configuration for local development
- `entrypoint.sh`: Container entry point script with AWS and Dask initialization
- `requirements.txt`: Python dependencies required for retrodiction training

## Building and Running Locally

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ (for local development outside containers)
- AWS credentials (if using S3 integration)

### Building the Container

```bash
# From the repository root
docker build -t pulse-retrodiction-training:latest -f cloud/docker/Dockerfile .
```

### Running with Docker Compose

The Docker Compose configuration provides a complete environment with Dask for distributed processing:

```bash
# From the repository root
cd cloud/docker
docker-compose up
```

This will start:
- The main retrodiction training container
- A Dask scheduler
- Multiple Dask workers

The Dask dashboard will be available at http://localhost:8787 for monitoring.

### Environment Variables

The following environment variables can be used to configure the containers:

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for S3 access | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 | - |
| `S3_DATA_BUCKET` | S3 bucket for input data | `pulse-retrodiction-data-poc` |
| `S3_RESULTS_BUCKET` | S3 bucket for results | `pulse-retrodiction-results-poc` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `USE_DASK` | Enable Dask for distributed processing | `true` |
| `DASK_THREADS` | Number of threads per Dask worker | `2` |
| `DASK_MEMORY_LIMIT` | Memory limit per Dask worker | `4GB` |

## AWS Batch Usage

The AWS Batch configuration is optimized for cloud execution:

### Building for AWS Batch

```bash
# From the repository root
docker build -t pulse-retrodiction-batch:latest -f cloud/docker/Dockerfile.aws_batch .
```

### Pushing to Amazon ECR

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {aws_account_id}.dkr.ecr.us-east-1.amazonaws.com

# Tag the image
docker tag pulse-retrodiction-batch:latest {aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/pulse-retrodiction:latest

# Push the image
docker push {aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/pulse-retrodiction:latest
```

### AWS Batch Job Definition

An example AWS Batch job definition:

```json
{
  "jobDefinitionName": "pulse-retrodiction",
  "type": "container",
  "containerProperties": {
    "image": "{aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/pulse-retrodiction:latest",
    "vcpus": 4,
    "memory": 16384,
    "command": [
      "python", 
      "-m", 
      "recursive_training.run_training", 
      "--variables", 
      "spx_close", 
      "us_10y_yield", 
      "--batch-size-days", 
      "30"
    ],
    "environment": [
      {
        "name": "S3_DATA_BUCKET",
        "value": "pulse-retrodiction-data-poc"
      },
      {
        "name": "S3_RESULTS_BUCKET",
        "value": "pulse-retrodiction-results-poc"
      }
    ],
    "jobRoleArn": "arn:aws:iam::{aws_account_id}:role/pulse-retrodiction-s3-access-role-poc"
  }
}
```

## Running Different Configurations

### Training Mode

```bash
docker run pulse-retrodiction-training:latest python -m recursive_training.run_training --variables spx_close us_10y_yield --batch-size-days 30
```

### Interactive Mode

```bash
docker run -it --entrypoint /bin/bash pulse-retrodiction-training:latest
```

### Using S3 Data Store

```bash
docker run -e AWS_ACCESS_KEY_ID=your_key -e AWS_SECRET_ACCESS_KEY=your_secret pulse-retrodiction-training:latest python -m recursive_training.run_training --variables spx_close us_10y_yield --s3-data-bucket your-data-bucket
```

## Best Practices

1. **Data Persistence**: Mount volumes for data persistence in development
2. **Security**: Use IAM roles instead of access keys in production
3. **Versioning**: Tag container images with version numbers
4. **Logging**: Configure LOG_LEVEL appropriately for your environment
5. **Resource Limits**: Set appropriate resource limits for containers