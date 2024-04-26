output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = module.lambda.function_arn
}

output "eventbridge_rule_name" {
  description = "EventBridge Scheduled Rule Name"
  value       = module.eventbridge.rule_name
}

output "slack_secret_arn" {
  description = "ARN of Slack Webhook Secret in AWS Secrets Manager"
  value       = module.secrets.secret_arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group storing execution logs"
  value       = module.lambda.log_group_name
}
