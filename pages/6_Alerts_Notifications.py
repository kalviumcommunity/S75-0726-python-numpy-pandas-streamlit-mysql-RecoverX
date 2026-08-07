import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import os
import pandas as pd
import streamlit as st

from src.charts import alert_severity_chart
from src.email_service import send_test_email
from src.payment_queries import (
    create_alert_rule,
    delete_alert_rule,
    get_active_alerts,
    get_alert_rules,
    get_resolved_alerts,
    generate_alerts_from_rules,
    mark_alert_resolved,
    update_alert_rule,
)
from src.ui_components import setup_page, render_header, render_sidebar, render_footer


get_active_alerts = st.cache_data(show_spinner=False, ttl=300)(get_active_alerts)
get_alert_rules = st.cache_data(show_spinner=False, ttl=300)(get_alert_rules)
get_resolved_alerts = st.cache_data(show_spinner=False, ttl=300)(get_resolved_alerts)


setup_page("Alerts & Notifications", "🚨")
render_header()
date_range = render_sidebar()

st.subheader("Alerts & Notifications")
st.info(
    """
Monitor payment failures, retry issues and gateway problems.
Create rules, trigger real-time alert generation, and resolve incidents.
"""
)

top_action_col1, top_action_col2, top_action_col3 = st.columns(3)
with top_action_col1:
    if st.button("🔄 Refresh Alerts"):
        refresh_sd = (
            pd.Timestamp(date_range[0]).strftime("%Y-%m-%d 00:00:00")
            if isinstance(date_range, tuple) and len(date_range) == 2 and date_range[0]
            else None
        )
        refresh_ed = (
            pd.Timestamp(date_range[1]).strftime("%Y-%m-%d 23:59:59")
            if isinstance(date_range, tuple) and len(date_range) == 2 and date_range[1]
            else None
        )
        with st.spinner("Refreshing alerts and rerunning rules..."):
            try:
                created = generate_alerts_from_rules(
                    start_date=refresh_sd,
                    end_date=refresh_ed,
                )
                if created:
                    st.success(f"Refreshed — {len(created)} new alert(s) triggered.")
                else:
                    st.info("Refreshed — no new alerts triggered by rules.")
            except Exception as err:
                st.warning(f"Rules could not be re-evaluated: {err}")
        st.rerun()
with top_action_col2:
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
    if st.button("⚡ Generate Alerts Now"):
        with st.spinner("Evaluating alert rules..."):
            created = generate_alerts_from_rules(
                start_date=start_date_value,
                end_date=end_date_value,
            )
        if created:
            st.success(f"Generated {len(created)} new alert(s) based on active rules.")
        else:
            st.info("No new alerts were triggered by the current rules.")
        st.rerun()
with top_action_col3:
    with st.expander("📧 Email Test / Configuration", expanded=False):
        st.markdown("Configure and send a test email via your SMTP server.")
        smtp_col1, smtp_col2 = st.columns(2)
        with smtp_col1:
            smtp_host = st.text_input(
                "SMTP Host",
                value=os.getenv("SMTP_HOST", "localhost"),
                key="smtp_host_alerts",
            )
            smtp_port = st.number_input(
                "SMTP Port",
                min_value=1,
                max_value=65535,
                value=int(os.getenv("SMTP_PORT", "1025")),
                key="smtp_port_alerts",
            )
            use_tls = st.checkbox(
                "Use TLS (STARTTLS)",
                value=str(os.getenv("SMTP_USE_TLS", "false")).strip().lower()
                in {"1", "true", "yes", "y"},
                key="smtp_tls_alerts",
            )
            smtp_from = st.text_input(
                "From Email",
                value=os.getenv("SMTP_FROM", ""),
                key="smtp_from_alerts",
            )
        with smtp_col2:
            smtp_user = st.text_input(
                "SMTP Username",
                value=os.getenv("SMTP_USER", ""),
                key="smtp_user_alerts",
            )
            smtp_password = st.text_input(
                "SMTP Password",
                value=os.getenv("SMTP_PASSWORD", ""),
                type="password",
                key="smtp_password_alerts",
            )
            to_email = st.text_input("To Email", value="", key="smtp_to_alerts")
        subject = st.text_input("Subject", value="RecoverX Test Email", key="smtp_subject_alerts")
        body = st.text_area(
            "Body",
            value="This is a test email from RecoverX.",
            height=120,
            key="smtp_body_alerts",
        )
        send_clicked = st.button("Send Test Email", key="smtp_send_btn")
        if send_clicked:
            ok, error = send_test_email(
                to_email=to_email.strip(),
                subject=subject,
                body=body,
                smtp_host=smtp_host.strip(),
                smtp_port=int(smtp_port),
                smtp_user=smtp_user.strip(),
                smtp_password=smtp_password,
                smtp_from=smtp_from.strip() if smtp_from else None,
                use_tls=use_tls,
            )
            if ok:
                st.success("Test email sent successfully.")
            else:
                st.error(f"Failed to send test email: {error}")

