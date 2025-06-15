from celery_app import celery_app
from services.analyses import ListeningAnalyseService

@celery_app.task(name="tasks.analyses.listening_tasks.analyse_listening_task")
async def analyse_listening_task(session_id: int):
    """Analyse listening session."""
    await ListeningAnalyseService.analyse(session_id)