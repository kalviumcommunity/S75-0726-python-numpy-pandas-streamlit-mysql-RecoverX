import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from src.ui_components import setup_page, render_header, render_sidebar, render_footer, require_page_permission
from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes,
    dedupe_and_count,
)

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
        return False, 0, 0, 0

    try:
        cleaned_df = clean_transactions(df)
        # Dedup: reject PK duplicates (in-file + in-DB)
        dedup = dedupe_and_count(
            cleaned_df,
            table="transactions",
            pk_columns=["transaction_id"],
            connection_factory=connect_to_db,
        )
        deduped_df = dedup["df"]
        skipped_in_file = dedup["skipped_in_file"]
        skipped_in_db = dedup["skipped_in_db"]

        if len(deduped_df) == 0:
            return True, 0, skipped_in_file, skipped_in_db

        cursor = connection.cursor()
        for _, row in deduped_df.iterrows():
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
        return True, len(deduped_df), skipped_in_file, skipped_in_db
    except Exception as e:
        st.error(f"Error importing transactions: {e}")
        return False, 0, 0, 0
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_payment_retries(df):
    connection = connect_to_db()
    if not connection:
        return False, 0, 0, 0

    try:
        cleaned_df = clean_payment_retries(df)
        # Dedup on natural key (transaction_id, attempt_number)
        dedup = dedupe_and_count(
            cleaned_df,
            table="payment_retries",
            pk_columns=["transaction_id", "attempt_number"],
            connection_factory=connect_to_db,
        )
        deduped_df = dedup["df"]
        skipped_in_file = dedup["skipped_in_file"]
        skipped_in_db = dedup["skipped_in_db"]

        if len(deduped_df) == 0:
            return True, 0, skipped_in_file, skipped_in_db

        cursor = connection.cursor()
        for _, row in deduped_df.iterrows():
            cursor.execute("""
                INSERT INTO payment_retries (transaction_id, attempt_number, retry_timestamp, retry_status, response_code, response_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['transaction_id'], row['attempt_number'], pd.to_datetime(row['retry_timestamp']),
                row['retry_status'], row.get('response_code', None), row.get('response_message', None)
            ))
        connection.commit()
        cursor.close()
        return True, len(deduped_df), skipped_in_file, skipped_in_db
    except Exception as e:
        st.error(f"Error importing payment retries: {e}")
        return False, 0, 0, 0
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_bank_response_codes(df):
    connection = connect_to_db()
    if not connection:
        return False, 0, 0, 0

    try:
        cleaned_df = clean_bank_response_codes(df)
        dedup = dedupe_and_count(
            cleaned_df,
            table="bank_response_codes",
            pk_columns=["response_code"],
            connection_factory=connect_to_db,
        )
        deduped_df = dedup["df"]
        skipped_in_file = dedup["skipped_in_file"]
        skipped_in_db = dedup["skipped_in_db"]

        if len(deduped_df) == 0:
            return True, 0, skipped_in_file, skipped_in_db

        cursor = connection.cursor()
        for _, row in deduped_df.iterrows():
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
        return True, len(deduped_df), skipped_in_file, skipped_in_db
    except Exception as e:
        st.error(f"Error importing bank response codes: {e}")
        return False, 0, 0, 0
    finally:
        if connection and connection.is_connected():
            connection.close()

setup_page("CSV Import", "📥")
render_header()
date_range = render_sidebar()

require_page_permission("CSV Import")

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
            success, count, skipped_file, skipped_db = import_transactions(df)
        elif table == "payment_retries":
            success, count, skipped_file, skipped_db = import_payment_retries(df)
        elif table == "bank_response_codes":
            success, count, skipped_file, skipped_db = import_bank_response_codes(df)

        if success:
            total_skipped = skipped_file + skipped_db
            lines = [f"Successfully imported **{count}** records!"]
            if skipped_file:
                lines.append(f"• Skipped {skipped_file} duplicate(s) within file (same PK kept last)")
            if skipped_db:
                lines.append(f"• Skipped {skipped_db} duplicate(s) already in database")
            st.success("  \n".join(lines))

st.divider()
st.subheader("Example CSV Templates")
st.write("Download example CSV templates to know the required format:")
with open("example_transactions.csv", "rb") as f:
    st.download_button("Download Transactions Template", f, "example_transactions.csv")
with open("example_payment_retries.csv", "rb") as f:
    st.download_button("Download Payment Retries Template", f, "example_payment_retries.csv")
with open("example_bank_response_codes.csv", "rb") as f:
    st.download_button("Download Bank Response Codes Template", f, "example_bank_response_codes.csv")

render_footer()
