import sys
from io import BytesIO
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from src.charts import (
    recovery_score_distribution_chart,
    revenue_impact_by_gateway_chart,
    revenue_impact_over_time_chart,
)
from src.numpy_utils import compute_distribution_stats
from src.payment_queries import (
    get_high_value_failed_transactions,
    get_prioritized_transactions_to_retry,
    get_recovery_score_distribution,
    get_revenue_impact_by_gateway,
    get_revenue_impact_over_time,
    get_revenue_recovery_summary,
)
from src.ui_components import render_footer, render_header, render_sidebar, setup_page


get_revenue_recovery_summary = st.cache_data(show_spinner=False, ttl=300)(get_revenue_recovery_summary)
get_revenue_impact_over_time = st.cache_data(show_spinner=False, ttl=300)(get_revenue_impact_over_time)
get_recovery_score_distribution = st.cache_data(show_spinner=False, ttl=300)(get_recovery_score_distribution)
get_revenue_impact_by_gateway = st.cache_data(show_spinner=False, ttl=300)(get_revenue_impact_by_gateway)
get_high_value_failed_transactions = st.cache_data(show_spinner=False, ttl=300)(get_high_value_failed_transactions)
get_prioritized_transactions_to_retry = st.cache_data(show_spinner=False, ttl=300)(get_prioritized_transactions_to_retry)


def _fmt_money(value):
    try:
        return f"${float(value or 0):,.2f}"
    except Exception:
        return "$0.00"


def _fmt_percent(value):
    try:
        return f"{float(value or 0):.2f}%"
    except Exception:
        return "0.00%"


def _to_excel_bytes(kpi_rows, over_time_df, gateway_df, high_value_df):
    with BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            pd.DataFrame(kpi_rows).to_excel(writer, sheet_name="KPI_Summary", index=False)
            if over_time_df is not None and not over_time_df.empty:
                over_time_df.to_excel(writer, sheet_name="Revenue_Over_Time", index=False)
            if gateway_df is not None and not gateway_df.empty:
                gateway_df.to_excel(writer, sheet_name="By_Gateway", index=False)
            if high_value_df is not None and not high_value_df.empty:
                high_value_df.to_excel(writer, sheet_name="High_Value_Recovery", index=False)
        return buffer.getvalue()


setup_page("Revenue Recovery Analytics", "💰")
render_header()
date_range = render_sidebar()

st.subheader("Revenue Recovery Analytics")
st.info(
    """
Quantify how much failed-payment value is still recoverable versus permanently lost.
Prioritize retries on high-value, high-likelihood transactions first.
"""
)

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

# =========================================================
# KPI Cards
# =========================================================

st.subheader("Recovery KPI Overview")

try:
    summary = get_revenue_recovery_summary(
        start_date=start_date_value,
        end_date=end_date_value,
    )
except Exception as error:
    st.error(f"Unable to load revenue recovery summary: {error}")
    summary = {}

recoverable = float(summary.get("recoverable_revenue", 0) or 0)
permanently_lost = float(summary.get("permanently_lost_revenue", 0) or 0)
total_at_risk = recoverable + permanently_lost
successful_amount = float(summary.get("successful_revenue", 0) or 0)
total_amount = float(summary.get("total_revenue", 0) or 0)
recovered_so_far = float(summary.get("recovered_revenue", 0) or 0)
recovery_pct = (recovered_so_far / total_at_risk * 100.0) if total_at_risk > 0 else 0.0
overall_at_risk_pct = (total_at_risk / total_amount * 100.0) if total_amount > 0 else 0.0

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
kpi_col1.metric("Recoverable Revenue", _fmt_money(recoverable))
kpi_col2.metric("Permanently Lost", _fmt_money(permanently_lost))
kpi_col3.metric("Total At Risk", _fmt_money(total_at_risk), f"{overall_at_risk_pct:.2f}% of total")
kpi_col4.metric("Already Recovered", _fmt_money(recovered_so_far))
kpi_col5.metric("Recovery Progress", _fmt_percent(recovery_pct))

st.divider()

# =========================================================
# Insights Box
# =========================================================

st.subheader("Recovery Insights")
insights_lines = []

if total_at_risk > 0:
    insights_lines.append(
        f"You can recover up to **{_fmt_money(recoverable)}** by retrying failed payments "
        f"that are currently classified as TEMPORARY friction."
    )

    if permanently_lost > 0:
        insights_lines.append(
            f"**{_fmt_money(permanently_lost)}** is classified as permanently lost — "
            f"these payments have been classified as PERMANENT failures and should not be retried further."
        )

    if recoverable > 0 and total_at_risk > 0:
        temp_share = recoverable / total_at_risk * 100.0
        insights_lines.append(
            f"About **{temp_share:.1f}%** of the at-risk value is still recoverable — "
            f"this is an excellent opportunity for revenue retention."
        )

