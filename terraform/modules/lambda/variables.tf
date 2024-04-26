variable "function_name" {
  type        = string
  description = "Name of the AWS Lambda Function"
}

variable "role_arn" {
  type        = string
  description = "IAM role ARN executing the Lambda function"
}

variable "source_dir" {
  type        = string
  description = "Path to python source directory"
}

variable "output_zip_path" {
  type        = string
  description = "Path to write compiled zip package"
  default     = "lambda_payload.zip"
}

variable "runtime" {
  type        = string
  default     = "python3.11"
  description = "Python runtime environment"
}

variable "timeout" {
  type        = number
  default     = 180
  description = "Lambda function execution timeout in seconds"
}

variable "memory_size" {
  type        = number
  default     = 256
  description = "Lambda function memory in MB"
}

variable "environment_variables" {
  type        = map(string)
  default     = {}
  description = "Environment variables passed into Lambda"
}

variable "log_retention_in_days" {
  type        = number
  default     = 30
  description = "CloudWatch log retention in days"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to Lambda resources"
}
