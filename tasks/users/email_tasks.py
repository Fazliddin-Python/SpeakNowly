from celery_app import celery_app
from services.users.email_service import EmailService

@celery_app.task(name="tasks.users.email_tasks.send_email_task")
async def send_email_task(subject: str, recipients: list[str], body: str = None, html_body: str = None):
    """Send email asynchronously."""
    await EmailService.send_email(subject, recipients, body, html_body)