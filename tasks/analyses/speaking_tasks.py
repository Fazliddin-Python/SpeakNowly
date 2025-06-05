from celery_app import celery_app
import logging
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task
def analyse_speaking_task(test_id: int, api_key: str):
    """
    Celery task to analyze a speaking test.
    """
    from services.analyses.speaking_analyse_service import SpeakingAnalyseService

    try:
        asyncio.run(SpeakingAnalyseService.analyse(test_id, api_key))
        logger.info(f"Speaking analysis completed for test {test_id}")
    except Exception as exc:
        logger.error(f"Speaking analysis failed for test {test_id}: {exc}")