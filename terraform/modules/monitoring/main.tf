resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.function_name}-invocation-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggers if the Cost Anomaly Alerting Bot fails during execution"
  alarm_actions       = var.alarm_sns_topic_arns

  dimensions = {
    FunctionName = var.function_name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.function_name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggers if the Cost Anomaly Alerting Bot experiences Lambda concurrency throttling"
  alarm_actions       = var.alarm_sns_topic_arns

  dimensions = {
    FunctionName = var.function_name
  }

  tags = var.tags
}
