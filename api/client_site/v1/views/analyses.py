from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from models.analyses import (
    ListeningAnalyse,
    ReadingAnalyse,
    SpeakingAnalyse,
    WritingAnalyse,
)
from models.tests import Writing, Speaking, Reading
from ..serializers.analyses import (
    ListeningAnalyseSerializer,
    ReadingAnalyseSerializer,
    SpeakingAnalyseSerializer,
    WritingAnalyseSerializer,
)
from config import OPENAI_API_KEY

router = APIRouter()

# --- Listening ---
@router.post("/listening/{session_id}/analyse/")
async def analyse_listening(
    session_id: int,
):
    from tasks.analyses.listening_tasks import analyse_listening_task
    analyse_listening_task.apply_async(args=[session_id], queue='analyses')
    return {"message": "Listening analysis started. Check back later for results."}

@router.get("/listening/{session_id}/analyse/", response_model=ListeningAnalyseSerializer)
async def get_listening_analysis(session_id: int):
    analyse = await ListeningAnalyse.get_or_none(session_id=session_id)
    if not analyse:
        raise HTTPException(status_code=404, detail="Listening analysis not found")
    return analyse

# --- Reading ---
@router.post("/reading/{reading_id}/analyse/")
async def analyse_reading(
    reading_id: int,
):
    from tasks.analyses.reading_tasks import analyse_reading_task
    analyse_reading_task.apply_async(args=[reading_id], queue='analyses')
    return {"message": "Reading analysis started. Check back later for results."}

@router.get("/reading/{session_id}/analyse/", response_model=List[ReadingAnalyseSerializer])
async def get_reading_analysis(session_id: int, user_id: int):
    from models.tests.reading import Reading
    reading = await Reading.get_or_none(id=session_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    passages = await reading.passages.all()
    passage_ids = [p.id for p in passages]
    analyses = await ReadingAnalyse.filter(passage_id__in=passage_ids, user_id=user_id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No analyses found for this reading session")
    return analyses

@router.get("/reading/analysis/", response_model=List[ReadingAnalyseSerializer])
async def get_user_reading_analyses(user_id: int):
    """
    Получить все анализы пользователя по всем сессиям.
    """
    analyses = await ReadingAnalyse.filter(user_id=user_id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No reading analyses found for the user")
    return analyses

@router.get("/reading/{session_id}/all_analyses/", response_model=List[ReadingAnalyseSerializer])
async def get_all_reading_analyses(session_id: int, user_id: int):
    """
    Получить все анализы по всем passage в сессии (по токену/ID сессии).
    """
    from models.tests.reading import Reading
    reading = await Reading.get_or_none(id=session_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    passages = await reading.passages.all()
    passage_ids = [p.id for p in passages]
    analyses = await ReadingAnalyse.filter(passage_id__in=passage_ids, user_id=user_id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No analyses found for this reading")
    return analyses

# --- Writing ---
@router.post("/writing/{test_id}/analyse/")
async def analyse_writing(
    test_id: int,
):
    from tasks.analyses.writing_tasks import analyse_writing_task
    analyse_writing_task.apply_async(args=[test_id, OPENAI_API_KEY], queue='analyses')
    return {"message": "Writing analysis started. Check back later for results."}

@router.get("/writing/{id}/analyse/", response_model=WritingAnalyseSerializer)
async def get_writing_analysis(id: int):
    analysis = await WritingAnalyse.get_or_none(id=id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Writing analysis not found")
    return analysis

# --- Speaking ---
@router.post("/speaking/{test_id}/analyse/")
async def analyse_speaking(
    test_id: int,
    background_tasks: BackgroundTasks
):
    from tasks.analyses.speaking_tasks import analyse_speaking_task
    analyse_speaking_task.apply_async(args=[test_id], queue='analyses')
    return {"message": "Speaking analysis started. Check back later for results."}

@router.get("/speaking/{id}/analyse/", response_model=SpeakingAnalyseSerializer)
async def get_speaking_analysis(id: int):
    analysis = await SpeakingAnalyse.get_or_none(id=id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Speaking analysis not found")
    return analysis
