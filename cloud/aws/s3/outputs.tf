# Outputs for the S3 Buckets

output "data_bucket_id" {
  description = "The name of the data bucket"
  value       = aws_s3_bucket.data_bucket.id
}

output "data_bucket_arn" {
  description = "The ARN of the data bucket"
  value       = aws_s3_bucket.data_bucket.arn
}

output "results_bucket_id" {
  description = "The name of the results bucket"
  value       = aws_s3_bucket.results_bucket.id
}

output "results_bucket_arn" {
  description = "The ARN of the results bucket"
  value       = aws_s3_bucket.results_bucket.arn
}

output "s3_access_role_arn" {
  description = "The ARN of the IAM role for S3 access"
  value       = aws_iam_role.s3_access_role.arn
}

output "s3_access_role_name" {
  description = "The name of the IAM role for S3 access"
  value       = aws_iam_role.s3_access_role.name
}

output "s3_access_policy_arn" {
  description = "The ARN of the IAM policy for S3 access"
  value       = aws_iam_policy.s3_access_policy.arn
}