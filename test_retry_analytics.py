import src.payment_queries as payment_queries
import pandas as pd
from datetime import datetime, timedelta


def test_get_retry_success_by_time_heatmap_builds_matrix(monkeypatch):
    rows = [
        {"day_index": 0, "hour_of_day": 8, "total_retries": 4, "successful": 3},
        {"day_index": 2, "hour_of_day": 9, "total_retries": 2, "successful": 1},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    heatmap = payment_queries.get_retry_success_by_time_heatmap()

    assert heatmap["days"] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    assert heatmap["hours"] == list(range(24))
    assert heatmap["values"][0][8] == 75.0
    assert heatmap["values"][2][9] == 50.0


def test_get_retry_success_by_time_heatmap_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: None)

    heatmap = payment_queries.get_retry_success_by_time_heatmap()

    assert len(heatmap["days"]) == 7
    assert len(heatmap["hours"]) == 24
    assert len(heatmap["values"]) == 7
    assert len(heatmap["values"][0]) == 24
    assert all(v == 0.0 for v in heatmap["values"][0])


def test_get_retry_success_rate_per_attempt_calculates_rates(monkeypatch):
    rows = [
        {"attempt_number": 1, "total_attempts": 100, "successful": 60, "failed": 40},
        {"attempt_number": 2, "total_attempts": 50, "successful": 35, "failed": 15},
        {"attempt_number": 3, "total_attempts": 20, "successful": 10, "failed": 10},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_success_rate_per_attempt()

    assert len(result) == 3
    assert result[0]["attempt_number"] == 1
    assert result[0]["total_attempts"] == 100
    assert result[0]["successful"] == 60
    assert result[0]["failed"] == 40
    assert result[0]["success_rate"] == 60.0

    assert result[1]["success_rate"] == 70.0
    assert result[2]["success_rate"] == 50.0


def test_get_retry_success_rate_per_attempt_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [])

    result = payment_queries.get_retry_success_rate_per_attempt()

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_retry_success_rate_per_attempt_zero_total(monkeypatch):
    rows = [
        {"attempt_number": 1, "total_attempts": 0, "successful": 0, "failed": 0},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_success_rate_per_attempt()

    assert len(result) == 1
    assert result[0]["success_rate"] == 0


def test_get_retry_timing_analysis_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: None)

    result = payment_queries.get_retry_timing_analysis()

    assert isinstance(result, dict)
    assert "average_hours_between_retries" in result
    assert "median_hours_between_retries" in result
    assert "best_window" in result
    assert "best_window_count" in result
    assert "window_distribution" in result
    assert result["average_hours_between_retries"] == 0
    assert result["median_hours_between_retries"] == 0
    assert result["window_distribution"] == []


