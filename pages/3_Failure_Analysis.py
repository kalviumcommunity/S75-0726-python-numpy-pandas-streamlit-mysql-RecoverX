import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import (
    placeholder_failure_distribution,
    placeholder_response_code_distribution,
    failure_type_distribution_chart,
)
from src.payment_queries import get_failure_type_distribution

setup_page("Failure Analysis", "❌")
render_header()
date_range = render_sidebar()

st.subheader("Analyze payment failure patterns")
st.divider()

# --- Failure Type Distribution (TEMPORARY vs PERMANENT) ---
st.subheader("Failure Distribution by Type (TEMPORARY vs PERMANENT)")
type_col1, type_col2 = st.columns([2, 1])

with type_col1:
    distribution = get_failure_type_distribution()
    fig_type = failure_type_distribution_chart(distribution)
    st.plotly_chart(fig_type, width='stretch')

with type_col2:
    st.markdown("#### Summary")
    if distribution:
        temp_count = 0
        perm_count = 0
        for row in distribution:
            ftype = str(row.get("failure_type", "")).upper()
            cnt = int(row.get("count", 0) or 0)
            if ftype == "TEMPORARY":
                temp_count += cnt
            elif ftype == "PERMANENT":
                perm_count += cnt
        total = temp_count + perm_count
        pct_temp = round(temp_count / total * 100, 1) if total else 0
        pct_perm = round(perm_count / total * 100, 1) if total else 0
    else:
        temp_count, perm_count, total = 0, 0, 0
        pct_temp, pct_perm = 0.0, 0.0

    m1, m2 = st.columns(2)
    m1.metric(
        "TEMPORARY",
        f"{temp_count:,}",
        f"{pct_temp}%",
        delta_color="normal" if pct_temp > pct_perm else "inverse",
    )
    m2.metric(
        "PERMANENT",
        f"{perm_count:,}",
        f"{pct_perm}%",
        delta_color="inverse",
    )
    st.markdown("---")
    summary_df = pd.DataFrame({
        "Failure Type": ["TEMPORARY", "PERMANENT"],
        "Count": [temp_count, perm_count],
        "Percentage": [f"{pct_temp}%", f"{pct_perm}%"],
        "Recovery Potential": [
            "Retry possible (recoverable)",
            "Requires user action (hard to recover)",
        ],
    })
    st.dataframe(summary_df, hide_index=True, width='stretch')

st.divider()

# --- Other Charts ---
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
