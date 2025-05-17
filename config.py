import os
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent

# === Core settings ===
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM", default="HS256")
DEBUG = config("DEBUG", cast=bool, default=False)

# === Allowed hosts / CORS ===
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv(), default="*")
if isinstance(ALLOWED_HOSTS, str):
    ALLOWED_HOSTS = [ALLOWED_HOSTS]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = [
    "accept-language",
    "authorization",
    "content-type",
]

# === Database (Tortoise ORM) ===
DATABASE_URL = config("DATABASE_URL")
DATABASE_CONFIG = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}

# === Email settings ===
EMAIL_BACKEND = config("EMAIL_BACKEND", default="http")  # smtp или http
EMAIL_FROM = config("EMAIL_FROM", default="no-reply@example.com")

# SMTP backend
SMTP_HOST = config("SMTP_HOST", default="")
SMTP_PORT = config("SMTP_PORT", cast=int, default=0)
SMTP_USER = config("SMTP_USER", default="")
SMTP_PASSWORD = config("SMTP_PASSWORD", default="")

# HTTP API (fallback)
EMAIL_PROVIDER_URL = config("EMAIL_PROVIDER_URL", default="")
EMAIL_PROVIDER_APIKEY = config("EMAIL_PROVIDER_APIKEY", default="")

# === JWT settings ===
ACCESS_TOKEN_EXPIRE = timedelta(days=5)
REFRESH_TOKEN_EXPIRE = timedelta(days=90)

# === Celery (Redis) ===
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TASK_ROUTES = {
    "services.users.email_service.send_email_task": {"queue": "emails"},
    "tasks.users.activity_tasks.log_user_activity": {"queue": "user_activity"},
}