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
