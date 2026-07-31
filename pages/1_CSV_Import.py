import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes,
    validate_import_dataframe,
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
        return False

    try:
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
        return True, len(cleaned_df)
    except Exception as e:
        st.error(f"Error importing transactions: {e}")
        return False, 0
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_payment_retries(df):
    connection = connect_to_db()
    if not connection:
        return False, 0

    try:
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
        return True, len(cleaned_df)
    except Exception as e:
        st.error(f"Error importing payment retries: {e}")
        return False, 0
    finally:
        if connection and connection.is_connected():
            connection.close()

def import_bank_response_codes(df):
    connection = connect_to_db()
    if not connection:
        return False, 0

    try:
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
        return True, len(cleaned_df)
    except Exception as e:
        st.error(f"Error importing bank response codes: {e}")
        return False, 0
    finally:
        if connection and connection.is_connected():
            connection.close()

setup_page("CSV Import", "📥")
render_header()
date_range = render_sidebar()

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.subheader("CSV Import Center")

st.info(
    """
Import transaction data directly into the RecoverX database.

Supported tables:

• Transactions

• Payment Retries

• Bank Response Codes
"""
)

refresh = st.button("🔄 Refresh")

if refresh:
    st.rerun()

st.divider()

# ---------------------------------------------------------
# Import Configuration
# ---------------------------------------------------------

left, right = st.columns([1, 2])

with left:

    table = st.selectbox(
        "Destination Table",
        [
            "transactions",
            "payment_retries",
            "bank_response_codes",
        ],
    )

with right:

    uploaded_file = st.file_uploader(
        "📂 Drag & Drop your CSV here",
        type=["csv"],
        help="Only CSV files are supported.",
    )

# ---------------------------------------------------------
# File Details
# ---------------------------------------------------------

if uploaded_file is not None:

    file_size = uploaded_file.size / 1024

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Filename",
        uploaded_file.name,
    )

    c2.metric(
        "Size",
        f"{file_size:.1f} KB",
    )

    c3.metric(
        "Destination",
        table,
    )

    st.divider()

# ---------------------------------------------------------
# CSV Preview
# ---------------------------------------------------------

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.subheader("CSV Preview")

    st.dataframe(
        df.head(10),
        hide_index=True,
        width="stretch",
    )

# ---------------------------------------------------------
# CSV Validation
# ---------------------------------------------------------

    validation = validate_import_dataframe(df, table)

    st.divider()

    st.subheader("Validation Report")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Rows Uploaded",
        len(df)
    )

    col2.metric(
        "Valid Rows",
        validation["cleaned_rows"]
    )

    col3.metric(
        "Dropped Rows",
        validation["invalid_rows"]
    )

    st.divider()

    # ---------------------------------------------------------
    # Required Columns
    # ---------------------------------------------------------

    if validation["missing_columns"]:

        st.error(
            "Missing Required Columns:\n\n"
            + ", ".join(validation["missing_columns"])
        )

    else:

        st.success("✅ All required columns are present.")

    # ---------------------------------------------------------
    # Cleaned Data Preview
    # ---------------------------------------------------------

    if validation["valid"]:

        st.subheader("Cleaned Data Preview")

        st.dataframe(
            validation["cleaned_df"].head(10),
            hide_index=True,
            width="stretch",
        )

    if validation["invalid_rows"]:

        st.warning(
            f"{validation['invalid_rows']} invalid rows were removed during cleaning."
        )

    st.divider()

    if st.button("🚀 Import Data"):

        if not validation["valid"]:

            st.error("Import blocked. Please fix the CSV first.")

        else:

            with st.spinner("Importing data into database..."):

                if table == "transactions":

                    success, count = import_transactions(
                        validation["cleaned_df"]
                    )

                elif table == "payment_retries":

                    success, count = import_payment_retries(
                        validation["cleaned_df"]
                    )

                else:

                    success, count = import_bank_response_codes(
                        validation["cleaned_df"]
                    )

            if success:

                st.success(
                    f"🎉 Successfully imported {count} records!"
                )

                st.balloons()

            else:

                st.error("Import failed.")

st.divider()

st.subheader("📄 CSV Templates")

st.info(
    """
Need a sample CSV?

Download one of the templates below before importing your data.
"""
)

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown("### 💳 Transactions")

    st.caption(
        "Contains payment transaction records."
    )

    with open("example_transactions.csv", "rb") as f:

        st.download_button(
            "⬇ Download",
            f,
            file_name="example_transactions.csv",
            mime="text/csv",
            use_container_width=True,
        )

with col2:

    st.markdown("### 🔁 Payment Retries")

    st.caption(
        "Contains retry attempt history."
    )

    with open("example_payment_retries.csv", "rb") as f:

        st.download_button(
            "⬇ Download",
            f,
            file_name="example_payment_retries.csv",
            mime="text/csv",
            use_container_width=True,
        )

with col3:

    st.markdown("### 🏦 Bank Codes")

    st.caption(
        "Contains response codes from banks."
    )

    with open("example_bank_response_codes.csv", "rb") as f:

        st.download_button(
            "⬇ Download",
            f,
            file_name="example_bank_response_codes.csv",
            mime="text/csv",
            use_container_width=True,
        )

render_footer()

st.divider()

st.success("✅ RecoverX CSV Import Center Ready")

st.caption(
    "RecoverX • Day 8 • CSV Import Module"
)

st.success("✅ RecoverX CSV Import Center Ready")

st.caption(
    "RecoverX • Day 8 • CSV Import Module"
)

render_footer()