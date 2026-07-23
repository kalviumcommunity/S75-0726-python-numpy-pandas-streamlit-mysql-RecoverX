
# In-memory database for testing purposes
transactions_db = {}
retries_db = {}
bank_response_codes_db = {}


def get_db_connection():
    # Not needed for in-memory, but kept for compatibility
    return None


def close_db_connection(connection):
    # Not needed for in-memory
    pass


def execute_query(query, params=None, fetch=False):
    # This is a placeholder for in-memory testing
    return None


def execute_many(query, params_list):
    # This is a placeholder for in-memory testing
    return True
