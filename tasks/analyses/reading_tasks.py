from celery_app import celery_app
from services.analyses import ReadingAnalyseService

@celery_app.task(name="tasks.analyses.reading_tasks.analyse_reading_task")
async def analyse_reading_task(reading_id: int, user_id: int):
    """Analyse reading session."""
    await ReadingAnalyseService.analyse(reading_id, user_id)