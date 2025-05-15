import asyncio
import logging

from celery_app import celery_app
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist

from config import DATABASE_CONFIG
from models.users.users import UserActivityLog, User

logger = logging.getLogger(__name__)

async def _init_db():
    """
    Initialize Tortoise ORM using the same DATABASE_CONFIG as FastAPI.
    """
    await Tortoise.init(config=DATABASE_CONFIG)
    # If you have generated schemas manually, не вызывайте generate_schemas() в продакшене.

async def _close_db():
    """
    Close all connections after the task.
    """
    await Tortoise.close_connections()

async def _log_activity(user_id: int, action: str):
    """
    Async function to record user activity in the database.
    """
    await _init_db()
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        logger.error("User %s not found for activity log", user_id)
    else:
        await UserActivityLog.create(user=user, action=action)
        logger.info("Logged activity '%s' for user %s", action, user_id)
    finally:
        await _close_db()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def log_user_activity(self, user_id: int, action: str):
    """
    Celery task to record user activity logs.
    """
    try:
        asyncio.run(_log_activity(user_id, action))
    except Exception as exc:
        logger.exception("Failed to log activity %s for user %s", action, user_id)
        raise self.retry(exc=exc)
