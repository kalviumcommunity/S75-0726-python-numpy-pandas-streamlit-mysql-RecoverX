import os
from datetime import datetime

import pytest

from src.db import close_db_connection, get_db_connection

TEST_TRANSACTION_ID = "TEST-TXN-0001"


def cleanup_test_transaction(transaction_id: str):
    """Remove a leftover test transaction row if it exists."""
    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
        connection.commit()
    finally:
        cursor.close()
        close_db_connection(connection)


@pytest.fixture(scope="function")
def test_transaction_id():
    """Ensure the test transaction is removed before and after each test."""
    cleanup_test_transaction(TEST_TRANSACTION_ID)
    yield TEST_TRANSACTION_ID
    cleanup_test_transaction(TEST_TRANSACTION_ID)


def test_db_connection_success():
    """Verify the project can open a MySQL connection using the existing helper."""
    connection = get_db_connection()
    assert connection is not None, "Expected database connection to open successfully"
    assert connection.is_connected(), "Database connection should be active"
    close_db_connection(connection)


def test_db_connection_invalid_credentials(monkeypatch):
    """Verify invalid credentials are handled gracefully and return None."""
    monkeypatch.setenv("DB_PASSWORD", "invalid-password-for-testing")

    connection = get_db_connection()
    assert connection is None, "Expected connection helper to return None with invalid credentials"


def test_create_transaction(test_transaction_id):
    """Create a temporary transaction row in the real transactions table."""
    connection = get_db_connection()
    assert connection is not None, "Failed to open database connection for CREATE test"

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                test_transaction_id,
                "TEST-CUST-0001",
                123.45,
                "USD",
                "Test Card",
                "TestGateway",
                "Pending",
                "Pending",
                datetime.utcnow(),
            ),
        )
        connection.commit()
    finally:
        cursor.close()
        close_db_connection(connection)

    # Verify the row was inserted.
    connection = get_db_connection()
    assert connection is not None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", (test_transaction_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        close_db_connection(connection)

    assert row is not None, "Inserted transaction row should be present"
    assert row["customer_id"] == "TEST-CUST-0001"
    assert float(row["amount"]) == 123.45
    assert row["currency"] == "USD"


def test_read_transaction(test_transaction_id):
    """Read the temporary transaction row and verify its values."""
    connection = get_db_connection()
    assert connection is not None

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                test_transaction_id,
                "TEST-CUST-0002",
                200.00,
                "USD",
                "Test Card",
                "TestGateway",
                "Failed",
                "Failed",
                datetime.utcnow(),
            ),
        )
        connection.commit()

        cursor.close()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", (test_transaction_id,))
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_db_connection(connection)

    assert row is not None, "Expected to read the inserted transaction row"
    assert row["transaction_id"] == test_transaction_id
    assert row["initial_status"] == "Failed"
    assert row["final_status"] == "Failed"


def test_update_transaction(test_transaction_id):
    """Update the temporary transaction row and confirm the change."""
    connection = get_db_connection()
    assert connection is not None

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                test_transaction_id,
                "TEST-CUST-0003",
                300.00,
                "USD",
                "Test Card",
                "TestGateway",
                "Pending",
                "Pending",
                datetime.utcnow(),
            ),
        )
        connection.commit()

        cursor.execute(
            "UPDATE transactions SET final_status = %s WHERE transaction_id = %s",
            ("Success", test_transaction_id),
        )
        connection.commit()

        cursor.close()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT final_status FROM transactions WHERE transaction_id = %s", (test_transaction_id,))
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_db_connection(connection)

    assert row is not None, "Expected updated transaction row to exist"
    assert row["final_status"] == "Success"


def test_delete_transaction(test_transaction_id):
    """Delete the temporary transaction row and verify it no longer exists."""
    connection = get_db_connection()
    assert connection is not None

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                test_transaction_id,
                "TEST-CUST-0004",
                400.00,
                "USD",
                "Test Card",
                "TestGateway",
                "Pending",
                "Pending",
                datetime.utcnow(),
            ),
        )
        connection.commit()

        cursor.execute("DELETE FROM transactions WHERE transaction_id = %s", (test_transaction_id,))
        connection.commit()

        cursor.close()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", (test_transaction_id,))
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_db_connection(connection)

    assert row is None, "Transaction row should have been deleted"
