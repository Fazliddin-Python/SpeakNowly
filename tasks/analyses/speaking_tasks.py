from celery import shared_task
from services.analyses.speaking_analyse_service import SpeakingAnalyseService
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task
def analyse_speaking_task(test_id: int, api_key: str):
    """
    Celery task to analyze a speaking test.
    This function is called by the Celery worker to perform the analysis in the background.
    """
    logger.info("Celery: Start speaking analysis for test %s", test_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(SpeakingAnalyseService.analyse(test_id, api_key))
        logger.info("Celery: Speaking analysis for test %s finished", test_id)
    except Exception as e:
        logger.error("Celery: Error in speaking analysis for test %s: %s", test_id, str(e))
    finally:
        loop.close()