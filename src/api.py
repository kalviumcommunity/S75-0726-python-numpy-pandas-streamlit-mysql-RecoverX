import os
import json
import pandas as pd

from io import StringIO
from datetime import datetime
from typing import List, Optional

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
from pydantic import BaseModel

from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, condecimal
from typing import List, Optional
from datetime import datetime
from enum import Enum
from fastapi.security import APIKeyHeader

import os
import pandas as pd
import json
import io

from dotenv import load_dotenv
from io import StringIO

load_dotenv()

from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes
)

# Import in-memory databases
from src.db import (
    transactions_db,
    retries_db,
    bank_response_codes_db
)

# Initialize FastAPI app
app = FastAPI(title="RecoverX Data Integration API", version="1.0")

# API Key Authentication
API_KEY = os.getenv("API_KEY", "recoverx-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or Missing API Key")
    return api_key


# -----------------------------
# Pydantic Models
# -----------------------------

class FailureType(str, Enum):
    TEMPORARY = "TEMPORARY"
    PERMANENT = "PERMANENT"


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


# -----------------------------
# Transactions Endpoints
# -----------------------------

@app.get("/api/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    all_transactions = list(transactions_db.values())
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": all_transactions[start:end],
        "page": page,
        "limit": limit,
        "total": len(all_transactions),
        "pages": (len(all_transactions) + limit - 1) // limit
    }


@app.get("/api/transactions/{transaction_id}")
def get_transaction(
    transaction_id: str,
    api_key: str = Depends(verify_api_key)
):
    if transaction_id not in transactions_db:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"data": transactions_db[transaction_id]}


@app.post("/api/transactions")
def create_transaction(
    transaction: TransactionCreate,
    api_key: str = Depends(verify_api_key)
):
    txn_dict = transaction.model_dump()
    txn_dict["final_status"] = txn_dict.get("final_status") or txn_dict["initial_status"]
    txn_dict["updated_at"] = txn_dict.get("updated_at") or txn_dict["created_at"]
    transactions_db[transaction.transaction_id] = txn_dict
    return {
        "message": "Transaction created successfully",
        "data": txn_dict
    }


@app.get("/api/transactions/export/csv")
def export_transactions_csv(api_key: str = Depends(verify_api_key)):
    """Export all transactions as CSV."""
    # Convert transactions to DataFrame
    all_transactions = list(transactions_db.values())
    df = pd.DataFrame(all_transactions)
    
    # Create CSV in memory
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    # Return as StreamingResponse
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=transactions.csv"
        }
    )


@app.get("/api/transactions/export/excel")
def export_transactions_excel(api_key: str = Depends(verify_api_key)):
    """Export all transactions as Excel."""
    # Convert transactions to DataFrame
    all_transactions = list(transactions_db.values())
    df = pd.DataFrame(all_transactions)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    output.seek(0)
    
    # Return as StreamingResponse
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=transactions.xlsx"
        }
    )


# -----------------------------
# Payment Retries Endpoints
# -----------------------------

@app.get("/api/transactions/{transaction_id}/retries")
def list_payment_retries(
    transaction_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    all_retries = retries_db.get(transaction_id, [])
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": all_retries[start:end],
        "page": page,
        "limit": limit,
        "total": len(all_retries),
        "pages": (len(all_retries) + limit - 1) // limit
    }


@app.post("/api/transactions/{transaction_id}/retries")
def create_payment_retry(
    transaction_id: str,
    retry: PaymentRetryCreate,
    api_key: str = Depends(verify_api_key)
):
    if retry.transaction_id != transaction_id:
        raise HTTPException(status_code=400, detail="Transaction ID mismatch")
    if transaction_id not in retries_db:
        retries_db[transaction_id] = []
    retry_dict = retry.model_dump()
    retries_db[transaction_id].append(retry_dict)
    return {
        "message": "Payment retry created successfully",
        "data": retry_dict
    }


# -----------------------------
# Payment Lifecycle Endpoint
# -----------------------------

@app.get("/api/payment-lifecycle")
def get_payment_lifecycle_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    lifecycle = []
    for txn_id, txn in transactions_db.items():
        txn_retries = retries_db.get(txn_id, [])
        for retry in txn_retries:
            lifecycle.append({
                **txn,
                **retry
            })
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": lifecycle[start:end],
        "page": page,
        "limit": limit,
        "total": len(lifecycle),
        "pages": (len(lifecycle) + limit - 1) // limit
    }


# -----------------------------
# Bank Response Codes Endpoints
# -----------------------------

@app.get("/api/bank-response-codes")
def list_bank_response_codes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    all_codes = list(bank_response_codes_db.values())
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": all_codes[start:end],
        "page": page,
        "limit": limit,
        "total": len(all_codes),
        "pages": (len(all_codes) + limit - 1) // limit
    }


@app.get("/api/bank-response-codes/temporary")
def list_temporary_failures(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    all_codes = list(bank_response_codes_db.values())
    temp_failures = [c for c in all_codes if c["failure_type"] == "TEMPORARY"]
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": temp_failures[start:end],
        "page": page,
        "limit": limit,
        "total": len(temp_failures),
        "pages": (len(temp_failures) + limit - 1) // limit
    }


@app.get("/api/bank-response-codes/permanent")
def list_permanent_failures(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    all_codes = list(bank_response_codes_db.values())
    perm_failures = [c for c in all_codes if c["failure_type"] == "PERMANENT"]
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": perm_failures[start:end],
        "page": page,
        "limit": limit,
        "total": len(perm_failures),
        "pages": (len(perm_failures) + limit - 1) // limit
    }


