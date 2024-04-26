resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = var.rule_name
  description         = "Daily scheduled trigger for Serverless AWS Cost Anomaly Alerting Bot"
  schedule_expression = var.schedule_expression
  is_enabled          = var.is_enabled

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "TriggerCostAnomalyLambda"
  arn       = var.lambda_function_arn

  # Empty JSON object triggers standard T-1 baseline comparison
  input = jsonencode({})
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}
