from celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def analyse_reading_task(reading_id):
    """
    Celery task to analyze a reading.
    This function is called by the Celery worker to perform the analysis in the background.
    """
    from services.analyses.reading_analyse_service import ReadingAnalyseService
    import asyncio
    logger.info("Celery: Start reading analysis for reading %s", reading_id)
    try:
        asyncio.run(ReadingAnalyseService.analyse_reading(reading_id))
        logger.info("Celery: Reading analysis for reading %s finished", reading_id)
    except Exception as e:
        logger.error("Celery: Error in reading analysis for reading %s: %s", reading_id, str(e))