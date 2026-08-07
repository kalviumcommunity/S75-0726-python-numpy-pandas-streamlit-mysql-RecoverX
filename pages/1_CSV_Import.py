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

 frontend_changes
required_cols = {
    "transactions": ["transaction_id", "customer_id", "amount", "initial_status", "created_at"],
    "payment_retries": ["transaction_id", "attempt_number", "retry_timestamp", "retry_status"],
    "bank_response_codes": ["response_code", "description", "failure_type"],
}

cleaner_map = {
    "transactions": clean_transactions,
    "payment_retries": clean_payment_retries,
    "bank_response_codes": clean_bank_response_codes,
}

table = st.selectbox("Select table to import into:", ["transactions", "payment_retries", "bank_response_codes"])
st.caption(
    f"💡 **Drag & drop supported:** click the box below or drop a `.csv` file onto it. "
    f"Required columns for `{table}`: **{', '.join(required_cols[table])}**."
)

uploaded_file = st.file_uploader(
    "Upload a CSV file (drag and drop supported)",
    type=["csv"],
    accept_multiple_files=False,
    help=(
        "You can drag a CSV file from Explorer and drop it directly onto the upload area above. "
        "A validation summary will appear as soon as the file is loaded."
    ),
)

validation_state = {}

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as read_err:
        st.error(f"Could not read CSV: {read_err}")
        df = pd.DataFrame()

    if not df.empty:
        st.markdown("#### 📋 Upload Preview")
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"Raw rows uploaded: **{len(df):,}** · Columns: **{', '.join(df.columns)}**")

        st.markdown("#### 🔍 Validation Summary")
        required = required_cols[table]
        missing = [c for c in required if c not in df.columns]
        present = [c for c in required if c in df.columns]

        vcol1, vcol2, vcol3, vcol4 = st.columns(4)
        vcol1.metric("Raw Rows", f"{len(df):,}")
        vcol2.metric("Columns Found", f"{len(df.columns)}")
        vcol3.metric(
            "Required Columns",
            f"{len(present)}/{len(required)}",
            delta="OK" if not missing else "MISSING",
            delta_color="normal" if not missing else "inverse",
        )

        try:
            cleaned_df = cleaner_map[table](df)
        except Exception as clean_err:
            st.error(f"Data cleaning failed: {clean_err}")
            cleaned_df = pd.DataFrame()

        if not cleaned_df.empty:
            rows_dropped = len(df) - len(cleaned_df)
            dropped_pct = (rows_dropped / len(df) * 100.0) if len(df) else 0.0
            vcol4.metric(
                "Rows After Clean",
                f"{len(cleaned_df):,}",
                delta=f"-{rows_dropped:,} (-{dropped_pct:.1f}%)" if rows_dropped else "No drops",
                delta_color="inverse" if rows_dropped else "normal",
            )

            issues = []
            if missing:
                issues.append(
                    f"❌ **Missing required columns:** {', '.join(missing)} — "
                    f"these rows will be dropped or the import may fail. "
                    f"Add the missing headers to your CSV and re-upload."
                )
            else:
                issues.append(
                    f"✅ All required columns present: {', '.join(present)}."
                )

            if rows_dropped > 0:
                issues.append(
                    f"⚠️ **{rows_dropped:,} row(s) dropped** during cleaning "
                    f"({dropped_pct:.1f}% of upload) — rows with missing required fields, "
                    f"invalid dates, or duplicate primary keys are removed automatically."
                )

            if "amount" in df.columns:
                bad_amount = pd.to_numeric(df["amount"], errors="coerce").isna().sum()
                if bad_amount:
                    issues.append(
                        f"⚠️ **{bad_amount:,} row(s)** had non-numeric `amount` values — "
                        f"they were coerced to 0 or dropped."
                    )

            if "attempt_number" in df.columns:
                bad_attempt = pd.to_numeric(df["attempt_number"], errors="coerce").isna().sum()
                if bad_attempt:
                    issues.append(
                        f"⚠️ **{bad_attempt:,} row(s)** had non-integer `attempt_number` — "
                        f"values were coerced to 0."
                    )

            if "recovery_potential" in df.columns:
                rp = pd.to_numeric(df["recovery_potential"], errors="coerce")
                out_of_range = ((rp < 0) | (rp > 1)).fillna(False).sum()
                if out_of_range:
                    issues.append(
                        f"ℹ️ **{out_of_range:,} row(s)** had `recovery_potential` outside [0,1] — "
                        f"values were clipped to the valid range."
                    )

            if table == "bank_response_codes" and "failure_type" in df.columns:
                valid_ft = {"TEMPORARY", "PERMANENT"}
                bad_ft = (~df["failure_type"].astype(str).str.upper().isin(valid_ft)).sum()
                if bad_ft:
                    issues.append(
                        f"⚠️ **{bad_ft:,} row(s)** had invalid `failure_type` "
                        f"(expected TEMPORARY or PERMANENT) — rows will be dropped."
                    )

            for issue in issues:
                st.markdown(f"- {issue}")

            validation_state["cleaned_df"] = cleaned_df
            validation_state["table"] = table
        else:
            vcol4.metric("Rows After Clean", "0")
            st.error("Cleaning produced 0 valid rows — cannot import. Check the CSV format and required columns.")

if st.button("📥 Import Data", type="primary", disabled=not validation_state.get("cleaned_df", pd.DataFrame()).shape[0] if validation_state else True):
    cleaned_to_import = validation_state.get("cleaned_df")
    table_to_import = validation_state.get("table")
    if cleaned_to_import is None or cleaned_to_import.empty or table_to_import != table:
        st.warning("Upload a valid CSV first and wait for the validation summary to appear.")
    else:
        count = 0
        success = False
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