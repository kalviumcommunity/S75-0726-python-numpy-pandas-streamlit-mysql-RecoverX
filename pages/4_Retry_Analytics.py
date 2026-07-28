import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import placeholder_retry_attempts, retry_success_rate_per_attempt_chart
from src.payment_queries import get_retry_success_rate_per_attempt

setup_page("Retry Analytics", "🔁")
render_header()
date_range = render_sidebar()

st.subheader("Analyze retry performance")
st.divider()

# --- Metrics ---
st.subheader("Retry Success Rates per Attempt")
success_data = get_retry_success_rate_per_attempt()

if success_data:
    total_attempts_all = sum(int(d.get("total_attempts", 0) or 0) for d in success_data)
    total_successful = sum(int(d.get("successful", 0) or 0) for d in success_data)
    overall_rate = round((total_successful / total_attempts_all) * 100, 1) if total_attempts_all else 0.0
    best_idx = max(
        range(len(success_data)),
        key=lambda i: float(success_data[i].get("success_rate", 0) or 0),
    )
    best_attempt = success_data[best_idx]

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("Total Retry Attempts", f"{total_attempts_all:,}")
    mcol2.metric("Total Successful Retries", f"{total_successful:,}")
    mcol3.metric("Overall Retry Success Rate", f"{overall_rate}%")
    mcol4.metric(
        "Best Attempt",
        f"Attempt {int(best_attempt['attempt_number'])}",
        f"{float(best_attempt['success_rate'])}%",
        delta_color="normal",
    )
    st.markdown("---")

    chart_col, table_col = st.columns([2, 1])

    with chart_col:
        fig_rate = retry_success_rate_per_attempt_chart(success_data)
        st.plotly_chart(fig_rate, width='stretch')

    with table_col:
        st.markdown("#### Breakdown by Attempt")
        tbl_rows = []
        for d in success_data:
            an = int(d.get("attempt_number", 0))
            tot = int(d.get("total_attempts", 0) or 0)
            ok = int(d.get("successful", 0) or 0)
            bad = int(d.get("failed", 0) or 0)
            rate = float(d.get("success_rate", 0) or 0)
            tbl_rows.append({
                "Attempt": f"#{an}",
                "Total": tot,
                "Success": ok,
                "Failed": bad,
                "Success %": f"{rate}%",
            })
        df_tbl = pd.DataFrame(tbl_rows)
        st.dataframe(df_tbl, hide_index=True, width='stretch')
else:
    st.info("No retry data available yet.")

st.divider()

# --- Chart ---
st.subheader("Retry Attempts Distribution")
fig = placeholder_retry_attempts()
st.plotly_chart(fig, width='stretch')

render_footer()
