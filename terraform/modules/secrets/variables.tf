variable "name_prefix" {
  type        = string
  description = "Prefix for Secrets Manager secret name"
}

variable "slack_webhook_url" {
  type        = string
  description = "Slack incoming webhook URL (can be placeholder initially)"
  sensitive   = true
  default     = "https://example.com/replace-with-your-slack-webhook"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to secret"
}
