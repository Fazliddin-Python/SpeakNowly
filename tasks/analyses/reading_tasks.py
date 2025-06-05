from celery_app import celery_app
import logging
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task
def analyse_reading_task(reading_id: int):
    """
    Celery task to trigger ReadingAnalyseService.analyse_reading for a given reading session.
    """
    from services.analyses.reading_analyse_service import ReadingAnalyseService

    try:
        asyncio.run(ReadingAnalyseService.analyse_reading(reading_id))
        logger.info(f"Reading analysis completed for reading {reading_id}")
    except Exception as exc:
        logger.error(f"Reading analysis failed for reading {reading_id}: {exc}")