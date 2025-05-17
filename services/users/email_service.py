import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Template
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
    Service for sending verification emails asynchronously.
    """

    @staticmethod
    async def send_email(
        subject: str,
        recipients: list[str],
        verification_type: str,
        code: str
    ) -> dict:
        """
        1. Generate email content (HTML and plain text) using Jinja2 template.
        2. Create a multipart email message.
        3. Connect to the SMTP server and send the email.
        4. Return status or raise HTTPException on error.
        """
        # 1. Generate email content
        template_str = (
            "<html><body>"
            "<h3>{verification_type}</h3>"
            "<p>Your verification code is: <strong>{code}</strong></p>"
            "</body></html>"
        )
        html_content = template_str.format(
            verification_type=verification_type,
            code=code
        )
        text_content = f"{verification_type}\n\nYour verification code is: {code}"

        # 2. Create multipart message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        try:
            # 3. Connect to SMTP server and send email (blocking! use Celery in production)
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
            server.quit()
            logger.info(f"Verification email sent to {recipients}")
            return {"status": "sent"}
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            raise HTTPException(status_code=503, detail="Failed to send verification email")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self, subject, recipients, verification_type, code):
    """
    Celery task for sending emails asynchronously.
    """
    try:
        return asyncio.run(
            EmailService.send_email(subject, recipients, verification_type, code)
        )
    except Exception as exc:
        logger.error(f"Celery email send failed: {exc}")
        raise self.retry(exc=exc)
