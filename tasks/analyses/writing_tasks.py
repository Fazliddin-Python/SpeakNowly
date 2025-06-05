from celery_app import celery_app
import logging
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task
def analyse_writing_task(test_id: int, api_key: str):
    """
    Celery task to analyze a writing test.
    """
    from services.analyses.writing_analyse_service import WritingAnalyseService

    try:
        asyncio.run(WritingAnalyseService.analyse(test_id, api_key))
        logger.info(f"Writing analysis completed for test {test_id}")
    except Exception as exc:
        logger.error(f"Writing analysis failed for test {test_id}: {exc}")