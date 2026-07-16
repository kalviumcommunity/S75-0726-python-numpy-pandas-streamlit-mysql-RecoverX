
import random
import string
from datetime import datetime, timedelta
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def generate_transaction_id():
    """Generate a random transaction ID."""
    return f"TXN-{''.join(random.choices(string.ascii_uppercase + string.digits, k=12))}"

def generate_customer_id():
    """Generate a random customer ID."""
    return f"CUST-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

def generate_random_date(start_date, end_date):
    """Generate a random date between start and end date."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86399)
    return start_date + timedelta(days=random_days, seconds=random_seconds)

def connect_to_db():
    """Connect to MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "recoverx")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def insert_bank_response_codes(connection):
    """Insert bank response codes data."""
    response_codes = [
        ("00", "Global Bank", "Approved", "TEMPORARY", 0.00, "No action needed"),
        ("05", "Global Bank", "Do Not Honor", "PERMANENT", 0.10, "Contact customer for alternative payment"),
        ("14", "Global Bank", "Invalid Card Number", "PERMANENT", 0.00, "Request correct card details"),
        ("51", "Global Bank", "Insufficient Funds", "TEMPORARY", 0.80, "Retry after 24 hours"),
        ("54", "Global Bank", "Expired Card", "PERMANENT", 0.20, "Request updated card details"),
        ("65", "Global Bank", "Exceeds Withdrawal Limit", "TEMPORARY", 0.70, "Retry with lower amount"),
        ("91", "Global Bank", "Issuer Unavailable", "TEMPORARY", 0.90, "Retry after 1 hour"),
        ("02", "City Bank", "Refer to Issuer", "TEMPORARY", 0.60, "Contact issuer for details"),
        ("03", "City Bank", "Invalid Merchant", "PERMANENT", 0.00, "Verify merchant details"),
        ("12", "City Bank", "Invalid Transaction", "PERMANENT", 0.30, "Check transaction details")
    ]
    cursor = connection.cursor()
    for code in response_codes:
        try:
            cursor.execute("""
                INSERT INTO bank_response_codes (response_code, bank_name, description, failure_type, recovery_potential, recommended_action)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, code)
        except Error:
            pass  # Ignore duplicates
    connection.commit()
    cursor.close()

def insert_alert_rules(connection):
    """Insert alert rules data."""
    rules = [
        ("High Failure Rate", "failure_rate", 30.00, "&gt;", True),
        ("Response Code Trend", "response_trend", 20.00, "&gt;", True),
        ("Low Success Rate", "success_rate", 70.00, "&lt;", True)
    ]
    cursor = connection.cursor()
    for rule in rules:
        try:
            cursor.execute("""
                INSERT INTO alert_rules (rule_name, rule_type, threshold_value, threshold_condition, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, rule)
        except Error:
            pass  # Ignore duplicates
    connection.commit()
    cursor.close()

def generate_synthetic_data(num_transactions=100):
    """Generate synthetic test data."""
    transactions = []
    payment_retries = []
    failure_classifications = []
    alerts = []

    payment_methods = ["Credit Card", "Debit Card", "Net Banking", "UPI"]
    gateways = ["Stripe", "PayPal", "Razorpay", "Square"]
    statuses = ["Success", "Failed"]
    failure_types = ["TEMPORARY", "PERMANENT"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    # Get response codes
    response_codes = [
        "00", "05", "14", "51", "54", "65", "91", "02", "03", "12"
    ]

    for _ in range(num_transactions):
        transaction_id = generate_transaction_id()
        customer_id = generate_customer_id()
        amount = round(random.uniform(10.00, 5000.00), 2)
        currency = "USD"
        payment_method = random.choice(payment_methods)
        gateway = random.choice(gateways)
        initial_status = random.choice(statuses)
        final_status = initial_status if initial_status == "Success" else random.choice(statuses)
        created_at = generate_random_date(start_date, end_date)
        updated_at = created_at + timedelta(hours=random.randint(1, 72))

        transactions.append((
            transaction_id, customer_id, amount, currency, payment_method, gateway,
            initial_status, final_status, created_at, updated_at
        ))

        # Generate payment retries if initial status is Failed
        if initial_status == "Failed":
            num_retries = random.randint(1, 3)
            for attempt in range(1, num_retries + 1):
                retry_timestamp = created_at + timedelta(hours=attempt * random.randint(2, 24))
                retry_status = random.choice(statuses)
                response_code = random.choice(response_codes)
                response_message = f"Response: {response_code}"

                payment_retries.append((
                    transaction_id, attempt, retry_timestamp, retry_status,
                    response_code, response_message
                ))

                if retry_status == "Success":
                    break

        # Generate failure classification
        if initial_status == "Failed":
            failure_type = random.choice(failure_types)
            root_cause = "Insufficient funds" if failure_type == "TEMPORARY" else "Invalid card"
            recovery_score = round(random.uniform(0.1, 1.0), 2)
            is_high_value = amount &gt; 1000
            classified_at = created_at + timedelta(hours=1)

            failure_classifications.append((
                transaction_id, failure_type, root_cause, recovery_score,
                is_high_value, classified_at
            ))

    # Generate some alerts
    for _ in range(5):
        alert_type = random.choice(["failure_rate", "response_trend", "revenue_loss"])
        message = f"Alert: {alert_type} detected"
        severity = random.choice(severities)
        created_at = generate_random_date(start_date, end_date)

        alerts.append((
            random.randint(1, 3), alert_type, message, severity, created_at
        ))

    return transactions, payment_retries, failure_classifications, alerts

def insert_data(connection, transactions, payment_retries, failure_classifications, alerts):
    """Insert generated data into the database."""
    cursor = connection.cursor()

    # Insert transactions
    for txn in transactions:
        cursor.execute("""
            INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, txn)

    # Insert payment retries
    for retry in payment_retries:
        cursor.execute("""
            INSERT INTO payment_retries (transaction_id, attempt_number, retry_timestamp, retry_status, response_code, response_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, retry)

    # Insert failure classifications
    for fc in failure_classifications:
        cursor.execute("""
            INSERT INTO failure_classifications (transaction_id, failure_type, root_cause, recovery_score, is_high_value, classified_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, fc)

    # Insert alerts
    for alert in alerts:
        cursor.execute("""
            INSERT INTO alerts (rule_id, alert_type, message, severity, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, alert)

    connection.commit()
    cursor.close()

def main():
    """Main function to generate and insert data."""
    connection = connect_to_db()
    if not connection:
        print("Could not connect to database.")
        return

    print("Generating synthetic test data...")

    # Insert reference data
    insert_bank_response_codes(connection)
    insert_alert_rules(connection)

    # Generate synthetic data
    transactions, payment_retries, failure_classifications, alerts = generate_synthetic_data(num_transactions=100)

    # Insert into database
    insert_data(connection, transactions, payment_retries, failure_classifications, alerts)

    print("Successfully inserted synthetic data!")
    connection.close()

if __name__ == "__main__":
    main()

