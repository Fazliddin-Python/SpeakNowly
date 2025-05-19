from celery_app import celery_app
from models.notifications import Message

@celery_app.task
async def send_mass_notification(user_ids: list[int], title: str, content: str):
    for user_id in user_ids:
        await Message.create(user_id=user_id, title=title, content=content)