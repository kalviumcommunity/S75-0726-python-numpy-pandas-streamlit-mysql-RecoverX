import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


def send_test_email(
    to_email: str,
    subject: str,
    body: str,
    smtp_host: str = None,
    smtp_port: int = None,
    smtp_user: str = None,
    smtp_password: str = None,
    smtp_from: str = None,
    use_tls: bool = None,
):
    host = smtp_host or os.getenv("SMTP_HOST", "localhost")
    port = int(smtp_port or os.getenv("SMTP_PORT", "1025"))
    username = smtp_user if smtp_user is not None else os.getenv("SMTP_USER", "")
    password = smtp_password if smtp_password is not None else os.getenv("SMTP_PASSWORD", "")
    from_email = smtp_from or os.getenv("SMTP_FROM", username or "no-reply@recoverx.local")
    tls_setting = use_tls
    if tls_setting is None:
        tls_setting = str(os.getenv("SMTP_USE_TLS", "false")).strip().lower() in {"1", "true", "yes", "y"}

    if not to_email:
        return False, "Recipient email is required."

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject or "RecoverX Test Email"
    msg.set_content(body or "This is a test email from RecoverX.")

    try:
        with smtplib.SMTP(host=host, port=port, timeout=10) as server:
            server.ehlo()
            if tls_setting:
                server.starttls()
                server.ehlo()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)
