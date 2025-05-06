import os
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent

# Core settings
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv(), default="*")

# API keys
OPENAI_API_KEY = config("OPENAI_API_KEY")
PAYMENT_BOT_URL = config("PAYMENT_BOT_URL")
EMAIL_PROVIDER_URL = config("EMAIL_PROVIDER_URL")
EMAIL_PROVIDER_APIKEY = config("EMAIL_PROVIDER_APIKEY")

# Database configuration
DATABASE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": config("DB_HOST"),
                "port": config("DB_PORT", cast=int),
                "user": config("DB_USER"),
                "password": config("DB_PASSWORD"),
                "database": config("DB_NAME"),
            },
        }
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}

# CORS settings
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = [
    "accept-currency",
    "accept-language",
    "authorization",
    "content-type",
]

# JWT settings
JWT_SETTINGS = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# Static and media files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# CKEditor settings
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "imageUpload",
        ],
    },
}

# Celery settings
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Localization
LANGUAGE_CODE = "uz-ru-en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True