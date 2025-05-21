from celery import shared_task
from services.analyses.writing_analyse_service import WritingAnalyseService
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task
def analyse_writing_task(test_id: int, api_key: str):
    logger.info("Celery: Start writing analysis for test %s", test_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(WritingAnalyseService.analyse(test_id, api_key))
        logger.info("Celery: Writing analysis for test %s finished", test_id)
    except Exception as e:
        logger.error("Celery: Error in writing analysis for test %s: %s", test_id, str(e))
    finally:
        loop.close()