@app.post("/api/bank-response-codes")
def create_bank_response_code(
    code: BankResponseCodeCreate,
    api_key: str = Depends(verify_api_key)
):
    code_dict = code.model_dump()
    bank_response_codes_db[code.response_code] = code_dict
    return {
        "message": "Bank response code created successfully",
        "data": code_dict
    }


# -----------------------------
# Analytics Endpoints
# -----------------------------

@app.get("/api/analytics/overview")
def get_analytics_overview(
    api_key: str = Depends(verify_api_key)
):
    total = len(transactions_db)
    successful = sum(1 for txn in transactions_db.values() if txn["final_status"].lower() in ["success", "completed"])
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0
    return {
        "total_transactions": total,
        "successful_transactions": successful,
        "failed_transactions": failed,
        "success_rate": round(success_rate, 2)
    }


@app.get("/api/analytics/failure-classifications")
def get_failure_classifications_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    classifications = []
    for code, code_data in bank_response_codes_db.items():
        classifications.append({
            "response_code": code,
            "failure_type": code_data["failure_type"],
            "description": code_data["description"]
        })
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": classifications[start:end],
        "page": page,
        "limit": limit,
        "total": len(classifications),
        "pages": (len(classifications) + limit - 1) // limit
    }


@app.get("/api/analytics/response-code-analysis")
def get_response_code_analysis_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    analysis = []
    code_counts = {}
    for txn_id, retries in retries_db.items():
        for retry in retries:
            code = retry.get("response_code")
            if code:
                code_counts[code] = code_counts.get(code, 0) + 1
    for code, count in code_counts.items():
        code_data = bank_response_codes_db.get(code, {})
        analysis.append({
            "response_code": code,
            "count": count,
            "failure_type": code_data.get("failure_type"),
            "description": code_data.get("description")
        })
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": analysis[start:end],
        "page": page,
        "limit": limit,
        "total": len(analysis),
        "pages": (len(analysis) + limit - 1) // limit
    }


# -----------------------------
# Bulk Import Endpoints
# -----------------------------

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
            raise HTTPException(status_code=400, detail="No valid transactions to import")
        count = 0
        for _, row in cleaned_df.iterrows():
            txn_id = row["transaction_id"]
            txn_dict = row.to_dict()
            txn_dict["amount"] = float(txn_dict["amount"])
            txn_dict["final_status"] = txn_dict.get("final_status") or txn_dict["initial_status"]
            txn_dict["updated_at"] = txn_dict.get("updated_at") or txn_dict["created_at"]
            transactions_db[txn_id] = txn_dict
            count += 1
        return {"message": f"Successfully imported {count} transactions", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import transactions: {str(e)}")


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
            raise HTTPException(status_code=400, detail="No valid transactions to import")
        count = 0
        for _, row in cleaned_df.iterrows():
            txn_id = row["transaction_id"]
            txn_dict = row.to_dict()
            txn_dict["amount"] = float(txn_dict["amount"])
            txn_dict["final_status"] = txn_dict.get("final_status") or txn_dict["initial_status"]
            txn_dict["updated_at"] = txn_dict.get("updated_at") or txn_dict["created_at"]
            transactions_db[txn_id] = txn_dict
            count += 1
        return {"message": f"Successfully imported {count} transactions", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import transactions: {str(e)}")


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
            raise HTTPException(status_code=400, detail="No valid payment retries to import")
        count = 0
        for _, row in cleaned_df.iterrows():
            txn_id = row["transaction_id"]
            retry_dict = row.to_dict()
            if txn_id not in retries_db:
                retries_db[txn_id] = []
            retries_db[txn_id].append(retry_dict)
            count += 1
        return {"message": f"Successfully imported {count} payment retries", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import payment retries: {str(e)}")


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
            raise HTTPException(status_code=400, detail="No valid payment retries to import")
        count = 0
        for _, row in cleaned_df.iterrows():
            txn_id = row["transaction_id"]
            retry_dict = row.to_dict()
            if txn_id not in retries_db:
                retries_db[txn_id] = []
            retries_db[txn_id].append(retry_dict)
            count += 1
        return {"message": f"Successfully imported {count} payment retries", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import payment retries: {str(e)}")


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
            raise HTTPException(status_code=400, detail="No valid bank response codes to import")
        count = 0
        for _, row in cleaned_df.iterrows():
            code_id = row["response_code"]
            code_dict = row.to_dict()
            if code_dict.get("recovery_potential") is not None:
                code_dict["recovery_potential"] = float(code_dict["recovery_potential"])
            bank_response_codes_db[code_id] = code_dict
            count += 1
        return {"message": f"Successfully imported {count} bank response codes", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import bank response codes: {str(e)}")


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
            raise HTTPException(status_code=400, detail="No valid bank response codes to import")
        count = 0
        for _, row in cleaned_df.iterrows():
            code_id = row["response_code"]
            code_dict = row.to_dict()
            if code_dict.get("recovery_potential") is not None:
                code_dict["recovery_potential"] = float(code_dict["recovery_potential"])
            bank_response_codes_db[code_id] = code_dict
            count += 1
        return {"message": f"Successfully imported {count} bank response codes", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import bank response codes: {str(e)}")


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
