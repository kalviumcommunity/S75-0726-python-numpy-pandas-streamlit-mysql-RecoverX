import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.ui_components import (
    setup_page,
    render_header,
    render_sidebar,
    render_footer,
)

from src.charts import (
    placeholder_retry_attempts,
    retry_success_rate_per_attempt_chart,
    retry_success_heatmap_chart,
    retry_timing_analysis_chart,
    retry_gateway_performance_chart,
    retry_bank_performance_chart,
)

from src.payment_queries import (
    get_retry_success_rate_per_attempt,
    get_retry_success_by_time_heatmap,
    get_retry_timing_analysis,
    get_retry_gateway_performance,
    get_retry_bank_performance,
    get_prioritized_transactions_to_retry,
    get_retry_attempts_distribution,
    get_ineffective_retry_patterns,
)


get_retry_success_rate_per_attempt = st.cache_data(show_spinner=False, ttl=300)(get_retry_success_rate_per_attempt)
get_retry_success_by_time_heatmap = st.cache_data(show_spinner=False, ttl=300)(get_retry_success_by_time_heatmap)
get_retry_timing_analysis = st.cache_data(show_spinner=False, ttl=300)(get_retry_timing_analysis)
get_retry_gateway_performance = st.cache_data(show_spinner=False, ttl=300)(get_retry_gateway_performance)
get_retry_bank_performance = st.cache_data(show_spinner=False, ttl=300)(get_retry_bank_performance)
get_prioritized_transactions_to_retry = st.cache_data(show_spinner=False, ttl=300)(get_prioritized_transactions_to_retry)
get_retry_attempts_distribution = st.cache_data(show_spinner=False, ttl=300)(get_retry_attempts_distribution)
get_ineffective_retry_patterns = st.cache_data(show_spinner=False, ttl=300)(get_ineffective_retry_patterns)


# ----------------------------------------------------
# Page Setup
# ----------------------------------------------------

setup_page("Retry Analytics", "🔁")
render_header()
date_range = render_sidebar()
start_date = None
end_date = None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].isoformat() if date_range[0] else None
    end_date = date_range[1].isoformat() if date_range[1] else None

st.subheader("Analyze Retry Performance")

st.info(
    """
This dashboard helps analyze payment retry success,
retry timing, gateway performance,
and bank-level retry analytics.
"""
)

if st.button("🔄 Refresh Data"):
    st.rerun()

st.divider()

# ----------------------------------------------------
# Retry Success KPIs
# ----------------------------------------------------

success_data = get_retry_success_rate_per_attempt()

if success_data:

    total_attempts = sum(
        int(row.get("total_attempts", 0))
        for row in success_data
    )

    successful = sum(
        int(row.get("successful", 0))
        for row in success_data
    )

    overall_rate = (
        round(successful / total_attempts * 100, 1)
        if total_attempts else 0
    )

    best_attempt = max(
        success_data,
        key=lambda x: float(x.get("success_rate", 0))
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Retry Attempts",
        f"{total_attempts:,}"
    )

    c2.metric(
        "Successful",
        f"{successful:,}"
    )

    c3.metric(
        "Success Rate",
        f"{overall_rate}%"
    )

    c4.metric(
        "Best Attempt",
        f"Attempt {best_attempt['attempt_number']}",
        f"{best_attempt['success_rate']}%"
    )

else:

    st.warning("No retry analytics available.")

st.divider()

# ----------------------------------------------------
# Retry Recommendations
# ----------------------------------------------------

st.subheader("Retry Recommendations")

timing = get_retry_timing_analysis()
avg_time = timing.get("average_hours_between_retries", 0)
median_time = timing.get("median_hours_between_retries", 0)
best_window = timing.get("best_window", "No Data")
window_count = timing.get("best_window_count", 0)
distribution = timing.get("window_distribution", [])

recommendation_lines = []
if success_data:
    best_attempt = max(
        success_data,
        key=lambda x: float(x.get("success_rate", 0)),
    )
    worst_attempt = min(
        success_data,
        key=lambda x: float(x.get("success_rate", 0)),
    )
    recommendation_lines.append(
        f"**Best attempt to retry:** Attempt #{best_attempt['attempt_number']} achieves "
        f"the highest success rate at **{best_attempt['success_rate']}%** across "
        f"**{best_attempt['total_attempts']:,}** recorded attempts."
    )
    recommendation_lines.append(
        f"**Least effective attempt:** Attempt #{worst_attempt['attempt_number']} has success "
        f"rate of only **{worst_attempt['success_rate']}%** — consider dropping or delaying "
        f"this attempt further to save capacity."
    )

