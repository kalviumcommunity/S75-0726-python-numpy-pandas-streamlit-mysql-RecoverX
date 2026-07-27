import pandas as pd

from src.db import execute_query

def get_filtered_failed_transactions(
    failure_type: str = None,
    response_code: str = None,
    gateway: str = None,
    payment_method: str = None,
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