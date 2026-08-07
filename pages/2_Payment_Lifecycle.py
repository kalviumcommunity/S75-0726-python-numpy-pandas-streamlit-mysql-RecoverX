
import sys
from io import BytesIO, StringIO
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ui_components import setup_page, render_header, render_sidebar, render_footer, require_page_permission
from src.payment_queries import (
    get_filtered_transactions,
    count_filtered_transactions,
    get_transaction_status_over_time,
    get_retry_attempts_distribution,
    get_retry_history_with_bank_details,
)

@st.cache_data(ttl=60)
def _cached_get_filtered_transactions(start_date=None, end_date=None, transaction_id=None,
                                   customer_id=None, status=None, limit=100, offset=0):
    return get_filtered_transactions(start_date, end_date, transaction_id,
                                     customer_id, status, limit, offset)

@st.cache_data(ttl=60)
def _cached_count_filtered_transactions(start_date=None, end_date=None, transaction_id=None,
                                      customer_id=None, status=None):
    return count_filtered_transactions(start_date, end_date, transaction_id,
                                      customer_id, status)

@st.cache_data(ttl=60)
def _cached_get_transaction_status_over_time(start_date=None, end_date=None):
    return get_transaction_status_over_time(start_date, end_date)

@st.cache_data(ttl=60)
def _cached_get_retry_attempts_distribution(start_date=None, end_date=None):
    return get_retry_attempts_distribution(start_date, end_date)

@st.cache_data(ttl=60)
def _cached_get_retry_history(transaction_id):
    return get_retry_history(transaction_id)

get_filtered_transactions = _cached_get_filtered_transactions
count_filtered_transactions = _cached_count_filtered_transactions
get_transaction_status_over_time = _cached_get_transaction_status_over_time
get_retry_attempts_distribution = _cached_get_retry_attempts_distribution
get_retry_history = _cached_get_retry_history

setup_page("Payment Lifecycle", "🔄")
render_header()
date_range = render_sidebar()

require_page_permission("Payment Lifecycle")

st.subheader("Track complete journey of payments")
st.divider()

# --- Search/Filter Section ---
with st.expander("🔍 Search & Filter Transactions", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        transaction_id_filter = st.text_input("Transaction ID", placeholder="Enter transaction ID...")
        customer_id_filter = st.text_input("Customer ID", placeholder="Enter customer ID...")
    with col2:
        start_date_filter = st.date_input("Start Date", value=None)
        end_date_filter = st.date_input("End Date", value=None)
    status_filter = st.selectbox("Status", options=["All", "SUCCESS", "FAILED"], index=0)

# --- Charts Section ---
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.subheader("Transaction Status Over Time")
    status_over_time = get_transaction_status_over_time() or []
    if status_over_time:
        df_status = pd.DataFrame(status_over_time)
        fig = px.line(df_status, x="date", y=["success_count", "failed_count"], markers=True, 
                     color_discrete_sequence=["#16a34a", "#dc2626"],
                     labels={"date": "Date", "value": "Count", "variable": "Status"})
        fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0})
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No transaction status data available yet.")

with chart_col2:
    st.subheader("Retry Attempts Distribution")
    retry_dist_data = get_retry_attempts_distribution() or []
    if retry_dist_data:
        df_retry = pd.DataFrame(retry_dist_data)
        df_retry["attempt_category"] = df_retry["attempt_count"].apply(lambda x: "4+" if x >=4 else str(x))
        retry_counts = df_retry["attempt_category"].value_counts().reset_index()
        retry_counts.columns = ["Attempts", "Transactions"]
        retry_counts["sort_key"] = retry_counts["Attempts"].apply(lambda x: 4 if x == "4+" else int(x))
        retry_counts = retry_counts.sort_values("sort_key").drop("sort_key", axis=1)
        fig = px.bar(retry_counts, x="Attempts", y="Transactions", color="Attempts", 
                     color_discrete_sequence=["#2563eb", "#38bdf8", "#0ea5e9", "#0369a1", "#0c4a6e"])
        fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0}, showlegend=False)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No retry attempts data available yet.")

st.divider()

# --- Filtered Transactions Section ---
st.subheader("Filtered Transactions")

status_query = status_filter if status_filter != "All" else None
start_date_str = str(start_date_filter) if start_date_filter else None
end_date_str = str(end_date_filter) + " 23:59:59" if end_date_filter else None

try:
    transactions = get_filtered_transactions(
        transaction_id=transaction_id_filter,
        customer_id=customer_id_filter,
        start_date=start_date_str,
        end_date=end_date_str,
        status=status_query
    )
    total_transactions = count_filtered_transactions(
        transaction_id=transaction_id_filter,
        customer_id=customer_id_filter,
        start_date=start_date_str,
        end_date=end_date_str,
        status=status_query
    )
except Exception as error:
    st.error(f"Unable to load transactions from the database: {error}")
    transactions = pd.DataFrame()
    total_transactions = 0