if best_window and best_window != "No Data":
    recommendation_lines.append(
        f"**Best retry window:** `{best_window}` — observed "
        f"**{window_count:,}** successes in this bucket, so schedule high-priority retries here."
    )

recommendation_lines.append(
    f"**Average gap between retries:** {avg_time:.2f} hours (median {median_time:.2f}h). "
    f"Widening the gap may improve success for bank-issued temporary declines."
)

for line in recommendation_lines:
    st.markdown(f"- {line}")

if success_data and best_window and best_window != "No Data":
    best_attempt_rec = max(
        success_data,
        key=lambda x: float(x.get("success_rate", 0)),
    )
    st.success(
        f"**Best window:** {best_window} · **Best attempt:** Attempt "
        f"#{best_attempt_rec['attempt_number']} at {best_attempt_rec['success_rate']}%"
    )

st.divider()

# ----------------------------------------------------
# Success Rate Chart
# ----------------------------------------------------

st.subheader("Retry Success Rate per Attempt")

left, right = st.columns([2,1])

with left:

    if success_data:

        fig = retry_success_rate_per_attempt_chart(
            success_data
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("No retry data available.")

with right:

    if success_data:

        df = pd.DataFrame(success_data)

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "retry_success_rate.csv",
            "text/csv"
        )

st.divider()

# ----------------------------------------------------
# Retry Timing Analysis
# ----------------------------------------------------

st.subheader("Retry Timing Analysis")

timing = get_retry_timing_analysis()

avg_time = timing.get(
    "average_hours_between_retries",
    0
)

median_time = timing.get(
    "median_hours_between_retries",
    0
)

best_window = timing.get(
    "best_window",
    "No Data"
)

window_count = timing.get(
    "best_window_count",
    0
)

distribution = timing.get(
    "window_distribution",
    []
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Average Hours",
    f"{avg_time:.2f}"
)

c2.metric(
    "Median Hours",
    f"{median_time:.2f}"
)

c3.metric(
    "Best Retry Window",
    best_window
)

c4.metric(
    "Occurrences",
    f"{window_count:,}"
)

fig = retry_timing_analysis_chart(distribution)

st.plotly_chart(
    fig,
    use_container_width=True
)

if distribution:
    with st.expander("View Timing Data"):
        df_timing = pd.DataFrame(distribution)
        st.dataframe(df_timing, hide_index=True, use_container_width=True)
        st.download_button(
            "Download Timing CSV",
            df_timing.to_csv(index=False),
            "retry_timing_distribution.csv",
            "text/csv",
        )

st.divider()

# ----------------------------------------------------
# Retry Success Heatmap
# ----------------------------------------------------

st.subheader("Retry Success by Day and Hour")

heatmap_data = get_retry_success_by_time_heatmap()

if heatmap_data and heatmap_data.get("values"):
    fig = retry_success_heatmap_chart(heatmap_data)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Heatmap Data"):
        days = heatmap_data.get("days", [])
        hours = heatmap_data.get("hours", [])
        values = heatmap_data.get("values", [])
        heatmap_rows = []
        for day_idx, day in enumerate(days):
            for hour_idx, hour in enumerate(hours):
                rate = values[day_idx][hour_idx] if day_idx < len(values) and hour_idx < len(values[day_idx]) else 0.0
                heatmap_rows.append({
                    "Day": day,
                    "Hour": hour,
                    "Success Rate (%)": rate,
                })
        df_heatmap = pd.DataFrame(heatmap_rows)
        st.dataframe(df_heatmap, hide_index=True, use_container_width=True, height=300)
        st.download_button(
            "Download Heatmap CSV",
            df_heatmap.to_csv(index=False),
            "retry_heatmap_success_rates.csv",
            "text/csv",
        )
else:
    st.info("No retry timing data available for the heatmap.")

st.divider()

st.subheader("Prioritized Transactions to Retry")

df_prioritized = get_prioritized_transactions_to_retry(
    start_date=start_date,
    end_date=end_date,
)

if not df_prioritized.empty:
    st.dataframe(
        df_prioritized,
        hide_index=True,
        use_container_width=True,
        height=350,
    )
    st.download_button(
        "Download Prioritized Transactions CSV",
        df_prioritized.to_csv(index=False),
        "prioritized_transactions_to_retry.csv",
        "text/csv",
    )
else:
    st.info("No eligible transactions found to prioritize for retry.")

st.divider()

# ----------------------------------------------------
# Retry Attempts Distribution
# ----------------------------------------------------

st.subheader("Retry Attempts Distribution")

try:
    retry_dist_raw = get_retry_attempts_distribution() or []
    df_retry_dist = pd.DataFrame(retry_dist_raw)
