"""
AWS Cost Explorer client wrapper for daily spend extraction,
rolling baseline queries, and tag/account dimensions.
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CostExplorerClient:
    """Wrapper around AWS Cost Explorer boto3 client with retries and pagination."""

    def __init__(self, ce_client: Optional[Any] = None):
        self.client = ce_client or boto3.client("ce", region_name="us-east-1")

    def get_service_spend(
        self,
        start_date: str,
        end_date: str,
        metric: str = "UnblendedCost",
    ) -> List[Dict[str, Any]]:
        """
        Pulls daily spend grouped by SERVICE dimension.
        Dates in 'YYYY-MM-DD' format (end_date is exclusive per AWS CE API).
        """
        logger.info(f"Querying CE service spend from {start_date} to {end_date}")
        results = []
        next_page_token = None

        while True:
            kwargs: Dict[str, Any] = {
                "TimePeriod": {"Start": start_date, "End": end_date},
                "Granularity": "DAILY",
                "Metrics": [metric],
                "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
            }
            if next_page_token:
                kwargs["NextPageToken"] = next_page_token

            try:
                response = self.client.get_cost_and_usage(**kwargs)
            except ClientError as e:
                logger.error(f"Failed to query Cost Explorer: {e}")
                raise

            results.extend(response.get("ResultsByTime", []))
            next_page_token = response.get("NextPageToken")
            if not next_page_token:
                break

        return results

    def get_service_spend_with_accounts(
        self,
        start_date: str,
        end_date: str,
        metric: str = "UnblendedCost",
    ) -> List[Dict[str, Any]]:
        """
        Pulls spend grouped by LINKED_ACCOUNT and SERVICE for multi-account breakdown.
        """
        logger.info(f"Querying CE spend grouped by Account & Service: {start_date} to {end_date}")
        results = []
        next_page_token = None

        while True:
            kwargs: Dict[str, Any] = {
                "TimePeriod": {"Start": start_date, "End": end_date},
                "Granularity": "DAILY",
                "Metrics": [metric],
                "GroupBy": [
                    {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                ],
            }
            if next_page_token:
                kwargs["NextPageToken"] = next_page_token

            try:
                response = self.client.get_cost_and_usage(**kwargs)
            except ClientError as e:
                logger.error(f"Failed to query CE account/service spend: {e}")
                raise

            results.extend(response.get("ResultsByTime", []))
            next_page_token = response.get("NextPageToken")
            if not next_page_token:
                break

        return results

    def get_service_spend_by_tag(
        self,
        service_name: str,
        start_date: str,
        end_date: str,
        tag_key: str = "Owner",
        metric: str = "UnblendedCost",
    ) -> List[Dict[str, Any]]:
        """
        Pulls cost breakdown for a specific service grouped by a designated tag (e.g., Owner, Environment).
        """
        logger.info(f"Querying CE spend for service '{service_name}' grouped by tag '{tag_key}'")
        results = []
        next_page_token = None

        while True:
            kwargs: Dict[str, Any] = {
                "TimePeriod": {"Start": start_date, "End": end_date},
                "Granularity": "DAILY",
                "Filter": {
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": [service_name],
                    }
                },
                "Metrics": [metric],
                "GroupBy": [{"Type": "TAG", "Key": tag_key}],
            }
            if next_page_token:
                kwargs["NextPageToken"] = next_page_token

            try:
                response = self.client.get_cost_and_usage(**kwargs)
            except ClientError as e:
                logger.warning(f"Failed to query CE tag breakdown for {service_name}: {e}")
                return []

            results.extend(response.get("ResultsByTime", []))
            next_page_token = response.get("NextPageToken")
            if not next_page_token:
                break

        return results


def calculate_date_windows(target_date: Optional[date] = None, baseline_days: int = 14) -> Dict[str, str]:
    """
    Computes date ranges for the target day and the rolling baseline window.
    Because AWS Cost Explorer data has up to 24-48h finalization lag,
    the default target date is typically 'yesterday' (T-1).
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    target_start = target_date.strftime("%Y-%m-%d")
    target_end = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

    baseline_start = (target_date - timedelta(days=baseline_days)).strftime("%Y-%m-%d")
    baseline_end = target_start  # Exclusive, covers up to day before target

    return {
        "target_date": target_start,
        "target_start": target_start,
        "target_end": target_end,
        "baseline_start": baseline_start,
        "baseline_end": baseline_end,
        "full_query_start": baseline_start,
        "full_query_end": target_end,
    }
