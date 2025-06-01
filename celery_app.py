from celery import Celery
from config import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CELERY_ACCEPT_CONTENT,
    CELERY_TASK_SERIALIZER,
    CELERY_RESULT_SERIALIZER,
    CELERY_TIMEZONE,
    CELERY_TASK_ROUTES,
    CELERY_INCLUDE,
)

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=CELERY_INCLUDE,
)

celery_app.conf.update(
    task_routes=CELERY_TASK_ROUTES,
    accept_content=CELERY_ACCEPT_CONTENT,
    task_serializer=CELERY_TASK_SERIALIZER,
    result_serializer=CELERY_RESULT_SERIALIZER,
    timezone=CELERY_TIMEZONE,
)

