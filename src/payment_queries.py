
from src.db import execute_query


# -----------------------------
# Transactions
# -----------------------------

def get_all_transactions(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT *
    FROM transactions
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_all_transactions():
    query = """
    SELECT COUNT(*) AS total
    FROM transactions;
    """
    return execute_query(query, fetch=True)[0]["total"]


def get_transaction_by_id(transaction_id):
    query = """
    SELECT *
    FROM transactions
    WHERE transaction_id = %s;
    """
    return execute_query(query, (transaction_id,), fetch=True)


# -----------------------------
# Payment Retries
# -----------------------------

def get_retry_history(transaction_id, page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT *
    FROM payment_retries
    WHERE transaction_id = %s
    ORDER BY attempt_number
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (transaction_id, limit, offset), fetch=True)

def count_retry_history(transaction_id):
    query = """
    SELECT COUNT(*) AS total
    FROM payment_retries
    WHERE transaction_id = %s;
    """
    return execute_query(query, (transaction_id,), fetch=True)[0]["total"]


# -----------------------------
# Payment Lifecycle
# -----------------------------

def get_payment_lifecycle(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT
        t.transaction_id,
        t.customer_id,
        t.amount,
        r.attempt_number,
        r.retry_status,
        r.response_code,
        r.retry_timestamp
    FROM transactions t
    JOIN payment_retries r
        ON t.transaction_id = r.transaction_id
    ORDER BY
        t.transaction_id,
        r.attempt_number
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_payment_lifecycle():
    query = """
    SELECT COUNT(*) AS total
    FROM transactions t
    JOIN payment_retries r
        ON t.transaction_id = r.transaction_id;
    """
    return execute_query(query, fetch=True)[0]["total"]


# -----------------------------
# Response Codes
# -----------------------------

def get_bank_response_codes(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT *
    FROM bank_response_codes
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_bank_response_codes():
    query = """
    SELECT COUNT(*) AS total
    FROM bank_response_codes;
    """
    return execute_query(query, fetch=True)[0]["total"]


def get_temporary_failures(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT *
    FROM bank_response_codes
    WHERE failure_type='TEMPORARY'
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_temporary_failures():
    query = """
    SELECT COUNT(*) AS total
    FROM bank_response_codes
    WHERE failure_type='TEMPORARY';
    """
    return execute_query(query, fetch=True)[0]["total"]


def get_permanent_failures(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT *
    FROM bank_response_codes
    WHERE failure_type='PERMANENT'
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_permanent_failures():
    query = """
    SELECT COUNT(*) AS total
    FROM bank_response_codes
    WHERE failure_type='PERMANENT';
    """
    return execute_query(query, fetch=True)[0]["total"]


# -----------------------------
# Failure Classification
# -----------------------------

def get_failure_classifications(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT *
    FROM failure_classifications
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_failure_classifications():
    query = """
    SELECT COUNT(*) AS total
    FROM failure_classifications;
    """
    return execute_query(query, fetch=True)[0]["total"]


# -----------------------------
# Response Code Analysis
# -----------------------------

def get_response_code_analysis(page=1, limit=10):
    offset = (page - 1) * limit
    query = """
    SELECT
        r.transaction_id,
        r.response_code,
        b.description,
        b.failure_type,
        b.recovery_potential
    FROM payment_retries r
    JOIN bank_response_codes b
        ON r.response_code = b.response_code
    LIMIT %s OFFSET %s;
    """
    return execute_query(query, (limit, offset), fetch=True)

def count_response_code_analysis():
    query = """
    SELECT COUNT(*) AS total
    FROM payment_retries r
    JOIN bank_response_codes b
        ON r.response_code = b.response_code;
    """
    return execute_query(query, fetch=True)[0]["total"]


# -----------------------------
# Analytics
# -----------------------------

def get_total_transactions():
    query = """
    SELECT COUNT(*) AS total_transactions
    FROM transactions;
    """
    return execute_query(query, fetch=True)


def get_successful_transactions():
    query = """
    SELECT COUNT(*) AS successful_transactions
    FROM transactions
    WHERE final_status='SUCCESS';
    """
    return execute_query(query, fetch=True)


def get_failed_transactions():
    query = """
    SELECT COUNT(*) AS failed_transactions
    FROM transactions
    WHERE final_status='FAILED';
    """
    return execute_query(query, fetch=True)