try:
    by_gateway = get_revenue_impact_by_gateway(
        start_date=start_date_value,
        end_date=end_date_value,
    )
except Exception as error:
    by_gateway = pd.DataFrame([])

if not by_gateway.empty and "recoverable" in by_gateway.columns:
    try:
        by_gateway["recoverable_num"] = pd.to_numeric(by_gateway["recoverable"], errors="coerce").fillna(0)
        top_gateway_row = by_gateway.sort_values("recoverable_num", ascending=False).iloc[0]
        insights_lines.append(
            f"Gateway **{top_gateway_row.get('gateway') or 'Unknown'}** represents the largest recoverable bucket — "
            f"{_fmt_money(top_gateway_row.get('recoverable_num', 0))} is at stake there."
        )
    except Exception:
        pass

if not insights_lines:
    insights_lines.append("No at-risk revenue data yet — ensure transactions are loaded via the CSV Import page.")

for line in insights_lines:
    st.markdown(f"- {line}")

st.divider()

# =========================================================
# Section 1 — Revenue Impact Over Time
# =========================================================

st.subheader("Section 1 — Revenue Impact Over Time")

try:
    over_time = get_revenue_impact_over_time(
        start_date=start_date_value,
        end_date=end_date_value,
    )
except Exception as error:
    st.error(f"Unable to load revenue impact over time: {error}")
    over_time = pd.DataFrame([])

if over_time.empty:
    st.info("No time-series data for the selected date range.")
else:
    fig_time = revenue_impact_over_time_chart(over_time.to_dict("records"))
    st.plotly_chart(fig_time, width="stretch")
    with st.expander("Show Data Table"):
        st.dataframe(over_time, hide_index=True, width="stretch")

st.divider()

# =========================================================
# Section 2 — Recovery Score Distribution (NumPy)
# =========================================================

st.subheader("Section 2 — Recovery Potential Distribution (NumPy)")

try:
    score_dist = get_recovery_score_distribution(
        start_date=start_date_value,
        end_date=end_date_value,
    )
except Exception as error:
    st.error(f"Unable to load recovery score distribution: {error}")
    score_dist = pd.DataFrame([])

if score_dist.empty:
    st.info("No failed transaction scores available yet.")
else:
    try:
        scores = pd.to_numeric(score_dist["recovery_score"], errors="coerce").dropna().to_numpy()
    except Exception:
        scores = None

    if scores is not None and len(scores) > 0:
        stats = compute_distribution_stats(scores)

        s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
        s_col1.metric("Mean Score", f"{stats['mean']:.2f}")
        s_col2.metric("Median Score", f"{stats['median']:.2f}")
        s_col3.metric("25th Percentile", f"{stats['p25']:.2f}")
        s_col4.metric("75th Percentile", f"{stats['p75']:.2f}")
        s_col5.metric("90th Percentile", f"{stats['p90']:.2f}")

        extra1, extra2 = st.columns(2)
        extra1.metric("Std. Deviation", f"{stats['std']:.2f}")
        extra2.metric("Transactions Scored", f"{int(stats['count']):,}")

        st.caption(
            f"Recovery scores range **{stats['min']:.2f} – {stats['max']:.2f}** "
            f"across {int(stats['count']):,} failed attempts. A higher score means a transaction is more likely to succeed on retry."
        )

    fig_score = recovery_score_distribution_chart(score_dist.to_dict("records"))
    st.plotly_chart(fig_score, width="stretch")

    with st.expander("Show Distribution Bin Data"):
        st.dataframe(score_dist, hide_index=True, width="stretch")

st.divider()

# =========================================================
# Section 3 — Revenue Impact by Gateway
# =========================================================

st.subheader("Section 3 — Revenue Impact by Gateway")

if by_gateway is None or by_gateway.empty:
    try:
        by_gateway = get_revenue_impact_by_gateway(
            start_date=start_date_value,
            end_date=end_date_value,
        )
    except Exception as error:
        st.error(f"Unable to load revenue impact by gateway: {error}")
        by_gateway = pd.DataFrame([])

if by_gateway.empty:
    st.info("No gateway-level data for the selected range.")
else:
    fig_gateway = revenue_impact_by_gateway_chart(by_gateway.to_dict("records"))
    st.plotly_chart(fig_gateway, width="stretch")
    with st.expander("Show Gateway Data Table"):
        st.dataframe(by_gateway, hide_index=True, width="stretch")

st.divider()

# =========================================================
# Section 4 — High-Value Failed Transactions
# =========================================================

st.subheader("Section 4 — High-Value Failed Transactions")

