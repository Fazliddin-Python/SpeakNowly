import logging
import asyncio
from celery_app import celery_app
from tortoise.exceptions import DoesNotExist
from models.users.users import UserActivityLog, User

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.users.activity_tasks.log_user_activity", max_retries=3, default_retry_delay=10)
def log_user_activity(self, user_id: int, action: str):
    """
    Celery task to record user activity logs.
    Uses asyncio event loop; Redis and Tortoise initialized in celery_app.worker_process_init.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_log(user_id, action))
    except Exception as exc:
        logger.exception(f"[CELERY] Failed to log activity {action} for user {user_id}: {exc}")
        raise self.retry(exc=exc)

async def _async_log(user_id: int, action: str):
    """
    Async logic for logging user activity.
    """
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        logger.error(f"[CELERY] User {user_id} not found for activity log")
        return
    await UserActivityLog.create(user=user, action=action)
    logger.info(f"[CELERY] Logged activity '{action}' for user {user_id}")