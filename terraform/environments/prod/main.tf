terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.48.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4.2"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

data "aws_caller_identity" "current" {}

locals {
  name_prefix   = "${var.project_name}-${var.environment}"
  function_name = "${local.name_prefix}-lambda"
}

# 1. Secrets Manager: Secure Storage for Slack Webhook
module "secrets" {
  source            = "../../modules/secrets"
  name_prefix       = local.name_prefix
  slack_webhook_url = var.slack_webhook_url
  tags              = var.tags
}

# 2. IAM: Least Privilege Execution Role & Policies
module "iam" {
  source               = "../../modules/iam"
  name_prefix          = local.name_prefix
  lambda_function_name = local.function_name
  slack_secret_arn     = module.secrets.secret_arn
  tags                 = var.tags
}

# 3. Lambda: Python Anomaly Detection Core Function
module "lambda" {
  source          = "../../modules/lambda"
  function_name   = local.function_name
  role_arn        = module.iam.role_arn
  source_dir      = "${path.module}/../../../src"
  output_zip_path = "${path.module}/build/lambda_package.zip"
  runtime         = "python3.11"
  timeout         = 180
  memory_size     = 256

  environment_variables = {
    SLACK_SECRET_NAME      = module.secrets.secret_name
    ENVIRONMENT            = var.environment
    AWS_ACCOUNT_ID         = data.aws_caller_identity.current.account_id
    BASELINE_DAYS          = tostring(var.baseline_days)
    PERCENTAGE_THRESHOLD   = tostring(var.percentage_threshold)
    MIN_ABSOLUTE_SPIKE_USD = tostring(var.min_absolute_spike_usd)
    CRITICAL_ABSOLUTE_USD  = tostring(var.critical_absolute_usd)
    RESOURCE_TAG_KEY       = var.resource_tag_key
    SEND_DAILY_SUMMARY     = tostring(var.send_daily_summary)
    LOG_LEVEL              = "INFO"
  }

  tags = var.tags
}

# 4. EventBridge: Scheduled Daily Cron Trigger
module "eventbridge" {
  source               = "../../modules/eventbridge"
  rule_name            = "${local.name_prefix}-daily-cron"
  schedule_expression  = var.schedule_expression
  lambda_function_arn  = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  tags                 = var.tags
}

# 5. Monitoring: CloudWatch Alarms for Lambda Failures & Throttles
module "monitoring" {
  source        = "../../modules/monitoring"
  function_name = module.lambda.function_name
  tags          = var.tags
}