st.divider()


def _get_option_index(options, value, fallback=0):
    if value in options:
        return options.index(value)
    return fallback


# =========================================================
# KPI Metrics
# =========================================================

try:
    active_alerts = get_active_alerts() or []
except Exception as error:
    st.error(f"Unable to load active alerts: {error}")
    active_alerts = []

df_active = pd.DataFrame(active_alerts)

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

total_alerts = len(df_active)
critical = len(df_active[df_active["severity"] == "CRITICAL"]) if total_alerts else 0
high = len(df_active[df_active["severity"] == "HIGH"]) if total_alerts else 0
medium = len(df_active[df_active["severity"] == "MEDIUM"]) if total_alerts else 0
low = len(df_active[df_active["severity"] == "LOW"]) if total_alerts else 0

kpi_col1.metric("Active Alerts", total_alerts)
kpi_col2.metric("Critical", critical)
kpi_col3.metric("High", high)
kpi_col4.metric("Medium", medium)
kpi_col5.metric("Low", low)

st.divider()

# =========================================================
# Severity Chart
# =========================================================

if not df_active.empty:
    severity_counts = (
        df_active.groupby("severity")
        .size()
        .reset_index(name="count")
        .to_dict("records")
    )
    fig = alert_severity_chart(severity_counts)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active alerts available yet — click 'Generate Alerts Now' to run rules.")

st.divider()

# =========================================================
# Alert Rule Management
# =========================================================

st.subheader("Manage Alert Rules")

try:
    alert_rules = get_alert_rules()
except Exception as error:
    st.error(f"Unable to load alert rules from the database: {error}")
    alert_rules = []

default_rule_types = [
    "failure_rate",
    "response_trend",
    "success_rate",
    "revenue_loss",
]
rule_type_options = sorted(
    set(default_rule_types + [rule["rule_type"] for rule in alert_rules])
)
condition_options = [">", ">=", "<", "<=", "="]

with st.expander("Create Alert Rule", expanded=True):
    with st.form("create_alert_rule_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_rule_name = st.text_input(
                "Rule Name",
                placeholder="Enter alert rule name",
            )
            new_rule_type = st.selectbox(
                "Rule Type",
                options=rule_type_options,
                index=0,
                help=(
                    "failure_rate = % failure vs total | "
                    "success_rate = % success vs total | "
                    "response_trend = share of top failed response code % | "
                    "revenue_loss = $ (recoverable + permanently lost)"
                ),
            )
            new_threshold_value = st.number_input(
                "Threshold Value",
                min_value=0.0,
                step=0.01,
                format="%.2f",
            )
        with col2:
            new_threshold_condition = st.selectbox(
                "Threshold Condition",
                options=condition_options,
                index=0,
            )
            new_is_active = st.toggle(
                "Rule Active",
                value=True,
            )
        create_submitted = st.form_submit_button("Create Rule")
    if create_submitted:
        if not new_rule_name.strip():
            st.error("Rule name is required.")
        else:
            created = create_alert_rule(
                rule_name=new_rule_name.strip(),
                rule_type=new_rule_type,
                threshold_value=float(new_threshold_value),
                threshold_condition=new_threshold_condition,
                is_active=new_is_active,
            )
            if created:
                st.success("Alert rule created successfully.")
                st.rerun()
            else:
                st.error("Unable to create the alert rule.")

