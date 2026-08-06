import sys
from io import BytesIO, StringIO
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
frontend_changes
import streamlit as st

from src.charts import (
    payment_method_amounts_chart,
    transaction_status_over_time_chart,
)
from src.payment_queries import (
    get_active_alerts,
    get_dashboard_key_metrics,
    get_failure_breakdown_by_response_code,
    get_filtered_transactions,
    get_payment_method_amounts,
    get_transaction_status_over_time,
)
from src.ui_components import render_footer, render_header, render_sidebar, setup_page


@st.cache_data(show_spinner=False, ttl=300)
def cached_get_dashboard_key_metrics():
    return get_dashboard_key_metrics()


@st.cache_data(show_spinner=False, ttl=300)
def cached_get_transaction_status_over_time():
    return get_transaction_status_over_time() or []


@st.cache_data(show_spinner=False, ttl=300)
def cached_get_payment_method_amounts(start_date=None, end_date=None):
    return get_payment_method_amounts(start_date=start_date, end_date=end_date)


@st.cache_data(show_spinner=False, ttl=300)
def cached_get_active_alerts():
    return get_active_alerts() or []


@st.cache_data(show_spinner=False, ttl=300)
def cached_get_failure_breakdown_by_response_code():
    return get_failure_breakdown_by_response_code() or []


@st.cache_data(show_spinner=False, ttl=300)
def cached_get_filtered_transactions(start_date=None, end_date=None, limit=10):
    return get_filtered_transactions(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


def _highlight_status(val):
    if isinstance(val, str) and "success" in val.lower():
        return "color: #16a34a; font-weight: bold"
    if isinstance(val, str) and "fail" in val.lower():
        return "color: #dc2626; font-weight: bold"
    return "color: #ca8a04; font-weight: bold"


import plotly.express as px
import io
from src.ui_components import setup_page, render_header, render_sidebar, render_footer
 
from src.payment_queries import get_dashboard_key_metrics
 main

from src.payment_queries import (
    get_total_transactions,
    get_successful_transactions,
    get_failed_transactions,
    get_alerts,
    get_failure_causes_distribution,
)


def render_recent_alerts(limit: int = 5):
    """Render the most recent alerts in a compact table."""
    st.subheader("Recent Alerts")
    alerts = get_alerts(limit=limit) or []

    if not alerts:
        st.info("No alerts yet.")
        return

    alert_rows = []
    for alert in alerts:
        created_at = alert.get("created_at")
        if hasattr(created_at, "strftime"):
            timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp = str(created_at or "N/A")

        alert_rows.append(
            {
                "Alert Type": alert.get("alert_type") or "Unknown",
                "Status": "Resolved" if alert.get("is_resolved") else "Unresolved",
                "Timestamp": timestamp,
            }
        )

    df_alerts = pd.DataFrame(alert_rows)
    st.dataframe(df_alerts, use_container_width=True, hide_index=True)


def render_top_failures(limit: int = 5):
    """Render the most common failure reasons using the shared failure-cause query."""
    st.subheader("Top Failures")
    failure_causes = get_failure_causes_distribution() or []

    if not failure_causes:
        st.info("No failures recorded.")
        return

    failure_counts = pd.DataFrame(failure_causes)
    if "cause" in failure_counts.columns and "count" in failure_counts.columns:
        failure_counts = failure_counts.rename(columns={"cause": "Failure Reason", "count": "Count"})
    else:
        failure_counts = failure_counts.rename(columns={col: col for col in failure_counts.columns})

    failure_counts = (
        failure_counts.sort_values(by=["Count", "Failure Reason"], ascending=[False, True])
        .head(limit)
        .reset_index(drop=True)
    )

    if failure_counts.empty:
        st.info("No failures recorded.")
        return

    st.dataframe(failure_counts, use_container_width=True, hide_index=True)



setup_page("Dashboard", "📊")
render_header()
date_range = render_sidebar()

st.subheader("Key Metrics")

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
    metrics = cached_get_dashboard_key_metrics()
except Exception as error:
    st.error(f"Unable to load dashboard metrics from the database: {error}")
    metrics = {
        "total_transactions": 0,
        "success_rate": 0.0,
        "revenue_recovered": 0.0,
        "retry_attempts": 0,
    }

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Transactions", f"{int(metrics.get('total_transactions', 0)):,}")
with col2:
    st.metric("Success Rate", f"{float(metrics.get('success_rate', 0.0)):.1f}%")
with col3:
    st.metric(
        "Revenue Recovered",
        f"${float(metrics.get('revenue_recovered', 0.0)):,.2f}",
    )
with col4:
    st.metric("Retry Attempts", f"{int(metrics.get('retry_attempts', 0)):,}")

st.markdown("---")

# =========================================================
# Charts Section (Real DB data)
# =========================================================

chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("Transactions Overview")
    try:
        status_over_time = cached_get_transaction_status_over_time()
    except Exception as error:
        st.error(f"Unable to load transactions over time: {error}")
        status_over_time = []
    fig_overview = transaction_status_over_time_chart(status_over_time)
    st.plotly_chart(fig_overview, width="stretch")

with chart_col2:
    st.subheader("Payment Methods")
 frontend_changes
    try:
        payment_method_data = cached_get_payment_method_amounts(
            start_date=start_date_value,
            end_date=end_date_value,
        )
    except Exception as error:
        st.error(f"Unable to load payment method amounts: {error}")
        payment_method_data = pd.DataFrame([])

    if payment_method_data.empty:
        payment_method_records = []
    else:
        payment_method_records = payment_method_data.to_dict("records")
    fig_pm = payment_method_amounts_chart(payment_method_records)
    st.plotly_chart(fig_pm, width="stretch")


    payment_methods = ["Credit Card", "Debit Card", "Net Banking", "UPI"]
    amounts = [45000, 30000, 25000, 15000]
    df_bar = pd.DataFrame({"Payment Method": payment_methods, "Amount ($)": amounts})
    fig = px.bar(df_bar, x="Payment Method", y="Amount ($)", color="Payment Method", 
                 color_discrete_sequence=["#2563eb", "#38bdf8", "#0ea5e9", "#0369a1"])
    fig.update_layout(height=300, margin={"l": 0, "r": 0, "t": 30, "b": 0}, showlegend=False)
    st.plotly_chart(fig, width='stretch')

# --- Alerts & Failures Snapshot ---
st.markdown("---")
alert_col, failure_col = st.columns(2)
with alert_col:
    render_recent_alerts(limit=5)
with failure_col:
    render_top_failures(limit=5)

# --- Recent Transactions Table ---
 main
st.markdown("---")

# =========================================================
# Recent Alerts (Day 8 Yogesh)
# =========================================================

st.subheader("Recent Alerts")
alert_col1, alert_col2 = st.columns([1, 1])

with alert_col1:
    st.markdown("**Top 5 Unresolved Alerts**")
    try:
        all_active = cached_get_active_alerts()
    except Exception as error:
        st.error(f"Unable to load active alerts: {error}")
        all_active = []

    if not all_active:
        st.info("No active alerts. Go to the Alerts page and click 'Generate Alerts Now'.")
    else:
        recent_alerts_df = pd.DataFrame(all_active).head(5)
        cols_keep = [
            c for c in ["severity", "alert_title", "alert_message", "created_at"]
            if c in recent_alerts_df.columns
        ]
        recent_display = recent_alerts_df[cols_keep].copy()
        recent_display.columns = [c.replace("_", " ").title() for c in cols_keep]
        st.dataframe(recent_display, hide_index=True, width="stretch")

# =========================================================
# Top Failures (Day 8 Yogesh)
# =========================================================

with alert_col2:
    st.markdown("**Top 3 Response Code Failures**")
    try:
        failure_breakdown = cached_get_failure_breakdown_by_response_code()
    except Exception as error:
        st.error(f"Unable to load failure breakdown: {error}")
        failure_breakdown = []

    if not failure_breakdown:
        st.info("No bank response code failures to display yet.")
    else:
        fb_df = pd.DataFrame(failure_breakdown).head(3)
        cols_show = [c for c in ["response_code", "description", "total", "recovery_potential"] if c in fb_df.columns]
        fb_display = fb_df[cols_show].copy()
        fb_display.columns = [c.replace("_", " ").title() for c in cols_show]
        st.dataframe(fb_display, hide_index=True, width="stretch")

st.markdown("---")

# =========================================================
# Recent Transactions Table (Real DB)
# =========================================================

st.subheader("Recent Transactions")

try:
    recent_transactions = cached_get_filtered_transactions(
        start_date=start_date_value,
        end_date=end_date_value,
        limit=10,
    )
except Exception as error:
    st.error(f"Unable to load recent transactions: {error}")
    recent_transactions = pd.DataFrame([])

if recent_transactions.empty:
    st.info("No transactions loaded yet — import CSV files or run the FastAPI bulk endpoints to seed data.")
    df_recent = pd.DataFrame([])
else:
    desired_cols = [
        "transaction_id",
        "customer_id",
        "amount",
        "currency",
        "payment_method",
        "gateway",
        "final_status",
        "created_at",
    ]
    existing_cols = [c for c in desired_cols if c in recent_transactions.columns]
    df_recent = recent_transactions[existing_cols].copy()
    df_recent.columns = [c.replace("_", " ").title() for c in existing_cols]
    status_col = "Final Status"
    if status_col in df_recent.columns:
        st.dataframe(
            df_recent.style.map(_highlight_status, subset=[status_col]),
            hide_index=True,
            width="stretch",
        )
    else:
        st.dataframe(df_recent, hide_index=True, width="stretch")

st.markdown("---")

# =========================================================
# Export Section
# =========================================================

st.subheader("Export Dashboard Data")
exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    if not recent_transactions.empty and not df_recent.empty:
        csv_buffer = StringIO()
        df_recent.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Recent Transactions (CSV)",
            data=csv_buffer.getvalue(),
            file_name="recent_transactions.csv",
            mime="text/csv",
        )
    else:
        st.button("📥 Recent Transactions (CSV)", disabled=True, help="No transaction data available.")

