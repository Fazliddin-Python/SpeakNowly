from celery_app import celery_app
import logging
import asyncio

from tortoise import Tortoise
from config import DATABASE_CONFIG
from models.notifications import Message

logger = logging.getLogger(__name__)

async def _send_mass_notification(user_ids: list[int], title: str, content: str):
    await Tortoise.init(config=DATABASE_CONFIG)
    try:
        for user_id in user_ids:
            await Message.create(user_id=user_id, title=title, content=content)
        logger.info("[CELERY] Mass notification sent to %d users", len(user_ids))
    except Exception as exc:
        logger.error(f"[CELERY] Error sending mass notification: {exc}")
    finally:
        await Tortoise.close_connections()

@celery_app.task
def send_mass_notification(user_ids: list[int], title: str, content: str):
    """
    Celery task to send mass notifications to users.
    """
    asyncio.run(_send_mass_notification(user_ids, title, content))