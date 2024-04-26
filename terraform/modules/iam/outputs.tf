output "role_arn" {
  description = "ARN of the Lambda IAM Execution Role"
  value       = aws_iam_role.lambda_exec.arn
}

output "role_name" {
  description = "Name of the Lambda IAM Execution Role"
  value       = aws_iam_role.lambda_exec.name
}

output "policy_arn" {
  description = "ARN of the attached IAM Policy"
  value       = aws_iam_policy.lambda_policy.arn
}
