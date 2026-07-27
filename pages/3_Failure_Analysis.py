import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import placeholder_failure_distribution, placeholder_response_code_distribution
from src.payment_queries import get_filtered_failed_transactions

setup_page("Failure Analysis", "❌")
render_header()
date_range = render_sidebar()

st.subheader("Analyze payment failure patterns")
st.divider()

with st.expander("🔍 Filter failed transactions", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        failure_type_filter = st.selectbox("Failure Type", options=["All", "TEMPORARY", "PERMANENT"], index=0)
        response_code_filter = st.text_input("Bank Response Code", placeholder="e.g. 05")
        gateway_filter = st.text_input("Gateway", placeholder="Enter gateway...")
    with col2:
        payment_method_filter = st.text_input("Payment Method", placeholder="Enter payment method...")
        start_date_filter = st.date_input("Start Date", value=None)
        end_date_filter = st.date_input("End Date", value=None)

try:
    failed_transactions = get_filtered_failed_transactions(
        failure_type=failure_type_filter if failure_type_filter != "All" else None,
        response_code=response_code_filter.strip() or None,
        gateway=gateway_filter.strip() or None,
        payment_method=payment_method_filter.strip() or None,
        start_date=pd.Timestamp(start_date_filter).strftime("%Y-%m-%d 00:00:00") if start_date_filter else None,
        end_date=pd.Timestamp(end_date_filter).strftime("%Y-%m-%d 23:59:59") if end_date_filter else None,
    )
except Exception as error:
    st.error(f"Unable to load failed transactions from the database: {error}")
    failed_transactions = pd.DataFrame()

if not failed_transactions.empty:
    st.subheader("Failed Transactions")
    st.dataframe(failed_transactions, use_container_width=True, hide_index=True)
else:
    st.info("No failed transactions found matching the selected filters.")

st.divider()

# --- Charts ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Failure Cause Distribution")
    fig1 = placeholder_failure_distribution()
    st.plotly_chart(fig1, width='stretch')

with chart_col2:
    st.subheader("Bank Response Code Distribution")
    fig2 = placeholder_response_code_distribution()
    st.plotly_chart(fig2, width='stretch')

render_footer()
