
"""
RecoverX Data Refresh Utility (PRD 4.1.4)

Automated Data Refresh CLI script that can be called by cron / Windows Task Scheduler.

Key function:
    refresh_all_data_sources() -> re-reads watched folder CSVs, runs cleaning,
                                  re-upserts into DB with INSERT ... ON DUPLICATE KEY UPDATE

Watched folder default:  ./data/
Override via env var:    DATA_REFRESH_WATCH_DIR=/path/to/watched/csvs

Expected CSV file naming in watched folder:
    transactions.csv
    payment_retries.csv
    bank_response_codes.csv

Scheduling Instructions:
------------------------
Linux / cron:
    # Run every hour, every day
    0 * * * * cd /path/to/RecoverX && /usr/bin/python src/data_refresh.py >> data_refresh.log 2>&1

Windows Task Scheduler:
    1. Open "Task Scheduler" → Create Basic Task
    2. Name : RecoverX Data Refresh
       Trigger: Daily → repeat every 1 hour for 24 hours
       Action: Start a program
         Program/script : C:\\Path\\To\\Python\\python.exe
         Add arguments   : src\\data_refresh.py
         Start in        : C:\\Path\\To\\RecoverX
    3. Finish. Right-click task → Run to test.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes,
)
from src.db import execute_query, execute_many

load_dotenv()

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("data_refresh")

# -----------------------------
# Configuration
# -----------------------------
DEFAULT_WATCH_DIR = Path(__file__).resolve().parent.parent / "data"
WATCH_DIR = Path(os.getenv("DATA_REFRESH_WATCH_DIR", str(DEFAULT_WATCH_DIR)))


# -----------------------------
# Upsert helpers (INSERT ... ON DUPLICATE KEY UPDATE)
# -----------------------------
def _upsert_transactions(df: pd.DataFrame) -> int:
    """Upsert cleaned transactions using INSERT ... ON DUPLICATE KEY UPDATE.
    Returns the number of rows processed.
    """
    if len(df) == 0:
        return 0

    cols = [
        "transaction_id", "customer_id", "amount", "currency",
        "payment_method", "gateway", "initial_status", "final_status",
        "created_at", "updated_at",
    ]
    params_list = []
    for _, r in df.iterrows():
        row = {c: r.get(c, None) for c in cols}
        # Convert timestamps to ISO strings (safe for MySQL)
        for dt_col in ("created_at", "updated_at"):
            if row.get(dt_col) is not None and not isinstance(row[dt_col], str):
                try:
                    row[dt_col] = pd.Timestamp(row[dt_col]).to_pydatetime()
                except Exception:
                    row[dt_col] = None
        params_list.append((
            row["transaction_id"], row["customer_id"], row["amount"],
            row.get("currency", "USD"), row.get("payment_method"),
            row.get("gateway"), row["initial_status"], row.get("final_status"),
            row["created_at"], row["updated_at"],
            # ON DUPLICATE KEY UPDATE values
            row["customer_id"], row["amount"], row.get("currency", "USD"),
            row.get("payment_method"), row.get("gateway"), row["initial_status"],
            row.get("final_status"), row["created_at"], row["updated_at"],
        ))

    sql = """
        INSERT INTO transactions
            (transaction_id, customer_id, amount, currency,
             payment_method, gateway, initial_status, final_status,
             created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            customer_id = VALUES(customer_id),
            amount = VALUES(amount),
            currency = VALUES(currency),
            payment_method = VALUES(payment_method),
            gateway = VALUES(gateway),
            initial_status = VALUES(initial_status),
            final_status = VALUES(final_status),
            created_at = VALUES(created_at),
            updated_at = VALUES(updated_at);
    """
    ok = execute_many(sql, params_list)
    return len(params_list) if ok else 0


def _upsert_payment_retries(df: pd.DataFrame) -> int:
    """Upsert cleaned payment_retries.
    Returns rows processed.
    """
    if len(df) == 0:
        return 0

    cols = [
        "transaction_id", "attempt_number", "retry_timestamp",
        "retry_status", "response_code", "response_message",
    ]
    params_list = []
    for _, r in df.iterrows():
        row = {c: r.get(c, None) for c in cols}
        if row.get("retry_timestamp") is not None and not isinstance(row["retry_timestamp"], str):
            try:
                row["retry_timestamp"] = pd.Timestamp(row["retry_timestamp"]).to_pydatetime()
            except Exception:
                row["retry_timestamp"] = None
        params_list.append((
            row["transaction_id"], int(row["attempt_number"]),
            row["retry_timestamp"], row.get("retry_status"),
            row.get("response_code"), row.get("response_message"),
            # ON DUPLICATE KEY UPDATE
            row["retry_timestamp"], row.get("retry_status"),
            row.get("response_code"), row.get("response_message"),
        ))

    sql = """
        INSERT INTO payment_retries
            (transaction_id, attempt_number, retry_timestamp,
             retry_status, response_code, response_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            retry_timestamp = VALUES(retry_timestamp),
            retry_status = VALUES(retry_status),
            response_code = VALUES(response_code),
            response_message = VALUES(response_message);
    """
    ok = execute_many(sql, params_list)
    return len(params_list) if ok else 0


def _upsert_bank_response_codes(df: pd.DataFrame) -> int:
    """Upsert cleaned bank_response_codes.
    Returns rows processed.
    """
    if len(df) == 0:
        return 0

    cols = [
        "response_code", "bank_name", "description",
        "failure_type", "recovery_potential", "recommended_action",
    ]
    params_list = []
    for _, r in df.iterrows():
        row = {c: r.get(c, None) for c in cols}
        params_list.append((
            row["response_code"], row.get("bank_name"),
            row["description"], row.get("failure_type"),
            row.get("recovery_potential"), row.get("recommended_action"),
            # ON DUPLICATE KEY UPDATE
            row.get("bank_name"), row["description"],
            row.get("failure_type"), row.get("recovery_potential"),
            row.get("recommended_action"),
        ))

    sql = """
        INSERT INTO bank_response_codes
            (response_code, bank_name, description,
             failure_type, recovery_potential, recommended_action)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            bank_name = VALUES(bank_name),
            description = VALUES(description),
            failure_type = VALUES(failure_type),
            recovery_potential = VALUES(recovery_potential),
            recommended_action = VALUES(recommended_action);
    """
    ok = execute_many(sql, params_list)
    return len(params_list) if ok else 0


# -----------------------------
# File discovery
# -----------------------------
def _find_csv(watch_dir: Path, name: str) -> Path | None:
    """Locate a CSV by prefix name (case-insensitive).
    Returns path if found, else None.
    """
    if not watch_dir.exists():
        return None
    candidates = list(watch_dir.glob(f"{name}*.csv")) + list(watch_dir.glob(f"{name.upper()}*.CSV"))
    return candidates[0] if candidates else None


# -----------------------------
# Main entrypoint
# -----------------------------
def refresh_all_data_sources(watch_dir: Path | str | None = None) -> dict:
    """
    Re-read watched folder CSVs, re-run cleaning, re-upsert into DB.

    Args:
        watch_dir: Optional override for the watched folder path.

    Returns dict with keys:
        started_at, finished_at, watch_dir,
        transactions, payment_retries, bank_response_codes
        (each nested dict: {csv_found, cleaned_rows, upserted_rows, error})
    """
    started_at = datetime.utcnow().isoformat()
    base_dir = Path(watch_dir) if watch_dir else WATCH_DIR
    logger.info("Starting data refresh. Watch dir: %s", base_dir)

    if not base_dir.exists():
        logger.warning("Watch directory does not exist: %s — creating it.", base_dir)
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.error("Failed to create watch dir: %s", exc)

    # --- Transactions ---
    tx_result = {"csv_found": False, "cleaned_rows": 0, "upserted_rows": 0, "error": None}
    try:
        csv_path = _find_csv(base_dir, "transactions")
        if csv_path is not None:
            tx_result["csv_found"] = True
            logger.info("[transactions] Found CSV: %s", csv_path)
            raw = pd.read_csv(csv_path)
            cleaned = clean_transactions(raw)
            tx_result["cleaned_rows"] = len(cleaned)
            tx_result["upserted_rows"] = _upsert_transactions(cleaned)
            logger.info("[transactions] cleaned=%d, upserted=%d",
                        tx_result["cleaned_rows"], tx_result["upserted_rows"])
        else:
            logger.info("[transactions] No CSV found in %s", base_dir)
    except Exception as exc:
        logger.exception("[transactions] Failed")
        tx_result["error"] = str(exc)

    # --- Payment retries ---
    pr_result = {"csv_found": False, "cleaned_rows": 0, "upserted_rows": 0, "error": None}
    try:
        csv_path = _find_csv(base_dir, "payment_retries")
        if csv_path is not None:
            pr_result["csv_found"] = True
            logger.info("[payment_retries] Found CSV: %s", csv_path)
            raw = pd.read_csv(csv_path)
            cleaned = clean_payment_retries(raw)
            pr_result["cleaned_rows"] = len(cleaned)
            pr_result["upserted_rows"] = _upsert_payment_retries(cleaned)
            logger.info("[payment_retries] cleaned=%d, upserted=%d",
                        pr_result["cleaned_rows"], pr_result["upserted_rows"])
        else:
            logger.info("[payment_retries] No CSV found in %s", base_dir)
    except Exception as exc:
        logger.exception("[payment_retries] Failed")
        pr_result["error"] = str(exc)

    # --- Bank response codes ---
    brc_result = {"csv_found": False, "cleaned_rows": 0, "upserted_rows": 0, "error": None}
    try:
        csv_path = _find_csv(base_dir, "bank_response_codes")
        if csv_path is not None:
            brc_result["csv_found"] = True
            logger.info("[bank_response_codes] Found CSV: %s", csv_path)
            raw = pd.read_csv(csv_path)
            cleaned = clean_bank_response_codes(raw)
            brc_result["cleaned_rows"] = len(cleaned)
            brc_result["upserted_rows"] = _upsert_bank_response_codes(cleaned)
            logger.info("[bank_response_codes] cleaned=%d, upserted=%d",
                        brc_result["cleaned_rows"], brc_result["upserted_rows"])
        else:
            logger.info("[bank_response_codes] No CSV found in %s", base_dir)
    except Exception as exc:
        logger.exception("[bank_response_codes] Failed")
        brc_result["error"] = str(exc)

    finished_at = datetime.utcnow().isoformat()
    summary = {
        "started_at": started_at,
        "finished_at": finished_at,
        "watch_dir": str(base_dir),
        "transactions": tx_result,
        "payment_retries": pr_result,
        "bank_response_codes": brc_result,
    }
    logger.info("Data refresh complete. Summary: %s", summary)
    return summary


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RecoverX automated data refresh (PRD 4.1.4). Re-reads watched folder CSVs, cleans, and upserts into DB."
    )
    parser.add_argument(
        "--watch-dir",
        default=None,
        help="Override watched folder path (default: ./data/ or $DATA_REFRESH_WATCH_DIR)",
    )
    return parser


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()

    result = refresh_all_data_sources(watch_dir=args.watch_dir)

    # Non-zero exit if any dataset had an error
    had_error = any(
        (result[k].get("error") is not None)
        for k in ("transactions", "payment_retries", "bank_response_codes")
    )
    sys.exit(1 if had_error else 0)
