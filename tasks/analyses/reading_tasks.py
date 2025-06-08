import logging
import asyncio
from tortoise import Tortoise
from celery_app import celery_app
from config import DATABASE_CONFIG
from services.analyses.reading_analyse_service import ReadingAnalyseService

logger = logging.getLogger(__name__)


@celery_app.task
def analyse_reading_task(reading_id: int, user_id: int):
    """
    Celery task to trigger ReadingAnalyseService.analyse_reading for a given reading session.
    """

    async def _run():
        try:
            await Tortoise.init(config=DATABASE_CONFIG)
            await Tortoise.generate_schemas()
            await ReadingAnalyseService.analyse_reading(reading_id, user_id)
            logger.info(f"Reading analysis completed for reading {reading_id}")
        except Exception as exc:
            logger.error(f"Reading analysis failed for reading {reading_id}: {exc}")
        finally:
            await Tortoise.close_connections()

    asyncio.run(_run())
