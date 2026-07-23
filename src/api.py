from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Security,
    Query,
    UploadFile,
    File,
)

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, condecimal
from typing import List, Optional
from datetime import datetime
from enum import Enum
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

import os
import pandas as pd
import json

from dotenv import load_dotenv
from io import StringIO

load_dotenv()

from src.db import execute_query, execute_many
from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes
)

from src.payment_queries import (
    get_all_transactions,
    count_all_transactions,
    get_transaction_by_id,
    get_retry_history,
    count_retry_history,
    get_payment_lifecycle,
    count_payment_lifecycle,
    get_bank_response_codes,
    count_bank_response_codes,
    get_temporary_failures,
    count_temporary_failures,
    get_permanent_failures,
    count_permanent_failures,
    get_failure_classifications,
    count_failure_classifications,
    get_response_code_analysis,
    count_response_code_analysis,
    get_total_transactions,
    get_successful_transactions,
    get_failed_transactions
)

# Initialize FastAPI app
app = FastAPI(title="RecoverX Data Integration API", version="1.0")

API_KEY = "recoverx123"

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key"
        )
    return api_key

# =====================================================
# API KEY AUTHENTICATION
# =====================================================

API_KEY = os.getenv("API_KEY", "recoverx-secret-key")

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API Key from request header.
    """

    if api_key == API_KEY:
        return api_key

    raise HTTPException(
        status_code=401,
        detail="Invalid or Missing API Key"
    )

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
    """Request model for creating a transaction.
    Validates required transaction fields and types against the transactions table schema.
    """
    transaction_id: str = Field(..., max_length=100, description="Unique transaction identifier")
    customer_id: str = Field(..., max_length=100, description="Customer identifier")
    amount: condecimal(max_digits=15, decimal_places=2, gt=0) = Field(..., description="Transaction amount")
    currency: str = Field("USD", max_length=10, description="Currency code")
    payment_method: Optional[str] = Field(None, max_length=100, description="Payment method used")
    gateway: Optional[str] = Field(None, max_length=100, description="Payment gateway used")
    initial_status: str = Field(..., max_length=50, description="Initial transaction status")
    final_status: Optional[str] = Field(None, max_length=50, description="Final transaction status")
    created_at: datetime = Field(..., description="Transaction creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class PaymentRetryCreate(BaseModel):
    """Request model for creating a payment retry entry.
    Validates retry attempt payload based on the payment_retries schema.
    """
    transaction_id: str = Field(..., max_length=100, description="Associated transaction identifier")
    attempt_number: int = Field(..., gt=0, description="Retry attempt number")
    retry_timestamp: datetime = Field(..., description="Time of retry attempt")
    retry_status: str = Field(..., max_length=50, description="Retry status")
    response_code: Optional[str] = Field(None, max_length=50, description="Bank response code")
    response_message: Optional[str] = Field(None, description="Bank response message")


class BankResponseCodeCreate(BaseModel):
    """Request model for creating a bank response code lookup entry.
    Validates bank response code payload against bank_response_codes schema.
    """
    response_code: str = Field(..., max_length=50, description="Bank response code")
    bank_name: Optional[str] = Field(None, max_length=100, description="Issuing bank name")
    description: str = Field(..., description="Description of the response code")
    failure_type: FailureType = Field(..., description="Failure classification type")
    recovery_potential: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = Field(None, description="Recovery potential score")
    recommended_action: Optional[str] = Field(None, description="Recommended action for this response code")


# -----------------------------
# Transactions Endpoints
# -----------------------------

@app.get("/api/transactions")
def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    transactions = get_all_transactions(page, limit)

    if transactions is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve transactions"
        )

    total = count_all_transactions()

    return {
        "data": transactions,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }


@app.get("/api/transactions/{transaction_id}")
def get_transaction(
    transaction_id: str,
    api_key: str = Depends(verify_api_key)
):
    transaction = get_transaction_by_id(transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "data": transaction[0]
    }

@app.post("/api/transactions")
def create_transaction(
    transaction: TransactionCreate,
    api_key: str = Depends(verify_api_key)
):
    query = """
        INSERT INTO transactions (
            transaction_id,
            customer_id,
            amount,
            currency,
            payment_method,
            gateway,
            initial_status,
            final_status,
            created_at,
            updated_at
        )
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

    return {
        "message": "Transaction created successfully",
        "data": transaction
    }

