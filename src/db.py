
import os
import time

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error, pooling


load_dotenv()

# Kept for the API module, which uses these stores for its separate test API.
transactions_db = {}
retries_db = {}
bank_response_codes_db = {}


# -----------------------------
# Configuration
# -----------------------------

_QUERY_TIMEOUT_SECONDS = int(os.getenv("DB_QUERY_TIMEOUT", "30"))
_RETRY_MAX_ATTEMPTS = int(os.getenv("DB_RETRY_MAX_ATTEMPTS", "3"))
_RETRY_BASE_DELAY_SEC = float(os.getenv("DB_RETRY_BASE_DELAY_SEC", "0.5"))
_POOL_NAME = os.getenv("DB_POOL_NAME", "recoverx_pool")
_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
_POOL_RESET_SESSION = os.getenv("DB_POOL_RESET_SESSION", "True").lower() in (
    "1", "true", "yes", "on",
)

# MySQL error codes considered transient (safe to retry).
# Source: common MySQL client & server errors for transient failures.
_TRANSIENT_ERROR_CODES = {
    # Connection / networking
    2006,  # CR_SERVER_GONE_ERROR — MySQL server has gone away
    2013,  # CR_SERVER_LOST — Lost connection to server during query
    2003,  # CR_CONN_HOST_ERROR — Can't connect to MySQL server
    2002,  # CR_CONNECTION_ERROR — Can't connect to local server
    2005,  # CR_UNKNOWN_HOST — Unknown MySQL server host
    1040,  # ER_CON_COUNT_ERROR — Too many connections
    # Locking / transaction
    1205,  # ER_LOCK_WAIT_TIMEOUT — Lock wait timeout exceeded
    1213,  # ER_LOCK_DEADLOCK — Deadlock found
    # Replica / failover
    1290,  # ER_OPTION_PREVENTS_STATEMENT — server in read-only mode
    1836,  # ER_READ_ONLY_MODE — running in read-only mode
}


def _is_transient_error(err: Exception) -> bool:
    """Return True if this exception looks transient and safe to retry."""
    code = getattr(err, "errno", None)
    if code in _TRANSIENT_ERROR_CODES:
        return True
    msg = str(err).upper()
    transient_keywords = (
        "DEADLOCK",
        "LOCK WAIT TIMEOUT",
        "LOST CONNECTION",
        "SERVER GONE AWAY",
        "TOO MANY CONNECTIONS",
        "READ-ONLY MODE",
        "CAN'T CONNECT",
        "CONNECTION TIMED OUT",
        "CONNECTION REFUSED",
    )
    return any(k in msg for k in transient_keywords)


# -----------------------------
# Connection Pool
# -----------------------------

_pool = None
_pool_kwargs = None


