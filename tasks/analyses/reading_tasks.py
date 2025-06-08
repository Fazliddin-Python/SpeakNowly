import logging
import asyncio
from celery_app import celery_app
from services.analyses.reading_analyse_service import ReadingAnalyseService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.analyses.reading_tasks.analyse_reading_task")
def analyse_reading_task(self, reading_id: int, user_id: int):
    """
    Celery task to trigger ReadingAnalyseService.analyse_reading for a given reading session.
    Uses asyncio event loop to run the async service method.
    Redis and Tortoise are initialized in celery_app.worker_process_init.
    """
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(ReadingAnalyseService.analyse_reading(reading_id, user_id))
        logger.info(f"Reading analysis completed for reading {reading_id}")
    except Exception as exc:
        logger.exception(f"Reading analysis failed for reading {reading_id}: {exc}")
        raise