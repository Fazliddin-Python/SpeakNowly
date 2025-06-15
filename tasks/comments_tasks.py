import logging
import asyncio
from celery_app import celery_app
from services.users.email_service import send_email_task
from models.comments import Comment
from models.users.users import User

logger = logging.getLogger(__name__)
ADMIN_EMAILS = ["support@speaknowly.com"]

@celery_app.task(bind=True, name="tasks.comments_tasks.notify_admin_about_comment")
def notify_admin_about_comment(self, comment_id: int):
    """
    Celery task to notify admins about a new comment.
    Uses asyncio event loop, Redis and Tortoise initialized in celery_app.worker_process_init.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        user_email, comment_text = loop.run_until_complete(_async_notify_admin(comment_id))
        subject = "New comment on the platform"
        body = f"New comment from {user_email}: {comment_text}"
        html_body = f"<b>New comment from {user_email}:</b><br>{comment_text}"
        send_email_task.delay(subject, ADMIN_EMAILS, body, html_body)
        logger.info(f"[CELERY] Email task sent to admin about comment {comment_id}")
    except Exception as exc:
        logger.exception(f"[CELERY] notify_admin_about_comment failed for {comment_id}: {exc}")
        raise

async def _async_notify_admin(comment_id: int):
    """
    Async logic for notifying admin about a comment.
    """
    comment = await Comment.get(id=comment_id)
    user = await User.get(id=comment.user_id)
    logger.info(f"[CELERY] New comment from user {user.email}: {comment.text}")
    return user.email, comment.text