if not transactions.empty:
    df_transactions = transactions
    st.caption(f"Showing {len(df_transactions)} of {total_transactions} matching transactions.")
    st.dataframe(df_transactions, width='stretch')

    # --- CSV + Excel Export for Filtered Transactions ---
    st.markdown("#### Exports")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        csv_buffer = StringIO()
        df_transactions.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Filtered Transactions (CSV)",
            data=csv_buffer.getvalue(),
            file_name="filtered_transactions.csv",
            mime="text/csv",
        )

    with exp_col2:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_transactions.to_excel(writer, index=False, sheet_name="Transactions")
        st.download_button(
            label="📥 Filtered Transactions (Excel)",
            data=excel_buffer.getvalue(),
            file_name="filtered_transactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.divider()

    # Show transaction details on select
    selected_txn = st.selectbox(
        "Select a transaction to view its lifecycle",
        options=df_transactions["transaction_id"].tolist()
    )
    
    if selected_txn:
        st.markdown(f"### Transaction Lifecycle: {selected_txn}")
        try:
            retries = get_retry_history_with_bank_details(selected_txn)
        except Exception as error:
            st.error(f"Unable to load retry history: {error}")
            retries = pd.DataFrame()
        
        txn_data = df_transactions[df_transactions["transaction_id"] == selected_txn].iloc[0]
        
        # --- Enriched Timeline Data (with recommended_action) ---
        timeline_data = []
        timeline_data.append({
            "event": "Initial Transaction",
            "timestamp": pd.to_datetime(txn_data["created_at"]),
            "status": txn_data.get("initial_status", "UNKNOWN"),
            "type": "transaction",
            "response_code": txn_data.get("payment_method", ""),
            "response_message": "Original payment attempt",
            "recommended_action": "",
        })

        if not retries.empty:
            df_retries = retries
            for _, retry in df_retries.iterrows():
                timeline_data.append({
                    "event": f"Retry Attempt {retry['attempt_number']}",
                    "timestamp": pd.to_datetime(retry["retry_timestamp"]),
                    "status": retry["retry_status"],
                    "type": "retry",
                    "response_code": retry.get("response_code", ""),
                    "response_message": retry.get("response_message", ""),
                    "recommended_action": retry.get("recommended_action", ""),
                })

        df_timeline = pd.DataFrame(timeline_data)
        df_timeline = df_timeline.sort_values("timestamp").reset_index(drop=True)
        
        # --- Visual Timeline with recommended_action in tooltip ---
        st.subheader("Timeline")
        color_map = {"SUCCESS": "#16a34a", "FAILED": "#dc2626"}
        df_timeline["color"] = df_timeline["status"].map(lambda x: color_map.get(x, "#6b7280"))
        
        fig = go.Figure()
        for idx, row in df_timeline.iterrows():
            event_text = row["event"]
            response_code = row.get("response_code") or ""
            response_message = row.get("response_message") or ""
            action = row.get("recommended_action") or ""
            tooltip = (
                f"<b>{event_text}</b><br>"
                f"Timestamp: {row['timestamp']}<br>"
                f"Status: {row['status']}<br>"
                f"Response Code: {response_code}<br>"
                f"Response Message: {response_message}<br>"
                f"Recommended Action: {action if action else 'N/A'}"
            )
            fig.add_trace(go.Scatter(
                x=[row["timestamp"]],
                y=[idx],
                mode="markers+text",
                marker=dict(size=15, color=row["color"]),
                text=[event_text],
                textposition="top center",
                name=event_text,
                hovertemplate=tooltip + "<extra></extra>",
            ))
        
        if len(df_timeline) > 1:
            for i in range(1, len(df_timeline)):
                fig.add_trace(go.Scatter(
                    x=[df_timeline["timestamp"].iloc[i-1], df_timeline["timestamp"].iloc[i]],
                    y=[i-1, i],
                    mode="lines",
                    line=dict(color="#94a3b8", dash="dash"),
                    showlegend=False
                ))
        
        fig.update_layout(
            height=200 + (len(df_timeline)*30),
            margin={"l": 20, "r": 20, "t": 30, "b": 20},
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            xaxis=dict(
                title="Timestamp",
                showgrid=True,
                zeroline=False
            ),
            showlegend=False
        )
        st.plotly_chart(fig, width='stretch')
        
        # --- Per-transaction retry details with response codes ---
        st.subheader("Details")
        if not retries.empty and not df_retries.empty:
            detail_cols = [
                c for c in [
                    "attempt_number",
                    "retry_timestamp",
                    "retry_status",
                    "response_code",
                    "response_message",
                    "recommended_action",
                    "recovery_potential",
                    "gateway_txn_ref",
                ] if c in df_retries.columns
            ]
            display_details = df_retries[detail_cols].copy()
            display_details.columns = [c.replace("_", " ").title() for c in detail_cols]
            st.dataframe(display_details, hide_index=True, width="stretch")

            with st.expander("Export This Transaction's Retry Details"):
                dtc1, dtc2 = st.columns(2)
                with dtc1:
                    csv_det = df_retries.to_csv(index=False)
                    st.download_button(
                        "📥 Retry Details (CSV)",
                        csv_det,
                        f"retry_details_{selected_txn}.csv",
                        "text/csv",
                        key=f"export_csv_{selected_txn}",
                    )
                with dtc2:
                    excel_det = BytesIO()
                    with pd.ExcelWriter(excel_det, engine="openpyxl") as writer:
                        df_retries.to_excel(writer, index=False, sheet_name="RetryHistory")
                    st.download_button(
                        "📥 Retry Details (Excel)",
                        excel_det.getvalue(),
                        f"retry_details_{selected_txn}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"export_xlsx_{selected_txn}",
                    )
        else:
            st.info("No retry attempts found for this transaction.")
else:
    st.info("No transactions found matching your filters.")

render_footer()

