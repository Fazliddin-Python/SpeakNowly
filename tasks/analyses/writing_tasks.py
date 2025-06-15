from celery_app import celery_app
from services.analyses import WritingAnalyseService

@celery_app.task(name="tasks.analyses.writing_tasks.analyse_writing_task")
async def analyse_writing_task(test_id: int):
    """Analyse writing test."""
    await WritingAnalyseService.analyse(test_id)
