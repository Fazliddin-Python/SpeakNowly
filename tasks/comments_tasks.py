from celery_app import celery_app
import logging
import asyncio

from tortoise import Tortoise
from config import DATABASE_CONFIG
from models.comments import Comment
from models.users.users import User
from services.users.email_service import send_email_task

logger = logging.getLogger(__name__)

ADMIN_EMAILS = ["support@speaknowly.com"]

async def _notify_admin_about_comment(comment_id: int):
    await Tortoise.init(config=DATABASE_CONFIG)
    try:
        comment = await Comment.get(id=comment_id)
        user = await User.get(id=comment.user_id)
    except Exception as exc:
        logger.error(f"[CELERY] Error getting comment {comment_id}: {exc}")
        await Tortoise.close_connections()
        return

    logger.info(f"[CELERY] New comment from user {user.email}: {comment.text}")

    subject = "New comment on the platform"
    body = f"New comment from {user.email}: {comment.text}"
    html_body = f"<b>New comment from {user.email}:</b><br>{comment.text}"
    send_email_task.delay(subject, ADMIN_EMAILS, body, html_body)
    logger.info(f"[CELERY] Email task sent to admin about comment {comment_id}")
    await Tortoise.close_connections()

@celery_app.task
def notify_admin_about_comment(comment_id: int):
    asyncio.run(_notify_admin_about_comment(comment_id))