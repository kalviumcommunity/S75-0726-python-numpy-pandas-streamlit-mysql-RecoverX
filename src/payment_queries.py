import pandas as pd

from src.db import execute_query

def get_filtered_failed_transactions(
    failure_type: str = None,
    response_code: str = None,
    gateway: str = None,
    payment_method: str = None,

def _get_total(query, params=None):
    result = execute_query(query, params, fetch=True)
    return result[0]["total"] if result else 0


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
    return _get_total(query)


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
    offset = (page - 1) * limit if limit is not None else 0
    query = """
    SELECT *
    FROM payment_retries
    WHERE transaction_id = %s
    ORDER BY attempt_number
    """
    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params = (transaction_id, limit, offset)
    else:
        params = (transaction_id,)
    rows = execute_query(query, params, fetch=True)
    return pd.DataFrame(rows or [])

def count_retry_history(transaction_id):
    query = """
    SELECT COUNT(*) AS total
    FROM payment_retries
    WHERE transaction_id = %s;
    """
    return _get_total(query, (transaction_id,))


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
    return _get_total(query)


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
    return _get_total(query)


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
    return _get_total(query)


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
    return _get_total(query)


def get_failure_type_distribution():
    """
    Return the count of failures grouped by failure_type (TEMPORARY vs PERMANENT)
    from the failure_classifications table. Returns a list of dicts with keys:
    failure_type, count.
    """
    query = """
    SELECT
        failure_type,
        COUNT(*) AS count
    FROM failure_classifications
    GROUP BY failure_type
    ORDER BY failure_type;
    """
    result = execute_query(query, fetch=True)
    if not result:
        temp_count = count_temporary_failures()
        perm_count = count_permanent_failures()
        return [
            {"failure_type": "TEMPORARY", "count": temp_count or 0},
            {"failure_type": "PERMANENT", "count": perm_count or 0},
        ]
    return result


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
    return _get_total(query)


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
    return _get_total(query)


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


def get_filtered_transactions(
    transaction_id: str = None,
    customer_id: str = None,
    start_date: str = None,
    end_date: str = None,
    status: str = None,
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit if limit is not None else 0
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if transaction_id:
        query += " AND transaction_id LIKE %s"
        params.append(f"%{transaction_id}%")
    if customer_id:
        query += " AND customer_id LIKE %s"
        params.append(f"%{customer_id}%")
    if start_date:
        query += " AND created_at >= %s"
        params.append(start_date)
    if end_date:
        query += " AND created_at <= %s"
        params.append(end_date)
    if status:
        query += " AND final_status = %s"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    
    rows = execute_query(query, tuple(params), fetch=True)
    return pd.DataFrame(rows or [])


def count_filtered_transactions(
    transaction_id: str = None,
    customer_id: str = None,
    start_date: str = None,
    end_date: str = None,
):
    query = """
    SELECT DISTINCT
        t.transaction_id, t.customer_id, t.amount, t.currency,
        t.payment_method, t.gateway, t.final_status, t.created_at,
        pr.response_code,
        COALESCE(fc.failure_type, brc.failure_type) AS failure_type,
        COALESCE(brc.description, fc.root_cause) AS failure_description
    FROM transactions t
    LEFT JOIN payment_retries pr ON t.transaction_id = pr.transaction_id
    LEFT JOIN bank_response_codes brc ON pr.response_code = brc.response_code
    LEFT JOIN failure_classifications fc ON t.transaction_id = fc.transaction_id
    WHERE t.final_status != 'SUCCESS'
    """
    params = []
    if failure_type:
        query += " AND COALESCE(fc.failure_type, brc.failure_type) = %s"
        params.append(failure_type)
    if response_code:
        query += " AND pr.response_code = %s"
        params.append(response_code)
    if gateway:
        query += " AND t.gateway = %s"
        params.append(gateway)
    if payment_method:
        query += " AND t.payment_method = %s"
        params.append(payment_method)
    if start_date:
        query += " AND t.created_at >= %s"
        params.append(start_date)
    if end_date:
        query += " AND t.created_at <= %s"
        params.append(end_date)

    query += " ORDER BY t.created_at DESC"
    rows = execute_query(query, tuple(params), fetch=True)
    return pd.DataFrame(rows or [])

def get_failure_breakdown_by_response_code():
    query = """
    SELECT
        pr.response_code AS code,
        COALESCE(brc.description, 'Unknown') AS description,
        COUNT(*) AS count
    FROM payment_retries pr
    LEFT JOIN bank_response_codes brc
        ON pr.response_code = brc.response_code
    WHERE pr.retry_status = 'FAILED'
    GROUP BY pr.response_code, brc.description
    ORDER BY count DESC;
    """
    return execute_query(query, fetch=True)


def get_failure_breakdown_by_gateway():
    query = """
    SELECT
        COALESCE(gateway, 'Unknown') AS gateway,
        COUNT(*) AS count
    FROM transactions
    WHERE final_status = 'FAILED'
    GROUP BY gateway
    ORDER BY count DESC;
    """
    return execute_query(query, fetch=True)


def get_failure_breakdown_by_payment_method():
    query = """
    SELECT
        COALESCE(payment_method, 'Unknown') AS payment_method,
        COUNT(*) AS count
    FROM transactions
    WHERE final_status = 'FAILED'
    GROUP BY payment_method
    ORDER BY count DESC;
    """
    return execute_query(query, fetch=True)

