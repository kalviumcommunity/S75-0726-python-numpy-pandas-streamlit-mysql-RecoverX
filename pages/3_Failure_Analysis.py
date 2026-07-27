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
    failure_type_distribution_chart,
    failure_breakdown_by_response_code_chart,
    failure_breakdown_by_gateway_chart,
    failure_breakdown_by_payment_method_chart,
)

from src.payment_queries import (
    get_failure_type_distribution,
    get_failure_breakdown_by_response_code,
    get_failure_breakdown_by_gateway,
    get_failure_breakdown_by_payment_method,
)

# ----------------------------------------------------
# Page Setup
# ----------------------------------------------------

setup_page("Failure Analysis", "❌")
render_header()
date_range = render_sidebar()

st.subheader("Analyze Payment Failure Patterns")

st.info(
    """
This dashboard helps identify payment failures,
their causes, recovery potential, and payment gateway trends.
"""
)

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    selected_failure = st.selectbox(
        "Failure Type",
        ["All", "TEMPORARY", "PERMANENT"]
    )

with filter_col2:
    refresh = st.button("🔄 Refresh Data")

if refresh:
    st.rerun()

st.divider()

# ----------------------------------------------------
# KPI Cards
# ----------------------------------------------------

distribution = get_failure_type_distribution()

if selected_failure != "All":
    distribution = [
        row for row in distribution
        if row["failure_type"] == selected_failure
    ]

temp_count = 0
perm_count = 0

if distribution:
    for row in distribution:
        if str(row["failure_type"]).upper() == "TEMPORARY":
            temp_count = int(row["count"])
        elif str(row["failure_type"]).upper() == "PERMANENT":
            perm_count = int(row["count"])

total_failures = temp_count + perm_count

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Failures", f"{total_failures:,}")

with c2:
    st.metric("Temporary Failures", f"{temp_count:,}")

with c3:
    st.metric("Permanent Failures", f"{perm_count:,}")

st.divider()

# ----------------------------------------------------
# Failure Type Distribution
# ----------------------------------------------------

st.subheader("Failure Distribution by Type")

left, right = st.columns([2, 1])

with left:

    if distribution:

        fig = failure_type_distribution_chart(distribution)
        st.plotly_chart(fig, width="stretch")

    else:
        st.info("No failure data available.")

with right:

    st.markdown("### Summary")

    total = temp_count + perm_count

    pct_temp = round(temp_count / total * 100, 1) if total else 0
    pct_perm = round(perm_count / total * 100, 1) if total else 0

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "TEMPORARY",
            temp_count,
            f"{pct_temp}%"
        )

    with c2:
        st.metric(
            "PERMANENT",
            perm_count,
            f"{pct_perm}%"
        )

    summary = pd.DataFrame({
        "Failure Type": [
            "TEMPORARY",
            "PERMANENT"
        ],
        "Count": [
            temp_count,
            perm_count
        ],
        "Percentage": [
            f"{pct_temp}%",
            f"{pct_perm}%"
        ],
        "Recovery Potential": [
            "Retry Possible",
            "Requires User Action"
        ]
    })

    st.dataframe(
        summary,
        hide_index=True,
        width="stretch"
    )

st.success("### Recovery Insights")

if temp_count > perm_count:
    st.write(
        "Most payment failures are temporary. Improving retry logic can significantly increase recovered revenue."
    )
elif perm_count > temp_count:
    st.write(
        "Most payment failures are permanent. Focus on payment validation, customer guidance, and reducing invalid transactions."
    )
else:
    st.write(
        "Temporary and permanent failures are balanced. Both retry optimization and payment validation should be monitored."
    )

st.divider()

# ----------------------------------------------------
# Response Code Breakdown
# ----------------------------------------------------

st.subheader("Failure Breakdown by Response Code")

st.caption(
    "Shows which bank response codes contribute the most to failed payment attempts."
)

response_code_data = get_failure_breakdown_by_response_code()

if response_code_data:

    fig = failure_breakdown_by_response_code_chart(
        response_code_data
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    with st.expander("View Response Code Data"):

        df = pd.DataFrame(response_code_data)

        st.dataframe(
            df,
            width="stretch"
        )

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "response_code_analysis.csv",
            "text/csv"
        )

else:

    st.info("No response code data found.")

st.divider()

# ----------------------------------------------------
# Gateway & Payment Method
# ----------------------------------------------------

left, right = st.columns(2)

with left:

    st.subheader("Gateway Failures")
    st.caption("Compare payment failures across different payment gateways.")

    gateway_data = get_failure_breakdown_by_gateway()

    if gateway_data:

        fig = failure_breakdown_by_gateway_chart(
            gateway_data
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

        with st.expander("View Gateway Data"):

            df = pd.DataFrame(gateway_data)

            st.dataframe(
                df,
                width="stretch"
            )

            st.download_button(
                "Download Gateway CSV",
                df.to_csv(index=False),
                "gateway_failures.csv",
                "text/csv"
            )

    else:

        st.info("No gateway data available.")

with right:

    st.subheader("Payment Method Failures")
    st.caption("Identify which payment methods generate the highest number of failed payments.")

    pm_data = get_failure_breakdown_by_payment_method()

    if pm_data:

        fig = failure_breakdown_by_payment_method_chart(
            pm_data
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

        with st.expander("View Payment Method Data"):

            df = pd.DataFrame(pm_data)

            st.dataframe(
                df,
                width="stretch"
            )

            st.download_button(
                "Download Payment Method CSV",
                df.to_csv(index=False),
                "payment_method_failures.csv",
                "text/csv"
            )

    else:

        st.info("No payment method data available.")

st.divider()

# ----------------------------------------------------
# Dashboard Summary
# ----------------------------------------------------

st.subheader("Dashboard Summary")

st.markdown(f"""
### Key Findings

- **Total Failures:** {total_failures:,}
- **Temporary Failures:** {temp_count:,}
- **Permanent Failures:** {perm_count:,}

### Recommendations

- Improve retry strategies for temporary failures.
- Investigate gateways with high failure counts.
- Monitor bank response codes with low recovery potential.
- Optimize payment methods that frequently fail.
""")

st.divider()

render_footer()