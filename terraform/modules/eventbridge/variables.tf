variable "rule_name" {
  type        = string
  description = "Name of the EventBridge rule"
}

variable "schedule_expression" {
  type        = string
  default     = "cron(0 8 * * ? *)" # Runs daily at 08:00 UTC (after CE finishes final daily aggregation)
  description = "Cron or rate expression for the EventBridge trigger"
}

variable "lambda_function_arn" {
  type        = string
  description = "ARN of the target Lambda function"
}

variable "lambda_function_name" {
  type        = string
  description = "Name of the target Lambda function for permission granting"
}

variable "is_enabled" {
  type        = bool
  default     = true
  description = "Whether the EventBridge trigger rule is active"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to EventBridge resources"
}
