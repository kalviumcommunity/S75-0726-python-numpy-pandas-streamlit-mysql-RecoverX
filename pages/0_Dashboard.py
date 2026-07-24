import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import io
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.payment_queries import get_total_transactions, get_successful_transactions, get_failed_transactions

setup_page("Dashboard", "📊")
render_header()
date_range = render_sidebar()

# --- Metrics Cards ---
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Transactions", "12,345", "+8.0%", delta_color="normal")
with col2:
    st.metric("Success Rate", "85.3%", "+2.5%", delta_color="normal")
with col3:
    st.metric("Revenue Recovered", "$45,678", "+12.3%", delta_color="normal")
with col4:
    st.metric("Retry Attempts", "3,456", "-3.2%", delta_color="inverse")
st.markdown("---")

# --- Charts Section ---
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("Transactions Overview")
    # Sample transaction data
    date_ranges = ["Jun 21", "Jun 28", "Jul 5", "Jul 12", "Jul 19"]
    tx_counts = [2100, 2300, 2250, 2400, 2500]
    df_line = pd.DataFrame({"Date": date_ranges, "Transactions": tx_counts})
    fig = px.line(df_line, x="Date", y="Transactions", markers=True, color_discrete_sequence=["#2563eb"])
    fig.update_layout(height=300, margin={"l": 0, "r": 0, "t": 30, "b": 0})
    st.plotly_chart(fig, width='stretch')

with chart_col2:
    st.subheader("Payment Methods")
    payment_methods = ["Credit Card", "Debit Card", "Net Banking", "UPI"]
    amounts = [45000, 30000, 25000, 15000]
    df_bar = pd.DataFrame({"Payment Method": payment_methods, "Amount ($)": amounts})
    fig = px.bar(df_bar, x="Payment Method", y="Amount ($)", color="Payment Method", 
                 color_discrete_sequence=["#2563eb", "#38bdf8", "#0ea5e9", "#0369a1"])
    fig.update_layout(height=300, margin={"l": 0, "r": 0, "t": 30, "b": 0}, showlegend=False)
    st.plotly_chart(fig, width='stretch')

# --- Recent Transactions Table ---
st.markdown("---")
st.subheader("Recent Transactions")
# Sample transactions data
recent_transactions = [
    {"Customer": "John Doe", "Transaction ID": "TXN-ABC123", "Amount": "$99.99", "Status": "Success", "Retries": 0},
    {"Customer": "Jane Smith", "Transaction ID": "TXN-DEF456", "Amount": "$199.50", "Status": "Failed", "Retries": 2},
    {"Customer": "Bob Johnson", "Transaction ID": "TXN-GHI789", "Amount": "$59.00", "Status": "Success", "Retries": 1},
    {"Customer": "Alice Brown", "Transaction ID": "TXN-JKL012", "Amount": "$299.00", "Status": "Pending", "Retries": 3},
    {"Customer": "Charlie Wilson", "Transaction ID": "TXN-MNO345", "Amount": "$149.99", "Status": "Success", "Retries": 0},
]
df_recent = pd.DataFrame(recent_transactions)
# Style status column
def highlight_status(val):
    if val == "Success":
        return "color: #16a34a; font-weight: bold"
    elif val == "Failed":
        return "color: #dc2626; font-weight: bold"
    else:
        return "color: #ca8a04; font-weight: bold"
st.dataframe(df_recent.style.map(highlight_status, subset=["Status"]), width='stretch')

# --- Export Section ---
st.markdown("---")
st.subheader("Export Transactions")
col1, col2 = st.columns(2)
with col1:
    csv_buffer = io.StringIO()
    df_recent.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Export as CSV",
        data=csv_buffer.getvalue(),
        file_name="recent_transactions.csv",
        mime="text/csv"
    )

with col2:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_recent.to_excel(writer, index=False, sheet_name="Recent Transactions")
    st.download_button(
        label="📥 Export as Excel",
        data=excel_buffer.getvalue(),
        file_name="recent_transactions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

render_footer()
