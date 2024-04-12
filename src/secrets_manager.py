"""
AWS Secrets Manager helper for webhook URL retrieval.
"""

import json
import logging
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_secret(secret_name: str, region_name: str = "us-east-1", client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Fetches JSON or string secret from AWS Secrets Manager.
    """
    if client is None:
        client = boto3.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise

    if "SecretString" in response:
        secret_str = response["SecretString"]
        try:
            return json.loads(secret_str)
        except json.JSONDecodeError:
            return {"slack_webhook_url": secret_str}
    
    return {}
