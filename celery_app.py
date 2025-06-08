import os
import asyncio
import logging

from celery import Celery
from celery.signals import worker_ready, worker_process_init, worker_process_shutdown
from redis.asyncio import Redis
from tortoise import Tortoise

from config import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CELERY_ACCEPT_CONTENT,
    CELERY_TASK_SERIALIZER,
    CELERY_RESULT_SERIALIZER,
    CELERY_TIMEZONE,
    CELERY_TASK_ROUTES,
    CELERY_INCLUDE,
    REDIS_URL,
    DATABASE_URL,
)

# -----------------------------------------------------------------------------
# Logger Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger("celery_app")
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------------
# 1) Celery Application Initialization
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 2) Global Variables for Redis and Tortoise ORM
# -----------------------------------------------------------------------------
cache_redis: Redis

# -----------------------------------------------------------------------------
# 3) Log When Main Celery Worker is Ready
# -----------------------------------------------------------------------------
@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    logger.info("⏳ Celery main process is ready. Awaiting child worker initialization...")

# -----------------------------------------------------------------------------
# 4) Initialize Redis and Tortoise ORM in Each Worker Process
# -----------------------------------------------------------------------------
@worker_process_init.connect
def initialize_worker_process(**kwargs):
    # 4.1) Set up a new asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 4.2) Initialize Redis client
    global cache_redis
    cache_redis = Redis.from_url(REDIS_URL, decode_responses=True)
    loop.run_until_complete(cache_redis.ping())
    logger.info("✅ Worker process: Redis successfully initialized.")

    # 4.3) Initialize Tortoise ORM
    loop.run_until_complete(
        Tortoise.init(
            db_url=DATABASE_URL,
            modules={
                "models": [
                    "models.users.users",
                    "models.users",
                    "models.tests",
                    "models.tests.listening",
                    "models.tests.reading",
                    "models.tests.speaking",
                    "models.tests.writing",
                    "models.analyses",
                    "models.comments",
                    "models.notifications",
                    "models.tariffs",
                    "models.payments",
                    "models.transactions",
                    "aerich.models",
                ]
            }
        )
    )
    logger.info("✅ Worker process: Tortoise ORM successfully connected.")

# -----------------------------------------------------------------------------
# 5) Cleanup When a Worker Process Shuts Down
# -----------------------------------------------------------------------------
@worker_process_shutdown.connect
def shutdown_worker_process(**kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cache_redis.close())
    logger.info("🛑 Worker process: Redis connection closed.")
    loop.run_until_complete(Tortoise.close_connections())
    logger.info("🛑 Worker process: Tortoise ORM connection closed.")
