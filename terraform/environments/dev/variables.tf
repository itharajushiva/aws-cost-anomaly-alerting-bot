variable "aws_region" {
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  default     = "dev"
}

variable "project_name" {
  type        = string
  default     = "cost-anomaly-bot"
}

variable "slack_webhook_url" {
  type        = string
  sensitive   = true
  default     = "https://example.com/replace-with-your-slack-webhook"
}

variable "schedule_expression" {
  type        = string
  default     = "cron(0 8 * * ? *)"
}

variable "baseline_days" {
  type        = number
  default     = 7
}

variable "percentage_threshold" {
  type        = number
  default     = 20.0
}

variable "min_absolute_spike_usd" {
  type        = number
  default     = 5.0
}

variable "critical_absolute_usd" {
  type        = number
  default     = 50.0
}

variable "resource_tag_key" {
  type        = string
  default     = "Owner"
}

variable "send_daily_summary" {
  type        = bool
  default     = true
}

variable "tags" {
  type        = map(string)
  default     = {
    Project     = "CloudCostGovernance"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
