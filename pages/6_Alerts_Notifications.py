import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import os

import streamlit as st

from src.ui_components import setup_page, render_header, render_sidebar, render_footer
from src.email_service import send_test_email


setup_page("Alerts & Notifications", "📧")
render_header()
render_sidebar()

st.subheader("Email Notification Test Setup")

col1, col2 = st.columns(2)

with col1:
    smtp_host = st.text_input("SMTP Host", value=os.getenv("SMTP_HOST", "localhost"))
    smtp_port = st.number_input("SMTP Port", min_value=1, max_value=65535, value=int(os.getenv("SMTP_PORT", "1025")))
    use_tls = st.checkbox("Use TLS (STARTTLS)", value=str(os.getenv("SMTP_USE_TLS", "false")).strip().lower() in {"1", "true", "yes", "y"})
    smtp_from = st.text_input("From Email", value=os.getenv("SMTP_FROM", ""))

with col2:
    smtp_user = st.text_input("SMTP Username", value=os.getenv("SMTP_USER", ""))
    smtp_password = st.text_input("SMTP Password", value=os.getenv("SMTP_PASSWORD", ""), type="password")
    to_email = st.text_input("To Email", value="")

subject = st.text_input("Subject", value="RecoverX Test Email")
body = st.text_area("Body", value="This is a test email from RecoverX.", height=140)

send_clicked = st.button("Send Test Email")

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

render_footer()
