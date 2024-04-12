import pytest
from src.anomaly_detector import AnomalyDetector


def test_anomaly_detector_flags_spike():
    # Build 14 baseline days with $10/day for Amazon EC2, then $100 on target day
    target_date = "2024-05-15"
    ce_results = []
    for day in range(1, 15):
        day_str = f"2024-05-{day:02d}"
        next_day_str = f"2024-05-{(day+1):02d}"
        ce_results.append({
            "TimePeriod": {"Start": day_str, "End": next_day_str},
            "Groups": [
                {
                    "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                    "Metrics": {"UnblendedCost": {"Amount": "10.0"}},
                },
                {
                    "Keys": ["Amazon Simple Storage Service"],
                    "Metrics": {"UnblendedCost": {"Amount": "5.0"}},
                },
            ],
        })

    # Target day spike
    ce_results.append({
        "TimePeriod": {"Start": target_date, "End": "2024-05-16"},
        "Groups": [
            {
                "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                "Metrics": {"UnblendedCost": {"Amount": "110.0"}},  # +$100 spike!
            },
            {
                "Keys": ["Amazon Simple Storage Service"],
                "Metrics": {"UnblendedCost": {"Amount": "5.2"}},    # Normal steady spend
            },
        ],
    })

    detector = AnomalyDetector(min_absolute_spike_usd=15.0, percentage_threshold=25.0)
    anomalies = detector.analyze_service_spend(ce_results, target_date=target_date)

    assert len(anomalies) == 1
    ec2_anomaly = anomalies[0]
    assert ec2_anomaly.service == "Amazon Elastic Compute Cloud - Compute"
    assert ec2_anomaly.target_cost == 110.0
    assert ec2_anomaly.baseline_mean == 10.0
    assert ec2_anomaly.absolute_delta == 100.0
    assert ec2_anomaly.percentage_increase == 1000.0
    assert ec2_anomaly.severity == "CRITICAL"


def test_anomaly_detector_ignores_small_dollar_changes():
    # Service doubles from $0.10 to $0.20 (+100%), but delta is only $0.10 (< $15.0 min threshold)
    target_date = "2024-05-15"
    ce_results = [
        {
            "TimePeriod": {"Start": "2024-05-14", "End": "2024-05-15"},
            "Groups": [
                {
                    "Keys": ["AWS Key Management Service"],
                    "Metrics": {"UnblendedCost": {"Amount": "0.10"}},
                }
            ],
        },
        {
            "TimePeriod": {"Start": target_date, "End": "2024-05-16"},
            "Groups": [
                {
                    "Keys": ["AWS Key Management Service"],
                    "Metrics": {"UnblendedCost": {"Amount": "0.20"}},
                }
            ],
        },
    ]

    detector = AnomalyDetector(min_absolute_spike_usd=15.0, percentage_threshold=25.0)
    anomalies = detector.analyze_service_spend(ce_results, target_date=target_date)

    assert len(anomalies) == 0
