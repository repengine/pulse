# Variables for the AWS S3 Buckets

variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., poc, dev, staging, prod)"
  type        = string
  default     = "poc"
}

variable "project" {
  description = "Project name for tagging resources"
  type        = string
  default     = "pulse-retrodiction"
}

variable "bucket_name_prefix" {
  description = "Prefix for S3 bucket names"
  type        = string
  default     = "pulse-retrodiction"
}

variable "data_bucket_name" {
  description = "Name of the S3 bucket for data storage"
  type        = string
  default     = "data"
}

variable "results_bucket_name" {
  description = "Name of the S3 bucket for results storage"
  type        = string
  default     = "results"
}

variable "enable_versioning" {
  description = "Whether to enable versioning on the S3 buckets"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Whether to enable server-side encryption on the S3 buckets"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for the S3 buckets"
  type        = map(string)
  default     = {}
}