except Exception as error:
    st.error(f"Unable to load retry attempts distribution: {error}")
    df_retry_dist = pd.DataFrame([])

if df_retry_dist.empty:
    st.info("No retry attempt distribution data available yet.")
else:
    try:
        df_retry_dist["attempt_count"] = pd.to_numeric(
            df_retry_dist["attempt_count"], errors="coerce"
        ).fillna(0).astype(int)
        df_retry_dist["attempt_category"] = df_retry_dist["attempt_count"].apply(
            lambda x: "4+" if x >= 4 else str(x)
        )
        retry_counts = (
            df_retry_dist.groupby("attempt_category")
            .size()
            .reset_index(name="Transactions")
        )
        retry_counts.columns = ["Attempts", "Transactions"]
        retry_counts["sort_key"] = retry_counts["Attempts"].apply(
            lambda x: 4 if x == "4+" else int(x)
        )
        retry_counts = retry_counts.sort_values("sort_key").drop("sort_key", axis=1)
        fig_retry_dist = px.bar(
            retry_counts,
            x="Attempts",
            y="Transactions",
            color="Attempts",
            color_discrete_sequence=["#2563eb", "#38bdf8", "#0ea5e9", "#0369a1", "#0c4a6e"],
        )
        fig_retry_dist.update_layout(
            height=350,
            margin={"l": 0, "r": 0, "t": 30, "b": 0},
            showlegend=False,
        )
        st.plotly_chart(fig_retry_dist, use_container_width=True)
        with st.expander("Show Retry Distribution Data"):
            st.dataframe(retry_counts, hide_index=True, use_container_width=True)
    except Exception as err:
        st.warning(f"Could not render retry distribution chart: {err}")

st.divider()

# ----------------------------------------------------
# Ineffective Retry Patterns
# ----------------------------------------------------

st.subheader("⛔ Ineffective Retry Patterns (Success Rate < 20%)")
st.caption(
    "These segments rarely succeed on retry. Consider stopping retries here "
    "to save capacity, reduce issuer friction, and focus effort on high-value opportunities."
)

try:
    ineffective_patterns = get_ineffective_retry_patterns(threshold_success_rate=20.0)
except Exception as error:
    st.error(f"Unable to load ineffective retry patterns: {error}")
    ineffective_patterns = []

if not ineffective_patterns:
    st.success("🎉 No ineffective patterns detected — all retry segments exceed the 20% success threshold.")
