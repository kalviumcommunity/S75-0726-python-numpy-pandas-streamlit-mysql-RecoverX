import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from src.payment_queries import (
    create_alert_rule,
    delete_alert_rule,
    get_alert_rules,
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

render_footer()
