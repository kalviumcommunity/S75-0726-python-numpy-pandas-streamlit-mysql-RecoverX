
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from datetime import datetime
from src.data_cleaning import clean_transactions, clean_payment_retries, clean_bank_response_codes

load_dotenv()

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

def import_transactions_from_csv(csv_file_path):
    """Import transactions from a CSV file."""
    connection = connect_to_db()
    if not connection:
        return False

    try:
        df = pd.read_csv(csv_file_path)
        # Clean the data
        cleaned_df = clean_transactions(df)
        cursor = connection.cursor()

        for _, row in cleaned_df.iterrows():
            cursor.execute("""
                INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['transaction_id'], row['customer_id'], row['amount'], row.get('currency', 'USD'),
                row.get('payment_method', None), row.get('gateway', None), row['initial_status'],
                row.get('final_status', None),
                pd.to_datetime(row['created_at']),
                pd.to_datetime(row.get('updated_at', row['created_at']))
            ))

        connection.commit()
        cursor.close()
        print(f"Successfully imported {len(cleaned_df)} transactions!")
        return True
    except Exception as e:
        print(f"Error importing transactions: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_payment_retries_from_csv(csv_file_path):
    """Import payment retries from a CSV file."""
    connection = connect_to_db()
    if not connection:
        return False

    try:
        df = pd.read_csv(csv_file_path)
        # Clean the data
        cleaned_df = clean_payment_retries(df)
        cursor = connection.cursor()

        for _, row in cleaned_df.iterrows():
            cursor.execute("""
                INSERT INTO payment_retries (transaction_id, attempt_number, retry_timestamp, retry_status, response_code, response_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['transaction_id'], row['attempt_number'], pd.to_datetime(row['retry_timestamp']),
                row['retry_status'], row.get('response_code', None), row.get('response_message', None)
            ))

        connection.commit()
        cursor.close()
        print(f"Successfully imported {len(cleaned_df)} payment retries!")
        return True
    except Exception as e:
        print(f"Error importing payment retries: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_bank_response_codes_from_csv(csv_file_path):
    """Import bank response codes from a CSV file."""
    connection = connect_to_db()
    if not connection:
        return False

    try:
        df = pd.read_csv(csv_file_path)
        # Clean the data
        cleaned_df = clean_bank_response_codes(df)
        cursor = connection.cursor()

        for _, row in cleaned_df.iterrows():
            cursor.execute("""
                INSERT INTO bank_response_codes (response_code, bank_name, description, failure_type, recovery_potential, recommended_action)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['response_code'], row.get('bank_name', None), row['description'],
                row['failure_type'], row.get('recovery_potential', None),
                row.get('recommended_action', None)
            ))

        connection.commit()
        cursor.close()
        print(f"Successfully imported {len(cleaned_df)} bank response codes!")
        return True
    except Exception as e:
        print(f"Error importing bank response codes: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import CSV data into RecoverX database')
    parser.add_argument('table', choices=['transactions', 'payment_retries', 'bank_response_codes'], help='Table to import into')
    parser.add_argument('csv_file', help='Path to CSV file')

    args = parser.parse_args()

    if args.table == 'transactions':
        import_transactions_from_csv(args.csv_file)
    elif args.table == 'payment_retries':
        import_payment_retries_from_csv(args.csv_file)
    elif args.table == 'bank_response_codes':
        import_bank_response_codes_from_csv(args.csv_file)

if __name__ == "__main__":
    main()
