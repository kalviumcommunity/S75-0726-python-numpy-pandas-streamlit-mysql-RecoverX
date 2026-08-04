import pandas as pd

import src.payment_queries as payment_queries


def test_mark_alert_resolved_updates_state(monkeypatch):
    captured = {}

    def fake_execute_query(query, params=None, fetch=False):
        captured["query"] = query
        captured["params"] = params
        captured["fetch"] = fetch
        return True

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute_query)

    result = payment_queries.mark_alert_resolved(7)

    assert result is True
    assert "UPDATE alerts" in captured["query"]
    assert captured["params"] == (7,)
    assert captured["fetch"] is False


def test_get_resolved_alerts_returns_dataframe_with_filters(monkeypatch):
    rows = [
        {
            "alert_id": 2,
            "rule_id": 1,
            "alert_type": "failure_rate",
            "message": "Failure rate exceeded 20%",
            "severity": "HIGH",
            "is_resolved": True,
            "created_at": "2026-07-25 08:00:00",
            "resolved_at": "2026-07-25 09:00:00",
        }
    ]

    captured = {}

    def fake_execute_query(query, params=None, fetch=False):
        captured["query"] = query
        captured["params"] = params
        captured["fetch"] = fetch
        return rows

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute_query)

    df = payment_queries.get_resolved_alerts(
        start_date="2026-07-25 00:00:00",
        end_date="2026-07-25 23:59:59",
        severity="HIGH",
    )

    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["alert_id"] == 2
    assert "WHERE is_resolved = TRUE" in captured["query"]
    assert "resolved_at" in captured["query"]
    assert "severity = %s" in captured["query"]
    assert captured["params"] == (
        "2026-07-25 00:00:00",
        "2026-07-25 23:59:59",
        "HIGH",
    )


def test_get_active_alerts_returns_safe_placeholder_shape(monkeypatch):
    rows = [
        {
            "alert_id": 4,
            "alert_type": "response_trend",
            "message": "Response code 3DS declined",
            "severity": "MEDIUM",
            "is_resolved": False,
            "created_at": "2026-07-26 10:30:00",
        }
    ]

    monkeypatch.setattr(payment_queries, "execute_query", lambda *args, **kwargs: rows)

    result = payment_queries.get_active_alerts()

    assert result[0]["alert_title"] == "response_trend"
    assert result[0]["alert_message"] == "Response code 3DS declined"
    assert result[0]["status"] == "ACTIVE"


def test_generate_alerts_from_rules_creates_alerts_for_triggered_rules(monkeypatch):
    monkeypatch.setattr(
        payment_queries,
        "get_alert_rules",
        lambda: [
            {
                "rule_id": 1,
                "rule_name": "High Failure Rate",
                "rule_type": "failure_rate",
                "threshold_value": 30.0,
                "threshold_condition": ">",
                "is_active": True,
            }
        ],
    )
    monkeypatch.setattr(
        payment_queries,
        "get_transaction_counts",
        lambda start_date=None, end_date=None: {"total": 100, "success": 60, "failed": 40},
    )
    monkeypatch.setattr(
        payment_queries,
        "get_top_response_trend",
        lambda start_date=None, end_date=None: {"response_code": "05", "description": "Do Not Honor", "count": 10, "share": 25.0},
    )
    monkeypatch.setattr(payment_queries, "_alert_exists", lambda rule_id, message, window_hours=24: False)

    created = []

    def fake_create_alert(rule_id, alert_type, message, severity="MEDIUM", is_resolved=False):
        created.append((rule_id, alert_type, message, severity, is_resolved))
        return True

    monkeypatch.setattr(payment_queries, "create_alert", fake_create_alert)

    result = payment_queries.generate_alerts_from_rules()

    assert result == [
        {
            "rule_id": 1,
            "alert_type": "failure_rate",
            "message": "Failure rate is 40.0% which exceeds the threshold of 30.0%.",
            "severity": "HIGH",
        }
    ]
    assert created == [
        (1, "failure_rate", "Failure rate is 40.0% which exceeds the threshold of 30.0%.", "HIGH", False)
    ]


def test_generate_alerts_from_rules_skips_duplicate_alerts(monkeypatch):
    monkeypatch.setattr(
        payment_queries,
        "get_alert_rules",
        lambda: [
            {
                "rule_id": 2,
                "rule_name": "Low Success Rate",
                "rule_type": "success_rate",
                "threshold_value": 70.0,
                "threshold_condition": "<",
                "is_active": True,
            }
        ],
    )
    monkeypatch.setattr(
        payment_queries,
        "get_transaction_counts",
        lambda start_date=None, end_date=None: {"total": 100, "success": 60, "failed": 40},
    )
    monkeypatch.setattr(
        payment_queries,
        "get_top_response_trend",
        lambda start_date=None, end_date=None: {"response_code": "05", "description": "Do Not Honor", "count": 10, "share": 25.0},
    )
    monkeypatch.setattr(payment_queries, "_alert_exists", lambda rule_id, message, window_hours=24: True)

    create_calls = []

    def fake_create_alert(rule_id, alert_type, message, severity="MEDIUM", is_resolved=False):
        create_calls.append((rule_id, alert_type, message, severity, is_resolved))
        return True

    monkeypatch.setattr(payment_queries, "create_alert", fake_create_alert)

    result = payment_queries.generate_alerts_from_rules()

    assert result == []
    assert create_calls == []


def test_get_alerts_returns_rows_from_database(monkeypatch):
    rows = [
        {
            "alert_id": 5,
            "rule_id": 1,
            "alert_type": "failure_rate",
            "message": "Failure rate exceeded threshold",
            "severity": "HIGH",
            "is_resolved": False,
            "created_at": "2026-08-01 10:00:00",
        }
    ]

    captured = {}

    def fake_execute_query(query, params=None, fetch=False):
        captured["query"] = query
        captured["params"] = params
        captured["fetch"] = fetch
        return rows

    monkeypatch.setattr(payment_queries, "execute_query", fake_execute_query)

    result = payment_queries.get_alerts(is_resolved=False, limit=10)

    assert result == rows
    assert "WHERE is_resolved = %s" in captured["query"]
    assert captured["params"] == (False, 10)
    assert captured["fetch"] is True
