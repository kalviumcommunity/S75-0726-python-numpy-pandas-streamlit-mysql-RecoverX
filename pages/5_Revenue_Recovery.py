import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from src.ui_components import (
    setup_page,
    render_header,
    render_sidebar,
    render_footer,
)

from src.payment_queries import (
    get_active_alerts,
)

from src.charts import (
    alert_severity_chart,
)

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------

setup_page("Alerts & Notifications", "🚨")

render_header()

date_range = render_sidebar()

st.subheader("Alerts & Notifications")

st.info(
    """
Monitor payment failures, retry issues and gateway problems in real time.
"""
)

refresh = st.button("🔄 Refresh Alerts")

if refresh:
    st.rerun()

st.divider()

# ---------------------------------------------------------
# Load Alerts
# ---------------------------------------------------------

alerts = get_active_alerts()

df = pd.DataFrame(alerts)

if df.empty:

    st.warning("No active alerts found.")

    render_footer()

    st.stop()

# ---------------------------------------------------------
# KPI Metrics
# ---------------------------------------------------------

total_alerts = len(df)

critical = len(df[df["severity"] == "CRITICAL"])

high = len(df[df["severity"] == "HIGH"])

medium = len(df[df["severity"] == "MEDIUM"])

low = len(df[df["severity"] == "LOW"])

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Total Alerts",
    total_alerts,
)

c2.metric(
    "Critical",
    critical,
)

c3.metric(
    "High",
    high,
)

c4.metric(
    "Medium",
    medium,
)

c5.metric(
    "Low",
    low,
)

st.divider()

# ---------------------------------------------------------
# Severity Filter
# ---------------------------------------------------------

severity = st.selectbox(
    "Filter by Severity",
    [
        "ALL",
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ],
)

if severity != "ALL":
    df = df[df["severity"] == severity]

# ---------------------------------------------------------
# Alert Severity Chart
# ---------------------------------------------------------

st.subheader("Alert Severity Distribution")

severity_counts = (
    df.groupby("severity")
      .size()
      .reset_index(name="count")
      .to_dict("records")
)

fig = alert_severity_chart(severity_counts)

st.plotly_chart(
    fig,
    width="stretch",
)

st.divider()

# ---------------------------------------------------------
# Active Alerts
# ---------------------------------------------------------

st.subheader("Active Alerts")

severity_colors = {
    "LOW": "🟢",
    "MEDIUM": "🟡",
    "HIGH": "🟠",
    "CRITICAL": "🔴",
}

for _, row in df.iterrows():

    icon = severity_colors.get(row["severity"], "⚪")

    with st.container(border=True):

        st.markdown(
            f"### {icon} {row['severity']} - {row['alert_title']}"
        )

        st.write(row["alert_message"])

        col1, col2 = st.columns(2)

        with col1:
            st.caption(f"Status: {row['status']}")

        with col2:
            st.caption(f"Created: {row['created_at']}")

# ---------------------------------------------------------
# Alerts Table
# ---------------------------------------------------------

st.divider()

st.subheader("Alerts Table")

st.dataframe(
    df,
    hide_index=True,
    width="stretch",
)

# ---------------------------------------------------------
# Export CSV
# ---------------------------------------------------------

csv = df.to_csv(index=False)

st.download_button(
    "📥 Download Alerts CSV",
    csv,
    "alerts.csv",
    "text/csv",
)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

render_footer()