with exp_col2:
    if not recent_transactions.empty and not df_recent.empty:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_recent.to_excel(writer, index=False, sheet_name="Recent Transactions")
            kpi_sheet = pd.DataFrame(
                [
                    {"Metric": "Total Transactions", "Value": int(metrics.get("total_transactions", 0))},
                    {"Metric": "Success Rate (%)", "Value": float(metrics.get("success_rate", 0.0))},
                    {
                        "Metric": "Revenue Recovered ($)",
                        "Value": float(metrics.get("revenue_recovered", 0.0)),
                    },
                    {"Metric": "Retry Attempts", "Value": int(metrics.get("retry_attempts", 0))},
                ]
            )
            kpi_sheet.to_excel(writer, index=False, sheet_name="KPIs")
            if status_over_time:
                pd.DataFrame(status_over_time).to_excel(
                    writer, index=False, sheet_name="Transactions_Over_Time"
                )
            if not payment_method_data.empty:
                payment_method_data.to_excel(
                    writer, index=False, sheet_name="Payment_Methods"
                )
        st.download_button(
            label="📥 Full Dashboard Report (Excel)",
            data=excel_buffer.getvalue(),
            file_name="dashboard_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.button("📥 Full Dashboard Report (Excel)", disabled=True, help="No data available for export.")

render_footer()
