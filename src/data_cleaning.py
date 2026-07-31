import pandas as pd
import numpy as np


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean transactions DataFrame according to RecoverX schema.
    
    Args:
        df (pd.DataFrame): Raw transactions DataFrame
        
    Returns:
        pd.DataFrame: Cleaned transactions DataFrame
    """
    # Make a copy to avoid modifying original
    cleaned = df.copy()
    
    # Convert date columns to datetime
    date_columns = ["created_at", "updated_at"]
    for col in date_columns:
        if col in cleaned.columns:
            cleaned[col] = pd.to_datetime(cleaned[col], errors="coerce")
    
    # Normalize status fields (uppercase, strip whitespace)
    status_columns = ["initial_status", "final_status"]
    for col in status_columns:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype(str).str.strip().str.upper()
    
    # Ensure amount is numeric, handle currency
    if "amount" in cleaned.columns:
        cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    
    # Drop rows with missing required fields
    required_fields = ["transaction_id", "customer_id", "amount", "initial_status", "created_at"]
    cleaned = cleaned.dropna(subset=[col for col in required_fields if col in cleaned.columns])
    
    # Remove duplicate transaction_ids
    cleaned = cleaned.drop_duplicates(subset=["transaction_id"], keep="last")
    
    return cleaned


def clean_payment_retries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean payment_retries DataFrame according to RecoverX schema.
    
    Args:
        df (pd.DataFrame): Raw payment_retries DataFrame
        
    Returns:
        pd.DataFrame: Cleaned payment_retries DataFrame
    """
    cleaned = df.copy()
    
    # Convert retry_timestamp to datetime
    if "retry_timestamp" in cleaned.columns:
        cleaned["retry_timestamp"] = pd.to_datetime(cleaned["retry_timestamp"], errors="coerce")
    
    # Normalize retry_status and response_code
    if "retry_status" in cleaned.columns:
        cleaned["retry_status"] = cleaned["retry_status"].astype(str).str.strip().str.upper()
    
    if "response_code" in cleaned.columns:
        cleaned["response_code"] = cleaned["response_code"].astype(str).str.strip()
    
    # Ensure attempt_number is integer
    if "attempt_number" in cleaned.columns:
        cleaned["attempt_number"] = pd.to_numeric(cleaned["attempt_number"], downcast="integer", errors="coerce").fillna(0).astype(int)
    
    # Drop rows with missing required fields
    required_fields = ["transaction_id", "attempt_number", "retry_status", "retry_timestamp"]
    cleaned = cleaned.dropna(subset=[col for col in required_fields if col in cleaned.columns])
    
    return cleaned


def clean_bank_response_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean bank_response_codes DataFrame according to RecoverX schema.
    
    Args:
        df (pd.DataFrame): Raw bank_response_codes DataFrame
        
    Returns:
        pd.DataFrame: Cleaned bank_response_codes DataFrame
    """
    cleaned = df.copy()
    
    # Normalize response_code
    if "response_code" in cleaned.columns:
        cleaned["response_code"] = cleaned["response_code"].astype(str).str.strip()
    
    # Normalize failure_type
    if "failure_type" in cleaned.columns:
        cleaned["failure_type"] = cleaned["failure_type"].astype(str).str.strip().str.upper()
        # Validate failure_type is either TEMPORARY or PERMANENT
        valid_failure_types = ["TEMPORARY", "PERMANENT"]
        cleaned["failure_type"] = cleaned["failure_type"].apply(lambda x: x if x in valid_failure_types else np.nan)
    
    # Ensure recovery_potential is numeric between 0 and 1
    if "recovery_potential" in cleaned.columns:
        cleaned["recovery_potential"] = pd.to_numeric(cleaned["recovery_potential"], errors="coerce")
        cleaned["recovery_potential"] = cleaned["recovery_potential"].clip(0.0, 1.0)
    
    # Drop rows with missing required fields
    required_fields = ["response_code", "description", "failure_type"]
    cleaned = cleaned.dropna(subset=[col for col in required_fields if col in cleaned.columns])
    
    # Remove duplicates by response_code
    cleaned = cleaned.drop_duplicates(subset=["response_code"], keep="last")
    
    return cleaned


def validate_import_dataframe(df: pd.DataFrame, table_name: str) -> dict:
    """
    Validate a raw CSV DataFrame before import.

    Returns a dictionary containing validation status, cleaned rows, and any
    missing required columns.
    """
    table_name = str(table_name).lower()
    required_columns = {
        "transactions": ["transaction_id", "customer_id", "amount", "initial_status", "created_at"],
        "payment_retries": ["transaction_id", "attempt_number", "retry_status", "retry_timestamp"],
        "bank_response_codes": ["response_code", "description", "failure_type"],
    }

    if table_name not in required_columns:
        return {
            "valid": False,
            "cleaned_df": pd.DataFrame(),
            "missing_columns": [],
            "invalid_rows": len(df) if df is not None else 0,
            "cleaned_rows": 0,
            "errors": ["Unsupported table name for CSV validation."],
        }

    if df is None or df.empty:
        return {
            "valid": False,
            "cleaned_df": pd.DataFrame(),
            "missing_columns": [],
            "invalid_rows": 0,
            "cleaned_rows": 0,
            "errors": ["Uploaded file is empty."],
        }

    missing_columns = [column for column in required_columns[table_name] if column not in df.columns]
    if missing_columns:
        return {
            "valid": False,
            "cleaned_df": pd.DataFrame(),
            "missing_columns": missing_columns,
            "invalid_rows": len(df),
            "cleaned_rows": 0,
            "errors": [f"Missing required columns: {', '.join(missing_columns)}"],
        }

    if table_name == "transactions":
        cleaned_df = clean_transactions(df)
    elif table_name == "payment_retries":
        cleaned_df = clean_payment_retries(df)
    else:
        cleaned_df = clean_bank_response_codes(df)

    invalid_rows = int(len(df) - len(cleaned_df))

    return {
        "valid": len(cleaned_df) > 0,
        "cleaned_df": cleaned_df,
        "missing_columns": [],
        "invalid_rows": invalid_rows,
        "cleaned_rows": len(cleaned_df),
        "errors": [
            f"{invalid_rows} row(s) were dropped during cleaning."
        ] if invalid_rows else [],
    }


def merge_payment_lifecycle(transactions_df: pd.DataFrame, retries_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge transactions and payment retries into a single payment lifecycle DataFrame.
    
    Args:
        transactions_df (pd.DataFrame): Cleaned transactions DataFrame
        retries_df (pd.DataFrame): Cleaned payment retries DataFrame
        
    Returns:
        pd.DataFrame: Merged payment lifecycle DataFrame
    """
    # Merge on transaction_id
    merged = pd.merge(
        retries_df,
        transactions_df,
        on="transaction_id",
        how="left",
        suffixes=("_retry", "_txn")
    )
    
    # Sort by transaction_id and attempt_number
    merged = merged.sort_values(by=["transaction_id", "attempt_number"])
    
    return merged
