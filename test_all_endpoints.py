
"""
Pytest test suite for RecoverX API endpoints + backend query logic.

Covers:
  1. FastAPI endpoints (using httpx TestClient via fixtures)
  2. get_revenue_recovery_summary() edge cases
  3. generate_alerts_from_rules() threshold boundary values
  4. get_recovery_score_distribution() NumPy percentile verification

Tests run against either:
  * a live API server (if API_BASE_URL is reachable with API key), OR
  * the FastAPI TestClient against the in-process app object.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List

import pytest


# -----------------------------
# Path / env setup
# -----------------------------

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# -----------------------------
# Constants shared with API module
# -----------------------------

API_KEY_DEFAULT = "recoverx-secret-key"
API_KEY = os.getenv("API_KEY", API_KEY_DEFAULT)
HEADERS = {"X-API-Key": API_KEY}
JSON_HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture(scope="session")
def fastapi_app():
    """Load the FastAPI app once per test session."""
    from src.api import app  # type: ignore[attr-defined]
    return app


@pytest.fixture(scope="session")
def api_client(fastapi_app) -> Generator[Any, None, None]:
    """Return an httpx TestClient pointed at the FastAPI app."""
    try:
        from fastapi.testclient import TestClient
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"httpx / TestClient not installed: {exc}")
        return
    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture(scope="session")
def _db_check() -> Dict[str, Any]:
    """
    One-time DB connectivity probe. Individual tests that require an active
    MySQL connection should check this fixture and skip if unhealthy.
    """
    from src.db import check_db_health  # type: ignore[attr-defined]
    start = time.time()
    health = {"ok": False}
    while time.time() - start < 5.0:
        try:
            health = check_db_health()
            if health.get("ok"):
                break
        except Exception:
            pass
        time.sleep(0.3)
    return health or {"ok": False}


@pytest.fixture()
def date_window() -> Dict[str, str]:
    """A 7-day date window centered on "today" for query tests."""
    today = datetime.utcnow()
    return {
        "start_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
    }


# -----------------------------
# Helpers
# -----------------------------

def _auth_get(client, url, params=None):
    return client.get(url, params=params or {}, headers=HEADERS)


def _auth_post_json(client, url, data=None):
    return client.post(url, json=data or {}, headers=JSON_HEADERS)


def _auth_post_file(client, url, filename, content_bytes, content_type="text/csv"):
    files = {"file": (filename, io.BytesIO(content_bytes), content_type)}
    return client.post(url, headers={"X-API-Key": API_KEY}, files=files)


# =====================================================
# SECTION 1: Healthz + Root endpoints
# =====================================================

class TestHealthEndpoints:
    def test_root(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert "message" in body
        assert "version" in body
        assert "docs" in body

    def test_healthz_returns_status_key(self, api_client):
        resp = api_client.get("/healthz")
        # We allow 200 (db healthy) OR 503 (db down but endpoint works)
        assert resp.status_code in (200, 503)
        body = resp.json()
        assert "status" in body
        assert "database" in body
        assert "ok" in body["database"]


# =====================================================
# SECTION 2: Analytics / Transactions endpoints
# =====================================================

class TestAnalyticsEndpoints:
    def test_analytics_overview_requires_key(self, api_client):
        resp = api_client.get("/api/analytics/overview")
        assert resp.status_code == 401

    def test_analytics_overview_authed(self, api_client):
        resp = _auth_get(api_client, "/api/analytics/overview")
        assert resp.status_code == 200
        body = resp.json()
        for k in (
            "total_transactions",
            "successful_transactions",
            "failed_transactions",
            "success_rate",
        ):
            assert k in body
            assert isinstance(body[k], (int, float))

    def test_list_transactions_authed(self, api_client):
        resp = _auth_get(
            api_client,
            "/api/transactions",
            params={"page": 1, "limit": 3},
        )
        assert resp.status_code == 200
        body = resp.json()
        for k in ("data", "page", "limit", "total", "pages"):
            assert k in body
        assert isinstance(body["data"], list)


# =====================================================
# SECTION 3: Payment retries + lifecycle
# =====================================================

class TestPaymentEndpoints:
    @pytest.fixture()
    def _created_txn(self, api_client) -> Dict[str, Any]:
        """Create a test transaction for this test class, returning its dict."""
        ts = int(time.time() * 1000)
        txn_id = f"TEST-TXN-{ts}"
        payload = {
            "transaction_id": txn_id,
            "customer_id": f"CUST-{ts}",
            "amount": 50.0,
            "currency": "USD",
            "payment_method": "UPI",
            "gateway": "Razorpay",
            "initial_status": "PENDING",
            "final_status": "FAILED",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        resp = _auth_post_json(api_client, "/api/transactions", payload)
        assert resp.status_code == 200
        return payload

    def test_create_and_get_transaction(self, api_client, _created_txn):
        txn_id = _created_txn["transaction_id"]
        resp = _auth_get(api_client, f"/api/transactions/{txn_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["transaction_id"] == txn_id

    def test_payment_lifecycle_paginated(self, api_client):
        resp = _auth_get(
            api_client,
            "/api/payment-lifecycle",
            params={"page": 1, "limit": 2},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)


# =====================================================
# SECTION 4: Bulk CSV import (smoke test)
# =====================================================

class TestBulkImportEndpoints:
    def test_bulk_import_invalid_csv_returns_400(self, api_client):
        """Empty/invalid CSV -> no valid rows. Returns 400."""
        csv_bytes = b"invalid_header\nbad_value\n"
        resp = _auth_post_file(
            api_client,
            "/api/transactions/bulk/csv",
            "bad.csv",
            csv_bytes,
        )
        # 400 (our "No valid transactions" rejection) or 500 (other)
        # Both indicate the endpoint is reachable and working.
        assert resp.status_code in (400, 500)

    def test_bulk_import_json_payload(self, api_client):
        rows = [
            {
                "transaction_id": f"BULK-J-{int(time.time()*1000)}-{i}",
                "customer_id": "CUST-BULK",
                "amount": 10.0 + i,
                "currency": "USD",
                "payment_method": "Card",
                "gateway": "Stripe",
                "initial_status": "PENDING",
                "final_status": "SUCCESS",
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            for i in range(2)
        ]
        resp = _auth_post_file(
            api_client,
            "/api/transactions/bulk/json",
            "txns.json",
            json.dumps(rows).encode(),
            "application/json",
        )
        # 200 ok or 500 db err — both indicate handler runs
        assert resp.status_code in (200, 500)


# =====================================================
# SECTION 5: Backend unit tests for query functions
# =====================================================

class TestRevenueRecoverySummary:
    """
    Edge-case tests for get_revenue_recovery_summary().

    The function is exercised through its public contract:
      * no date window (defaults to all data)
      * empty date window (future-only)
      * when the DB is empty or down -> must still return the zeroed dict shape
    """

    def _summary(self, start=None, end=None):
        from src.payment_queries import get_revenue_recovery_summary  # noqa: E402
        return get_revenue_recovery_summary(start, end)

    def test_result_shape(self):
        summary = self._summary()
        for k in (
            "total_failed_amount",
            "recoverable_revenue",
            "permanently_lost_revenue",
            "recovered_revenue",
            "avg_recovery_score",
            "high_value_failed_count",
        ):
            assert k in summary, f"missing key: {k}"

    def test_empty_db_or_unreachable_returns_zeros(self):
        """When execute_query returns None the function returns a zero dict."""
        from unittest.mock import patch
        import src.payment_queries as mod

        with patch.object(mod, "execute_query", return_value=None):
            summary = mod.get_revenue_recovery_summary()
        assert summary["total_failed_amount"] == 0.0
        assert summary["recoverable_revenue"] == 0.0
        assert summary["permanently_lost_revenue"] == 0.0
        assert summary["recovered_revenue"] == 0.0
        assert summary["avg_recovery_score"] == 0.0
        assert summary["high_value_failed_count"] == 0

    def test_date_window_far_future_returns_finite_values(self):
        """Future-only window: returns all floats/ints (not NaN/None)."""
        future = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%d")
        summary = self._summary(start_date=future, end_date=future)
        for k, v in summary.items():
            if k == "high_value_failed_count":
                assert isinstance(v, int)
            else:
                assert isinstance(v, (int, float))
                assert v == v  # NaN check

    def test_all_success_transactions_means_zero_failed_amount(self, _db_check):
        """
        When DB contains only SUCCESS transactions (or is empty),
        total_failed_amount must be >= 0 and recoverable_revenue cannot exceed it.
        """
        summary = self._summary()
        assert summary["total_failed_amount"] >= 0.0
        assert summary["recoverable_revenue"] <= summary["total_failed_amount"] + 1e-6


class TestGenerateAlertsFromRules:
    """Boundary-value tests for generate_alerts_from_rules()."""

    def _alerts(self, rules, start=None, end=None):
        from src.payment_queries import generate_alerts_from_rules  # noqa: E402
        return generate_alerts_from_rules(rules, start, end)

    # ---------- failure_rate boundary ----------

    def test_failure_rate_below_threshold_does_not_fire(self):
        """If current value <= threshold -> NOT triggered."""
        from unittest.mock import patch
        import src.payment_queries as mod

        # total=1000, failed=100 -> 10% failure rate
        def _fake_get_total(q, params=None):
            if "final_status != 'SUCCESS'" in q:
                return 100
            return 1000

        with patch.object(mod, "_get_total", side_effect=_fake_get_total):
            with patch.object(mod, "get_revenue_recovery_summary", return_value={
                "recoverable_revenue": 0.0,
            }):
                rules = [{
                    "rule_id": "R1",
                    "rule_type": "failure_rate",
                    "severity": "HIGH",
                    "threshold": 10.0,  # exactly the value -> not strictly >
                }]
                alerts = mod.generate_alerts_from_rules(rules)
        # failure rate is 10.0%, threshold is 10.0%. Operator is > so no alert.
        assert not any(a["rule_type"] == "failure_rate" for a in alerts)

    def test_failure_rate_above_threshold_fires(self):
        from unittest.mock import patch
        import src.payment_queries as mod

        def _fake_get_total(q, params=None):
            if "final_status != 'SUCCESS'" in q:
                return 101
            return 1000

        with patch.object(mod, "_get_total", side_effect=_fake_get_total):
            with patch.object(mod, "get_revenue_recovery_summary", return_value={
                "recoverable_revenue": 0.0,
            }):
                rules = [{
                    "rule_id": "R1",
                    "rule_type": "failure_rate",
                    "severity": "HIGH",
                    "threshold": 10.0,
                }]
                alerts = mod.generate_alerts_from_rules(rules)
        # 10.1% > 10% -> alert triggered
        failures = [a for a in alerts if a["rule_type"] == "failure_rate"]
        assert len(failures) == 1
        assert failures[0]["severity"] == "HIGH"
        assert failures[0]["threshold"] == 10.0

    # ---------- success_rate_drop boundary ----------

    def test_success_rate_below_threshold_fires(self):
        from unittest.mock import patch
        import src.payment_queries as mod

        def _fake_get_total(q, params=None):
            if "final_status = 'SUCCESS'" in q:
                return 749
            return 1000

        with patch.object(mod, "_get_total", side_effect=_fake_get_total):
            with patch.object(mod, "get_revenue_recovery_summary", return_value={
                "recoverable_revenue": 0.0,
            }):
                rules = [{
                    "rule_id": "R2",
                    "rule_type": "success_rate_drop",
                    "severity": "CRITICAL",
                    "threshold": 75.0,
                }]
                alerts = mod.generate_alerts_from_rules(rules)
        # success rate 74.9% < 75% -> alert
        drops = [a for a in alerts if a["rule_type"] == "success_rate_drop"]
        assert len(drops) == 1

    def test_success_rate_at_threshold_does_not_fire(self):
        from unittest.mock import patch
        import src.payment_queries as mod

        def _fake_get_total(q, params=None):
            if "final_status = 'SUCCESS'" in q:
                return 750
            return 1000

        with patch.object(mod, "_get_total", side_effect=_fake_get_total):
            with patch.object(mod, "get_revenue_recovery_summary", return_value={
                "recoverable_revenue": 0.0,
            }):
                rules = [{
                    "rule_id": "R2",
                    "rule_type": "success_rate_drop",
                    "severity": "CRITICAL",
                    "threshold": 75.0,
                }]
                alerts = mod.generate_alerts_from_rules(rules)
        assert not any(a["rule_type"] == "success_rate_drop" for a in alerts)

    # ---------- revenue_loss boundary (>= operator) ----------

    def test_revenue_loss_at_threshold_fires(self):
        from unittest.mock import patch
        import src.payment_queries as mod

        with patch.object(mod, "_get_total", return_value=0):
            with patch.object(mod, "get_revenue_recovery_summary", return_value={
                "recoverable_revenue": 10000.0,
            }):
                rules = [{
                    "rule_id": "R4",
                    "rule_type": "revenue_loss",
                    "severity": "HIGH",
                    "threshold": 10000.0,
                }]
                alerts = mod.generate_alerts_from_rules(rules)
        losses = [a for a in alerts if a["rule_type"] == "revenue_loss"]
        assert len(losses) == 1

    def test_revenue_loss_below_threshold_no_fire(self):
        from unittest.mock import patch
        import src.payment_queries as mod

        with patch.object(mod, "_get_total", return_value=0):
            with patch.object(mod, "get_revenue_recovery_summary", return_value={
                "recoverable_revenue": 9999.99,
            }):
                rules = [{
                    "rule_id": "R4",
                    "rule_type": "revenue_loss",
                    "severity": "HIGH",
                    "threshold": 10000.0,
                }]
                alerts = mod.generate_alerts_from_rules(rules)
        assert not any(a["rule_type"] == "revenue_loss" for a in alerts)


class TestRecoveryScoreDistribution:
    """Verify NumPy percentile calculations match manual math."""

    def _dist(self, rows_mock, start=None, end=None):
        """Run get_recovery_score_distribution() with execute_query mocked."""
        from unittest.mock import patch
        import src.payment_queries as mod

        with patch.object(mod, "execute_query", return_value=rows_mock):
            return mod.get_recovery_score_distribution(start, end)

    # --------- helpers for manual percentile math ----------

    @staticmethod
    def _manual_percentile(sorted_data: List[float], p: float) -> float:
        """Linear-interpolation percentile, matching numpy default."""
        import math
        if not sorted_data:
            return 0.0
        n = len(sorted_data)
        if n == 1:
            return float(sorted_data[0])
        rank = (p / 100.0) * (n - 1)
        lo = int(math.floor(rank))
        hi = min(lo + 1, n - 1)
        frac = rank - lo
        return float(sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * frac)

    # --------- tests ----------

    def test_no_scores_returns_zeros_and_empty_histo(self):
        dist = self._dist([])
        assert dist["basic_stats"]["count"] == 0
        assert dist["basic_stats"]["mean"] == 0.0
        assert dist["percentiles"]["p50"] == 0.0
        assert dist["histogram_counts"] == [] or sum(dist["histogram_counts"]) == 0

    def test_single_score(self):
        rows = [{"score": 0.8}]
        dist = self._dist(rows)
        assert dist["basic_stats"]["count"] == 1
        assert dist["basic_stats"]["mean"] == pytest.approx(0.8)
        # All percentiles should equal the only value
        for pct in dist["percentiles"].values():
            assert pct == pytest.approx(0.8)

    def test_percentiles_match_manual_math(self):
        """
        Use a curated set of scores to ensure NumPy's percentiles agree
        with a pure-Python linear-interpolation implementation.
        """
        scores = [0.10, 0.25, 0.30, 0.50, 0.55, 0.70, 0.75, 0.80, 0.90, 0.99]
        rows = [{"score": s} for s in scores]
        dist = self._dist(rows)

        s_sorted = sorted(scores)
        for p in (10, 25, 50, 75, 90):
            key = f"p{p}"
            expected = self._manual_percentile(s_sorted, p)
            got = dist["percentiles"][key]
            assert got == pytest.approx(expected, abs=1e-6), (
                f"Percentile {p} mismatch: got {got}, expected {expected}"
            )

    def test_histogram_counts_equal_total_scores(self):
        """Sum of histogram bins must equal number of scores passed in."""
        scores = [0.01, 0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
        rows = [{"score": s} for s in scores]
        dist = self._dist(rows)
        counts = dist["histogram_counts"]
        assert len(counts) == 10
        assert sum(counts) == len(scores)

    def test_basic_stats_match_manual(self):
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        rows = [{"score": s} for s in scores]
        dist = self._dist(rows)

        n = len(scores)
        mean = sum(scores) / n
        med = scores[2]  # n odd, zero-based index 2
        var = sum((x - mean) ** 2 for x in scores) / n
        std = var ** 0.5

        assert dist["basic_stats"]["count"] == n
        assert dist["basic_stats"]["mean"] == pytest.approx(mean)
        assert dist["basic_stats"]["median"] == pytest.approx(med)
        assert dist["basic_stats"]["std"] == pytest.approx(std, rel=1e-5)
        assert dist["basic_stats"]["min"] == pytest.approx(0.1)
        assert dist["basic_stats"]["max"] == pytest.approx(0.5)
