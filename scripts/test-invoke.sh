#!/usr/bin/env bash
# ==============================================================================
# Script: test-invoke.sh
# Purpose: Manually trigger the Cost Anomaly Lambda function with custom dates
# ==============================================================================

set -euo pipefail

FUNCTION_NAME="${1:-cost-anomaly-bot-prod-lambda}"
TARGET_DATE="${2:-2024-05-15}"
REGION="${AWS_REGION:-us-east-1}"

echo "==========================================================="
echo " Invoking Cost Anomaly Bot Lambda: ${FUNCTION_NAME}"
echo " Target Date: ${TARGET_DATE}"
echo " Region: ${REGION}"
echo "==========================================================="

PAYLOAD=$(cat <<EOF
{
  "target_date": "${TARGET_DATE}"
}
EOF
)

aws lambda invoke \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}" \
  --payload "$(echo -n "${PAYLOAD}" | base64)" \
  --cli-binary-format raw-in-base64-out \
  response.json

echo "Lambda Invocation response:"
cat response.json | jq . || cat response.json
rm -f response.json
