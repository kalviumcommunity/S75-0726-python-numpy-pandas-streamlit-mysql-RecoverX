import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from src.payment_queries import (
    create_alert_rule,
    delete_alert_rule,
    get_active_alerts,
    get_alert_rules,
    get_resolved_alerts,
    mark_alert_resolved,
    update_alert_rule,
)
from src.ui_components import (
    render_footer,
    render_header,
    render_sidebar,
    setup_page,
)


def _get_option_index(options, value, fallback=0):
    if value in options:
        return options.index(value)
    return fallback


setup_page("Alerts & Notifications", "🚨")
render_header()
date_range = render_sidebar()

st.subheader("Manage Alert Rules")
st.info(
    """
Create new alert rules, update existing rules, or remove rules that are no longer needed.
"""
)

if st.button("🔄 Refresh Rules"):
    st.rerun()

st.divider()

try:
    alert_rules = get_alert_rules()
except Exception as error:
    st.error(f"Unable to load alert rules from the database: {error}")
    alert_rules = []

default_rule_types = [
    "failure_rate",
    "response_trend",
    "success_rate",
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
    st.dataframe(summary_df, hide_index=True, width="stretch")

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
                st.warning(
                    "This will permanently delete the selected alert rule."
                )
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
st.subheader("Active Alerts & History")

try:
    active_alerts = get_active_alerts() or []
except Exception as error:
    st.error(f"Unable to load active alerts: {error}")
    active_alerts = []

if active_alerts:
    st.subheader("Active Alerts")
    for alert in active_alerts:
        severity = alert.get("severity") or "LOW"
        icon = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴",
        }.get(severity, "⚪")

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {icon} {severity} - {alert['alert_title']}")
                st.write(alert.get("alert_message") or "")
                st.caption(f"Created: {alert.get('created_at') or 'Unknown'}")
            with col2:
                if st.button(
                    "Mark as Resolved",
                    key=f"resolve_alert_{alert['alert_id']}",
                ):
                    try:
                        resolved = mark_alert_resolved(alert["alert_id"])
                        if resolved:
                            st.success("Alert marked as resolved.")
                            st.rerun()
                        else:
                            st.error("Unable to mark the alert as resolved.")
                    except Exception as error:
                        st.error(f"Unable to mark the alert as resolved: {error}")
else:
    st.info("No active alerts to resolve right now.")

st.divider()
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

severity_filter = st.selectbox(
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
            severity=(None if severity_filter == "ALL" else severity_filter),
        )
    except Exception as error:
        st.error(f"Unable to load alert history: {error}")
        resolved_history = pd.DataFrame([])

if resolved_history.empty:
    st.info("No resolved alerts found for the selected filters.")
else:
    display_df = resolved_history[[
        "alert_id",
        "alert_type",
        "severity",
        "message",
        "created_at",
        "resolved_at",
    ]].copy()
    display_df.columns = [
        "Alert ID",
        "Alert Type",
        "Severity",
        "Message",
        "Created At",
        "Resolved At",
    ]
    st.dataframe(display_df, hide_index=True, width="stretch")

render_footer()
