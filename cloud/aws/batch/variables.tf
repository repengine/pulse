# Variables for AWS Batch Infrastructure

variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "The deployment environment (e.g., poc, dev, prod)"
  type        = string
  default     = "poc"
}

variable "project" {
  description = "The project name"
  type        = string
  default     = "Pulse"
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "batch_max_vcpus" {
  description = "Maximum number of vCPUs for the compute environment"
  type        = number
  default     = 32
}

variable "batch_min_vcpus" {
  description = "Minimum number of vCPUs for the compute environment"
  type        = number
  default     = 0
}

variable "batch_instance_types" {
  description = "List of EC2 instance types to use in the compute environment"
  type        = list(string)
  default     = ["c5.large", "c5.xlarge", "c5.2xlarge"]
}

variable "job_vcpus" {
  description = "Number of vCPUs to allocate to each job"
  type        = number
  default     = 4
}

variable "job_memory" {
  description = "Amount of memory (in MiB) to allocate to each job"
  type        = number
  default     = 16384
}

variable "ecr_repository_url" {
  description = "The URL of the ECR repository where container images are stored"
  type        = string
  default     = null
}

variable "data_bucket_name" {
  description = "Name of the S3 bucket for input data"
  type        = string
  default     = "pulse-retrodiction-data-poc"
}

variable "results_bucket_name" {
  description = "Name of the S3 bucket for results data"
  type        = string
  default     = "pulse-retrodiction-results-poc"
}