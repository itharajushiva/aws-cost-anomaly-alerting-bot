"""
Slack notification client using Block Kit formatting and incoming webhooks.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import urllib3

from .anomaly_detector import AnomalyRecord

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Dispatches Slack Block Kit alerts for detected cloud cost anomalies."""

    def __init__(self, webhook_url: str, http_pool: Optional[urllib3.PoolManager] = None):
        self.webhook_url = webhook_url
        self.http = http_pool or urllib3.PoolManager()

    def build_anomaly_blocks(
        self,
        target_date: str,
        anomalies: List[AnomalyRecord],
        aws_account_id: str = "Unknown",
        environment: str = "production",
        total_daily_spend: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Constructs a Slack Block Kit payload highlighting anomalies,
        top cost drivers, rolling baseline comparisons, and tag owners.
        """
        total_spike = sum(a.absolute_delta for a in anomalies)
        critical_count = sum(1 for a in anomalies if a.severity == "CRITICAL")

        header_emoji = "🚨" if critical_count > 0 else "⚠️"
        header_text = f"{header_emoji} AWS Cost Anomaly Alert — {target_date}"

        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Environment:*\n`{environment}`"},
                    {"type": "mrkdwn", "text": f"*AWS Account:*\n`{aws_account_id}`"},
                    {"type": "mrkdwn", "text": f"*Target Date:*\n{target_date}"},
                    {"type": "mrkdwn", "text": f"*Total Spike Above Baseline:*\n*+${total_spike:,.2f}*"},
                ],
            },
            {"type": "divider"},
        ]

        if total_daily_spend is not None:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📊 *Total AWS Spend on {target_date}:* `${total_daily_spend:,.2f}` | *Flagged Anomalous Services:* `{len(anomalies)}`",
                    }
                ],
            })

        # Top anomalous services details (limit to top 10 to keep within Slack block constraints)
        for idx, item in enumerate(anomalies[:10], 1):
            severity_badge = "🔴 *CRITICAL*" if item.severity == "CRITICAL" else "🟡 *WARNING*"
            delta_sign = "+" if item.absolute_delta >= 0 else ""
            
            # Format tag owners if present
            tags_text = ""
            if item.top_tags:
                tag_parts = [f"`{k}`: ${v:,.2f}" for k, v in list(item.top_tags.items())[:3]]
                tags_text = f"\n🏷️ *Top Owners/Tags:* {', '.join(tag_parts)}"

            service_section = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{idx}. {item.service}* — {severity_badge}\n"
                        f"• *Spend on {target_date}:* `${item.target_cost:,.2f}`\n"
                        f"• *Rolling 14-Day Baseline:* `${item.baseline_mean:,.2f}/day` (σ=${item.baseline_std:,.2f})\n"
                        f"• *Spike:* *{delta_sign}${item.absolute_delta:,.2f}* ({delta_sign}{item.percentage_increase:.1f}% | Z-Score: {item.z_score:.2f})"
                        f"{tags_text}"
                    ),
                },
            }
            blocks.append(service_section)

        # Action Buttons
        blocks.extend([
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in Cost Explorer", "emoji": True},
                        "url": "https://console.aws.amazon.com/cost-management/home#/cost-explorer",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Cost Anomaly Detection", "emoji": True},
                        "url": "https://console.aws.amazon.com/costmanagement/home#/anomaly-detection",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "AWS Cost Anomaly Detection | Automated Alert",
                    }
                ],
            },
        ])

        return {"blocks": blocks}

    def build_summary_ok_blocks(
        self,
        target_date: str,
        total_daily_spend: float,
        aws_account_id: str,
        environment: str,
    ) -> Dict[str, Any]:
        """Builds a positive daily confirmation block when no anomalies are detected."""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"✅ AWS Daily Cost Report — No Anomalies Detected",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Environment:*\n`{environment}`"},
                        {"type": "mrkdwn", "text": f"*AWS Account:*\n`{aws_account_id}`"},
                        {"type": "mrkdwn", "text": f"*Target Date:*\n{target_date}"},
                        {"type": "mrkdwn", "text": f"*Total Daily Spend:*\n*${total_daily_spend:,.2f}*"},
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "All service expenditures are within healthy 14-day rolling thresholds.",
                        }
                    ],
                },
            ]
        }

    def send_notification(self, payload: Dict[str, Any]) -> bool:
        """Sends serialized JSON payload to Slack Webhook."""
        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured; skipping transmission.")
            return False

        try:
            encoded_data = json.dumps(payload).encode("utf-8")
            response = self.http.request(
                "POST",
                self.webhook_url,
                body=encoded_data,
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )
            if response.status != 200:
                logger.error(f"Slack webhook error HTTP {response.status}: {response.data.decode('utf-8')}")
                return False
            logger.info("Slack notification delivered successfully.")
            return True
        except Exception as e:
            logger.error(f"Exception sending Slack notification: {e}")
            raise
