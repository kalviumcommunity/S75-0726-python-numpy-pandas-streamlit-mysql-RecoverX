import sys
from io import BytesIO, StringIO
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
    failure_causes_pie_chart,
    failure_causes_bar_chart,
    recovery_score_distribution_chart,
)

from src.payment_queries import (
    count_bank_response_codes,
    get_bank_response_codes,
    get_filtered_failed_transactions,
    get_failure_type_distribution,
    get_failure_breakdown_by_response_code,
    get_failure_breakdown_by_gateway,
    get_failure_breakdown_by_payment_method,
    get_failure_causes_distribution,
    get_recovery_score_distribution,
    get_recovery_score_buckets,
)

from src.numpy_utils import compute_distribution_stats


count_bank_response_codes = st.cache_data(show_spinner=False, ttl=300)(count_bank_response_codes)
get_bank_response_codes = st.cache_data(show_spinner=False, ttl=300)(get_bank_response_codes)
get_failure_type_distribution = st.cache_data(show_spinner=False, ttl=300)(get_failure_type_distribution)
get_recovery_score_distribution = st.cache_data(show_spinner=False, ttl=300)(get_recovery_score_distribution)
get_filtered_failed_transactions = st.cache_data(show_spinner=False, ttl=300)(get_filtered_failed_transactions)
get_failure_breakdown_by_response_code = st.cache_data(show_spinner=False, ttl=300)(get_failure_breakdown_by_response_code)
get_failure_breakdown_by_gateway = st.cache_data(show_spinner=False, ttl=300)(get_failure_breakdown_by_gateway)
get_failure_breakdown_by_payment_method = st.cache_data(show_spinner=False, ttl=300)(get_failure_breakdown_by_payment_method)
get_failure_causes_distribution = st.cache_data(show_spinner=False, ttl=300)(get_failure_causes_distribution)


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
        ["All", "TEMPORARY", "PERMANENT"],
        key="kpi_failure_type_filter"
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
# Recovery Potential Distribution (NumPy stats cards)
# ----------------------------------------------------

st.subheader("Recovery Potential Distribution")

try:
    score_dist_df = get_recovery_score_distribution()
except Exception as error:
    st.error(f"Unable to load recovery score distribution: {error}")
    score_dist_df = pd.DataFrame([])

if score_dist_df.empty:
    st.info("No recovery score distribution available yet.")
else:
    try:
        scores = pd.to_numeric(score_dist_df["recovery_score"], errors="coerce").dropna().to_numpy()
    except Exception:
        scores = None

    if scores is not None and len(scores) > 0:
        stats = compute_distribution_stats(scores)

        rp_col1, rp_col2, rp_col3, rp_col4, rp_col5 = st.columns(5)
        rp_col1.metric("Mean", f"{stats['mean']:.2f}")
        rp_col2.metric("Median", f"{stats['median']:.2f}")
        rp_col3.metric("25th", f"{stats['p25']:.2f}")
        rp_col4.metric("75th", f"{stats['p75']:.2f}")
        rp_col5.metric("90th", f"{stats['p90']:.2f}")

        extra_r1, extra_r2 = st.columns(2)
        extra_r1.metric("Std. Dev", f"{stats['std']:.2f}")
        extra_r2.metric("Failures Scored", f"{int(stats['count']):,}")

    with st.expander("Recovery Score Distribution Chart", expanded=False):
        fig_score = recovery_score_distribution_chart(get_recovery_score_buckets())
        st.plotly_chart(fig_score, use_container_width=True)

st.divider()

