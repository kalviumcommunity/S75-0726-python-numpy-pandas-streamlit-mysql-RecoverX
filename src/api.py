
import os
import json
import io
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from io import StringIO

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Security,
    Query,
    UploadFile,
    File,
)
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, condecimal
from enum import Enum

load_dotenv()

from src.db import execute_query, execute_many, check_db_health
from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes,
    dedupe_and_count,
)
from src.payment_queries import (
    get_total_transactions,
    get_successful_transactions,
    get_failed_transactions,
    get_failure_breakdown_by_response_code,
    get_failure_causes_distribution,
    get_recovery_success_stats,
    get_revenue_recovery_summary,
    generate_alerts_from_rules,
    generate_all_alerts,
)
from src.alert_scheduler import ensure_scheduler_running, get_alert_scheduler

# -----------------------------
# FastAPI app
# -----------------------------

app = FastAPI(title="RecoverX Data Integration API", version="1.1")

# API Key Authentication
API_KEY = os.getenv("API_KEY", "recoverx-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or Missing API Key")
    return api_key


def paginate_response(rows: List[Dict[str, Any]], total: int, page: int, limit: int):
    return {
        "data": rows,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": math.ceil(total / limit) if limit and total else 0,
    }


def _rows_to_dicts(rows) -> List[Dict[str, Any]]:
    """Normalize rows (list of dict-like objects) into plain dicts."""
    if rows is None:
        return []
    out: List[Dict[str, Any]] = []
    for r in rows:
        if hasattr(r, "items"):
            out.append({k: v for k, v in r.items()})
        else:
            out.append(dict(r))
    return out


def _ensure_db_up(rows, detail="Database unavailable or empty"):
    if rows is None:
        raise HTTPException(status_code=503, detail=detail)


# -----------------------------
# Pydantic Models
# -----------------------------

class FailureType(str, Enum):
    TEMPORARY = "TEMPORARY"
    PERMANENT = "PERMANENT"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., max_length=100)
    customer_id: str = Field(..., max_length=100)
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", max_length=10)
    payment_method: Optional[str] = Field(None, max_length=100)
    gateway: Optional[str] = Field(None, max_length=100)
    initial_status: str = Field(..., max_length=50)
    final_status: Optional[str] = Field(None, max_length=50)
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaymentRetryCreate(BaseModel):
    transaction_id: str = Field(..., max_length=100)
    attempt_number: int = Field(..., gt=0)
    retry_timestamp: datetime
    retry_status: str = Field(..., max_length=50)
    response_code: Optional[str] = Field(None, max_length=50)
    response_message: Optional[str] = Field(None)


