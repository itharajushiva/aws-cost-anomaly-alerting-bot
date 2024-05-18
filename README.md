# AWS Cost Anomaly Alerting Bot
> Automated cloud spend monitoring, rolling baseline anomaly detection, and Slack alerting for AWS environments.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Amazon EventBridge](https://img.shields.io/badge/Amazon-EventBridge-FF4F8B?logo=amazonaws&logoColor=white)](https://aws.amazon.com/eventbridge/)
[![AWS Cost Explorer](https://img.shields.io/badge/AWS-Cost_Explorer-232F3E?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)
[![Terraform](https://img.shields.io/badge/Terraform-1.7+-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Slack Block Kit](https://img.shields.io/badge/Slack-Block_Kit-4A154B?logo=slack&logoColor=white)](https://api.slack.com/block-kit)

---

## Overview

In multi-account AWS environments, sudden spending spikes often go unnoticed until monthly invoice reviews. Common root causes include unattached high-IOPS EBS volumes, forgotten GPU test instances, runaway Autoscaling policies, or unindexed API operations.

This repository provides an automated serverless pipeline that monitors daily service spend. Triggered daily via Amazon EventBridge, an AWS Lambda function:
1. Queries the **AWS Cost Explorer API** for daily service expenditures.
2. Evaluates costs against a **14-day rolling baseline** using statistical thresholds (mean, standard deviation, Z-score, percentage delta).
3. Identifies anomalous services and queries tag dimensions (`Owner`, `Environment`) to determine cost attribution.
4. Posts an interactive **Slack Block Kit** notification with direct links to AWS Cost Explorer.

All supporting AWS infrastructure is managed as code using modular Terraform.

---

## Architecture

```
                      +-----------------------------+
                      |     Amazon EventBridge      |
                      |   (Daily Cron: 08:00 UTC)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |         AWS Lambda          |
                      |        (Python 3.11)        |
                      +------+---------------+------+
                             |               |
              (1) Read URL   |               | (2) GetCostAndUsage
                             v               v
                   +----------------+ +-------------------+
                   |  AWS Secrets   | | AWS Cost Explorer |
                   |  Manager       | | API               |
                   +----------------+ +---------+---------+
                                                |
                                      Statistical Analysis
                                                |
                                      (3) Filter Anomalies
                                                |
                                                v
                                      +-------------------+
                                      |     Slack API     |
                                      | (Incoming Webhook)|
                                      +---------+---------+
                                                |
                                                v
                                      +-------------------+
                                      |  #finops-alerts   |
                                      +-------------------+
```

---

## Detection Algorithm

The anomaly detector flags cost spikes using a dual-threshold approach:

1. **Baseline Calculation**:
   Computes the mean ($\mu$) and sample standard deviation ($\sigma$) across a configurable historical window (default: 14 days):
   $$\mu = \frac{1}{N} \sum_{i=1}^{N} \text{Cost}_i$$
   $$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (\text{Cost}_i - \mu)^2}$$

2. **Outlier Filtering**:
   A service is flagged as an anomaly only if:
   - **Absolute dollar increase**: $\Delta = (\text{Cost}_{\text{target}} - \mu) \ge \text{MIN\_ABSOLUTE\_SPIKE\_USD}$ (default: $\$15.00$)
   - **Relative surge**: $\frac{\Delta}{\mu} \times 100\% \ge \text{PERCENTAGE\_THRESHOLD}$ (default: $25\%$) OR Z-Score: $Z = \frac{\Delta}{\sigma} \ge 2.0$

3. **Severity Classification**:
   - `CRITICAL`: Absolute delta $\ge \$100.00$ or percentage spike $\ge 100\%$.
   - `WARNING`: All other flagged anomalies meeting minimum thresholds.

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci-validation.yml             # Linting and automated test pipeline
├── docs/
│   ├── architecture/
│   │   └── system-design.md              # Detailed architecture & data models
│   └── runbooks/
│       └── cost-spike-triage.md          # FinOps incident response runbook
├── scripts/
│   ├── deploy.sh                         # Deployment automation script
│   ├── simulate-cost-spike.sh            # Local detector verification script
│   └── test-invoke.sh                    # Manual Lambda trigger script
├── src/
│   ├── anomaly_detector.py               # Rolling baseline detection engine
│   ├── cost_explorer.py                  # Cost Explorer API client
│   ├── lambda_function.py                # Main execution handler
│   ├── secrets_manager.py                # Secrets Manager client
│   └── slack_notifier.py                 # Slack Block Kit message builder
├── terraform/
│   ├── environments/
│   │   ├── dev/                          # Development configuration
│   │   └── prod/                         # Production configuration
│   └── modules/
│       ├── eventbridge/                  # CloudWatch Events rule & target
│       ├── iam/                          # Execution role & least-privilege policy
│       ├── lambda/                       # Lambda resource & archive packaging
│       ├── monitoring/                   # CloudWatch alarms for errors/throttles
│       └── secrets/                      # Secrets Manager secret definition
└── tests/
    ├── test_anomaly_detector.py          # Math & threshold evaluation tests
    ├── test_cost_explorer.py             # Date calculations & API mock tests
    └── test_slack_notifier.py            # Payload formatting tests
```

---

## Slack Alert Format

When an anomaly is detected, the bot posts a structured Block Kit message:

```text
[Header] AWS Cost Anomaly Alert — 2024-05-15
Environment: production  |  Account: 123456789012
Target Date: 2024-05-15  |  Total Spike: +$420.50

Total AWS Spend: $650.80 | Flagged Services: 2

1. Amazon Elastic Compute Cloud - Compute — CRITICAL
• Spend: $450.00
• 14-Day Baseline: $85.00/day (σ=$8.20)
• Spike: +$365.00 (+429.4% | Z-Score: 44.51)
• Top Owners/Tags: ml-training-cluster: $350.00, data-pipeline: $80.00

2. Amazon Relational Database Service — WARNING
• Spend: $115.50
• 14-Day Baseline: $60.00/day (σ=$4.10)
• Spike: +$55.50 (+92.5% | Z-Score: 13.54)
• Top Owners/Tags: staging-aurora: $52.00

[ View in Cost Explorer ]   [ Cost Anomaly Detection ]
```

---

## Getting Started

### Prerequisites
- AWS CLI v2 configured with adequate permissions
- Terraform >= 1.7.0
- Python 3.11+
- Incoming Slack Webhook URL

### Deployment

1. Navigate to the desired environment:
   ```bash
   cd terraform/environments/prod
   ```

2. Copy the sample variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Update `terraform.tfvars` with your settings:
   ```hcl
   aws_region             = "us-east-1"
   environment            = "prod"
   slack_webhook_url      = "https://example.com/replace-with-your-slack-webhook"
   percentage_threshold   = 25.0
   min_absolute_spike_usd = 15.0
   baseline_days          = 14
   resource_tag_key       = "Owner"
   ```

4. Initialize and apply:
   ```bash
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

---

## Testing

Run unit tests locally:
```bash
pip install -r requirements-dev.txt
pytest -v tests/
```

Run syntax and style checks:
```bash
flake8 src tests
```

Simulate the detection engine with synthetic data:
```bash
./scripts/simulate-cost-spike.sh
```

Trigger an on-demand invocation for a specific past date:
```bash
./scripts/test-invoke.sh cost-anomaly-bot-prod-lambda 2024-05-15
```

---

## Security & Best Practices

- **Credential Management**: Slack incoming webhook URLs are stored in AWS Secrets Manager and retrieved dynamically at runtime; no secrets exist in source files or Terraform state.
- **Least Privilege IAM**: The Lambda execution role policy permits read-only Cost Explorer operations (`ce:GetCostAndUsage`, `ce:GetDimensionValues`, `ce:GetTags`) and access strictly to its designated secret ARN.
- **Error Monitoring**: CloudWatch Metric Alarms monitor Lambda invocation failures and throttle events.
