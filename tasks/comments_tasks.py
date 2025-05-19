from celery_app import celery_app
import logging

from models.comments import Comment
from models.users.users import User
from services.users.email_service import send_email_task

logger = logging.getLogger(__name__)

ADMIN_EMAILS = ["support@speaknowly.com"]

@celery_app.task
def notify_admin_about_comment(comment_id: int):
    try:
        comment = Comment.get(id=comment_id)
        user = User.get(id=comment.user_id)
    except Exception as exc:
        logger.error(f"[CELERY] Error getting comment {comment_id}: {exc}")
        return

    logger.info(f"[CELERY] New comment from user {user.email}: {comment.text}")

    subject = "New comment on the platform"
    # You can pass comment.text as code, or add a separate parameter
    send_email_task.delay(
        subject,
        ADMIN_EMAILS,
        "comment_notification",
        comment.text
    )
    logger.info(f"[CELERY] Email task sent to admin about comment {comment_id}")