import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src.ui_components import setup_page, render_header, render_sidebar, render_footer, require_page_permission
from src.charts import (
    placeholder_retry_attempts,
    retry_success_rate_per_attempt_chart,
    inter_retry_gap_histogram,
    retry_success_by_hour_chart,
    retry_success_by_gap_chart,
)
from src.payment_queries import (
    get_retry_success_rate_per_attempt,
    get_inter_retry_times,
    get_retry_success_by_hour,
    get_retry_success_by_gap,
)

@st.cache_data(ttl=60)
def _cached_get_retry_success_rate_per_attempt(start_date=None, end_date=None):
    return get_retry_success_rate_per_attempt(start_date, end_date)

@st.cache_data(ttl=60)
def _cached_get_inter_retry_times(start_date=None, end_date=None):
    return get_inter_retry_times(start_date, end_date)

@st.cache_data(ttl=60)
def _cached_get_retry_success_by_hour(start_date=None, end_date=None):
    return get_retry_success_by_hour(start_date, end_date)

@st.cache_data(ttl=60)
def _cached_get_retry_success_by_gap(start_date=None, end_date=None, bin_width_minutes=5):
    return get_retry_success_by_gap(start_date, end_date, bin_width_minutes)

get_retry_success_rate_per_attempt = _cached_get_retry_success_rate_per_attempt
get_inter_retry_times = _cached_get_inter_retry_times
get_retry_success_by_hour = _cached_get_retry_success_by_hour
get_retry_success_by_gap = _cached_get_retry_success_by_gap

setup_page("Retry Analytics", "🔁")
render_header()
date_range = render_sidebar()

require_page_permission("Retry Analytics")

st.subheader("Analyze retry performance")
st.divider()

# --- Retry Success Rates per Attempt ---
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

# --- Retry Attempts Distribution ---
st.subheader("Retry Attempts Distribution")
fig = placeholder_retry_attempts()
st.plotly_chart(fig, width='stretch')

st.divider()

# -----------------------------
# Retry Timing Analysis
# -----------------------------
st.subheader("⏱️  Retry Timing Analysis")
st.markdown("Analyze time between retries and identify best retry windows")

# ---- Average time between retries ----
gap_data = get_inter_retry_times()
gap_success_data = get_retry_success_by_gap()
hour_data = get_retry_success_by_hour()

if gap_data:
    gap_minutes_list = [int(d.get("gap_minutes", 0) or 0) for d in gap_data]
    if gap_minutes_list:
        avg_gap_min = round(sum(gap_minutes_list) / len(gap_minutes_list), 1)
        median_gap_min = pd.Series(gap_minutes_list).median()
        min_gap_min = min(gap_minutes_list)
        max_gap_min = max(gap_minutes_list)
        num_gaps = len(gap_minutes_list)

        tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns(5)
        tcol1.metric("# of Inter-Retry Gaps", f"{num_gaps:,}")
        tcol2.metric("Average Gap", f"{avg_gap_min} min")
        tcol3.metric("Median Gap", f"{median_gap_min} min")
        tcol4.metric("Min Gap", f"{min_gap_min} min")
        tcol5.metric("Max Gap", f"{max_gap_min} min")

st.divider()

# ---- Distribution of gaps ----
st.subheader("Gap Distribution Between Consecutive Retries")
fig_gaps = inter_retry_gap_histogram(gap_data)
st.plotly_chart(fig_gaps, width='stretch')

st.divider()

# ---- Best retry windows: by gap bucket + by hour ----
st.subheader("🎯 Best Retry Windows")

gap_col, hour_col = st.columns(2)

with gap_col:
    st.markdown("#### By Time Gap")
    fig_gap_success = retry_success_by_gap_chart(gap_success_data)
    st.plotly_chart(fig_gap_success, width='stretch')
    # Best gap bucket
    if gap_success_data:
        best_gap = max(
            gap_success_data,
            key=lambda d: float(d.get("success_rate", 0) or 0),
        )
        st.success(
            f"💡 Best gap: **{best_gap['gap_bucket']}** with "
            f"**{float(best_gap['success_rate'])}%** success rate "
            f"({int(best_gap.get('total_attempts',0) or 0)} attempts)"
        )

with hour_col:
    st.markdown("#### By Hour of Day")
    fig_hour = retry_success_by_hour_chart(hour_data)
    st.plotly_chart(fig_hour, width='stretch')
    # Best hour
    if hour_data:
        filtered_hours = [h for h in hour_data if int(h.get("total_attempts", 0) or 0) > 0]
        if filtered_hours:
            best_hour = max(
                filtered_hours,
                key=lambda d: float(d.get("success_rate", 0) or 0),
            )
            h = int(best_hour["hour_of_day"])
            st.success(
                f"💡 Best hour: **{h:02d}:00 – {h+1:02d}:00** with "
                f"**{float(best_hour['success_rate'])}%** success rate "
                f"({int(best_hour.get('total_attempts',0) or 0)} attempts)"
            )

render_footer()
