import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import placeholder_failure_distribution, placeholder_response_code_distribution

setup_page("Failure Analysis", "❌")
render_header()
date_range = render_sidebar()

st.subheader("Analyze payment failure patterns")
st.divider()

# --- Charts ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Failure Cause Distribution")
    fig1 = placeholder_failure_distribution()
    st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    st.subheader("Bank Response Code Distribution")
    fig2 = placeholder_response_code_distribution()
    st.plotly_chart(fig2, use_container_width=True)

render_footer()