def test_get_retry_timing_analysis_with_intervals(monkeypatch):
    base_time = datetime(2026, 7, 20, 10, 0, 0)
    rows = [
        {"transaction_id": "TXN-1", "attempt_number": 1, "retry_timestamp": base_time},
        {"transaction_id": "TXN-1", "attempt_number": 2, "retry_timestamp": base_time + timedelta(hours=3)},
        {"transaction_id": "TXN-1", "attempt_number": 3, "retry_timestamp": base_time + timedelta(hours=10)},
        {"transaction_id": "TXN-2", "attempt_number": 1, "retry_timestamp": base_time},
        {"transaction_id": "TXN-2", "attempt_number": 2, "retry_timestamp": base_time + timedelta(hours=20)},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_timing_analysis()

    assert result["average_hours_between_retries"] > 0
    assert result["median_hours_between_retries"] > 0
    assert isinstance(result["window_distribution"], list)
    assert len(result["window_distribution"]) > 0
    assert "window" in result["window_distribution"][0]
    assert "count" in result["window_distribution"][0]
    assert "0-6 hrs" in [w["window"] for w in result["window_distribution"]]
    assert "6-12 hrs" in [w["window"] for w in result["window_distribution"]]
    assert "12-24 hrs" in [w["window"] for w in result["window_distribution"]]


def test_get_retry_timing_analysis_no_second_attempt(monkeypatch):
    rows = [
        {"transaction_id": "TXN-A", "attempt_number": 1, "retry_timestamp": datetime(2026, 7, 20, 10, 0, 0)},
        {"transaction_id": "TXN-B", "attempt_number": 1, "retry_timestamp": datetime(2026, 7, 20, 14, 0, 0)},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_timing_analysis()

    assert result["average_hours_between_retries"] == 0
    assert result["median_hours_between_retries"] == 0
    assert result["best_window_count"] == 0
    assert result["window_distribution"] == []


def test_get_retry_gateway_performance_calculates_rates(monkeypatch):
    rows = [
        {"gateway": "Stripe", "total_retries": 100, "successful": 75},
        {"gateway": "Razorpay", "total_retries": 200, "successful": 120},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_gateway_performance()

    assert len(result) == 2
    assert result[0]["gateway"] == "Stripe"
    assert result[0]["total_retries"] == 100
    assert result[0]["successful"] == 75
    assert result[0]["success_rate"] == 75.0

    assert result[1]["gateway"] == "Razorpay"
    assert result[1]["success_rate"] == 60.0


def test_get_retry_gateway_performance_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [])

    result = payment_queries.get_retry_gateway_performance()

    assert len(result) == 3
    assert result[0]["gateway"] == "Stripe"
    assert "total_retries" in result[0]
    assert "successful" in result[0]
    assert "success_rate" in result[0]


def test_get_retry_gateway_performance_zero_total(monkeypatch):
    rows = [
        {"gateway": "EmptyGW", "total_retries": 0, "successful": 0},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_gateway_performance()

    assert result[0]["success_rate"] == 0


def test_get_retry_bank_performance_calculates_rates(monkeypatch):
    rows = [
        {"bank": "HDFC Bank", "total_retries": 200, "successful": 150},
        {"bank": "SBI", "total_retries": 100, "successful": 40},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_bank_performance()

    assert len(result) == 2
    assert result[0]["bank"] == "HDFC Bank"
    assert result[0]["total_retries"] == 200
    assert result[0]["successful"] == 150
    assert result[0]["success_rate"] == 75.0
    assert result[1]["success_rate"] == 40.0


def test_get_retry_bank_performance_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [])

    result = payment_queries.get_retry_bank_performance()

    assert len(result) == 3
    assert "bank" in result[0]
    assert "success_rate" in result[0]


def test_get_failure_type_distribution_with_data(monkeypatch):
    rows = [
        {"failure_type": "TEMPORARY", "count": 75},
        {"failure_type": "PERMANENT", "count": 25},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_failure_type_distribution()

    assert len(result) == 2
    temp = next(r for r in result if r["failure_type"] == "TEMPORARY")
    perm = next(r for r in result if r["failure_type"] == "PERMANENT")
    assert temp["count"] == 75
    assert perm["count"] == 25


def test_get_failure_type_distribution_fallback(monkeypatch):
    call_count = {"n": 0}

    def fake_execute(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return None
        elif call_count["n"] == 2:
            return [{"total": 50}]
        elif call_count["n"] == 3:
            return [{"total": 30}]
        return []

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute)

    result = payment_queries.get_failure_type_distribution()

    assert len(result) == 2
    temp = next(r for r in result if r["failure_type"] == "TEMPORARY")
    perm = next(r for r in result if r["failure_type"] == "PERMANENT")
    assert temp["count"] == 50
    assert perm["count"] == 30


def test_get_failure_causes_distribution_primary(monkeypatch):
    rows = [
        {"cause": "Insufficient Funds", "count": 40},
        {"cause": "Invalid Card", "count": 20},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_failure_causes_distribution()

    assert len(result) == 2
    assert result[0]["cause"] == "Insufficient Funds"
    assert result[0]["count"] == 40


def test_get_failure_causes_distribution_fallback(monkeypatch):
    call_count = {"n": 0}

    def fake_execute(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return None
        return [
            {"cause": "Do Not Honor", "count": 15},
            {"cause": "Expired Card", "count": 10},
        ]

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute)

    result = payment_queries.get_failure_causes_distribution()

    assert len(result) == 2
    assert result[0]["cause"] == "Do Not Honor"
    assert result[1]["count"] == 10


def test_get_failure_causes_distribution_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: None)

    result = payment_queries.get_failure_causes_distribution()

    assert isinstance(result, list)
    assert result == []


def test_get_failure_breakdown_by_response_code(monkeypatch):
    rows = [
        {"code": "05", "description": "Do Not Honor", "count": 30},
        {"code": "51", "description": "Insufficient Funds", "count": 50},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_failure_breakdown_by_response_code()

    assert len(result) == 2
    assert result[0]["code"] == "05"
    assert result[0]["description"] == "Do Not Honor"
    assert result[1]["count"] == 50


def test_get_failure_breakdown_by_gateway(monkeypatch):
    rows = [
        {"gateway": "Stripe", "count": 45},
        {"gateway": "PayPal", "count": 35},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_failure_breakdown_by_gateway()

    assert len(result) == 2
    assert result[0]["gateway"] == "Stripe"
    assert result[1]["count"] == 35


def test_get_failure_breakdown_by_payment_method(monkeypatch):
    rows = [
        {"payment_method": "Credit Card", "count": 60},
        {"payment_method": "UPI", "count": 25},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_failure_breakdown_by_payment_method()

    assert len(result) == 2
    assert result[0]["payment_method"] == "Credit Card"
    assert result[1]["count"] == 25


def test_count_filtered_transactions_no_filters(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [{"total": 150}])

    result = payment_queries.count_filtered_transactions()

    assert result == 150


def test_count_filtered_transactions_with_all_filters(monkeypatch):
    captured = {}

    def fake_execute(query, params, **kwargs):
        captured["query"] = query
        captured["params"] = params
        return [{"total": 42}]

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute)

    result = payment_queries.count_filtered_transactions(
        transaction_id="TXN123",
        customer_id="CUST456",
        start_date="2026-01-01",
        end_date="2026-12-31",
        status="FAILED",
    )

    assert result == 42
    assert "%TXN123%" in captured["params"]
    assert "%CUST456%" in captured["params"]
    assert "2026-01-01" in captured["params"]
    assert "2026-12-31" in captured["params"]
    assert "FAILED" in captured["params"]


def test_get_filtered_transactions_returns_dataframe(monkeypatch):
    rows = [
        {"transaction_id": "TXN-001", "customer_id": "C-1", "amount": 100.0, "final_status": "SUCCESS"},
        {"transaction_id": "TXN-002", "customer_id": "C-2", "amount": 200.0, "final_status": "FAILED"},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    df = payment_queries.get_filtered_transactions()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["transaction_id", "customer_id", "amount", "final_status"]


def test_get_filtered_transactions_empty(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: None)

    df = payment_queries.get_filtered_transactions()

    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_get_total_transactions(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [{"total_transactions": 500}])

    result = payment_queries.get_total_transactions()

    assert result[0]["total_transactions"] == 500


def test_get_successful_transactions(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [{"successful_transactions": 350}])

    result = payment_queries.get_successful_transactions()

    assert result[0]["successful_transactions"] == 350


def test_get_failed_transactions(monkeypatch):
    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: [{"failed_transactions": 150}])

    result = payment_queries.get_failed_transactions()

    assert result[0]["failed_transactions"] == 150


def test_get_transaction_status_over_time(monkeypatch):
    rows = [
        {"date": "2026-07-20", "success_count": 50, "failed_count": 10},
        {"date": "2026-07-21", "success_count": 60, "failed_count": 15},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_transaction_status_over_time()

    assert len(result) == 2
    assert result[0]["success_count"] == 50
    assert result[1]["failed_count"] == 15


def test_get_retry_attempts_distribution(monkeypatch):
    rows = [
        {"transaction_id": "TXN-1", "attempt_count": 1},
        {"transaction_id": "TXN-2", "attempt_count": 3},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_retry_attempts_distribution()

    assert len(result) == 2
    assert result[0]["attempt_count"] == 1
    assert result[1]["attempt_count"] == 3


def test_get_filtered_failed_transactions_returns_dataframe(monkeypatch):
    rows = [
        {"transaction_id": "TXN-F1", "failure_type": "TEMPORARY", "failure_description": "Insufficient Funds"},
        {"transaction_id": "TXN-F2", "failure_type": "PERMANENT", "failure_description": "Do Not Honor"},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    df = payment_queries.get_filtered_failed_transactions()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "failure_type" in df.columns


def test_get_filtered_failed_transactions_with_filters_builds_params(monkeypatch):
    captured = {}

    def fake_execute(query, params, **kwargs):
        captured["query"] = query
        captured["params"] = params
        return []

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute)

    payment_queries.get_filtered_failed_transactions(
        failure_type="TEMPORARY",
        response_code="05",
        gateway="Stripe",
        payment_method="Credit Card",
        start_date="2026-07-01",
        end_date="2026-07-31",
    )

    assert "TEMPORARY" in captured["params"]
    assert "05" in captured["params"]
    assert "Stripe" in captured["params"]
    assert "Credit Card" in captured["params"]
    assert "2026-07-01" in captured["params"]
    assert "2026-07-31" in captured["params"]


def test_get_retry_success_by_time_heatmap_numeric_coercion(monkeypatch):
    rows = [
        {"day_index": "1", "hour_of_day": "14", "total_retries": "10", "successful": "8"},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    heatmap = payment_queries.get_retry_success_by_time_heatmap()

    assert heatmap["values"][1][14] == 80.0


def test_get_retry_success_by_time_heatmap_zero_total_no_division(monkeypatch):
    rows = [
        {"day_index": 3, "hour_of_day": 2, "total_retries": 0, "successful": 0},
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    heatmap = payment_queries.get_retry_success_by_time_heatmap()

    assert heatmap["values"][3][2] == 0.0
