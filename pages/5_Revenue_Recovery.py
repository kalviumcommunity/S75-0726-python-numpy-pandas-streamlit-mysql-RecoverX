import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from io import BytesIO
import pandas as pd
import streamlit as st

from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.charts import (
    recovery_score_distribution_chart,
    revenue_impact_by_gateway_chart,
    revenue_impact_over_time_chart,
)
from src.payment_queries import (
    get_recovery_score_distribution,
    get_revenue_recovery_summary,
    get_revenue_impact_by_gateway,
    get_revenue_impact_over_time,
)

setup_page("Revenue Recovery", "💸")
render_header()
date_range = render_sidebar()
start_date = None
end_date = None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].isoformat() if date_range[0] else None
    end_date = date_range[1].isoformat() if date_range[1] else None

st.subheader("Identify and track recoverable revenue")
st.divider()

try:
    revenue_summary = get_revenue_recovery_summary(start_date=start_date, end_date=end_date)
    score_data = get_recovery_score_distribution(start_date=start_date, end_date=end_date)
    impact_by_gateway = get_revenue_impact_by_gateway(start_date=start_date, end_date=end_date)
    impact_over_time = get_revenue_impact_over_time(start_date=start_date, end_date=end_date)
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
    impact_by_gateway = pd.DataFrame()
    impact_over_time = pd.DataFrame()

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

st.divider()

st.subheader("Revenue Impact")

left, right = st.columns(2)

with left:
    fig = revenue_impact_over_time_chart(impact_over_time)
    st.plotly_chart(fig, width="stretch")

with right:
    fig = revenue_impact_by_gateway_chart(impact_by_gateway)
    st.plotly_chart(fig, width="stretch")

table_left, table_right = st.columns(2)

with table_left:
    if isinstance(impact_over_time, pd.DataFrame) and not impact_over_time.empty:
        st.dataframe(impact_over_time, hide_index=True, width="stretch", height=250)
    else:
        st.info("No revenue impact time series available.")

with table_right:
    if isinstance(impact_by_gateway, pd.DataFrame) and not impact_by_gateway.empty:
        st.dataframe(impact_by_gateway, hide_index=True, width="stretch", height=250)
    else:
        st.info("No revenue impact by gateway available.")

st.divider()

st.subheader("Export to Excel")

export_buffer = BytesIO()
with pd.ExcelWriter(export_buffer, engine="openpyxl") as writer:
    pd.DataFrame(
        [
            {"Metric": "Total Recoverable Revenue", "Value": revenue_summary.get("recoverable_revenue", 0)},
            {"Metric": "Permanently Lost Revenue", "Value": revenue_summary.get("permanently_lost_revenue", 0)},
        ]
    ).to_excel(writer, sheet_name="Summary", index=False)

    pd.DataFrame(distribution).to_excel(writer, sheet_name="Score Distribution", index=False)

    if isinstance(impact_by_gateway, pd.DataFrame):
        impact_by_gateway.to_excel(writer, sheet_name="Impact by Gateway", index=False)
    else:
        pd.DataFrame().to_excel(writer, sheet_name="Impact by Gateway", index=False)

    if isinstance(impact_over_time, pd.DataFrame):
        impact_over_time.to_excel(writer, sheet_name="Impact Over Time", index=False)
    else:
        pd.DataFrame().to_excel(writer, sheet_name="Impact Over Time", index=False)

st.download_button(
    "Download Revenue Impact Excel",
    export_buffer.getvalue(),
    "revenue_impact_report.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

render_footer()