# -----------------------------
# Payment Retries Endpoints
# -----------------------------

@app.get("/api/transactions/{transaction_id}/retries")
def list_payment_retries(
    transaction_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    retries = get_retry_history(transaction_id, page, limit)

    if retries is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve payment retries"
        )

    total = count_retry_history(transaction_id)

    return {
        "data": retries,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@app.post("/api/transactions/{transaction_id}/retries")
def create_payment_retry(
    transaction_id: str,
    retry: PaymentRetryCreate,
    api_key: str = Depends(verify_api_key)
):
    if retry.transaction_id != transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID mismatch"
        )

    query = """
        INSERT INTO payment_retries (
            transaction_id,
            attempt_number,
            retry_timestamp,
            retry_status,
            response_code,
            response_message
        )
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

    return {
        "message": "Payment retry created successfully",
        "data": retry
    }

# -----------------------------
# Payment Lifecycle Endpoint
# -----------------------------

@app.get("/api/payment-lifecycle")
def get_payment_lifecycle_data(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    lifecycle = get_payment_lifecycle(page, limit)

    if lifecycle is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve payment lifecycle"
        )

    total = count_payment_lifecycle()

    return {
        "data": lifecycle,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

# -----------------------------
# Bank Response Codes Endpoints
# -----------------------------

@app.get("/api/bank-response-codes")
def list_bank_response_codes(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    codes = get_bank_response_codes(page, limit)

    if codes is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve bank response codes"
        )

    total = count_bank_response_codes()

    return {
        "data": codes,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@app.get("/api/bank-response-codes/temporary")
def list_temporary_failures(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    failures = get_temporary_failures(page, limit)

    if failures is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve temporary failures"
        )

    total = count_temporary_failures()

    return {
        "data": failures,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@app.get("/api/bank-response-codes/permanent")
def list_permanent_failures(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    failures = get_permanent_failures(page, limit)

    if failures is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve permanent failures"
        )

    total = count_permanent_failures()

    return {
        "data": failures,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@app.post("/api/bank-response-codes")
def create_bank_response_code(
    code: BankResponseCodeCreate,
    api_key: str = Depends(verify_api_key)
):
    query = """
        INSERT INTO bank_response_codes (
            response_code,
            bank_name,
            description,
            failure_type,
            recovery_potential,
            recommended_action
        )
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

    return {
        "message": "Bank response code created successfully",
        "data": code
    }

# -----------------------------
# Analytics Endpoints
# -----------------------------

@app.get("/api/analytics/overview")
def get_analytics_overview(
    api_key: str = Depends(verify_api_key)
):
    total = get_total_transactions()
    successful = get_successful_transactions()
    failed = get_failed_transactions()

    total_count = total[0]["total_transactions"] if total else 0
    successful_count = successful[0]["successful_transactions"] if successful else 0
    failed_count = failed[0]["failed_transactions"] if failed else 0

    success_rate = (
        successful_count / total_count * 100
        if total_count > 0 else 0
    )

    return {
        "total_transactions": total_count,
        "successful_transactions": successful_count,
        "failed_transactions": failed_count,
        "success_rate": round(success_rate, 2)
    }

