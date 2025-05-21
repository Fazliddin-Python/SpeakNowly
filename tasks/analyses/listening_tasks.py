from celery import shared_task
from services.analyses.listening_analyse_service import ListeningAnalyseService
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task
def analyse_listening_session_task(session_id: int):
    """
    Celery task to analyse a listening session asynchronously.
    """
    logger.info("Celery: Start listening analysis for session %s", session_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(ListeningAnalyseService.analyse_session(session_id))
        logger.info("Celery: Listening analysis for session %s finished", session_id)
    except Exception as e:
        logger.error("Celery: Error in listening analysis for session %s: %s", session_id, str(e))
    finally:
        loop.close()