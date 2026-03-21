"""Async email sender for alert notifications."""

import structlog
from email.message import EmailMessage

from orchestra.config import get_settings

logger = structlog.get_logger("notifications.email")


async def send_alert_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text alert email via SMTP.

    Returns True if sent, False if SMTP is not configured or sending failed.
    """
    settings = get_settings()

    if not settings.has_smtp:
        logger.debug("smtp_not_configured", subject=subject)
        return False

    try:
        import aiosmtplib

        msg = EmailMessage()
        msg["From"] = settings.smtp_from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password.get_secret_value() or None,
            start_tls=True,
        )

        logger.info("alert_email_sent", to=to, subject=subject)
        return True
    except Exception as e:
        logger.warning("alert_email_failed", to=to, subject=subject, error=str(e))
        return False
