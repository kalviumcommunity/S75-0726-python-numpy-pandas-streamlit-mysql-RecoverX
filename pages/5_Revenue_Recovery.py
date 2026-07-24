import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import placeholder_revenue_recovery

setup_page("Revenue Recovery", "💸")
render_header()
date_range = render_sidebar()

st.subheader("Identify and track recoverable revenue")
st.divider()

# --- Metrics ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Recoverable Revenue", "$45,000", "+12%")
with col2:
    st.metric("Recovered This Month", "$20,000", "+15%")
with col3:
    st.metric("Average Recovery Time", "48h", "-5h")
with col4:
    st.metric("High-Value Failed Transactions", "12", "-2")

st.divider()

# --- Chart ---
st.subheader("Revenue Recovery Trend")
fig = placeholder_revenue_recovery()
st.plotly_chart(fig, width='stretch')

render_footer()
