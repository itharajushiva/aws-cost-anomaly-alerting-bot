variable "name_prefix" {
  type        = string
  description = "Prefix for IAM role and policy resources"
}

variable "lambda_function_name" {
  type        = string
  description = "Name of the Lambda function for scoped CloudWatch logs permission"
}

variable "slack_secret_arn" {
  type        = string
  description = "ARN of the Secrets Manager secret holding the Slack Webhook URL"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to all IAM resources"
}
