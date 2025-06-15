from celery_app import celery_app
from services.analyses import SpeakingAnalyseService

@celery_app.task(name="tasks.analyses.speaking_tasks.analyse_speaking_task")
async def analyse_speaking_task(test_id: int):
    """Analyse speaking test."""
    await SpeakingAnalyseService.analyse(test_id)