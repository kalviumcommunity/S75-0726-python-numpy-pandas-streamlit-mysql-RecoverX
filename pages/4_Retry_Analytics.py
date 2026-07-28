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
)

# ----------------------------------------------------
# Page Setup
# ----------------------------------------------------

setup_page("Retry Analytics", "🔁")
render_header()
date_range = render_sidebar()

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
            width="stretch"
        )

    else:

        st.info("No retry data available.")

with right:

    if success_data:

        df = pd.DataFrame(success_data)

        st.dataframe(
            df,
            hide_index=True,
            width="stretch"
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
    width="stretch"
)

st.divider()

# ----------------------------------------------------
# Retry Success Heatmap
# ----------------------------------------------------

st.subheader("Retry Success by Day and Hour")

heatmap_data = get_retry_success_by_time_heatmap()

if heatmap_data and heatmap_data.get("values"):
    fig = retry_success_heatmap_chart(heatmap_data)
    st.plotly_chart(fig, width="stretch")
else:
    st.info("No retry timing data available for the heatmap.")

st.divider()

# ----------------------------------------------------
# Retry Attempts Distribution
# ----------------------------------------------------

st.subheader("Retry Attempts Distribution")

fig = placeholder_retry_attempts()

st.plotly_chart(
    fig,
    width="stretch"
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
            width="stretch"
        )

    with right:

        df = pd.DataFrame(gateway_data)

        st.dataframe(
            df,
            hide_index=True,
            width="stretch"
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
            width="stretch"
        )

    with right:

        df = pd.DataFrame(bank_data)

        st.dataframe(
            df,
            hide_index=True,
            width="stretch"
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