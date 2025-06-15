import os
import asyncio
import logging

from celery import Celery
from celery.signals import worker_ready, worker_process_init, worker_process_shutdown
from redis.asyncio import Redis
from tortoise import Tortoise
from config import REDIS_URL, DATABASE_URL

# Set up logger for Celery app
logger = logging.getLogger("celery_app")
logger.setLevel(logging.INFO)

# Create Celery app with Redis as broker and backend
celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.users.activity_tasks",
        "tasks.users.email_tasks",
        "tasks.analyses.listening_tasks",
        "tasks.analyses.reading_tasks",
        "tasks.analyses.speaking_tasks",
        "tasks.analyses.writing_tasks",
        "tasks.tariffs_tasks",
    ],
)

# Celery configuration for routing, serialization, and timezone
celery_app.conf.update(
    task_routes={
        "tasks.users.activity_tasks.log_user_activity": {"queue": "user_activity"},
        "tasks.users.email_tasks.send_email_task": {"queue": "email"},
        "tasks.analyses.listening_tasks.analyse_listening_task": {"queue": "analyses"},
        "tasks.analyses.reading_tasks.analyse_reading_task": {"queue": "analyses"},
        "tasks.analyses.speaking_tasks.analyse_speaking_task": {"queue": "analyses"},
        "tasks.analyses.writing_tasks.analyse_writing_task": {"queue": "analyses"},
        "tasks.tariffs_tasks.check_expired_tariffs": {"queue": "tariffs"},
        "tasks.tariffs_tasks.give_daily_tariff_bonus": {"queue": "tariffs"},
    },
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
)

# Global Redis cache variable for worker processes
cache_redis: Redis

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    # Log when the main Celery process is ready
    logger.info("⏳ Celery main process is ready. Awaiting child worker initialization...")

@worker_process_init.connect
def initialize_worker_process(**kwargs):
    # Initialize Redis and Tortoise ORM for each worker process
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    global cache_redis
    cache_redis = Redis.from_url(REDIS_URL, decode_responses=True)
    loop.run_until_complete(cache_redis.ping())
    logger.info("✅ Worker process: Redis successfully initialized.")
    loop.run_until_complete(
        Tortoise.init(
            db_url=DATABASE_URL,
            modules={
                "models": [
                    "models.users",
                    "models.tests",
                    "models.analyses",
                    "models.comments",
                    "models.notifications",
                    "models.tariffs",
                    "models.transactions",
                    "models.payments",
                    "aerich.models"
                ]
            }
        )
    )
    logger.info("✅ Worker process: Tortoise ORM successfully connected.")

@worker_process_shutdown.connect
def shutdown_worker_process(**kwargs):
    # Gracefully close Redis and Tortoise ORM connections on worker shutdown
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cache_redis.close())
    logger.info("🛑 Worker process: Redis connection closed.")
    loop.run_until_complete(Tortoise.close_connections())
    logger.info("🛑 Worker process: Tortoise ORM connection closed.")
