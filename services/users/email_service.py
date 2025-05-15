import asyncio
import httpx
from jinja2 import Template
from fastapi import HTTPException

from config import EMAIL_PROVIDER_APIKEY, EMAIL_PROVIDER_URL, EMAIL_FROM
from celery_app import celery_app


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
        Send an email with the given verification code.
        """
        template_str = (
            "<html><body>"
            "<h3>{{ verification_type }}</h3>"
            "<p>Your verification code is: <strong>{{ code }}</strong></p>"
            "</body></html>"
        )
        html_content = Template(template_str).render(
            verification_type=verification_type,
            code=code
        )

        headers = {"X-API-KEY": EMAIL_PROVIDER_APIKEY}
        payload = {
            "to_email": recipients,
            "subject": subject,
            "message": html_content,
            "from_email": EMAIL_FROM,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    EMAIL_PROVIDER_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Email service unavailable: {e}")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self, subject, recipients, verification_type, code):
    """
    Synchronous Celery task that calls the asynchronous email sending function.
    """
    try:
        return asyncio.run(
            EmailService.send_email(subject, recipients, verification_type, code)
        )
    except Exception as exc:
        raise self.retry(exc=exc)
