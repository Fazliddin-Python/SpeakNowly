from celery_app import celery_app
from tortoise.exceptions import DoesNotExist
from models.users.users import UserActivityLog, User

@celery_app.task(name="tasks.users.activity_tasks.log_user_activity")
async def log_user_activity(user_id: int, action: str):
    """Log user activity (async)."""
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        return
    await UserActivityLog.create(user=user, action=action)