st.divider()

st.subheader("Existing Alert Rules")

if alert_rules:
    summary_df = pd.DataFrame(
        [
            {
                "Rule ID": rule["rule_id"],
                "Rule Name": rule["rule_name"],
                "Rule Type": rule["rule_type"],
                "Condition": rule["threshold_condition"],
                "Threshold": rule["threshold_value"],
                "Status": "Active" if rule["is_active"] else "Inactive",
            }
            for rule in alert_rules
        ]
    )
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    st.divider()

    for rule in alert_rules:
        status_label = "Active" if rule["is_active"] else "Inactive"
        with st.expander(
            f"Rule #{rule['rule_id']} - {rule['rule_name']} ({status_label})"
        ):
            with st.form(f"edit_alert_rule_{rule['rule_id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    edited_rule_name = st.text_input(
                        "Rule Name",
                        value=rule["rule_name"],
                        key=f"rule_name_{rule['rule_id']}",
                    )
                    edited_rule_type = st.selectbox(
                        "Rule Type",
                        options=rule_type_options,
                        index=_get_option_index(
                            rule_type_options,
                            rule["rule_type"],
                        ),
                        key=f"rule_type_{rule['rule_id']}",
                    )
                    edited_threshold_value = st.number_input(
                        "Threshold Value",
                        min_value=0.0,
                        value=float(rule["threshold_value"]),
                        step=0.01,
                        format="%.2f",
                        key=f"threshold_value_{rule['rule_id']}",
                    )
                with col2:
                    edited_threshold_condition = st.selectbox(
                        "Threshold Condition",
                        options=condition_options,
                        index=_get_option_index(
                            condition_options,
                            rule["threshold_condition"],
                        ),
                        key=f"threshold_condition_{rule['rule_id']}",
                    )
                    edited_is_active = st.toggle(
                        "Rule Active",
                        value=rule["is_active"],
                        key=f"is_active_{rule['rule_id']}",
                    )
                save_changes = st.form_submit_button("Save Changes")
            if save_changes:
                if not edited_rule_name.strip():
                    st.error("Rule name is required.")
                else:
                    updated = update_alert_rule(
                        rule_id=rule["rule_id"],
                        rule_name=edited_rule_name.strip(),
                        rule_type=edited_rule_type,
                        threshold_value=float(edited_threshold_value),
                        threshold_condition=edited_threshold_condition,
                        is_active=edited_is_active,
                    )
                    if updated:
                        st.success("Alert rule updated successfully.")
                        st.rerun()
                    else:
                        st.error("Unable to update the alert rule.")

            delete_state_key = "confirm_delete_rule_id"
            if st.session_state.get(delete_state_key) == rule["rule_id"]:
                st.warning("This will permanently delete the selected alert rule.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(
                        "Confirm Delete",
                        key=f"confirm_delete_{rule['rule_id']}",
                    ):
                        deleted = delete_alert_rule(rule["rule_id"])
                        if deleted:
                            st.session_state.pop(delete_state_key, None)
                            st.success("Alert rule deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Unable to delete the alert rule.")
                with c2:
                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_{rule['rule_id']}",
                    ):
                        st.session_state.pop(delete_state_key, None)
                        st.rerun()
            else:
                if st.button(
                    "Delete Rule",
                    key=f"delete_rule_{rule['rule_id']}",
                ):
                    st.session_state[delete_state_key] = rule["rule_id"]
                    st.rerun()
else:
    st.info("No alert rules available yet.")

st.divider()

# =========================================================
# Active Alerts
# =========================================================

st.subheader("Active Alerts")

severity_filter = st.selectbox(
    "Filter by Severity",
    ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
    key="active_severity_filter",
)

if severity_filter != "ALL":
    df_display = df_active[df_active["severity"] == severity_filter].copy()
else:
    df_display = df_active.copy()

severity_colors = {
    "LOW": "🟢",
    "MEDIUM": "🟡",
    "HIGH": "🟠",
    "CRITICAL": "🔴",
}

if df_display.empty:
    st.info("No active alerts match the selected filter.")
