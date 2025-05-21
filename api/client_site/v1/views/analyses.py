from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List
from models.analyses import (
    ListeningAnalyse,
    ReadingAnalyse,
    SpeakingAnalyse,
    WritingAnalyse,
)
from models.tests.writing import Writing
from models.tests.speaking import Speaking
from ..serializers.analyses import (
    ListeningAnalyseSerializer,
    ReadingAnalyseSerializer,
    SpeakingAnalyseSerializer,
    WritingAnalyseSerializer,
)
from tasks.analyses.listening_tasks import analyse_listening_session_task
from tasks.analyses.reading_tasks import analyse_reading_task
from tasks.analyses.speaking_tasks import analyse_speaking_task
from tasks.analyses.writing_tasks import analyse_writing_task

from config import OPENAI_API_KEY

router = APIRouter()

# --- Listening ---
@router.post("/listening/{session_id}/analyse/")
async def analyse_listening(
    session_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(analyse_listening_session_task.delay, session_id)
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
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(analyse_reading_task.delay, reading_id)
    return {"message": "Reading analysis started. Check back later for results."}

@router.get("/reading/{reading_id}/analyse/", response_model=ReadingAnalyseSerializer)
async def get_reading_analysis(reading_id: int):
    analyse = await ReadingAnalyse.get_or_none(reading_id=reading_id)
    if not analyse:
        raise HTTPException(status_code=404, detail="Reading analysis not found")
    return analyse

@router.get("/reading/analysis/", response_model=List[ReadingAnalyseSerializer])
async def get_user_reading_analyses(user_id: int):
    analyses = await ReadingAnalyse.filter(user_id=user_id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No reading analyses found for the user")
    return analyses

# --- Writing ---
@router.post("/writing/{test_id}/analyse/")
async def analyse_writing(
    test_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(analyse_writing_task.delay, test_id, OPENAI_API_KEY)
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
    background_tasks.add_task(analyse_speaking_task.delay, test_id, OPENAI_API_KEY)
    return {"message": "Speaking analysis started. Check back later for results."}

@router.get("/speaking/{id}/analyse/", response_model=SpeakingAnalyseSerializer)
async def get_speaking_analysis(id: int):
    analysis = await SpeakingAnalyse.get_or_none(id=id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Speaking analysis not found")
    return analysis
