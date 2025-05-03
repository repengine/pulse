# AWS Batch infrastructure for Pulse Retrodiction Training POC
# This Terraform configuration sets up the AWS Batch resources for running containerized jobs

provider "aws" {
  region = var.aws_region
}

# Local variables
locals {
  common_tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

# IAM role for AWS Batch service
resource "aws_iam_role" "batch_service_role" {
  name = "pulse-retrodiction-batch-service-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "batch.amazonaws.com"
        }
      },
    ]
  })

  tags = local.common_tags
}

# Attach the AWS Batch service role policy
resource "aws_iam_role_policy_attachment" "batch_service_role" {
  role       = aws_iam_role.batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

# Instance profile for EC2 instances in the compute environment
resource "aws_iam_instance_profile" "batch_instance_profile" {
  name = "pulse-retrodiction-batch-instance-profile-${var.environment}"
  role = aws_iam_role.ec2_instance_role.name
}

# IAM role for EC2 instances in the compute environment
resource "aws_iam_role" "ec2_instance_role" {
  name = "pulse-retrodiction-batch-instance-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })

  tags = local.common_tags
}

# Attach the EC2 container service role policy
resource "aws_iam_role_policy_attachment" "ec2_instance_role" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSContainerServiceforEC2Role"
}

# Attach the S3 access policy to the EC2 instance role
resource "aws_iam_role_policy_attachment" "ec2_s3_access" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = data.aws_iam_policy.s3_access_policy.arn
}

# Get the S3 access policy ARN from the S3 module
data "aws_iam_policy" "s3_access_policy" {
  name = "pulse-retrodiction-s3-access-policy-${var.environment}"
}

# AWS Batch compute environment
resource "aws_batch_compute_environment" "retrodiction_training" {
  compute_environment_name = "pulse-retrodiction-compute-${var.environment}"
  type                     = "MANAGED"
  service_role             = aws_iam_role.batch_service_role.arn
  state                    = "ENABLED"

  compute_resources {
    type                = "EC2"
    allocation_strategy = "BEST_FIT_PROGRESSIVE"
    
    max_vcpus = var.batch_max_vcpus
    min_vcpus = var.batch_min_vcpus

    instance_type = var.batch_instance_types

    security_group_ids = [
      data.aws_security_group.retrodiction_training_sg.id
    ]

    subnets = data.aws_subnets.private_subnets.ids

    instance_role = aws_iam_instance_profile.batch_instance_profile.arn
  }

  tags = merge(
    local.common_tags,
    {
      Name = "Pulse Retrodiction Training Compute Environment"
    }
  )

  depends_on = [aws_iam_role_policy_attachment.batch_service_role]
}

# Get the security group from the VPC module
data "aws_security_group" "retrodiction_training_sg" {
  name = "retrodiction-training-sg"
}

# Get the private subnets from the VPC module
data "aws_subnets" "private_subnets" {
  filter {
    name   = "tag:Name"
    values = ["private-subnet-*"]
  }
}

# AWS Batch job queue
resource "aws_batch_job_queue" "retrodiction_training" {
  name                 = "pulse-retrodiction-queue-${var.environment}"
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.retrodiction_training.arn]

  tags = merge(
    local.common_tags,
    {
      Name = "Pulse Retrodiction Training Job Queue"
    }
  )
}

# AWS Batch job definition
resource "aws_batch_job_definition" "retrodiction_training" {
  name = "pulse-retrodiction-training-${var.environment}"
  type = "container"
  
  container_properties = jsonencode({
    image = "${var.ecr_repository_url}:latest"
    vcpus = var.job_vcpus
    memory = var.job_memory
    command = [
      "python", 
      "-m", 
      "recursive_training.run_training", 
      "--variables", 
      "spx_close", 
      "us_10y_yield", 
      "--batch-size-days", 
      "30",
      "--use-dask"
    ]
    jobRoleArn = data.aws_iam_role.s3_access_role.arn
    environment = [
      {
        name = "S3_DATA_BUCKET"
        value = var.data_bucket_name
      },
      {
        name = "S3_RESULTS_BUCKET"
        value = var.results_bucket_name
      },
      {
        name = "LOG_LEVEL"
        value = "INFO"
      },
      {
        name = "USE_DASK"
        value = "true"
      },
      {
        name = "DASK_THREADS"
        value = "2"
      },
      {
        name = "DASK_MEMORY_LIMIT"
        value = "8GB"
      }
    ]
    volumes = [
      {
        name = "temp-volume"
        host = {
          sourcePath = "/tmp"
        }
      }
    ]
    mountPoints = [
      {
        containerPath = "/app/logs"
        sourceVolume = "temp-volume"
        readOnly = false
      }
    ]
    ulimits = [
      {
        hardLimit = 10240
        name = "nofile"
        softLimit = 10240
      }
    ]
    resourceRequirements = [
      {
        type = "MEMORY"
        value = toString(var.job_memory)
      },
      {
        type = "VCPU"
        value = toString(var.job_vcpus)
      }
    ]
  })

  retry_strategy {
    attempts = 3
    evaluate_on_exit {
      action    = "RETRY"
      on_exit_code = "1"
    }
    evaluate_on_exit {
      action    = "EXIT"
      on_exit_code = "0"
    }
    evaluate_on_exit {
      action    = "EXIT"
      on_reason = "*"
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "Pulse Retrodiction Training Job Definition"
    }
  )
}

# Get the S3 access role from the S3 module
data "aws_iam_role" "s3_access_role" {
  name = "pulse-retrodiction-s3-access-role-${var.environment}"
}