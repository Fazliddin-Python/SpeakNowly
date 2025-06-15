import logging
import asyncio
from celery_app import celery_app
from models.notifications import Message

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.notifications_tasks.send_mass_notification")
def send_mass_notification(self, user_ids: list[int], title: str, content: str):
    """
    Celery task to send mass notifications to users.
    Uses asyncio event loop, Redis and Tortoise initialized in celery_app.worker_process_init.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_send_mass_notification(user_ids, title, content))
    except Exception as exc:
        logger.exception(f"[CELERY] send_mass_notification failed: {exc}")
        raise

async def _async_send_mass_notification(user_ids: list[int], title: str, content: str):
    """
    Async logic for sending mass notifications.
    """
    for uid in user_ids:
        await Message.create(user_id=uid, title=title, content=content)
    logger.info(f"[CELERY] Mass notification sent to {len(user_ids)} users")
