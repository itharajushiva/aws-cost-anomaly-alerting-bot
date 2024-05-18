# FinOps Incident & Cost Anomaly Runbook

---

## 1. Trigger Scenario

When an alert is received in `#finops-alerts` or `#devops-oncall`:

```text
[CRITICAL] AWS Cost Anomaly Alert — 2024-05-15
• Amazon Elastic Compute Cloud - Compute
• Spend on 2024-05-15: $425.80
• Rolling 14-Day Baseline: $48.20/day (std dev: $4.50)
• Spike: +$377.60 (+783.4% | Z-Score: 83.91)
• Top Owners/Tags: ml-training-job: $320.00, data-eng: $45.00
```

---

## 2. Standard Triage Procedure

### Step 1: Verify Slack Alert Details
- Note the **Target Date**, **AWS Account ID**, **Service Name**, and **Reported Spike**.
- Check the **Top Owners/Tags** section in the alert to identify the team or application owner.

### Step 2: Open Cost Explorer Console
Click the **"View in Cost Explorer"** button directly on the Slack message, or navigate to:
```
AWS Console -> Cost Management -> Cost Explorer
```
- Group by: `Usage Type` or `API Operation`.
- Filter by: Flagged Service (e.g. `Amazon Elastic Compute Cloud - Compute`).

### Step 3: Investigate Resource Runaway Causes
Common root causes by service:
- **Amazon EC2 / GPU Instances**:
  - Runaway GPU instances (e.g. `p3.8xlarge`, `g5.4xlarge`) left running overnight after model training.
  - Autoscaling group failure to scale in due to unhealthy target group health checks.
- **Amazon RDS / Aurora**:
  - Large automated snapshots taken hourly without retention expiration.
  - Multi-AZ read replica spun up for testing and forgotten.
- **Amazon S3**:
  - Incomplete multi-part uploads without lifecycle cleanup rules.
  - Massive unindexed API `LIST` / `GET` requests from external applications.
- **AWS NAT Gateway**:
  - Large cross-region data transfer egress.

### Step 4: Remediation
1. Contact the tag owner identified in the alert.
2. If confirmed accidental or runaway, terminate/stop the non-production resource:
   ```bash
   aws ec2 stop-instances --instance-ids i-xxxxxxxxx --region <region>
   ```
3. Attach/Verify resource lifecycle policies or auto-stop schedules.

---

## 3. Maintenance & Threshold Adjustments

If alerts are too frequent (false positives) or too strict, tune the Terraform variables in `terraform/environments/prod/terraform.tfvars`:
- `min_absolute_spike_usd`: Increase to `$25.0` or `$50.0` for high-volume enterprise accounts.
- `percentage_threshold`: Adjust between `20%` and `50%`.
- `baseline_days`: Default is `14` days to account for weekend/weekday cyclicality.

Apply changes via Terraform:
```bash
./scripts/deploy.sh prod
```
