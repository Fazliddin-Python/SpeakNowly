from celery import shared_task
from services.analyses.listening_analyse_service import ListeningAnalyseService
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task
def analyse_listening_task(test_id: int):
    """
    Celery task to analyze a listening test.
    This function is called by the Celery worker to perform the analysis in the background.
    """
    logger.info("Celery: Start listening analysis for test %s", test_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(ListeningAnalyseService.analyse(test_id))
        logger.info("Celery: Listening analysis for test %s finished", test_id)
    except Exception as e:
        logger.error("Celery: Error in listening analysis for test %s: %s", test_id, str(e))
    finally:
        loop.close()