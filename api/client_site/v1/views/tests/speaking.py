from fastapi import APIRouter, HTTPException, UploadFile, Form, Depends, status
from typing import List, Optional
from datetime import datetime, timezone
from models.tests.speaking import Speaking, SpeakingQuestions, SpeakingAnswers
from ...serializers.tests.speaking import (
    SpeakingSerializer,
    SpeakingQuestionSerializer,
    SpeakingAnswerSerializer,
)
from services.tests.speaking_service import SpeakingService

router = APIRouter()


@router.get("/", response_model=List[SpeakingSerializer])
async def get_speaking_tests(user_id: int):
    return await SpeakingService.get_speaking_tests(user_id)


@router.get("/{test_id}/", response_model=SpeakingSerializer)
async def get_speaking_test(test_id: int):
    return await SpeakingService.get_speaking_test(test_id)


@router.post("/", response_model=SpeakingSerializer, status_code=status.HTTP_201_CREATED)
async def create_speaking_test(user_id: int, start_time: Optional[datetime] = None):
    return await SpeakingService.create_speaking_test(user_id, start_time)


@router.post("/{test_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_speaking_answer(
    test_id: int,
    question_id: int = Form(...),
    audio_answer: Optional[UploadFile] = None,
    text_answer: Optional[str] = Form(None),
):
    return await SpeakingService.submit_speaking_answer(test_id, question_id, audio_answer, text_answer)


@router.post("/{test_id}/complete/", status_code=status.HTTP_200_OK)
async def complete_speaking_test(test_id: int):
    return await SpeakingService.complete_speaking_test(test_id)


@router.get("/{test_id}/questions/", response_model=List[SpeakingQuestionSerializer])
async def get_speaking_questions(test_id: int):
    return await SpeakingService.get_speaking_questions(test_id)


@router.post("/{test_id}/questions/", response_model=SpeakingQuestionSerializer)
async def create_speaking_question(
    test_id: int,
    part: str = Form(...),
    title: Optional[str] = Form(None),
    content: str = Form(...),
):
    return await SpeakingService.create_speaking_question(test_id, part, title, content)


@router.get("/{test_id}/answers/", response_model=List[SpeakingAnswerSerializer])
async def get_speaking_answers(test_id: int):
    return await SpeakingService.get_speaking_answers(test_id)