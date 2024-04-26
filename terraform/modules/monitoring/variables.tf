variable "function_name" {
  type        = string
  description = "Name of the Lambda function to monitor"
}

variable "alarm_sns_topic_arns" {
  type        = list(string)
  default     = []
  description = "SNS Topic ARNs to notify when Lambda fails or throttles"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}
