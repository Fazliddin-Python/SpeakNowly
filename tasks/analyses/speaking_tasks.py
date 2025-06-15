import logging
import asyncio
from celery_app import celery_app
from services.analyses.speaking_analyse_service import SpeakingAnalyseService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.analyses.speaking_tasks.analyse_speaking_task")
def analyse_speaking_task(self, test_id: int):
    """
    Celery task to analyze a speaking test using SpeakingAnalyseService.
    Uses asyncio event loop to run the async service method.
    Redis and Tortoise are initialized in celery_app.worker_process_init.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(SpeakingAnalyseService.analyse(test_id))
        logger.info(f"Speaking analysis completed for test {test_id}")
    except Exception as exc:
        logger.exception(f"Speaking analysis failed for test {test_id}: {exc}")
        raise