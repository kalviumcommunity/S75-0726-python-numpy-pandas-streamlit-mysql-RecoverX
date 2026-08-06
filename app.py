
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.payment_queries import (
    get_dashboard_key_metrics,
    get_active_alerts,
    get_revenue_recovery_summary,
)
import pandas as pd


get_dashboard_key_metrics = st.cache_data(show_spinner=False, ttl=300)(get_dashboard_key_metrics)
get_revenue_recovery_summary = st.cache_data(show_spinner=False, ttl=300)(get_revenue_recovery_summary)
get_active_alerts = st.cache_data(show_spinner=False, ttl=300)(get_active_alerts)


setup_page("Welcome", "💰")
render_header()
date_range = render_sidebar()

st.markdown(
    """
    <div style="text-align: center; padding: 2rem 1rem;">
        <h1 style="font-size: 2.5rem; margin: 0; color: #2563eb;">💰 RecoverX</h1>
        <h3 style="color: #64748b; margin: 0.5rem 0 2rem 0;">Payment Recovery Analytics &amp; Retry Intelligence</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    """
    **RecoverX** helps engineering, finance, and operations teams recover failed payment revenue
    through data-driven retry decisions. Use the sidebar to navigate between modules —
    start with the **Dashboard** for an overview, then drill into Lifecycle, Failure Analysis,
    Retry Analytics, Revenue Recovery, Alerts, or CSV Import.
    """
)

st.divider()

start_date_value = (
    pd.Timestamp(date_range[0]).strftime("%Y-%m-%d 00:00:00")
    if isinstance(date_range, tuple) and len(date_range) == 2 and date_range[0]
    else None
)
end_date_value = (
    pd.Timestamp(date_range[1]).strftime("%Y-%m-%d 23:59:59")
    if isinstance(date_range, tuple) and len(date_range) == 2 and date_range[1]
    else None
)

try:
    metrics = get_dashboard_key_metrics()
except Exception:
    metrics = {}

try:
    summary = get_revenue_recovery_summary(
        start_date=start_date_value,
        end_date=end_date_value,
    ) or {}
except Exception:
    summary = {}

try:
    active = get_active_alerts() or []
except Exception:
    active = []

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Total Transactions",
    f"{int(metrics.get('total_transactions', 0)):,}",
)
col2.metric(
    "Success Rate",
    f"{float(metrics.get('success_rate', 0.0)):.1f}%",
)
col3.metric(
    "Revenue Recovered",
    f"${float(metrics.get('revenue_recovered', 0.0)):,.2f}",
)
col4.metric(
    "Active Alerts",
    f"{len(active):,}",
)

st.divider()

st.subheader("🧭 Quick Navigation")
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    st.markdown(
        """
        **📊 Dashboard**
        - KPIs & overview charts
        - Recent alerts & top failures
        """
    )
with nav_col2:
    st.markdown(
        """
        **🔄 Payment Lifecycle**
        - Track individual txn journeys
        - Retry timeline & bank codes
        """
    )
with nav_col3:
    st.markdown(
        """
        **❌ Failure Analysis**
        - TEMPORARY vs PERMANENT split
        - Recovery potential distribution
        """
    )
with nav_col4:
    st.markdown(
        """
        **🔁 Retry Analytics**
        - Best attempt & time windows
        - Ineffective pattern detection
        """
    )

nav_col5, nav_col6, nav_col7 = st.columns(3)
with nav_col5:
    st.markdown(
        """
        **💰 Revenue Recovery**
        - Recoverable vs permanently lost
        - Prioritized high-value retry list
        """
    )
with nav_col6:
    st.markdown(
        """
        **🚨 Alerts & Notifications**
        - Rule-based alert management
        - Email test & dispatch
        """
    )
with nav_col7:
    st.markdown(
        """
        **📥 CSV Import**
        - Seed transactions & retries
        - Bank response code library
        """
    )

st.divider()

insight_lines = []
recoverable = float(summary.get("recoverable_revenue", 0) or 0)
permanently_lost = float(summary.get("permanently_lost_revenue", 0) or 0)
total_at_risk = recoverable + permanently_lost
if total_at_risk > 0:
    insight_lines.append(
        f"You have **${total_at_risk:,.2f}** at-risk revenue in the selected window — "
        f"**${recoverable:,.2f}** is still recoverable through smart retries."
    )
if len(active) > 0:
    crit = sum(1 for a in active if str(a.get("severity", "")).upper() == "CRITICAL")
    high = sum(1 for a in active if str(a.get("severity", "")).upper() == "HIGH")
    if crit or high:
        insight_lines.append(
            f"There are **{crit} CRITICAL** and **{high} HIGH** severity active alerts — "
            f"visit the Alerts page to resolve them."
        )
if insight_lines:
    st.subheader("💡 Live Insights")
    for line in insight_lines:
        st.markdown(f"- {line}")

st.divider()
render_footer()