else:
    for _, row in df_display.iterrows():
        icon = severity_colors.get(row["severity"], "⚪")
        with st.container(border=True):
            st.markdown(f"### {icon} {row['severity']} - {row['alert_title']}")
            st.write(row.get("alert_message") or "")
            btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 2])
            with btn_col1:
                st.caption(f"Created: {row.get('created_at') or 'Unknown'}")
            with btn_col2:
                if st.button(
                    "Resolve",
                    key=f"resolve_alert_{row['alert_id']}",
                    type="primary",
                ):
                    try:
                        resolved = mark_alert_resolved(row["alert_id"])
                        if resolved:
                            st.success("Alert marked as resolved.")
                            st.rerun()
                        else:
                            st.error("Unable to mark the alert as resolved.")
                    except Exception as error:
                        st.error(f"Unable to mark the alert as resolved: {error}")
            with btn_col3:
                if st.button(
                    "Send Email",
                    key=f"email_alert_{row['alert_id']}",
                ):
                    recipient = (
                        st.session_state.get("smtp_to_alerts") if False else ""
                    )
                    default_to = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")[0]
                    if not default_to:
                        st.warning(
                            "No default recipient set. Add ALERT_EMAIL_RECIPIENTS to .env or use the Email Test expander to fill a 'To Email' first."
                        )
                    else:
                        with st.spinner(f"Sending alert email to {default_to}..."):
                            ok, err = send_test_email(
                                to_email=default_to.strip(),
                                subject=f"[RecoverX][{row['severity']}] {row['alert_title']}",
                                body=(
                                    f"Alert ID: {row['alert_id']}\n"
                                    f"Severity: {row['severity']}\n"
                                    f"Created: {row.get('created_at') or 'Unknown'}\n"
                                    f"Message:\n{row.get('alert_message') or ''}"
                                ),
                            )
                            if ok:
                                st.success("Alert email dispatched.")
                            else:
                                st.error(f"Could not send email: {err}")

    st.divider()
    st.subheader("Active Alerts Table")
    st.dataframe(df_display, hide_index=True, use_container_width=True)

    st.divider()
    csv = df_display.to_csv(index=False)
    st.download_button(
        "📥 Download Active Alerts CSV",
        csv,
        "active_alerts.csv",
        "text/csv",
    )

st.divider()

# =========================================================
# Alert History (Resolved)
# =========================================================

st.subheader("Alert History")

history_col1, history_col2 = st.columns(2)
with history_col1:
    history_start = st.date_input(
        "Start Date",
        value=None,
        key="alert_history_start",
    )
with history_col2:
    history_end = st.date_input(
        "End Date",
        value=None,
        key="alert_history_end",
    )

history_severity = st.selectbox(
    "Severity",
    ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
    key="alert_history_severity",
)

if history_start and history_end and history_start > history_end:
    st.error("The start date must be before or equal to the end date.")
    resolved_history = pd.DataFrame([])
else:
    try:
        start_date_value = (
            pd.Timestamp(history_start).strftime("%Y-%m-%d 00:00:00")
            if history_start is not None
            else None
        )
        end_date_value = (
            pd.Timestamp(history_end).strftime("%Y-%m-%d 23:59:59")
            if history_end is not None
            else None
        )
        resolved_history = get_resolved_alerts(
            start_date=start_date_value,
            end_date=end_date_value,
            severity=(None if history_severity == "ALL" else history_severity),
        )
    except Exception as error:
        st.error(f"Unable to load alert history: {error}")
        resolved_history = pd.DataFrame([])

if resolved_history.empty:
    st.info("No resolved alerts found for the selected filters.")
else:
    display_df = resolved_history[
        [
            "alert_id",
            "alert_type",
            "severity",
            "message",
            "created_at",
            "resolved_at",
        ]
    ].copy()
    display_df.columns = [
        "Alert ID",
        "Alert Type",
        "Severity",
        "Message",
        "Created At",
        "Resolved At",
    ]
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    csv_hist = display_df.to_csv(index=False)
    st.download_button(
        "📥 Download Alert History CSV",
        csv_hist,
        "alert_history.csv",
        "text/csv",
    )

st.divider()
render_footer()
