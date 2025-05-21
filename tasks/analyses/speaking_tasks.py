from celery import shared_task
from services.analyses.speaking_analyse_service import SpeakingAnalyseService
import asyncio

@shared_task
def analyse_speaking_task(test_id: int, api_key: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(SpeakingAnalyseService.analyse(test_id, api_key))
    loop.close()