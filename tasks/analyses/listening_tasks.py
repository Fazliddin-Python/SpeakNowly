from celery_app import celery_app
import logging
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task
def analyse_listening_task(session_id: int):
    """
    Celery task to trigger ListeningAnalyseService.analyse for a given session.
    """
    from services.analyses.listening_analyse_service import ListeningAnalyseService

    try:
        asyncio.run(ListeningAnalyseService.analyse(session_id))
        logger.info(f"Listening analysis completed for session {session_id}")
    except Exception as exc:
        logger.error(f"Listening analysis failed for session {session_id}: {exc}")
