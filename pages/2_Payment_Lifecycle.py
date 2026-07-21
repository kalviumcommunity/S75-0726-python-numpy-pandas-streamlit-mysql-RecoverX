import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import placeholder_transactions_overview

setup_page("Payment Lifecycle", "🔄")
render_header()
date_range = render_sidebar()

st.subheader("Track complete journey of payments")
st.divider()

# --- Charts ---
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.subheader("Transaction Status Over Time")
    fig = placeholder_transactions_overview()
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("Recent Payment Lifecycle (Sample)")
    sample_lifecycle = [
        {"Transaction ID": "TXN-XYZ789", "Customer": "Jane Smith", "Initial Status": "Failed", "Attempts": 2, "Final Status": "Success"},
        {"Transaction ID": "TXN-GHI789", "Customer": "Bob Johnson", "Initial Status": "Failed", "Attempts": 1, "Final Status": "Success"},
        {"Transaction ID": "TXN-JKL012", "Customer": "Alice Brown", "Initial Status": "Failed", "Attempts": 3, "Final Status": "Failed"},
    ]
    import pandas as pd
    df_sample = pd.DataFrame(sample_lifecycle)
    st.dataframe(df_sample, use_container_width=True)

render_footer()
