from celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def analyse_listening_task(session_id):
    from services.analyses.listening_analyse_service import ListeningAnalyseService
    import asyncio
    asyncio.run(ListeningAnalyseService.analyse(session_id))

def trigger_analysis(session_id):
    from tasks.analyses.listening_tasks import analyse_listening_task
    analyse_listening_task.delay(session_id)