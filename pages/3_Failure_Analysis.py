import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import (
    placeholder_failure_distribution,
    failure_type_distribution_chart,
    failure_breakdown_by_response_code_chart,
    failure_breakdown_by_gateway_chart,
    failure_breakdown_by_payment_method_chart,
)
from src.payment_queries import (
    get_failure_type_distribution,
    get_failure_breakdown_by_response_code,
    get_failure_breakdown_by_gateway,
    get_failure_breakdown_by_payment_method,
)

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

# --- Breakdown by Bank Response Code ---
st.subheader("Failure Breakdown by Bank Response Code")
response_code_data = get_failure_breakdown_by_response_code()
fig_response_code = failure_breakdown_by_response_code_chart(response_code_data)
st.plotly_chart(fig_response_code, width='stretch')

st.divider()

# --- Breakdown by Gateway and Payment Method ---
bd_col1, bd_col2 = st.columns(2)

with bd_col1:
    st.subheader("By Gateway")
    gateway_data = get_failure_breakdown_by_gateway()
    fig_gateway = failure_breakdown_by_gateway_chart(gateway_data)
    st.plotly_chart(fig_gateway, width='stretch')

with bd_col2:
    st.subheader("By Payment Method")
    pm_data = get_failure_breakdown_by_payment_method()
    fig_pm = failure_breakdown_by_payment_method_chart(pm_data)
    st.plotly_chart(fig_pm, width='stretch')

st.divider()

# --- Extra: Failure Cause Distribution (kept for reference) ---
st.subheader("Failure Cause Distribution")
fig1 = placeholder_failure_distribution()
st.plotly_chart(fig1, width='stretch')

render_footer()
