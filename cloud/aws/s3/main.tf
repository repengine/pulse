# AWS S3 Buckets for Pulse Retrodiction Training POC

provider "aws" {
  region = var.aws_region
}

# Local variables for bucket naming and common configurations
locals {
  data_bucket_name    = "${var.bucket_name_prefix}-${var.data_bucket_name}-${var.environment}"
  results_bucket_name = "${var.bucket_name_prefix}-${var.results_bucket_name}-${var.environment}"
  common_tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

# S3 bucket for input data storage
resource "aws_s3_bucket" "data_bucket" {
  bucket = local.data_bucket_name

  tags = merge(
    local.common_tags,
    {
      Name = "Pulse Retrodiction Data Bucket"
      Type = "data-storage"
    }
  )
}

# S3 bucket for results storage
resource "aws_s3_bucket" "results_bucket" {
  bucket = local.results_bucket_name

  tags = merge(
    local.common_tags,
    {
      Name = "Pulse Retrodiction Results Bucket"
      Type = "results-storage"
    }
  )
}

# Enable versioning for data bucket if specified
resource "aws_s3_bucket_versioning" "data_bucket_versioning" {
  bucket = aws_s3_bucket.data_bucket.id
  
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Enable versioning for results bucket if specified
resource "aws_s3_bucket_versioning" "results_bucket_versioning" {
  bucket = aws_s3_bucket.results_bucket.id
  
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Enable encryption for data bucket if specified
resource "aws_s3_bucket_server_side_encryption_configuration" "data_bucket_encryption" {
  count = var.enable_encryption ? 1 : 0
  
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Enable encryption for results bucket if specified
resource "aws_s3_bucket_server_side_encryption_configuration" "results_bucket_encryption" {
  count = var.enable_encryption ? 1 : 0
  
  bucket = aws_s3_bucket.results_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to data bucket
resource "aws_s3_bucket_public_access_block" "data_bucket_public_access_block" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Block public access to results bucket
resource "aws_s3_bucket_public_access_block" "results_bucket_public_access_block" {
  bucket = aws_s3_bucket.results_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role for accessing the S3 buckets
resource "aws_iam_role" "s3_access_role" {
  name = "pulse-retrodiction-s3-access-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "batch.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for S3 bucket access
resource "aws_iam_policy" "s3_access_policy" {
  name        = "pulse-retrodiction-s3-access-policy-${var.environment}"
  description = "Policy for accessing Pulse Retrodiction S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          aws_s3_bucket.results_bucket.arn
        ]
      },
      {
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.data_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.results_bucket.arn}/*"
        ]
      }
    ]
  })
}

# Attach the S3 access policy to the IAM role
resource "aws_iam_role_policy_attachment" "s3_access_policy_attachment" {
  role       = aws_iam_role.s3_access_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}