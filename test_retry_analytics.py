import src.payment_queries as payment_queries


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
