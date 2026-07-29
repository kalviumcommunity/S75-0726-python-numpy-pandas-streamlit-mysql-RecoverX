import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import recovery_score_distribution_chart
from src.payment_queries import (
    get_recovery_score_distribution,
    get_revenue_recovery_summary,
)

setup_page("Revenue Recovery", "💸")
render_header()
date_range = render_sidebar()

st.subheader("Identify and track recoverable revenue")
st.divider()

try:
    revenue_summary = get_revenue_recovery_summary()
    score_data = get_recovery_score_distribution()
except Exception as error:
    st.error(f"Unable to load revenue recovery data from the database: {error}")
    revenue_summary = {
        "recoverable_revenue": 0.0,
        "permanently_lost_revenue": 0.0,
    }
    score_data = {
        "distribution": [],
        "stats": {},
        "percentiles": {},
        "total_scores": 0,
    }

col1, col2 = st.columns(2)
with col1:
    st.metric(
        "Total Recoverable Revenue",
        f"${revenue_summary['recoverable_revenue']:,.2f}",
    )
with col2:
    st.metric(
        "Permanently Lost Revenue",
        f"${revenue_summary['permanently_lost_revenue']:,.2f}",
    )

st.divider()

st.subheader("Recovery Score Distribution")

distribution = score_data.get("distribution", [])
stats = score_data.get("stats", {})
percentiles = score_data.get("percentiles", {})

if distribution:
    left, right = st.columns([2, 1])

    with left:
        fig = recovery_score_distribution_chart(distribution)
        st.plotly_chart(fig, width="stretch")

    with right:
        c1, c2 = st.columns(2)
        c1.metric("Transactions Scored", f"{score_data.get('total_scores', 0):,}")
        c2.metric("Average Score", f"{stats.get('mean', 0) * 100:.1f}%")

        summary_df = pd.DataFrame(
            [
                {"Metric": "Median Score", "Value": f"{stats.get('median', 0) * 100:.1f}%"},
                {"Metric": "25th Percentile", "Value": f"{percentiles.get('p25', 0) * 100:.1f}%"},
                {"Metric": "75th Percentile", "Value": f"{percentiles.get('p75', 0) * 100:.1f}%"},
                {"Metric": "90th Percentile", "Value": f"{percentiles.get('p90', 0) * 100:.1f}%"},
            ]
        )
        st.dataframe(summary_df, hide_index=True, width="stretch")
else:
    st.info("No recovery score data available.")

render_footer()
