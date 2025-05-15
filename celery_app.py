# from celery import Celery
# from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_ACCEPT_CONTENT, CELERY_TASK_SERIALIZER, CELERY_RESULT_SERIALIZER, CELERY_TIMEZONE

# celery_app = Celery(
#     "tasks",
#     broker=CELERY_BROKER_URL,
#     backend=CELERY_RESULT_BACKEND,
# )

# celery_app.conf.update(
#     accept_content=CELERY_ACCEPT_CONTENT,
#     task_serializer=CELERY_TASK_SERIALIZER,
#     result_serializer=CELERY_RESULT_SERIALIZER,
#     timezone=CELERY_TIMEZONE,
#     task_routes={
#         "services.email_service.send_email_task": {"queue": "emails"},
#     },
# )
from celery import Celery
from tomlkit import table

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_routes={
        "services.email_service.send_email_task": {"queue": "emails"},
        "tasks.users.activity_tasks.log_user_activity": {"queue": "user_activity"},
    },
)