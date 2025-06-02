import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import HTTPException

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_FROM
)
from celery_app import celery_app

logger = logging.getLogger("email_service")


class EmailService:
    """
    Service for sending emails asynchronously.
    """

    @staticmethod
    async def send_email(
        subject: str,
        recipients: list[str],
        body: str = None,
        html_body: str = None,
    ) -> dict:
        """
        Send an email with plain text and/or HTML content.
        """
        if not body and not html_body:
            raise HTTPException(status_code=400, detail="Email body is required")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(recipients)

        if body:
            msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
            server.quit()
            logger.info(f"Email sent to {recipients} with subject '{subject}'")
            return {"status": "sent"}
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            raise HTTPException(status_code=503, detail="Failed to send email")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self, subject, recipients, body=None, html_body=None):
    """
    Celery task for sending emails asynchronously.
    """
    try:
        return asyncio.run(
            EmailService.send_email(subject, recipients, body, html_body)
        )
    except Exception as exc:
        logger.error(f"Celery email send failed: {exc}")
        raise self.retry(exc=exc)