hv_col1, hv_col2 = st.columns(2)
with hv_col1:
    hv_limit = st.slider(
        "Max rows to return",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        key="hv_limit",
    )
with hv_col2:
    hv_min_amount = st.number_input(
        "Minimum transaction amount ($)",
        min_value=0,
        max_value=100000,
        value=0,
        step=50,
        key="hv_min_amount",
    )

try:
    high_value = get_high_value_failed_transactions(
        limit=int(hv_limit),
        min_amount=float(hv_min_amount),
        start_date=start_date_value,
        end_date=end_date_value,
    )
except Exception as error:
    st.error(f"Unable to load high-value failed transactions: {error}")
    high_value = pd.DataFrame([])

if high_value.empty:
    st.info(
        "No high-value failed transactions were found for the selected filters. "
        "Consider lowering the minimum amount or expanding the date range."
    )
else:
    display_cols = [
        "transaction_id",
        "customer_id",
        "amount",
        "currency",
        "payment_method",
        "gateway",
        "failure_type",
        "recovery_score",
        "value_score",
        "recommended_action",
        "failure_description",
        "created_at",
    ]
    existing_cols = [c for c in display_cols if c in high_value.columns]
    hv_display = high_value[existing_cols].copy()
    hv_display.columns = [
        c.replace("_", " ").title() for c in existing_cols
    ]
    st.dataframe(
        hv_display,
        hide_index=True,
        width="stretch",
        use_container_width=True,
    )

    st.caption(
        f"List is sorted by **Value Score (Recovery Score × Amount)** descending. "
        f"Use it to prioritize retries that have the highest expected recovery impact."
    )

st.divider()

# =========================================================
# Section 5 — Prioritized Retry List
# =========================================================

st.subheader("Section 5 — Prioritized Transactions to Retry")

with st.expander("Show / hide prioritized retry list"):
    retry_cols = {
        "Attempts": "Max retries",
        "Hours": "Min hours since last",
    }
    rc1, rc2 = st.columns(2)
    with rc1:
        max_attempts = st.slider(
            "Max retries already attempted",
            min_value=1,
            max_value=10,
            value=5,
            key="rep_max_attempts",
        )
    with rc2:
        min_hours = st.slider(
            "Min hours since last attempt",
            min_value=0,
            max_value=168,
            value=24,
            key="rep_min_hours",
        )

    try:
        prioritized = get_prioritized_transactions_to_retry(
            max_attempts=int(max_attempts),
            min_hours_since_last=int(min_hours),
            limit=100,
            start_date=start_date_value,
            end_date=end_date_value,
        )
    except Exception as error:
        st.error(f"Unable to load prioritized retry list: {error}")
        prioritized = pd.DataFrame([])

    if prioritized.empty:
        st.info("No transactions currently meet the retry prioritization criteria.")
    else:
        st.dataframe(prioritized, hide_index=True, width="stretch")

st.divider()

# =========================================================
# Exports
# =========================================================

st.subheader("Downloads / Exports")

exp_col1, exp_col2, exp_col3 = st.columns(3)

with exp_col1:
    if not high_value.empty:
        hv_csv = high_value.to_csv(index=False)
        st.download_button(
            "📥 High-Value List (CSV)",
            hv_csv,
            "high_value_failed_transactions.csv",
            "text/csv",
        )
    else:
        st.button("📥 High-Value List (CSV)", disabled=True, help="No data to export.")

with exp_col2:
    if not prioritized.empty:
        pr_csv = prioritized.to_csv(index=False)
        st.download_button(
            "📥 Retry Priority List (CSV)",
            pr_csv,
            "prioritized_retry_list.csv",
            "text/csv",
        )
    else:
        st.button("📥 Retry Priority List (CSV)", disabled=True, help="No data to export.")

with exp_col3:
    kpi_rows = [
        {"Metric": "Recoverable Revenue", "Value": _fmt_money(recoverable)},
        {"Metric": "Permanently Lost Revenue", "Value": _fmt_money(permanently_lost)},
        {"Metric": "Total At Risk", "Value": _fmt_money(total_at_risk)},
        {"Metric": "Already Recovered", "Value": _fmt_money(recovered_so_far)},
        {"Metric": "Recovery Progress %", "Value": _fmt_percent(recovery_pct)},
        {"Metric": "Total Revenue", "Value": _fmt_money(total_amount)},
        {"Metric": "Successful Revenue", "Value": _fmt_money(successful_amount)},
    ]
    try:
        excel_bytes = _to_excel_bytes(kpi_rows, over_time, by_gateway, high_value)
        st.download_button(
            "📊 Full Revenue Report (Excel)",
            excel_bytes,
            "revenue_recovery_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as error:
        st.warning(f"Excel report unavailable (need `openpyxl`): {error}")

st.divider()
render_footer()
