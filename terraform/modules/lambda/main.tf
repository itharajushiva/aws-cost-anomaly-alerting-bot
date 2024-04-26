data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = var.output_zip_path
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_in_days
  tags              = var.tags
}

resource "aws_lambda_function" "cost_bot" {
  function_name    = var.function_name
  role             = var.role_arn
  handler          = "lambda_function.lambda_handler"
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = var.tags
}
