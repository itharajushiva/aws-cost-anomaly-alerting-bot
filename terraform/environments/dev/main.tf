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

module "secrets" {
  source            = "../../modules/secrets"
  name_prefix       = local.name_prefix
  slack_webhook_url = var.slack_webhook_url
  tags              = var.tags
}

module "iam" {
  source               = "../../modules/iam"
  name_prefix          = local.name_prefix
  lambda_function_name = local.function_name
  slack_secret_arn     = module.secrets.secret_arn
  tags                 = var.tags
}

module "lambda" {
  source          = "../../modules/lambda"
  function_name   = local.function_name
  role_arn        = module.iam.role_arn
  source_dir      = "${path.module}/../../../src"
  output_zip_path = "${path.module}/build/lambda_package.zip"
  runtime         = "python3.11"
  timeout         = 120
  memory_size     = 128

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
    LOG_LEVEL              = "DEBUG"
  }

  tags = var.tags
}

module "eventbridge" {
  source               = "../../modules/eventbridge"
  rule_name            = "${local.name_prefix}-daily-cron"
  schedule_expression  = var.schedule_expression
  lambda_function_arn  = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  is_enabled           = false # Disabled by default in dev to prevent accidental triggers
  tags                 = var.tags
}
