import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def connect_to_db():
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
        st.error(f"Error connecting to MySQL: {e}")
        return None

def import_transactions(df):
    connection = connect_to_db()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO transactions (transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['transaction_id'], row['customer_id'], row['amount'], row.get('currency', 'USD'),
                row.get('payment_method', ''), row.get('gateway', ''), row['initial_status'],
                row.get('final_status', row['initial_status']),
                pd.to_datetime(row['created_at']),
                pd.to_datetime(row.get('updated_at', row['created_at']))
            ))
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"Error importing transactions: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_payment_retries(df):
    connection = connect_to_db()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO payment_retries (transaction_id, attempt_number, retry_timestamp, retry_status, response_code, response_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['transaction_id'], row['attempt_number'], pd.to_datetime(row['retry_timestamp']),
                row['retry_status'], row.get('response_code', ''), row.get('response_message', '')
            ))
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"Error importing payment retries: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_bank_response_codes(df):
    connection = connect_to_db()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO bank_response_codes (response_code, bank_name, description, failure_type, recovery_potential, recommended_action)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['response_code'], row.get('bank_name', ''), row['description'],
                row['failure_type'], row.get('recovery_potential', 0.0),
                row.get('recommended_action', '')
            ))
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"Error importing bank response codes: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

st.set_page_config(
    page_title="RecoverX - CSV Import",
    page_icon="📥",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.header("💰 RecoverX")
    st.caption("Recover Your Revenue")
    st.divider()
    st.subheader("Filters")
    date_range = st.date_input("Select Date Range")

# Main Content
st.title("📥 CSV Import")
st.subheader("Import CSV data into the RecoverX database")
st.divider()

table = st.selectbox("Select table to import into:", ["transactions", "payment_retries", "bank_response_codes"])
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded data:")
    st.dataframe(df.head())

    if st.button("Import Data"):
        if table == "transactions":
            success = import_transactions(df)
        elif table == "payment_retries":
            success = import_payment_retries(df)
        elif table == "bank_response_codes":
            success = import_bank_response_codes(df)

        if success:
            st.success(f"Successfully imported {len(df)} records!")

st.divider()
st.subheader("Example CSV Templates")
st.write("Download example CSV templates to know the required format:")
with open("example_transactions.csv", "rb") as f:
    st.download_button("Download Transactions Template", f, "example_transactions.csv")
with open("example_payment_retries.csv", "rb") as f:
    st.download_button("Download Payment Retries Template", f, "example_payment_retries.csv")
with open("example_bank_response_codes.csv", "rb") as f:
    st.download_button("Download Bank Response Codes Template", f, "example_bank_response_codes.csv")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
