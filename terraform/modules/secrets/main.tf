resource "aws_secretsmanager_secret" "slack_webhook" {
  name                    = "${var.name_prefix}/slack-webhook"
  description             = "Incoming Slack Webhook URL for Cost Anomaly Alerting Bot"
  recovery_window_in_days = 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "slack_webhook" {
  secret_id = aws_secretsmanager_secret.slack_webhook.id
  secret_string = jsonencode({
    slack_webhook_url = var.slack_webhook_url
  })
}
