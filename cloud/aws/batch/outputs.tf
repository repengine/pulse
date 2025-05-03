# Output definitions for the AWS Batch infrastructure

output "compute_environment_arn" {
  description = "The ARN of the AWS Batch compute environment"
  value       = aws_batch_compute_environment.retrodiction_training.arn
}

output "compute_environment_name" {
  description = "The name of the AWS Batch compute environment"
  value       = aws_batch_compute_environment.retrodiction_training.compute_environment_name
}

output "job_queue_arn" {
  description = "The ARN of the AWS Batch job queue"
  value       = aws_batch_job_queue.retrodiction_training.arn
}

output "job_queue_name" {
  description = "The name of the AWS Batch job queue"
  value       = aws_batch_job_queue.retrodiction_training.name
}

output "job_definition_arn" {
  description = "The ARN of the AWS Batch job definition"
  value       = aws_batch_job_definition.retrodiction_training.arn
}

output "job_definition_name" {
  description = "The name of the AWS Batch job definition"
  value       = aws_batch_job_definition.retrodiction_training.name
}

output "batch_service_role_arn" {
  description = "The ARN of the IAM role for AWS Batch service"
  value       = aws_iam_role.batch_service_role.arn
}

output "batch_instance_profile_arn" {
  description = "The ARN of the IAM instance profile for EC2 instances in the compute environment"
  value       = aws_iam_instance_profile.batch_instance_profile.arn
}

output "batch_instance_role_arn" {
  description = "The ARN of the IAM role for EC2 instances in the compute environment"
  value       = aws_iam_role.ec2_instance_role.arn
}