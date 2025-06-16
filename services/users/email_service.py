from fastapi import HTTPException

import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_FROM
)

logger = logging.getLogger("email_service")


class EmailService:
    """Service for sending emails asynchronously."""

    @staticmethod
    async def send_email(
        subject: str,
        recipients: list[str],
        body: str = None,
        html_body: str = None,
    ) -> dict:
        """Send an email with plain text and/or HTML content."""

        # 1. Validate input
        if not body and not html_body:
            raise HTTPException(status_code=400, detail="Email body is required")

        # 2. Prepare message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(recipients)

        if body:
            msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # 3. Send email via SMTP
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
            server.quit()
            return {"status": "sent"}
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            raise HTTPException(status_code=503, detail="Failed to send email")