class BankResponseCodeCreate(BaseModel):
    response_code: str = Field(..., max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    description: str
    failure_type: FailureType
    recovery_potential: Optional[float] = Field(None, ge=0, le=1)
    recommended_action: Optional[str] = None


class AlertRule(BaseModel):
    rule_id: Optional[str] = None
    name: Optional[str] = None
    rule_type: str
    severity: Severity = Severity.MEDIUM
    threshold: float
    metric: Optional[str] = None


class Alert(BaseModel):
    rule_id: Optional[str] = None
    rule_type: str
    severity: Severity
    name: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[Any] = None
    message: str


class AlertGenerateRequest(BaseModel):
    rules: Optional[List[AlertRule]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AlertResolveResponse(BaseModel):
    alert_id: int
    resolved: bool
    resolved_at: Optional[str] = None
    message: str


class RevenueSummary(BaseModel):
    total_failed_amount: float
    recoverable_revenue: float
    permanently_lost_revenue: float
    recovered_revenue: float
    avg_recovery_score: float
    high_value_failed_count: int


class RetryPerformance(BaseModel):
    total_retries: int
    successful_retries: int
    failed_retries: int
    overall_retry_success_rate: float
    by_attempt: List[Dict[str, Any]]
    by_gateway: List[Dict[str, Any]]


# -----------------------------
# Transactions Endpoints
# -----------------------------

@app.get("/api/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    final_status: Optional[str] = Query(None),
    api_key: str = Depends(verify_api_key),
):
    offset = (page - 1) * limit
    where_parts = ["1=1"]
    params: List[Any] = []
    if final_status:
        where_parts.append("final_status = %s")
        params.append(final_status)
    where_sql = " AND ".join(where_parts)

    total_rows = execute_query(
        f"SELECT COUNT(*) AS total FROM transactions WHERE {where_sql};",
        tuple(params) if params else None,
        fetch=True,
    )
    _ensure_db_up(total_rows)
    total = int(total_rows[0].get("total", 0) or 0) if total_rows else 0

    data_rows = execute_query(
        f"""
        SELECT transaction_id, customer_id, amount, currency, payment_method,
               gateway, initial_status, final_status, created_at, updated_at
        FROM transactions
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """,
        tuple(params + [limit, offset]),
        fetch=True,
    )
    _ensure_db_up(data_rows)
    return paginate_response(_rows_to_dicts(data_rows), total, page, limit)


@app.get("/api/transactions/{transaction_id}")
def get_transaction(
    transaction_id: str,
    api_key: str = Depends(verify_api_key),
):
    rows = execute_query(
        """
        SELECT transaction_id, customer_id, amount, currency, payment_method,
               gateway, initial_status, final_status, created_at, updated_at
        FROM transactions
        WHERE transaction_id = %s
        LIMIT 1;
        """,
        (transaction_id,),
        fetch=True,
    )
    _ensure_db_up(rows)
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"data": dict(rows[0])}


@app.post("/api/transactions")
def create_transaction(
    transaction: TransactionCreate,
    api_key: str = Depends(verify_api_key),
):
    txn_dict = transaction.model_dump()
    final_status = txn_dict.get("final_status") or txn_dict["initial_status"]
    updated_at = txn_dict.get("updated_at") or txn_dict["created_at"]
    ok = execute_query(
        """
        INSERT INTO transactions
            (transaction_id, customer_id, amount, currency, payment_method,
             gateway, initial_status, final_status, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            customer_id = VALUES(customer_id),
            amount = VALUES(amount),
            currency = VALUES(currency),
            payment_method = VALUES(payment_method),
            gateway = VALUES(gateway),
            initial_status = VALUES(initial_status),
            final_status = VALUES(final_status),
            updated_at = VALUES(updated_at);
        """,
        (
            txn_dict["transaction_id"],
            txn_dict["customer_id"],
            float(txn_dict["amount"]),
            txn_dict["currency"],
            txn_dict.get("payment_method"),
            txn_dict.get("gateway"),
            txn_dict["initial_status"],
            final_status,
            txn_dict["created_at"],
            updated_at,
        ),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to persist transaction")
    txn_dict["final_status"] = final_status
    txn_dict["updated_at"] = updated_at
    return {"message": "Transaction created successfully", "data": txn_dict}


@app.get("/api/transactions/export/csv")
def export_transactions_csv(api_key: str = Depends(verify_api_key)):
    rows = execute_query(
        """
        SELECT transaction_id, customer_id, amount, currency, payment_method,
               gateway, initial_status, final_status, created_at, updated_at
        FROM transactions
        ORDER BY created_at DESC;
        """,
        fetch=True,
    )
    _ensure_db_up(rows)
    df = pd.DataFrame(_rows_to_dicts(rows))
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@app.get("/api/transactions/export/excel")
def export_transactions_excel(api_key: str = Depends(verify_api_key)):
    rows = execute_query(
        """
        SELECT transaction_id, customer_id, amount, currency, payment_method,
               gateway, initial_status, final_status, created_at, updated_at
        FROM transactions
        ORDER BY created_at DESC;
        """,
        fetch=True,
    )
    _ensure_db_up(rows)
    df = pd.DataFrame(_rows_to_dicts(rows))
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Transactions")
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl is required for Excel export; install openpyxl",
        )
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=transactions.xlsx"},
    )


# -----------------------------
# Payment Retries Endpoints
# -----------------------------

