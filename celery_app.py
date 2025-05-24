from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "tasks.users.activity_tasks",
        "services.users.email_service",
        "tasks.analyses.listening_tasks",
        "tasks.analyses.reading_tasks",
        "tasks.analyses.speaking_tasks",
        "tasks.analyses.writing_tasks",
    ],
)

celery_app.conf.update(
    task_routes={
        "services.users.email_service.send_email_task": {"queue": "emails"},
        "tasks.analyses.listening_tasks.analyse_listening_task": {"queue": "analyses"},
        "tasks.analyses.reading_tasks.analyse_reading_task": {"queue": "analyses"},
        "tasks.analyses.speaking_tasks.analyse_speaking_task": {"queue": "analyses"},
        "tasks.analyses.writing_tasks.analyse_writing_task": {"queue": "analyses"},
        "tasks.users.activity_tasks.log_user_activity": {"queue": "user_activity"},
    }
)