else:
    df_ineffective = pd.DataFrame(ineffective_patterns)
    display_ineffective = df_ineffective.rename(columns={
        "category": "Category",
        "pattern": "Pattern",
        "total": "Total Retries",
        "successful": "Successful",
        "success_rate": "Success Rate (%)",
        "recommendation": "Recommendation",
    })
    category_map = {
        "Attempt Number": "🔁 Attempt",
        "Gateway": "🌐 Gateway",
        "Bank/Response Code": "🏦 Bank/Code",
    }
    display_ineffective["Category"] = display_ineffective["Category"].map(
        lambda c: category_map.get(str(c), c)
    )
    st.dataframe(
        display_ineffective,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### 🛑 Stop Retrying These")
    for _, p in df_ineffective.iterrows():
        st.warning(
            f"**[{p['category']}] {p['pattern']}**: "
            f"{p['success_rate']:.1f}% success across {p['total']:,} attempts → "
            f"{p['recommendation']}"
        )

    ineff_csv = display_ineffective.to_csv(index=False)
    st.download_button(
        "📥 Download Ineffective Patterns CSV",
        ineff_csv,
        "ineffective_retry_patterns.csv",
        "text/csv",
    )

st.divider()

# ----------------------------------------------------
# Gateway Performance
# ----------------------------------------------------

st.subheader("Retry Performance by Gateway")

gateway_data = get_retry_gateway_performance()

if gateway_data:

    left, right = st.columns([2, 1])

    with left:

        fig = retry_gateway_performance_chart(
            gateway_data
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        df = pd.DataFrame(gateway_data)

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            "Download Gateway CSV",
            df.to_csv(index=False),
            "gateway_retry_performance.csv",
            "text/csv"
        )

else:

    st.info("No gateway retry data available.")

st.divider()

# ----------------------------------------------------
# Bank Performance
# ----------------------------------------------------

st.subheader("Retry Performance by Bank")

bank_data = get_retry_bank_performance()

if bank_data:

    left, right = st.columns([2, 1])

    with left:

        fig = retry_bank_performance_chart(
            bank_data
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        df = pd.DataFrame(bank_data)

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            "Download Bank CSV",
            df.to_csv(index=False),
            "bank_retry_performance.csv",
            "text/csv"
        )

else:

    st.info("No bank retry data available.")

st.divider()

# ----------------------------------------------------
# Export All Retry Analytics
# ----------------------------------------------------

st.subheader("Export Retry Analytics")

st.caption(
    "Download combined retry analytics data in a single consolidated CSV report."
)

export_col1, export_col2 = st.columns(2)

with export_col1:

    analytics_rows = []

    if success_data:
        for row in success_data:
            analytics_rows.append({
                "Category": "Success per Attempt",
                "Segment": f"Attempt {row['attempt_number']}",
                "Metric 1": row["total_attempts"],
                "Metric 1 Label": "Total Attempts",
                "Metric 2": row["successful"],
                "Metric 2 Label": "Successful",
                "Metric 3": row["success_rate"],
                "Metric 3 Label": "Success Rate (%)",
            })

    if distribution:
        for row in distribution:
            analytics_rows.append({
                "Category": "Timing Window",
                "Segment": row["window"],
                "Metric 1": row["count"],
                "Metric 1 Label": "Count",
                "Metric 2": "",
                "Metric 2 Label": "",
                "Metric 3": "",
                "Metric 3 Label": "",
            })

    if gateway_data:
        for row in gateway_data:
            analytics_rows.append({
                "Category": "Gateway Performance",
                "Segment": row.get("gateway", "Unknown"),
                "Metric 1": row.get("total_retries", 0),
                "Metric 1 Label": "Total Retries",
                "Metric 2": row.get("successful", 0),
                "Metric 2 Label": "Successful",
                "Metric 3": row.get("success_rate", 0),
                "Metric 3 Label": "Success Rate (%)",
            })

    if bank_data:
        for row in bank_data:
            analytics_rows.append({
                "Category": "Bank Performance",
                "Segment": row.get("bank", "Unknown"),
                "Metric 1": row.get("total_retries", 0),
                "Metric 1 Label": "Total Retries",
                "Metric 2": row.get("successful", 0),
                "Metric 2 Label": "Successful",
                "Metric 3": row.get("success_rate", 0),
                "Metric 3 Label": "Success Rate (%)",
            })

    if analytics_rows:
        df_combined = pd.DataFrame(analytics_rows)
        st.download_button(
            "📊 Download Combined Analytics CSV",
            df_combined.to_csv(index=False),
            "retry_analytics_combined.csv",
            "text/csv",
            use_container_width=True,
        )
    else:
        st.info("No analytics data available for combined export.")

with export_col2:

    kpi_export_rows = []

    if success_data:
        total_attempts_export = sum(int(r.get("total_attempts", 0)) for r in success_data)
        total_successful_export = sum(int(r.get("successful", 0)) for r in success_data)
        overall_rate_export = round(total_successful_export / total_attempts_export * 100, 1) if total_attempts_export else 0
        best_attempt_export = max(success_data, key=lambda x: float(x.get("success_rate", 0)))

        kpi_export_rows.extend([
            {"KPI": "Total Retry Attempts", "Value": total_attempts_export},
            {"KPI": "Successful Retries", "Value": total_successful_export},
            {"KPI": "Overall Success Rate (%)", "Value": overall_rate_export},
            {"KPI": "Best Attempt Number", "Value": best_attempt_export["attempt_number"]},
            {"KPI": "Best Attempt Success Rate (%)", "Value": best_attempt_export["success_rate"]},
        ])

    kpi_export_rows.extend([
        {"KPI": "Average Hours Between Retries", "Value": avg_time},
        {"KPI": "Median Hours Between Retries", "Value": median_time},
        {"KPI": "Best Retry Window", "Value": best_window},
        {"KPI": "Best Window Occurrences", "Value": window_count},
    ])

    df_kpi = pd.DataFrame(kpi_export_rows)
    st.download_button(
        "📈 Download KPI Summary CSV",
        df_kpi.to_csv(index=False),
        "retry_analytics_kpi_summary.csv",
        "text/csv",
        use_container_width=True,
    )

st.divider()

# ----------------------------------------------------
# Summary
# ----------------------------------------------------

st.subheader("Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.success(
        """
✅ Retry analytics helps identify:

• Best retry attempt

• Best retry time window

• Gateway performance

• Bank-wise success trends
"""
    )

with summary_col2:

    st.info(
        """
📈 Recommendations

• Retry more during the best-performing window

• Prefer high-performing gateways

• Monitor banks with low retry success

• Reduce retries on consistently failing banks
"""
    )

st.divider()

# ----------------------------------------------------
# Footer
# ----------------------------------------------------

render_footer()
