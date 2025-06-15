import logging
import asyncio
from celery_app import celery_app
from services.users.email_service import EmailService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.users.email_tasks.send_email_async", max_retries=3, default_retry_delay=10)
def send_email_async(self, subject: str, recipients: list[str], body: str = None, html_body: str = None):
    """
    Celery task to send emails asynchronously.
    Uses asyncio event loop, Redis and Tortoise initialized in celery_app.worker_process_init.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            EmailService.send_email(subject, recipients, body, html_body)
        )
        logger.info(f"[CELERY] Email sent to {recipients} with subject '{subject}'")
    except Exception as exc:
        logger.exception(f"[CELERY] send_email_async failed: {exc}")
        raise self.retry(exc=exc)