variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS deployment region"
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Deployment environment name"
}

variable "project_name" {
  type        = string
  default     = "cost-anomaly-bot"
  description = "Project name prefix"
}

variable "slack_webhook_url" {
  type        = string
  description = "Slack Incoming Webhook URL"
  sensitive   = true
}

variable "schedule_expression" {
  type        = string
  default     = "cron(0 8 * * ? *)" # 08:00 UTC daily
  description = "EventBridge cron schedule"
}

variable "baseline_days" {
  type        = number
  default     = 14
  description = "Number of historical days to evaluate baseline"
}

variable "percentage_threshold" {
  type        = number
  default     = 25.0
  description = "Percentage increase required to flag an anomaly"
}

variable "min_absolute_spike_usd" {
  type        = number
  default     = 15.0
  description = "Minimum dollar jump required to flag an anomaly"
}

variable "critical_absolute_usd" {
  type        = number
  default     = 100.0
  description = "Dollar spike threshold for CRITICAL severity tag"
}

variable "resource_tag_key" {
  type        = string
  default     = "Owner"
  description = "Primary resource tag used for cost driver attribution"
}

variable "send_daily_summary" {
  type        = bool
  default     = true
  description = "Whether to send OK summary message if no spikes are flagged"
}

variable "tags" {
  type        = map(string)
  default     = {
    Project     = "CloudCostGovernance"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
