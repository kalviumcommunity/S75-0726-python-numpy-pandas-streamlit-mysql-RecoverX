
import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


load_dotenv()

# Kept for the API module, which uses these stores for its separate test API.
transactions_db = {}
retries_db = {}
bank_response_codes_db = {}


def get_db_connection():
    """Open the configured MySQL connection, returning None on failure."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "recoverx"),
        )
        return connection if connection.is_connected() else None
    except (Error, ValueError):
        return None


def close_db_connection(connection):
    """Close a connection if one was opened."""
    if connection and connection.is_connected():
        connection.close()


def execute_query(query, params=None, fetch=False):
    """Execute a query using dictionary rows and close its resources."""
    connection = get_db_connection()
    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        connection.commit()
        return True
    except Error:
        return None
    finally:
        cursor.close()
        close_db_connection(connection)


def execute_many(query, params_list):
    connection = get_db_connection()
    if not connection:
        return False

    cursor = connection.cursor()
    try:
        cursor.executemany(query, params_list)
        connection.commit()
        return True
    except Error:
        return False
    finally:
        cursor.close()
        close_db_connection(connection)
