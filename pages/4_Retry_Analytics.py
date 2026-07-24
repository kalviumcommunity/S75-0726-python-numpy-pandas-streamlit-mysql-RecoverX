import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import placeholder_retry_attempts

setup_page("Retry Analytics", "🔁")
render_header()
date_range = render_sidebar()

st.subheader("Analyze retry performance")
st.divider()

# --- Metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Attempts per Failure", "1.8", "+0.2")
with col2:
    st.metric("Retry Success Rate", "78%", "+3.5%")
with col3:
    st.metric("Total Retries", "3,456", "-5.2%")

st.divider()

# --- Chart ---
st.subheader("Retry Attempts Distribution")
fig = placeholder_retry_attempts()
st.plotly_chart(fig, width='stretch')

render_footer()
