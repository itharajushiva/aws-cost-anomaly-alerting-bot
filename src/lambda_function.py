"""
Lambda handler for scheduled CloudWatch / EventBridge execution.
Orchestrates: Cost Explorer -> Anomaly Detection -> Tag Enrichment -> Slack Alerts.
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict

from .cost_explorer import CostExplorerClient, calculate_date_windows
from .anomaly_detector import AnomalyDetector
from .slack_notifier import SlackNotifier
from .secrets_manager import get_secret

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda invocation handler triggered by EventBridge rule daily.
    Can also accept a test event with `{"target_date": "2024-05-15"}` for historical runs.
    """
    logger.info(f"Initiating Cost Anomaly Bot. Received event: {event}")

    # Environment variables configuration
    secret_name = os.getenv("SLACK_SECRET_NAME", "aws-cost-bot/slack-webhook")
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    environment = os.getenv("ENVIRONMENT", "production")
    aws_account_id = os.getenv("AWS_ACCOUNT_ID", "Unknown")
    
    # Anomaly thresholds
    baseline_days = int(os.getenv("BASELINE_DAYS", "14"))
    pct_threshold = float(os.getenv("PERCENTAGE_THRESHOLD", "25.0"))
    min_dollar_spike = float(os.getenv("MIN_ABSOLUTE_SPIKE_USD", "15.0"))
    critical_dollar_spike = float(os.getenv("CRITICAL_ABSOLUTE_USD", "100.0"))
    send_ok_summary = os.getenv("SEND_DAILY_SUMMARY", "true").lower() == "true"
    owner_tag_key = os.getenv("RESOURCE_TAG_KEY", "Owner")

    # 1. Fetch Slack Webhook Secret
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url and secret_name:
        try:
            secret_data = get_secret(secret_name, region_name=aws_region)
            webhook_url = secret_data.get("slack_webhook_url") or secret_data.get("webhook_url")
        except Exception as e:
            logger.error(f"Error reading Slack webhook from Secrets Manager: {e}")

    # 2. Compute date windows (defaults to yesterday if not overridden in event)
    target_date_override = event.get("target_date") if isinstance(event, dict) else None
    if target_date_override:
        parsed_target = datetime.strptime(target_date_override, "%Y-%m-%d").date()
        windows = calculate_date_windows(target_date=parsed_target, baseline_days=baseline_days)
    else:
        windows = calculate_date_windows(baseline_days=baseline_days)

    target_date = windows["target_date"]
    full_start = windows["full_query_start"]
    full_end = windows["full_query_end"]

    logger.info(
        f"Target analysis date: {target_date}. Rolling baseline query window: {full_start} to {full_end}"
    )

    # 3. Pull service-level spend from AWS Cost Explorer
    ce_client = CostExplorerClient()
    ce_results = ce_client.get_service_spend(start_date=full_start, end_date=full_end)

    # Calculate total daily spend on target date
    total_target_spend = 0.0
    for day_data in ce_results:
        if day_data["TimePeriod"]["Start"] == target_date:
            for grp in day_data.get("Groups", []):
                total_target_spend += float(grp.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0.0))

    # 4. Run Anomaly Detection Engine
    detector = AnomalyDetector(
        min_absolute_spike_usd=min_dollar_spike,
        percentage_threshold=pct_threshold,
        critical_absolute_usd=critical_dollar_spike,
    )
    anomalies = detector.analyze_service_spend(ce_results=ce_results, target_date=target_date)

    logger.info(f"Identified {len(anomalies)} anomalous services for {target_date}")

    # 5. Enrich Top Anomalies with Tag Ownership
    for record in anomalies[:5]:
        tag_data = ce_client.get_service_spend_by_tag(
            service_name=record.service,
            start_date=windows["target_start"],
            end_date=windows["target_end"],
            tag_key=owner_tag_key,
        )
        tag_breakdown: Dict[str, float] = {}
        for day in tag_data:
            for grp in day.get("Groups", []):
                keys = grp.get("Keys", [])
                tag_val = keys[0].replace(f"{owner_tag_key}$", "") if keys else "Untagged"
                cost = float(grp.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0.0))
                if cost > 0:
                    tag_breakdown[tag_val] = round(cost, 2)
        record.top_tags = tag_breakdown

    # 6. Deliver Slack Notification
    notifier = SlackNotifier(webhook_url=webhook_url or "")

    alert_sent = False
    if anomalies:
        payload = notifier.build_anomaly_blocks(
            target_date=target_date,
            anomalies=anomalies,
            aws_account_id=aws_account_id,
            environment=environment,
            total_daily_spend=round(total_target_spend, 2),
        )
        alert_sent = notifier.send_notification(payload)
    elif send_ok_summary:
        payload = notifier.build_summary_ok_blocks(
            target_date=target_date,
            total_daily_spend=round(total_target_spend, 2),
            aws_account_id=aws_account_id,
            environment=environment,
        )
        alert_sent = notifier.send_notification(payload)

    return {
        "statusCode": 200,
        "target_date": target_date,
        "total_spend_usd": round(total_target_spend, 2),
        "anomalies_detected": len(anomalies),
        "alert_dispatched": alert_sent,
        "anomalies": [
            {
                "service": a.service,
                "delta": a.absolute_delta,
                "percentage": a.percentage_increase,
                "severity": a.severity,
            }
            for a in anomalies
        ],
    }
