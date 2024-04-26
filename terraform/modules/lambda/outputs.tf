output "function_arn" {
  description = "ARN of the provisioned Lambda Function"
  value       = aws_lambda_function.cost_bot.arn
}

output "function_name" {
  description = "Name of the provisioned Lambda Function"
  value       = aws_lambda_function.cost_bot.function_name
}

output "log_group_name" {
  description = "Name of the CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}
