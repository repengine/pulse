# AWS Batch Configuration for Pulse Retrodiction Training

This directory contains Terraform configuration for AWS Batch resources needed to run Pulse retrodiction training jobs in the cloud. AWS Batch automatically provisions and scales compute resources based on workload needs, making it ideal for the intensive computational requirements of retrodiction training.

## Architecture Overview

The AWS Batch infrastructure consists of:

1. **Compute Environment**: A managed environment that uses EC2 instances to run containerized batch jobs
2. **Job Queue**: A queue that holds submitted jobs before they are executed
3. **Job Definition**: A specification for how to run the containerized retrodiction training job
4. **IAM Roles**: Roles with appropriate permissions for AWS Batch and EC2 instances

## Infrastructure Components

### Compute Environment

The compute environment is configured with:
- EC2 instance types optimized for computation (c5 family)
- Auto-scaling between minimum and maximum vCPUs
- Placement in private subnets with NAT gateway for secure outbound connectivity
- Security group allowing necessary network traffic

### Job Queue

A priority-based queue that schedules jobs to run on the compute environment.

### Job Definition

The job definition specifies:
- Container image from ECR
- Resource requirements (vCPUs, memory)
- Command to run (`recursive_training.run_training`)
- Environment variables for S3 bucket access and Dask configuration
- Retry strategy for fault tolerance

### IAM Roles and Policies

- **Batch Service Role**: Allows AWS Batch to manage AWS resources
- **EC2 Instance Role**: Allows EC2 instances to access ECR and run containers
- **S3 Access Role**: Allows containers to access S3 buckets for data and results

## Prerequisites

Before deploying this infrastructure, ensure:

1. The VPC infrastructure is deployed (see `cloud/aws/vpc`)
2. The S3 buckets are created (see `cloud/aws/s3`)
3. The Docker image is built and pushed to Amazon ECR (see `cloud/docker`)

## Deployment

### 1. Initialize Terraform

```bash
cd cloud/aws/batch
terraform init
```

### 2. Review and Customize Variables

Edit `variables.tf` or create a `terraform.tfvars` file to customize:

```hcl
aws_region         = "us-east-1"
environment        = "poc"
batch_max_vcpus    = 32
batch_min_vcpus    = 0
batch_instance_types = ["c5.large", "c5.xlarge"]
job_vcpus          = 4
job_memory         = 16384
ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/pulse-retrodiction"
```

### 3. Apply the Terraform Configuration

```bash
terraform apply
```

Review the execution plan and confirm the resource creation.

## Submitting Jobs

After deploying the infrastructure, you can submit jobs using the AWS CLI:

```bash
aws batch submit-job \
  --job-name pulse-retrodiction-job-1 \
  --job-queue pulse-retrodiction-queue-poc \
  --job-definition pulse-retrodiction-training-poc
```

For customized job parameters:

```bash
aws batch submit-job \
  --job-name pulse-retrodiction-custom \
  --job-queue pulse-retrodiction-queue-poc \
  --job-definition pulse-retrodiction-training-poc \
  --container-overrides '{
    "command": ["python", "-m", "recursive_training.run_training", "--variables", "spx_close", "us_10y_yield", "wb_gdp_growth_annual", "--batch-size-days", "15", "--use-dask"],
    "environment": [
      {"name": "DASK_MEMORY_LIMIT", "value": "12GB"}
    ]
  }'
```

## Monitoring Jobs

### View Job Status

```bash
aws batch describe-jobs --jobs job-id
```

### View Logs

Jobs log to CloudWatch Logs:

```bash
aws logs get-log-events --log-group-name /aws/batch/job --log-stream-name pulse-retrodiction-job/default/job-id
```

## Optimization and Best Practices

1. **Cost Management**:
   - Use Spot Instances to reduce costs (set `capacity_type` to "SPOT" in compute resources)
   - Set appropriate `min_vcpus` to keep idle resources minimal

2. **Performance Tuning**:
   - Adjust job `vcpus` and `memory` based on workload requirements
   - Configure Dask parameters for efficient parallel processing

3. **Security**:
   - All security groups, IAM roles, and policies follow the principle of least privilege
   - Containers run in private subnets with controlled access

## Troubleshooting

Common issues and solutions:

1. **Job Stuck in RUNNABLE State**:
   - Insufficient compute capacity (increase `max_vcpus`)
   - Issues with subnet or security group configuration

2. **Job Fails with Exit Code 1**:
   - Check CloudWatch Logs for application errors
   - Verify environment variables are correctly set

3. **Container Cannot Access S3**:
   - Verify IAM role permissions
   - Check that NAT Gateway is properly configured for private subnets

## Clean Up

To remove the AWS Batch infrastructure:

```bash
terraform destroy
```

Note: This will remove only the Batch resources. S3 buckets and VPC infrastructure managed by other Terraform configurations will not be affected.