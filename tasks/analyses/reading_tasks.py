from celery import shared_task
from services.analyses.reading_analyse_service import ReadingAnalyseService
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task
def analyse_reading_task(reading_id: int):
    """
    Celery task to analyze a reading.
    This function is called by the Celery worker to perform the analysis in the background.
    """
    logger.info("Celery: Start reading analysis for reading %s", reading_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(ReadingAnalyseService.analyse_reading(reading_id))
        logger.info("Celery: Reading analysis for reading %s finished", reading_id)
    except Exception as e:
        logger.error("Celery: Error in reading analysis for reading %s: %s", reading_id, str(e))
    finally:
        loop.close()