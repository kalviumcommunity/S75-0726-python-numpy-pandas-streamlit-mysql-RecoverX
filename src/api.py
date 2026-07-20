from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.db import execute_query, execute_many
from src.payment_queries import (
    get_all_transactions,
    get_transaction_by_id,
    get_retry_history,
    get_payment_lifecycle,
    get_bank_response_codes,
    get_temporary_failures,
    get_permanent_failures,
    get_failure_classifications,
    get_response_code_analysis,
    get_total_transactions,
    get_successful_transactions,
    get_failed_transactions
)

# Initialize FastAPI app
app = FastAPI(title="RecoverX Data Integration API", version="1.0")


# -----------------------------
# Pydantic Models
# -----------------------------

class TransactionCreate(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    currency: str = "USD"
    payment_method: str = ""
    gateway: str = ""
    initial_status: str
    final_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaymentRetryCreate(BaseModel):
    transaction_id: str
    attempt_number: int
    retry_timestamp: datetime
    retry_status: str
    response_code: Optional[str] = ""
    response_message: Optional[str] = ""


class BankResponseCodeCreate(BaseModel):
    response_code: str
    bank_name: Optional[str] = ""
    description: str
    failure_type: str
    recovery_potential: Optional[float] = 0.0
    recommended_action: Optional[str] = ""


# -----------------------------
# Transactions Endpoints
# -----------------------------

@app.get("/api/transactions")
def list_transactions():
    transactions = get_all_transactions()
    if transactions is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")
    return {"data": transactions}


@app.get("/api/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"data": transaction[0]}


@app.post("/api/transactions")
def create_transaction(transaction: TransactionCreate):
    query = """
        INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    final_status = transaction.final_status or transaction.initial_status
    updated_at = transaction.updated_at or transaction.created_at
    params = (
        transaction.transaction_id,
        transaction.customer_id,
        transaction.amount,
        transaction.currency,
        transaction.payment_method,
        transaction.gateway,
        transaction.initial_status,
        final_status,
        transaction.created_at,
        updated_at
    )
    execute_query(query, params)
    return {"message": "Transaction created successfully", "data": transaction}


# -----------------------------
# Payment Retries Endpoints
# -----------------------------

@app.get("/api/transactions/{transaction_id}/retries")
def list_payment_retries(transaction_id: str):
    retries = get_retry_history(transaction_id)
    if retries is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve payment retries")
    return {"data": retries}


@app.post("/api/transactions/{transaction_id}/retries")
def create_payment_retry(transaction_id: str, retry: PaymentRetryCreate):
    if retry.transaction_id != transaction_id:
        raise HTTPException(status_code=400, detail="Transaction ID mismatch")
    query = """
        INSERT INTO payment_retries (transaction_id, attempt_number, retry_timestamp, retry_status, response_code, response_message)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        retry.transaction_id,
        retry.attempt_number,
        retry.retry_timestamp,
        retry.retry_status,
        retry.response_code,
        retry.response_message
    )
    execute_query(query, params)
    return {"message": "Payment retry created successfully", "data": retry}


# -----------------------------
# Payment Lifecycle Endpoint
# -----------------------------

@app.get("/api/payment-lifecycle")
def get_payment_lifecycle_data():
    lifecycle = get_payment_lifecycle()
    if lifecycle is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve payment lifecycle")
    return {"data": lifecycle}


# -----------------------------
# Bank Response Codes Endpoints
# -----------------------------

@app.get("/api/bank-response-codes")
def list_bank_response_codes():
    codes = get_bank_response_codes()
    if codes is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve bank response codes")
    return {"data": codes}


@app.get("/api/bank-response-codes/temporary")
def list_temporary_failures():
    failures = get_temporary_failures()
    if failures is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve temporary failures")
    return {"data": failures}


@app.get("/api/bank-response-codes/permanent")
def list_permanent_failures():
    failures = get_permanent_failures()
    if failures is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve permanent failures")
    return {"data": failures}


@app.post("/api/bank-response-codes")
def create_bank_response_code(code: BankResponseCodeCreate):
    query = """
        INSERT INTO bank_response_codes (response_code, bank_name, description, failure_type, recovery_potential, recommended_action)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        code.response_code,
        code.bank_name,
        code.description,
        code.failure_type,
        code.recovery_potential,
        code.recommended_action
    )
    execute_query(query, params)
    return {"message": "Bank response code created successfully", "data": code}


# -----------------------------
# Analytics Endpoints
# -----------------------------

@app.get("/api/analytics/overview")
def get_analytics_overview():
    total = get_total_transactions()
    successful = get_successful_transactions()
    failed = get_failed_transactions()
    
    total_count = total[0]["total_transactions"] if total else 0
    successful_count = successful[0]["successful_transactions"] if successful else 0
    failed_count = failed[0]["failed_transactions"] if failed else 0
    
    success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "total_transactions": total_count,
        "successful_transactions": successful_count,
        "failed_transactions": failed_count,
        "success_rate": round(success_rate, 2)
    }


@app.get("/api/analytics/failure-classifications")
def get_failure_classifications_data():
    classifications = get_failure_classifications()
    if classifications is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve failure classifications")
    return {"data": classifications}


@app.get("/api/analytics/response-code-analysis")
def get_response_code_analysis_data():
    analysis = get_response_code_analysis()
    if analysis is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve response code analysis")
    return {"data": analysis}


# -----------------------------
# Health Check Endpoint
# -----------------------------

@app.get("/")
def read_root():
    return {
        "message": "RecoverX Data Integration API",
        "version": "1.0",
        "docs": "/docs"
    }
