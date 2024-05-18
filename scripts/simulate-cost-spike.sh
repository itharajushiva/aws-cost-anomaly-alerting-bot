#!/usr/bin/env bash
# ==============================================================================
# Script: simulate-cost-spike.sh
# Purpose: Offline dry-run simulation of anomaly detection algorithm using synthetic data
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Running cost anomaly detection simulation using Python..."

python3 - << 'EOF'
import sys
import os
sys.path.insert(0, os.path.abspath("src"))

from anomaly_detector import AnomalyDetector
from slack_notifier import SlackNotifier

# Synthetic 14-day history
synthetic_ce = []
for day in range(1, 15):
    synthetic_ce.append({
        "TimePeriod": {"Start": f"2024-05-{day:02d}", "End": f"2024-05-{(day+1):02d}"},
        "Groups": [
            {"Keys": ["Amazon Elastic Compute Cloud - Compute"], "Metrics": {"UnblendedCost": {"Amount": "45.20"}}},
            {"Keys": ["Amazon Relational Database Service"], "Metrics": {"UnblendedCost": {"Amount": "28.50"}}},
            {"Keys": ["Amazon Simple Storage Service"], "Metrics": {"UnblendedCost": {"Amount": "12.10"}}},
        ]
    })

# Anomalous day
synthetic_ce.append({
    "TimePeriod": {"Start": "2024-05-15", "End": "2024-05-16"},
    "Groups": [
        {"Keys": ["Amazon Elastic Compute Cloud - Compute"], "Metrics": {"UnblendedCost": {"Amount": "345.80"}}}, # +$300 spike
        {"Keys": ["Amazon Relational Database Service"], "Metrics": {"UnblendedCost": {"Amount": "29.10"}}},
        {"Keys": ["Amazon Simple Storage Service"], "Metrics": {"UnblendedCost": {"Amount": "85.40"}}},          # +$73 spike
    ]
})

detector = AnomalyDetector(min_absolute_spike_usd=15.0, percentage_threshold=25.0)
anomalies = detector.analyze_service_spend(synthetic_ce, "2024-05-15")

print(f"\n[SIMULATION RESULT] Detected {len(anomalies)} anomalies on 2024-05-15:")
for a in anomalies:
    print(f" -> {a.service}: Target=${a.target_cost:.2f} (Baseline=${a.baseline_mean:.2f}) | Spike=+${a.absolute_delta:.2f} (+{a.percentage_increase:.1f}%) | Severity={a.severity}")

notifier = SlackNotifier(webhook_url="")
blocks = notifier.build_anomaly_blocks(
    target_date="2024-05-15",
    anomalies=anomalies,
    aws_account_id="123456789012",
    environment="production",
    total_daily_spend=460.30
)
print("\nSlack Block Kit Preview generated successfully!")
print(f"Total Block elements: {len(blocks['blocks'])}")
EOF
