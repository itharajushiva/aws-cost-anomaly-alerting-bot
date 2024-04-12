import pytest
from datetime import date
from src.cost_explorer import calculate_date_windows, CostExplorerClient


def test_calculate_date_windows():
    custom_date = date(2024, 5, 15)
    windows = calculate_date_windows(target_date=custom_date, baseline_days=14)

    assert windows["target_date"] == "2024-05-15"
    assert windows["target_start"] == "2024-05-15"
    assert windows["target_end"] == "2024-05-16"
    assert windows["baseline_start"] == "2024-05-01"
    assert windows["baseline_end"] == "2024-05-15"
    assert windows["full_query_start"] == "2024-05-01"
    assert windows["full_query_end"] == "2024-05-16"


def test_cost_explorer_get_service_spend_pagination(mocker):
    mock_boto_ce = mocker.MagicMock()
    mock_boto_ce.get_cost_and_usage.side_effect = [
        {
            "ResultsByTime": [{"TimePeriod": {"Start": "2024-05-01", "End": "2024-05-02"}}],
            "NextPageToken": "token-123",
        },
        {
            "ResultsByTime": [{"TimePeriod": {"Start": "2024-05-02", "End": "2024-05-03"}}],
        },
    ]

    client = CostExplorerClient(ce_client=mock_boto_ce)
    results = client.get_service_spend("2024-05-01", "2024-05-03")

    assert len(results) == 2
    assert mock_boto_ce.get_cost_and_usage.call_count == 2
