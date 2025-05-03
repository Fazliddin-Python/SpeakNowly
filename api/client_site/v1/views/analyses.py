from fastapi import APIRouter, HTTPException, Depends
from typing import List
from tortoise.exceptions import DoesNotExist

from models.analyses import (
    ListeningAnalyse,
    ReadingAnalyse,
    SpeakingAnalyse,
    WritingAnalyse,
)
from ..serializers.analyses import (
    ListeningAnalyseSerializer,
    ReadingAnalyseSerializer,
    SpeakingAnalyseSerializer,
    WritingAnalyseSerializer,
)

router = APIRouter(prefix="/api/v1/tests", tags=["Analyses"])


@router.get("/listening/{session_id}/analyse/", response_model=ListeningAnalyseSerializer)
async def analyse_listening(session_id: int):
    """
    Analyse a listening test session.
    """
    try:
        analysis = await ListeningAnalyse.get(session_id=session_id)
        return analysis
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Listening analysis not found")


@router.get("/reading/analysis/", response_model=List[ReadingAnalyseSerializer])
async def analyse_reading(user_id: int):
    """
    Analyse all reading tests for a user.
    """
    analyses = await ReadingAnalyse.filter(user_id=user_id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No reading analyses found for the user")
    return analyses


@router.get("/speaking/{id}/analyse/", response_model=SpeakingAnalyseSerializer)
async def analyse_speaking(id: int):
    """
    Analyse a speaking test.
    """
    try:
        analysis = await SpeakingAnalyse.get(id=id)
        return analysis
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Speaking analysis not found")


@router.get("/writing/{id}/analyse/", response_model=WritingAnalyseSerializer)
async def analyse_writing(id: int):
    """
    Analyse a writing test.
    """
    try:
        analysis = await WritingAnalyse.get(id=id)
        return analysis
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Writing analysis not found")