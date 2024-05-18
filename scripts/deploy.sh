#!/usr/bin/env bash
# ==============================================================================
# Script: deploy.sh
# Purpose: Build, package, and deploy Cost Anomaly Bot using Terraform
# ==============================================================================

set -euo pipefail

ENV="${1:-prod}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT_DIR}/terraform/environments/${ENV}"

echo "==========================================================="
echo " Deploying Serverless Cloud Cost Anomaly Bot to [${ENV}]"
echo "==========================================================="

if [ ! -d "${TF_DIR}" ]; then
  echo "Error: Environment directory ${TF_DIR} not found!"
  exit 1
fi

cd "${TF_DIR}"

if [ ! -f "terraform.tfvars" ]; then
  echo "Warning: terraform.tfvars not detected in ${TF_DIR}."
  if [ -f "terraform.tfvars.example" ]; then
    echo "Copying terraform.tfvars.example to terraform.tfvars. Please update with secrets."
    cp terraform.tfvars.example terraform.tfvars
  fi
fi

echo "[1/3] Initializing Terraform..."
terraform init

echo "[2/3] Validating & Planning Terraform..."
terraform plan -out=tfplan

echo "[3/3] Applying Terraform execution plan..."
terraform apply -auto-approve tfplan

echo "Deployment complete! Lambda function and EventBridge schedules are active."
