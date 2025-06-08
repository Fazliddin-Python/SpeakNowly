import logging
import asyncio
from celery_app import celery_app
from services.analyses.listening_analyse_service import ListeningAnalyseService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.analyses.listening_tasks.analyse_listening_task")
def analyse_listening_task(self, session_id: int):
    """
    Celery task to trigger ListeningAnalyseService.analyse for a given session.
    Uses asyncio event loop to run the async service method.
    Redis and Tortoise are initialized in celery_app.worker_process_init.
    """
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(ListeningAnalyseService.analyse(session_id))
        logger.info(f"Listening analysis completed for session {session_id}")
    except Exception as exc:
        logger.exception(f"Listening analysis failed for session {session_id}: {exc}")
        raise