"""
Anomaly detection engine computing rolling statistical baselines
(mean, standard deviation, Z-score, and percentage delta) for cloud spend.
"""

import math
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnomalyRecord:
    service: str
    target_cost: float
    baseline_mean: float
    baseline_std: float
    percentage_increase: float
    absolute_delta: float
    z_score: float
    linked_account: Optional[str] = None
    top_tags: Dict[str, float] = field(default_factory=dict)
    severity: str = "WARNING"  # CRITICAL or WARNING


class AnomalyDetector:
    """
    Evaluates target day spend against rolling historical baselines.
    Flags services exceeding percentage threshold AND minimum absolute dollar threshold,
    with secondary validation using standard deviation / Z-score.
    """

    def __init__(
        self,
        min_absolute_spike_usd: float = 15.0,
        percentage_threshold: float = 25.0,
        z_score_threshold: float = 2.0,
        critical_absolute_usd: float = 100.0,
    ):
        self.min_absolute_spike_usd = min_absolute_spike_usd
        self.percentage_threshold = percentage_threshold
        self.z_score_threshold = z_score_threshold
        self.critical_absolute_usd = critical_absolute_usd

    def analyze_service_spend(
        self,
        ce_results: List[Dict[str, Any]],
        target_date: str,
    ) -> List[AnomalyRecord]:
        """
        Parses raw ResultsByTime from AWS CE, builds daily time-series per service,
        computes rolling mean and std dev on baseline days, and evaluates target day spend.
        """
        # Data structure: { service_name: { date_str: cost } }
        history: Dict[str, Dict[str, float]] = {}

        for period in ce_results:
            day_str = period["TimePeriod"]["Start"]
            for group in period.get("Groups", []):
                service_keys = group.get("Keys", [])
                if not service_keys:
                    continue
                service_name = service_keys[0]
                cost = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0.0))

                if service_name not in history:
                    history[service_name] = {}
                history[service_name][day_str] = cost

        anomalies: List[AnomalyRecord] = []

        for service, day_costs in history.items():
            target_cost = day_costs.get(target_date, 0.0)

            # Baseline days are all days in history prior to target_date
            baseline_costs = [
                cost for d_str, cost in day_costs.items() if d_str < target_date
            ]

            if not baseline_costs:
                # No baseline history available (e.g. brand new service usage)
                if target_cost >= self.min_absolute_spike_usd:
                    record = AnomalyRecord(
                        service=service,
                        target_cost=round(target_cost, 2),
                        baseline_mean=0.0,
                        baseline_std=0.0,
                        percentage_increase=100.0,
                        absolute_delta=round(target_cost, 2),
                        z_score=999.0,
                        severity="CRITICAL" if target_cost >= self.critical_absolute_usd else "WARNING",
                    )
                    anomalies.append(record)
                continue

            mean = sum(baseline_costs) / len(baseline_costs)
            variance = sum((x - mean) ** 2 for x in baseline_costs) / len(baseline_costs)
            std_dev = math.sqrt(variance)

            absolute_delta = target_cost - mean
            pct_increase = ((target_cost - mean) / mean * 100.0) if mean > 0 else (100.0 if target_cost > 0 else 0.0)

            z_score = (absolute_delta / std_dev) if std_dev > 0.001 else (absolute_delta if absolute_delta > 0 else 0.0)

            # Anomaly Condition:
            # 1. Absolute cost jump is at least `min_absolute_spike_usd`
            # 2. Percentage increase is >= `percentage_threshold` OR Z-score >= `z_score_threshold`
            is_anomaly = (
                absolute_delta >= self.min_absolute_spike_usd
                and (pct_increase >= self.percentage_threshold or z_score >= self.z_score_threshold)
            )

            if is_anomaly:
                severity = "CRITICAL" if (absolute_delta >= self.critical_absolute_usd or pct_increase >= 100.0) else "WARNING"
                anomalies.append(
                    AnomalyRecord(
                        service=service,
                        target_cost=round(target_cost, 2),
                        baseline_mean=round(mean, 2),
                        baseline_std=round(std_dev, 2),
                        percentage_increase=round(pct_increase, 1),
                        absolute_delta=round(absolute_delta, 2),
                        z_score=round(z_score, 2),
                        severity=severity,
                    )
                )

        # Sort anomalies by largest absolute dollar spike descending
        anomalies.sort(key=lambda a: a.absolute_delta, reverse=True)
        return anomalies
