output "error_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.lambda_errors.arn
}

output "throttle_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.lambda_throttles.arn
}
