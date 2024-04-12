import json
import pytest
from src.anomaly_detector import AnomalyRecord
from src.slack_notifier import SlackNotifier


def test_build_anomaly_blocks():
    notifier = SlackNotifier(webhook_url="https://example.com/slack/test-webhook")
    records = [
        AnomalyRecord(
            service="Amazon Relational Database Service",
            target_cost=150.0,
            baseline_mean=20.0,
            baseline_std=2.5,
            percentage_increase=650.0,
            absolute_delta=130.0,
            z_score=52.0,
            top_tags={"data-eng-team": 140.0, "analytics-qa": 10.0},
            severity="CRITICAL",
        )
    ]

    payload = notifier.build_anomaly_blocks(
        target_date="2024-05-15",
        anomalies=records,
        aws_account_id="123456789012",
        environment="production",
        total_daily_spend=280.50,
    )

    blocks = payload["blocks"]
    assert any("AWS Cost Anomaly Alert" in json.dumps(b) for b in blocks)
    assert any("Amazon Relational Database Service" in json.dumps(b) for b in blocks)
    assert any("CRITICAL" in json.dumps(b) for b in blocks)
    assert any("data-eng-team" in json.dumps(b) for b in blocks)


def test_send_notification_success(mocker):
    mock_pool = mocker.MagicMock()
    mock_pool.request.return_value.status = 200
    mock_pool.request.return_value.data = b"ok"

    notifier = SlackNotifier(
        webhook_url="https://example.com/slack/test-webhook",
        http_pool=mock_pool,
    )

    success = notifier.send_notification({"text": "Hello Slack"})
    assert success is True
    assert mock_pool.request.call_count == 1
