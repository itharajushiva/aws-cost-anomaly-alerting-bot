# Architecture & System Design
## Serverless Cloud Cost Anomaly Alerting Bot

---

## 1. Overview

Unplanned cloud cost increases often stem from unattached EBS volumes, abandoned test instances, runaway autoscaling policies, or unexpected data transfer. 

This project provides an automated AWS cost anomaly alerting pipeline. Running as a serverless workload on AWS Lambda and triggered daily by Amazon EventBridge, it queries the AWS Cost Explorer API, compares service spend against a 14-day rolling baseline, identifies resource owners by tag, and dispatches formatted alerts to Slack via Block Kit.

---

## 2. High-Level Architecture Diagram

```
       +---------------------------------------------+
       | Amazon EventBridge (CloudWatch Events Rule)  |
       |  Schedule: Daily at 08:00 UTC (Post-CE sync)|
       +----------------------+----------------------+
                              |
                              | triggers
                              v
       +---------------------------------------------+
       |               AWS Lambda                    |
       |   Runtime: Python 3.11 (Cost Anomaly Bot)   |
       +-------+--------------+---------------+------+
               |              |               |
               | (1) Read     | (2) Query     | (3) Dispatch
               v              v               v
  +------------------+  +-------------------+  +------------------+
  |  AWS Secrets     |  | AWS Cost Explorer |  |  Slack API       |
  |  Manager         |  | API               |  |  (Incoming       |
  |  - Webhook URL   |  | - Service spend   |  |   Webhook)       |
  |  - Auth Tokens   |  | - 14-day baseline |  |  - Formatted     |
  +------------------+  | - Tag breakdown   |  |    Block Kit     |
                        +-------------------+  |  - Top Drivers   |
                                               +------------------+
                                                        |
                                                        v
                                               +------------------+
                                               | FinOps & DevOps  |
                                               | Slack Channels   |
                                               +------------------+
```

---

## 3. Data Flow & Execution Stages

1. **Trigger Phase**:
   - Amazon EventBridge initiates execution at `08:00 UTC` daily, granting AWS billing systems sufficient time to finalize the preceding day's billing aggregates.
2. **Configuration & Secrets Fetch**:
   - Lambda retrieves encrypted Slack incoming webhook credentials from AWS Secrets Manager using IAM least privilege.
3. **Historical Baseline Query**:
   - Queries AWS Cost Explorer API across a rolling window (e.g., prior 14 days) grouped by `SERVICE` and `LINKED_ACCOUNT`.
4. **Statistical Analysis Engine**:
   - For each active service:
     - Calculates rolling mean $\mu$ and standard deviation $\sigma$.
     - Computes absolute delta: $\Delta = \text{Cost}_{\text{target}} - \mu$.
     - Calculates percentage increase: $\frac{\Delta}{\mu} \times 100\%$.
     - Calculates Z-score: $Z = \frac{\text{Cost}_{\text{target}} - \mu}{\sigma}$.
     - Evaluates against dual-gates: minimum absolute dollar spike (default: $\$15$) AND percentage jump (default: $\ge 25\%$).
5. **Tag & Driver Enrichment**:
   - For all flagged anomalous services, queries Cost Explorer filtered by service and grouped by tag (e.g., `Owner`, `Environment`, `Team`) to pinpoint root causes.
6. **Slack Block Kit Notification**:
   - Serializes payload with interactive buttons (linking directly to AWS Cost Explorer and Cost Anomaly console), critical indicators, and tag summaries.