@app.get("/api/analytics/failure-classifications")
def get_failure_classifications_data(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    classifications = get_failure_classifications(page, limit)

    if classifications is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve failure classifications"
        )

    total = count_failure_classifications()

    return {
        "data": classifications,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@app.get("/api/analytics/response-code-analysis")
def get_response_code_analysis_data(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    analysis = get_response_code_analysis(page, limit)

    if analysis is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve response code analysis"
        )

    total = count_response_code_analysis()

    return {
        "data": analysis,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

# -----------------------------
# Bulk Import Endpoints
# -----------------------------

def df_to_transaction_params(df):
    """Convert cleaned transactions DataFrame to list of tuples for execute_many."""
    params = []
    for _, row in df.iterrows():
        final_status = row.get("final_status") or row["initial_status"]
        updated_at = row.get("updated_at") or row["created_at"]
        params.append((
            row["transaction_id"],
            row["customer_id"],
            row["amount"],
            row.get("currency", "USD"),
            row.get("payment_method"),
            row.get("gateway"),
            row["initial_status"],
            final_status,
            pd.to_datetime(row["created_at"]),
            pd.to_datetime(updated_at)
        ))
    return params


def df_to_payment_retry_params(df):
    """Convert cleaned payment retries DataFrame to list of tuples for execute_many."""
    params = []
    for _, row in df.iterrows():
        params.append((
            row["transaction_id"],
            row["attempt_number"],
            pd.to_datetime(row["retry_timestamp"]),
            row["retry_status"],
            row.get("response_code"),
            row.get("response_message")
        ))
    return params


def df_to_bank_response_code_params(df):
    """Convert cleaned bank response codes DataFrame to list of tuples for execute_many."""
    params = []
    for _, row in df.iterrows():
        params.append((
            row["response_code"],
            row.get("bank_name"),
            row["description"],
            row["failure_type"],
            row.get("recovery_potential"),
            row.get("recommended_action")
        ))
    return params


@app.post("/api/transactions/bulk/csv")
async def bulk_import_transactions_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        cleaned_df = clean_transactions(df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid transactions to import"
            )

        params = df_to_transaction_params(cleaned_df)

        execute_many("""
            INSERT INTO transactions (
                transaction_id,
                customer_id,
                amount,
                currency,
                payment_method,
                gateway,
                initial_status,
                final_status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, params)

        return {
            "message": f"Successfully imported {len(cleaned_df)} transactions",
            "count": len(cleaned_df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import transactions: {str(e)}"
        )

@app.post("/api/transactions/bulk/json")
async def bulk_import_transactions_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
        df = pd.DataFrame(data)
        cleaned_df = clean_transactions(df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid transactions to import"
            )

        params = df_to_transaction_params(cleaned_df)

        execute_many("""
            INSERT INTO transactions (
                transaction_id,
                customer_id,
                amount,
                currency,
                payment_method,
                gateway,
                initial_status,
                final_status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, params)

        return {
            "message": f"Successfully imported {len(cleaned_df)} transactions",
            "count": len(cleaned_df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import transactions: {str(e)}"
        )

@app.post("/api/payment-retries/bulk/csv")
async def bulk_import_payment_retries_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        cleaned_df = clean_payment_retries(df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid payment retries to import"
            )

        params = df_to_payment_retry_params(cleaned_df)

        execute_many("""
            INSERT INTO payment_retries (
                transaction_id,
                attempt_number,
                retry_timestamp,
                retry_status,
                response_code,
                response_message
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, params)

        return {
            "message": f"Successfully imported {len(cleaned_df)} payment retries",
            "count": len(cleaned_df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import payment retries: {str(e)}"
        )

@app.post("/api/payment-retries/bulk/json")
async def bulk_import_payment_retries_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
        df = pd.DataFrame(data)
        cleaned_df = clean_payment_retries(df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid payment retries to import"
            )

        params = df_to_payment_retry_params(cleaned_df)

        execute_many("""
            INSERT INTO payment_retries (
                transaction_id,
                attempt_number,
                retry_timestamp,
                retry_status,
                response_code,
                response_message
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, params)

        return {
            "message": f"Successfully imported {len(cleaned_df)} payment retries",
            "count": len(cleaned_df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import payment retries: {str(e)}"
        )

@app.post("/api/bank-response-codes/bulk/csv")
async def bulk_import_bank_response_codes_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        cleaned_df = clean_bank_response_codes(df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid bank response codes to import"
            )

        params = df_to_bank_response_code_params(cleaned_df)

        execute_many("""
            INSERT INTO bank_response_codes (
                response_code,
                bank_name,
                description,
                failure_type,
                recovery_potential,
                recommended_action
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, params)

        return {
            "message": f"Successfully imported {len(cleaned_df)} bank response codes",
            "count": len(cleaned_df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import bank response codes: {str(e)}"
        )

@app.post("/api/bank-response-codes/bulk/json")
async def bulk_import_bank_response_codes_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
        df = pd.DataFrame(data)
        cleaned_df = clean_bank_response_codes(df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid bank response codes to import"
            )

        params = df_to_bank_response_code_params(cleaned_df)

        execute_many("""
            INSERT INTO bank_response_codes (
                response_code,
                bank_name,
                description,
                failure_type,
                recovery_potential,
                recommended_action
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, params)

        return {
            "message": f"Successfully imported {len(cleaned_df)} bank response codes",
            "count": len(cleaned_df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import bank response codes: {str(e)}"
        )

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