with st.expander("🔍 Filter failed transactions", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        failure_type_filter = st.selectbox(
            "Failure Type",
            options=["All", "TEMPORARY", "PERMANENT"],
            index=0,
            key="table_failure_type_filter"
        )
        response_code_filter = st.text_input("Bank Response Code", placeholder="e.g. 05")
        gateway_filter = st.text_input("Gateway", placeholder="Enter gateway...")
    with col2:
        payment_method_filter = st.text_input("Payment Method", placeholder="Enter payment method...")
        start_date_filter = st.date_input("Start Date", value=None)
        end_date_filter = st.date_input("End Date", value=None)

try:
    failed_transactions = get_filtered_failed_transactions(
        failure_type=failure_type_filter if failure_type_filter != "All" else None,
        response_code=response_code_filter.strip() or None,
        gateway=gateway_filter.strip() or None,
        payment_method=payment_method_filter.strip() or None,
        start_date=pd.Timestamp(start_date_filter).strftime("%Y-%m-%d 00:00:00") if start_date_filter else None,
        end_date=pd.Timestamp(end_date_filter).strftime("%Y-%m-%d 23:59:59") if end_date_filter else None,
    )
except Exception as error:
    st.error(f"Unable to load failed transactions from the database: {error}")
    failed_transactions = pd.DataFrame()

if not failed_transactions.empty:
    if "recovery_potential" in failed_transactions.columns:
        failed_transactions["recovery_potential"] = pd.to_numeric(
            failed_transactions["recovery_potential"], errors="coerce"
        )
        high_value_threshold = 0.75
        high_value_candidates = failed_transactions.loc[
            failed_transactions["recovery_potential"].fillna(0) >= high_value_threshold
        ].copy()

        if not high_value_candidates.empty:
            high_value_candidates = high_value_candidates.sort_values(
                by=["recovery_potential", "amount"],
                ascending=[False, False]
            ).head(5)

            st.subheader("High-Value Recovery Candidates")
            st.markdown(
                "These failed transactions have the highest recovery potential and value."
            )
            st.dataframe(
                high_value_candidates[
                    [
                        "transaction_id",
                        "customer_id",
                        "amount",
                        "currency",
                        "gateway",
                        "failure_type",
                        "recovery_potential",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    st.subheader("Failed Transactions")
    failed_display = failed_transactions.copy()

    if "response_code" in failed_display.columns:
        try:
            total_codes = count_bank_response_codes() or 0
            all_codes = []
            page = 1
            per_page = 500
            while len(all_codes) < total_codes or total_codes == 0:
                batch = get_bank_response_codes(page=page, limit=per_page) or []
                if not batch:
                    break
                all_codes.extend(batch)
                if len(batch) < per_page:
                    break
                page += 1
                if page > 100:
                    break
            response_lookup = {
                str(row.get("response_code", "")).strip(): {
                    "recommended_action": row.get("recommended_action") or "",
                    "bank_failure_type": row.get("failure_type") or "",
                    "bank_recovery_potential": row.get("recovery_potential"),
                    "bank_description": row.get("description") or "",
                }
                for row in all_codes
                if row.get("response_code") is not None
            }
        except Exception:
            response_lookup = {}

        def _lookup_action(code):
            if code is None:
                return ""
            hit = response_lookup.get(str(code).strip())
            return hit.get("recommended_action", "") if hit else ""

        def _lookup_failure_type(code):
            if code is None:
                return None
            hit = response_lookup.get(str(code).strip())
            if not hit:
                return None
            return hit.get("bank_failure_type") or None

        def _lookup_desc(code):
            if code is None:
                return ""
            hit = response_lookup.get(str(code).strip())
            return hit.get("bank_description", "") if hit else ""

        failed_display["recommended_action"] = failed_display["response_code"].apply(_lookup_action)
        if "failure_type" not in failed_display.columns or not failed_display["failure_type"].notna().any():
            enriched_ft = failed_display["response_code"].apply(_lookup_failure_type)
            if enriched_ft.notna().any():
                failed_display["failure_type"] = enriched_ft.fillna(failed_display.get("failure_type", pd.NA))
        if not response_lookup:
            st.caption(
                "Tip: Upload bank_response_codes.csv via the CSV Import page to auto-enrich "
                "recommended_action, failure classification, and recovery potential per code."
            )
    elif "recommended_action" not in failed_display.columns:
        failed_display["recommended_action"] = ""

    preferred_cols = [
        "transaction_id", "customer_id", "amount", "currency",
        "gateway", "payment_method", "response_code",
        "failure_type", "recovery_potential", "recommended_action",
        "initial_status", "final_status", "created_at",
    ]
    existing_pref = [c for c in preferred_cols if c in failed_display.columns]
    other_cols = [c for c in failed_display.columns if c not in existing_pref]
    keep_cols = existing_pref + other_cols
    st.dataframe(failed_display[keep_cols], use_container_width=True, hide_index=True)

    st.markdown("#### Export Failed Transactions")
    fexp1, fexp2 = st.columns(2)
    with fexp1:
        csv_buffer = StringIO()
        failed_display.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Failed Transactions (CSV)",
            data=csv_buffer.getvalue(),
            file_name="failed_transactions.csv",
            mime="text/csv",
            key="failed_txn_csv",
        )
    with fexp2:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            failed_display.to_excel(writer, index=False, sheet_name="FailedTransactions")
            if "recovery_potential" in failed_transactions.columns:
                hv_df = failed_transactions.loc[
                    pd.to_numeric(failed_transactions["recovery_potential"], errors="coerce").fillna(0) >= 0.75
                ].copy()
                if not hv_df.empty:
                    hv_df.to_excel(writer, index=False, sheet_name="HighValueCandidates")
        st.download_button(
            label="📥 Failed Transactions (Excel)",
            data=excel_buffer.getvalue(),
            file_name="failed_transactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="failed_txn_xlsx",
        )
else:
    st.info("No failed transactions found matching the selected filters.")

st.divider()

# --- Charts ---
chart_col1, chart_col2 = st.columns(2)
# ----------------------------------------------------
# Failure Type Distribution
# ----------------------------------------------------

st.subheader("Failure Distribution by Type")

left, right = st.columns([2, 1])

with left:

    if distribution:

        fig = failure_type_distribution_chart(distribution)
        st.plotly_chart(fig, use_container_width=True)

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
        use_container_width=True
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
        use_container_width=True
    )

    with st.expander("View Response Code Data"):

        df = pd.DataFrame(response_code_data)

        st.dataframe(
            df,
            use_container_width=True
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
# Failure Causes Visualizations
# ----------------------------------------------------

st.subheader("Failure Causes Analysis")

st.caption(
    "Visualize the distribution of payment failure causes using pie and bar charts."
)

failure_causes_data = get_failure_causes_distribution()

if failure_causes_data:

    pie_col, bar_col = st.columns(2)

    with pie_col:
        fig_pie = failure_causes_pie_chart(failure_causes_data)
        st.plotly_chart(fig_pie, use_container_width=True)

    with bar_col:
        fig_bar = failure_causes_bar_chart(failure_causes_data)
        st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("View Failure Causes Data"):

        df_causes = pd.DataFrame(failure_causes_data)
        df_causes["percentage"] = round(
            df_causes["count"] / df_causes["count"].sum() * 100, 1
        )
        df_causes = df_causes.rename(columns={
            "cause": "Failure Cause",
            "count": "Count",
            "percentage": "Percentage (%)",
        })

        st.dataframe(
            df_causes,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Failure Causes CSV",
            df_causes.to_csv(index=False),
            "failure_causes.csv",
            "text/csv",
        )

    total_failures_causes = sum(row["count"] for row in failure_causes_data)
    top_cause = failure_causes_data[0] if failure_causes_data else None
    if top_cause:
        top_pct = round(top_cause["count"] / total_failures_causes * 100, 1) if total_failures_causes else 0
        st.warning(
            f"**Top Failure Cause:** {top_cause['cause']} accounts for "
            f"{top_pct}% ({top_cause['count']:,}) of all failures. "
            f"Focus on resolving this to achieve the biggest impact."
        )

else:

    st.info("No failure cause data available.")

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
            use_container_width=True
        )

        with st.expander("View Gateway Data"):

            df = pd.DataFrame(gateway_data)

            st.dataframe(
                df,
                use_container_width=True
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
            use_container_width=True
        )

        with st.expander("View Payment Method Data"):

            df = pd.DataFrame(pm_data)

            st.dataframe(
                df,
                use_container_width=True
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