@app.get("/api/transactions/{transaction_id}/retries")
def list_payment_retries(
    transaction_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    offset = (page - 1) * limit
    total_rows = execute_query(
        "SELECT COUNT(*) AS total FROM payment_retries WHERE transaction_id = %s;",
        (transaction_id,),
        fetch=True,
    )
    _ensure_db_up(total_rows)
    total = int(total_rows[0].get("total", 0) or 0) if total_rows else 0

    data_rows = execute_query(
        """
        SELECT retry_id, transaction_id, attempt_number, retry_timestamp,
               retry_status, response_code, response_message, created_at
        FROM payment_retries
        WHERE transaction_id = %s
        ORDER BY attempt_number ASC
        LIMIT %s OFFSET %s;
        """,
        (transaction_id, limit, offset),
        fetch=True,
    )
    _ensure_db_up(data_rows)
    return paginate_response(_rows_to_dicts(data_rows), total, page, limit)


@app.post("/api/transactions/{transaction_id}/retries")
def create_payment_retry(
    transaction_id: str,
    retry: PaymentRetryCreate,
    api_key: str = Depends(verify_api_key),
):
    if retry.transaction_id != transaction_id:
        raise HTTPException(status_code=400, detail="Transaction ID mismatch")
    retry_dict = retry.model_dump()
    ok = execute_query(
        """
        INSERT INTO payment_retries
            (transaction_id, attempt_number, retry_timestamp, retry_status,
             response_code, response_message)
        VALUES (%s,%s,%s,%s,%s,%s);
        """,
        (
            transaction_id,
            retry_dict["attempt_number"],
            retry_dict["retry_timestamp"],
            retry_dict["retry_status"],
            retry_dict.get("response_code"),
            retry_dict.get("response_message"),
        ),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to persist retry")
    return {"message": "Payment retry created successfully", "data": retry_dict}


# -----------------------------
# Payment Lifecycle Endpoint
# -----------------------------

@app.get("/api/payment-lifecycle")
def get_payment_lifecycle_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    offset = (page - 1) * limit
    total_rows = execute_query(
        "SELECT COUNT(*) AS total FROM payment_retries pr JOIN transactions t ON pr.transaction_id = t.transaction_id;",
        fetch=True,
    )
    _ensure_db_up(total_rows)
    total = int(total_rows[0].get("total", 0) or 0) if total_rows else 0
    data_rows = execute_query(
        """
        SELECT
            t.transaction_id, t.customer_id, t.amount, t.currency,
            t.payment_method, t.gateway, t.initial_status, t.final_status,
            t.created_at AS txn_created_at, t.updated_at,
            pr.retry_id, pr.attempt_number, pr.retry_timestamp,
            pr.retry_status, pr.response_code, pr.response_message
        FROM payment_retries pr
        JOIN transactions t ON pr.transaction_id = t.transaction_id
        ORDER BY pr.retry_timestamp DESC
        LIMIT %s OFFSET %s;
        """,
        (limit, offset),
        fetch=True,
    )
    _ensure_db_up(data_rows)
    return paginate_response(_rows_to_dicts(data_rows), total, page, limit)


# -----------------------------
# Bank Response Codes Endpoints
# -----------------------------

def _list_brc_filtered(failure_type: Optional[str], page: int, limit: int):
    offset = (page - 1) * limit
    where_parts = ["1=1"]
    params: List[Any] = []
    if failure_type:
        where_parts.append("failure_type = %s")
        params.append(failure_type)
    where_sql = " AND ".join(where_parts)

    total_rows = execute_query(
        f"SELECT COUNT(*) AS total FROM bank_response_codes WHERE {where_sql};",
        tuple(params) if params else None,
        fetch=True,
    )
    _ensure_db_up(total_rows)
    total = int(total_rows[0].get("total", 0) or 0) if total_rows else 0
    data_rows = execute_query(
        f"""
        SELECT response_code, bank_name, description, failure_type,
               recovery_potential, recommended_action
        FROM bank_response_codes
        WHERE {where_sql}
        ORDER BY response_code ASC
        LIMIT %s OFFSET %s;
        """,
        tuple(params + [limit, offset]),
        fetch=True,
    )
    _ensure_db_up(data_rows)
    return paginate_response(_rows_to_dicts(data_rows), total, page, limit)


@app.get("/api/bank-response-codes")
def list_bank_response_codes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    return _list_brc_filtered(None, page, limit)


@app.get("/api/bank-response-codes/temporary")
def list_temporary_failures(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    return _list_brc_filtered("TEMPORARY", page, limit)


@app.get("/api/bank-response-codes/permanent")
def list_permanent_failures(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    return _list_brc_filtered("PERMANENT", page, limit)


@app.post("/api/bank-response-codes")
def create_bank_response_code(
    code: BankResponseCodeCreate,
    api_key: str = Depends(verify_api_key),
):
    code_dict = code.model_dump()
    rp = code_dict.get("recovery_potential")
    ok = execute_query(
        """
        INSERT INTO bank_response_codes
            (response_code, bank_name, description, failure_type,
             recovery_potential, recommended_action)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            bank_name = VALUES(bank_name),
            description = VALUES(description),
            failure_type = VALUES(failure_type),
            recovery_potential = VALUES(recovery_potential),
            recommended_action = VALUES(recommended_action);
        """,
        (
            code_dict["response_code"],
            code_dict.get("bank_name"),
            code_dict["description"],
            code_dict["failure_type"].value,
            float(rp) if rp is not None else None,
            code_dict.get("recommended_action"),
        ),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to persist response code")
    code_dict["failure_type"] = code_dict["failure_type"].value
    return {"message": "Bank response code created successfully", "data": code_dict}


# -----------------------------
# Analytics Endpoints
# -----------------------------

@app.get("/api/analytics/overview")
def get_analytics_overview(
    api_key: str = Depends(verify_api_key),
):
    total_v = get_total_transactions()
    success_v = get_successful_transactions()
    failed_v = get_failed_transactions()
    total = int(total_v or 0)
    successful = int(success_v or 0)
    failed = int(failed_v or 0)
    # Recalculate failed to guarantee totals add up if DB values differ
    failed = failed if failed == (total - successful) else max(total - successful, failed)
    success_rate = round((successful / total * 100), 2) if total > 0 else 0
    return {
        "total_transactions": total,
        "successful_transactions": successful,
        "failed_transactions": failed,
        "success_rate": success_rate,
    }


@app.get("/api/analytics/failure-classifications")
def get_failure_classifications_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    offset = (page - 1) * limit
    all_rows = execute_query(
        """
        SELECT response_code, failure_type, description
        FROM bank_response_codes
        ORDER BY response_code ASC;
        """,
        fetch=True,
    )
    _ensure_db_up(all_rows)
    data = _rows_to_dicts(all_rows)
    total = len(data)
    return paginate_response(data[offset: offset + limit], total, page, limit)


@app.get("/api/analytics/response-code-analysis")
def get_response_code_analysis_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    offset = (page - 1) * limit
    breakdown = get_failure_breakdown_by_response_code(limit=9999)
    total = len(breakdown)
    return paginate_response(breakdown[offset: offset + limit], total, page, limit)


@app.get("/api/analytics/revenue-recovery", response_model=RevenueSummary)
def get_api_revenue_recovery(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    api_key: str = Depends(verify_api_key),
):
    summary = get_revenue_recovery_summary(start_date, end_date)
    return RevenueSummary(**summary)


@app.get("/api/analytics/retry-performance", response_model=RetryPerformance)
def get_api_retry_performance(
    api_key: str = Depends(verify_api_key),
):
    recovery_stats = get_recovery_success_stats() or {}
    total_retries = int(recovery_stats.get("total_retries", 0) or 0)
    successful_retries = int(recovery_stats.get("successful_retries", 0) or 0)
    failed_retries = int(recovery_stats.get("failed_retries", 0) or 0)
    overall_rate = (
        round((successful_retries / total_retries) * 100, 2)
        if total_retries
        else 0.0
    )

    attempt_rows = execute_query(
        """
        SELECT
            attempt_number,
            COUNT(*) AS total_attempts,
            SUM(CASE WHEN UPPER(retry_status) = 'SUCCESS' THEN 1 ELSE 0 END) AS successful,
            SUM(CASE WHEN UPPER(retry_status) != 'SUCCESS' THEN 1 ELSE 0 END) AS failed
        FROM payment_retries
        GROUP BY attempt_number
        ORDER BY attempt_number ASC;
        """,
        fetch=True,
    )
    by_attempt: List[Dict[str, Any]] = []
    for r in _rows_to_dicts(attempt_rows or []):
        total = int(r.get("total_attempts", 0) or 0)
        succ = int(r.get("successful", 0) or 0)
        rate = round((succ / total) * 100, 2) if total else 0.0
        by_attempt.append({**r, "success_rate_pct": rate})

    gateway_rows = execute_query(
        """
        SELECT
            t.gateway,
            COUNT(*) AS total_attempts,
            SUM(CASE WHEN UPPER(pr.retry_status) = 'SUCCESS' THEN 1 ELSE 0 END) AS successful,
            SUM(CASE WHEN UPPER(pr.retry_status) != 'SUCCESS' THEN 1 ELSE 0 END) AS failed
        FROM payment_retries pr
        JOIN transactions t ON pr.transaction_id = t.transaction_id
        WHERE t.gateway IS NOT NULL AND t.gateway != ''
        GROUP BY t.gateway
        ORDER BY total_attempts DESC;
        """,
        fetch=True,
    )
    by_gateway: List[Dict[str, Any]] = []
    for r in _rows_to_dicts(gateway_rows or []):
        total = int(r.get("total_attempts", 0) or 0)
        succ = int(r.get("successful", 0) or 0)
        rate = round((succ / total) * 100, 2) if total else 0.0
        by_gateway.append({**r, "success_rate_pct": rate})

    return RetryPerformance(
        total_retries=total_retries,
        successful_retries=successful_retries,
        failed_retries=failed_retries,
        overall_retry_success_rate=overall_rate,
        by_attempt=by_attempt,
        by_gateway=by_gateway,
    )


# -----------------------------
# Alerts Endpoints
# -----------------------------

def _persist_alert(rule_id_any: Any, alert_type: str, message: str, severity: str) -> Optional[int]:
    """Best-effort: store a generated alert in the MySQL alerts table; return inserted id or None."""
    try:
        rule_id_val = int(rule_id_any) if rule_id_any is not None and str(rule_id_any).isdigit() else None
    except (TypeError, ValueError):
        rule_id_val = None
    rows = execute_query(
        """
        INSERT INTO alerts (rule_id, alert_type, message, severity, is_resolved, created_at)
        VALUES (%s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP);
        """,
        (rule_id_val, alert_type[:50], message, severity),
        fetch=False,
    )
    if rows:
        last = execute_query(
            "SELECT LAST_INSERT_ID() AS id;", fetch=True
        )
        if last:
            return int(last[0].get("id", 0) or 0)
    return None


@app.post("/api/alerts/generate")
def post_alerts_generate(
    req: Optional[AlertGenerateRequest] = None,
    api_key: str = Depends(verify_api_key),
):
    req = req or AlertGenerateRequest()
    rules = None
    if req.rules:
        rules = [r.model_dump() for r in req.rules]
    if rules:
        alerts = generate_alerts_from_rules(rules, req.start_date, req.end_date)
        result = {"alerts": alerts, "active_count": len(alerts)}
    else:
        result = generate_all_alerts(req.start_date, req.end_date)

    for a in result.get("alerts") or []:
        _persist_alert(
            a.get("rule_id"),
            a.get("rule_type") or "alert",
            a.get("message") or "",
            a.get("severity") or "MEDIUM",
        )
    return result


@app.get("/api/alerts")
def get_alerts(
    resolved: Optional[bool] = Query(False),
    severity: Optional[Severity] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
):
    offset = (page - 1) * limit
    where_parts = ["1=1"]
    params: List[Any] = []
    if resolved is not None:
        where_parts.append("is_resolved = %s")
        params.append(bool(resolved))
    if severity is not None:
        where_parts.append("severity = %s")
        params.append(severity.value)
    where_sql = " AND ".join(where_parts)

    total_rows = execute_query(
        f"SELECT COUNT(*) AS total FROM alerts WHERE {where_sql};",
        tuple(params) if params else None,
        fetch=True,
    )
    _ensure_db_up(total_rows)
    total = int(total_rows[0].get("total", 0) or 0) if total_rows else 0

    data_rows = execute_query(
        f"""
        SELECT alert_id, rule_id, alert_type, message, severity,
               is_resolved, created_at, resolved_at
        FROM alerts
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """,
        tuple(params + [limit, offset]),
        fetch=True,
    )
    _ensure_db_up(data_rows)
    return paginate_response(_rows_to_dicts(data_rows), total, page, limit)


@app.patch("/api/alerts/{alert_id}/resolve", response_model=AlertResolveResponse)
def resolve_alert(
    alert_id: int,
    api_key: str = Depends(verify_api_key),
):
    existing = execute_query(
        "SELECT alert_id FROM alerts WHERE alert_id = %s LIMIT 1;",
        (alert_id,),
        fetch=True,
    )
    _ensure_db_up(existing)
    if not existing:
        raise HTTPException(status_code=404, detail="Alert not found")

    ok = execute_query(
        "UPDATE alerts SET is_resolved = TRUE, resolved_at = CURRENT_TIMESTAMP WHERE alert_id = %s;",
        (alert_id,),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

    row = execute_query(
        "SELECT resolved_at FROM alerts WHERE alert_id = %s LIMIT 1;",
        (alert_id,),
        fetch=True,
    )
    resolved_at = None
    if row and row[0].get("resolved_at"):
        try:
            resolved_at = row[0]["resolved_at"].isoformat()
        except AttributeError:
            resolved_at = str(row[0]["resolved_at"])
    return AlertResolveResponse(
        alert_id=alert_id,
        resolved=True,
        resolved_at=resolved_at,
        message="Alert resolved",
    )


# -----------------------------
# Bulk Import Endpoints (MySQL-backed)
# -----------------------------

def _bulk_insert_transactions(df: pd.DataFrame) -> dict:
    dedup = dedupe_and_count(
        df,
        table="transactions",
        pk_columns=["transaction_id"],
    )
    deduped_df = dedup["df"]
    result = {
        "inserted": 0,
        "skipped_in_file": int(dedup["skipped_in_file"]),
        "skipped_in_db": int(dedup["skipped_in_db"]),
    }
    if deduped_df.empty:
        return result

    params_list = []
    for _, row in deduped_df.iterrows():
        txn = row.to_dict()
        final_status = txn.get("final_status") or txn.get("initial_status")
        updated_at = txn.get("updated_at") or txn.get("created_at")
        params_list.append((
            txn["transaction_id"],
            txn["customer_id"],
            float(txn["amount"]),
            txn.get("currency", "USD"),
            txn.get("payment_method"),
            txn.get("gateway"),
            txn.get("initial_status"),
            final_status,
            txn.get("created_at"),
            updated_at,
        ))
    ok = execute_many(
        """
        INSERT INTO transactions
            (transaction_id, customer_id, amount, currency, payment_method,
             gateway, initial_status, final_status, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """,
        params_list,
    )
    result["inserted"] = len(params_list) if ok else 0
    return result


def _bulk_insert_retries(df: pd.DataFrame) -> dict:
    dedup = dedupe_and_count(
        df,
        table="payment_retries",
        pk_columns=["transaction_id", "attempt_number"],
    )
    deduped_df = dedup["df"]
    result = {
        "inserted": 0,
        "skipped_in_file": int(dedup["skipped_in_file"]),
        "skipped_in_db": int(dedup["skipped_in_db"]),
    }
    if deduped_df.empty:
        return result

    params_list = []
    for _, row in deduped_df.iterrows():
        r = row.to_dict()
        params_list.append((
            r["transaction_id"],
            int(r["attempt_number"]),
            r["retry_timestamp"],
            r["retry_status"],
            r.get("response_code"),
            r.get("response_message"),
        ))
    ok = execute_many(
        """
        INSERT INTO payment_retries
            (transaction_id, attempt_number, retry_timestamp, retry_status,
             response_code, response_message)
        VALUES (%s,%s,%s,%s,%s,%s);
        """,
        params_list,
    )
    result["inserted"] = len(params_list) if ok else 0
    return result


def _bulk_insert_brc(df: pd.DataFrame) -> dict:
    dedup = dedupe_and_count(
        df,
        table="bank_response_codes",
        pk_columns=["response_code"],
    )
    deduped_df = dedup["df"]
    result = {
        "inserted": 0,
        "skipped_in_file": int(dedup["skipped_in_file"]),
        "skipped_in_db": int(dedup["skipped_in_db"]),
    }
    if deduped_df.empty:
        return result

    params_list = []
    for _, row in deduped_df.iterrows():
        r = row.to_dict()
        rp = r.get("recovery_potential")
        if rp is not None:
            try:
                rp = float(rp)
            except (TypeError, ValueError):
                rp = None
        params_list.append((
            r["response_code"],
            r.get("bank_name"),
            r["description"],
            r["failure_type"],
            rp,
            r.get("recommended_action"),
        ))
    ok = execute_many(
        """
        INSERT INTO bank_response_codes
            (response_code, bank_name, description, failure_type,
             recovery_potential, recommended_action)
        VALUES (%s,%s,%s,%s,%s,%s);
        """,
        params_list,
    )
    result["inserted"] = len(params_list) if ok else 0
    return result


@app.post("/api/transactions/bulk/csv")
async def bulk_import_transactions_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        cleaned_df = clean_transactions(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="No valid transactions to import")
        r = _bulk_insert_transactions(cleaned_df)
        return {
            "message": f"Successfully imported {r['inserted']} transactions",
            "count": r["inserted"],
            "inserted": r["inserted"],
            "skipped_in_file": r["skipped_in_file"],
            "skipped_in_db": r["skipped_in_db"],
            "skipped_total": r["skipped_in_file"] + r["skipped_in_db"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import transactions: {str(e)}")


@app.post("/api/transactions/bulk/json")
async def bulk_import_transactions_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
        df = pd.DataFrame(data)
        cleaned_df = clean_transactions(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="No valid transactions to import")
        r = _bulk_insert_transactions(cleaned_df)
        return {
            "message": f"Successfully imported {r['inserted']} transactions",
            "count": r["inserted"],
            "inserted": r["inserted"],
            "skipped_in_file": r["skipped_in_file"],
            "skipped_in_db": r["skipped_in_db"],
            "skipped_total": r["skipped_in_file"] + r["skipped_in_db"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import transactions: {str(e)}")


@app.post("/api/payment-retries/bulk/csv")
async def bulk_import_payment_retries_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        cleaned_df = clean_payment_retries(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="No valid payment retries to import")
        r = _bulk_insert_retries(cleaned_df)
        return {
            "message": f"Successfully imported {r['inserted']} payment retries",
            "count": r["inserted"],
            "inserted": r["inserted"],
            "skipped_in_file": r["skipped_in_file"],
            "skipped_in_db": r["skipped_in_db"],
            "skipped_total": r["skipped_in_file"] + r["skipped_in_db"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import payment retries: {str(e)}")


@app.post("/api/payment-retries/bulk/json")
async def bulk_import_payment_retries_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
        df = pd.DataFrame(data)
        cleaned_df = clean_payment_retries(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="No valid payment retries to import")
        r = _bulk_insert_retries(cleaned_df)
        return {
            "message": f"Successfully imported {r['inserted']} payment retries",
            "count": r["inserted"],
            "inserted": r["inserted"],
            "skipped_in_file": r["skipped_in_file"],
            "skipped_in_db": r["skipped_in_db"],
            "skipped_total": r["skipped_in_file"] + r["skipped_in_db"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import payment retries: {str(e)}")


@app.post("/api/bank-response-codes/bulk/csv")
async def bulk_import_bank_response_codes_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        cleaned_df = clean_bank_response_codes(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="No valid bank response codes to import")
        r = _bulk_insert_brc(cleaned_df)
        return {
            "message": f"Successfully imported {r['inserted']} bank response codes",
            "count": r["inserted"],
            "inserted": r["inserted"],
            "skipped_in_file": r["skipped_in_file"],
            "skipped_in_db": r["skipped_in_db"],
            "skipped_total": r["skipped_in_file"] + r["skipped_in_db"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import bank response codes: {str(e)}")


@app.post("/api/bank-response-codes/bulk/json")
async def bulk_import_bank_response_codes_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
        df = pd.DataFrame(data)
        cleaned_df = clean_bank_response_codes(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="No valid bank response codes to import")
        r = _bulk_insert_brc(cleaned_df)
        return {
            "message": f"Successfully imported {r['inserted']} bank response codes",
            "count": r["inserted"],
            "inserted": r["inserted"],
            "skipped_in_file": r["skipped_in_file"],
            "skipped_in_db": r["skipped_in_db"],
            "skipped_total": r["skipped_in_file"] + r["skipped_in_db"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import bank response codes: {str(e)}")


# -----------------------------
# Scheduler start hook + Health Check
# -----------------------------

@app.on_event("startup")
def _startup_hook():
    try:
        ensure_scheduler_running()
    except Exception:  # pragma: no cover - defensive
        pass


@app.get("/")
def read_root():
    sched = get_alert_scheduler()
    return {
        "message": "RecoverX Data Integration API",
        "version": "1.1",
        "docs": "/docs",
        "alert_scheduler": {
            "running": sched.is_running,
            "last_active_count": sched.last_result.get("active_count", 0),
        },
    }


@app.get("/healthz")
def healthz():
    """Liveness + readiness probe. Returns 200 only when DB is reachable."""
    db = check_db_health()
    sched = get_alert_scheduler()
    overall_ok = bool(db.get("ok"))
    status_code = 200 if overall_ok else 503
    body = {
        "status": "ok" if overall_ok else "degraded",
        "database": {
            "ok": bool(db.get("ok")),
            "latency_ms": db.get("latency_ms"),
            "error": db.get("error"),
        },
        "alert_scheduler": {
            "running": sched.is_running,
            "last_active_count": sched.last_result.get("active_count", 0),
        },
        "version": "1.1",
    }
    return JSONResponse(status_code=status_code, content=body)