def _get_pool_kwargs():
    """Build the config dict used for pool connection creation."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "recoverx"),
    }


def _init_pool():
    """Create (or recreate) the MySQL connection pool using mysql.connector.pooling."""
    global _pool, _pool_kwargs
    try:
        pool_kwargs = _get_pool_kwargs()
        _pool_kwargs = dict(pool_kwargs)
        _pool = pooling.MySQLConnectionPool(
            pool_name=_POOL_NAME,
            pool_size=_POOL_SIZE,
            pool_reset_session=_POOL_RESET_SESSION,
            connection_timeout=_QUERY_TIMEOUT_SECONDS,
            **pool_kwargs,
        )
        return _pool
    except (Error, ValueError):
        _pool = None
        return None


def get_pool():
    """Return the current pool, initializing it lazily on first access."""
    global _pool, _pool_kwargs
    if _pool is None:
        return _init_pool()
    current_kwargs = _get_pool_kwargs()
    # If env changed (rare), recreate the pool.
    if _pool_kwargs != current_kwargs:
        try:
            _init_pool()
        except Exception:
            pass
    return _pool


def get_db_connection():
    """
    Return a connected MySQL connection.

    Tries the connection pool first; falls back to a one-off connection
    when the pool is unavailable. Returns None on failure.
    """
    # 1) Try pool
    pool = get_pool()
    if pool is not None:
        try:
            conn = pool.get_connection()
            if conn is not None and conn.is_connected():
                return conn
        except (Error, ValueError):
            # Pool exhausted or unhealthy; fall through to direct connection.
            pass

    # 2) Fallback: direct one-off connection
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "recoverx"),
            connection_timeout=_QUERY_TIMEOUT_SECONDS,
        )
        return conn if conn.is_connected() else None
    except (Error, ValueError):
        return None


def close_db_connection(connection):
    """Close a connection if one was opened.

    For pooled connections this returns the connection back to the pool.
    """
    try:
        if connection is not None and connection.is_connected():
            connection.close()
    except Exception:
        pass


# -----------------------------
# Retry / timeout helpers
# -----------------------------

def _sleep_for_retry(attempt: int):
    """Exponential backoff: base_delay * (2 ** attempt)."""
    delay = _RETRY_BASE_DELAY_SEC * (2 ** max(0, attempt - 1))
    time.sleep(delay)


# -----------------------------
# Public query execution
# -----------------------------

def execute_query(query, params=None, fetch=False):
    """
    Execute a query, with:
      * connection pool / fallback connections
      * per-statement timeout
      * automatic retries for transient DB errors
    """
    last_error = None
    max_attempts = max(1, _RETRY_MAX_ATTEMPTS)

    for attempt in range(1, max_attempts + 1):
        connection = get_db_connection()
        if not connection:
            last_error = RuntimeError("Unable to obtain database connection")
            if attempt < max_attempts:
                _sleep_for_retry(attempt)
                continue
            return None

        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            # Set session-level max_execution_time (ms) for server-side timeout.
            try:
                cursor.execute(
                    f"SET SESSION MAX_EXECUTION_TIME = %s;",
                    (_QUERY_TIMEOUT_SECONDS * 1000,),
                )
            except Exception:
                pass  # Server may not support the variable; continue anyway.

            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            connection.commit()
            return True
        except Error as err:
            last_error = err
            if fetch:
                # SELECTs — safe to retry transient errors.
                if _is_transient_error(err) and attempt < max_attempts:
                    _sleep_for_retry(attempt)
                    continue
            else:
                # Non-SELECT: only retry when safe (transient connection errors
                # BEFORE any write reached the server). We conservatively retry
                # connection-loss classes because the commit hasn't been acked.
                if _is_transient_error(err) and attempt < max_attempts:
                    _sleep_for_retry(attempt)
                    continue
            return None
        except Exception as err:
            last_error = err
            if attempt < max_attempts:
                _sleep_for_retry(attempt)
                continue
            return None
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            close_db_connection(connection)

    # Ran out of attempts
    return None


def execute_many(query, params_list):
    """Bulk parameter execution (INSERT/UPDATE many rows) with retries."""
    if not params_list:
        return True

    last_error = None
    max_attempts = max(1, _RETRY_MAX_ATTEMPTS)

    for attempt in range(1, max_attempts + 1):
        connection = get_db_connection()
        if not connection:
            last_error = RuntimeError("Unable to obtain database connection")
            if attempt < max_attempts:
                _sleep_for_retry(attempt)
                continue
            return False

        cursor = None
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"SET SESSION MAX_EXECUTION_TIME = %s;",
                    (_QUERY_TIMEOUT_SECONDS * 1000,),
                )
            except Exception:
                pass
            cursor.executemany(query, params_list)
            connection.commit()
            return True
        except Error as err:
            last_error = err
            if _is_transient_error(err) and attempt < max_attempts:
                _sleep_for_retry(attempt)
                continue
            return False
        except Exception as err:
            last_error = err
            if attempt < max_attempts:
                _sleep_for_retry(attempt)
                continue
            return False
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            close_db_connection(connection)

    return False


def check_db_health() -> dict:
    """
    Run a simple connectivity + responsiveness probe.

    Returns dict:
      { "ok": bool, "latency_ms": float|None, "error": str|None }
    """
    start = time.perf_counter()
    try:
        rows = execute_query("SELECT 1 AS ping;", fetch=True)
        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
        if rows:
            return {
                "ok": True,
                "latency_ms": latency_ms,
                "error": None,
            }
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": "Query returned no rows",
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": str(exc),
        }
