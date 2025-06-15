import logging
import asyncio
from celery_app import celery_app
from services.analyses.writing_analyse_service import WritingAnalyseService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.analyses.writing_tasks.analyse_writing_task")
def analyse_writing_task(self, test_id: int, api_key: str):
    """
    Celery task to analyze a writing test using WritingAnalyseService.
    Uses asyncio event loop to run the async service method.
    Redis and Tortoise are initialized in celery_app.worker_process_init.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(WritingAnalyseService.analyse(test_id, api_key))
        logger.info(f"Writing analysis completed for test {test_id}")
    except Exception as exc:
        logger.exception(f"Writing analysis failed for test {test_id}: {exc}")
        raise
