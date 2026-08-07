
import os
import smtplib
import logging
from email.message import EmailMessage
from typing import Iterable, List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ALERT_EMAIL_RECIPIENTS_ENV = "ALERT_EMAIL_RECIPIENTS"
SMTP_HOST_ENV = "SMTP_HOST"
SMTP_PORT_ENV = "SMTP_PORT"
SMTP_USER_ENV = "SMTP_USER"
SMTP_PASSWORD_ENV = "SMTP_PASSWORD"
SMTP_FROM_ENV = "SMTP_FROM"


def get_alert_email_recipients() -> List[str]:
    """
    Return the list of admin recipients from ALERT_EMAIL_RECIPIENTS.

    Accepts either a comma-separated or a semicolon-separated string.
    When the env var is empty, returns an empty list.
    """
    raw = os.getenv(ALERT_EMAIL_RECIPIENTS_ENV, "") or ""
    for sep in [",", ";"]:
        if sep in raw:
            return [r.strip() for r in raw.split(sep) if r.strip()]
    return [raw.strip()] if raw.strip() else []


def _format_alert_lines(alerts: Iterable[dict]) -> str:
    lines = []
    for a in alerts:
        sev = str(a.get("severity", "UNKNOWN")).upper()
        name = a.get("name") or a.get("rule_id") or "Alert"
        msg = a.get("message") or ""
        lines.append(f"- [{sev}] {name}: {msg}")
    return "\n".join(lines) if lines else "(no details)"


def send_test_email(
    subject: str = "RecoverX Alert",
    body: Optional[str] = None,
    alerts: Optional[List[dict]] = None,
    recipients: Optional[List[str]] = None,
) -> bool:
    """
    Send a plain-text email via SMTP using configuration from env.

    Env vars used:
      - SMTP_HOST (default: empty -> no real delivery, logs only)
      - SMTP_PORT (default: 587)
      - SMTP_USER, SMTP_PASSWORD (optional)
      - SMTP_FROM (default: SMTP_USER or 'alerts@recoverx.local')

    If SMTP_HOST is not configured (the default for dev), the call
    returns True after logging the email details so the feature can be
    demoed without a live server. Recipients default to
    ALERT_EMAIL_RECIPIENTS from .env.

    Pass either a raw body string OR a list of alert dicts to have the
    body auto-rendered from the alert list.
    """
    recipients = recipients or get_alert_email_recipients()
    if not recipients:
        logger.info("No alert email recipients configured; skipping send.")
        return False

    if body is None:
        intro = "The following RecoverX alerts were generated:\n\n"
        body = intro + _format_alert_lines(alerts or [])

    smtp_host = os.getenv(SMTP_HOST_ENV, "") or ""
    smtp_port = int(os.getenv(SMTP_PORT_ENV, "587") or "587")
    smtp_user = os.getenv(SMTP_USER_ENV, "") or ""
    smtp_password = os.getenv(SMTP_PASSWORD_ENV, "") or ""
    smtp_from = (
        os.getenv(SMTP_FROM_ENV, "")
        or smtp_user
        or "alerts@recoverx.local"
    )

    logger.info(
        "ALERT EMAIL TO=%s SUBJECT=%s BODY_PREVIEW=%s",
        ", ".join(recipients),
        subject,
        body[:120],
    )

    if not smtp_host:
        logger.warning(
            "SMTP_HOST not configured; email not actually delivered. "
            "Logged only."
        )
        return True

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as s:
            s.ehlo()
            if smtp_user and smtp_password:
                try:
                    s.starttls()
                    s.ehlo()
                except smtplib.SMTPException:
                    pass
                s.login(smtp_user, smtp_password)
            s.send_message(msg)
        return True
    except Exception as e:  # pragma: no cover - depends on live SMTP
        logger.error("Failed to send alert email: %s", e)
        return False
