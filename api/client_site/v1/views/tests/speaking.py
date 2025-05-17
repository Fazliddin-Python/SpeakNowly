from fastapi import APIRouter, HTTPException, UploadFile, Form, Depends, status
from typing import List, Optional
from tortoise.exceptions import DoesNotExist
from models.tests.speaking import Speaking, SpeakingQuestions, SpeakingAnswers
from ...serializers.tests.speaking import (
    SpeakingSerializer,
    SpeakingQuestionSerializer,
    SpeakingAnswerSerializer,
)
from datetime import datetime, timezone

router = APIRouter()


@router.get("/", response_model=List[SpeakingSerializer])
async def get_speaking_tests(user_id: int):
    """
    Retrieve all speaking tests for a specific user.
    """
    tests = await Speaking.filter(user_id=user_id).all()
    if not tests:
        raise HTTPException(status_code=404, detail="No speaking tests found for the user")
    return tests


@router.get("/{test_id}/", response_model=SpeakingSerializer)
async def get_speaking_test(test_id: int):
    """
    Retrieve a specific speaking test by ID.
    """
    test = await Speaking.get_or_none(id=test_id).prefetch_related("questions")
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")
    return test


@router.post("/", response_model=SpeakingSerializer, status_code=status.HTTP_201_CREATED)
async def create_speaking_test(user_id: int, start_time: Optional[datetime] = None):
    """
    Create a new speaking test for a user.
    """
    test = await Speaking.create(
        user_id=user_id,
        start_time=start_time or datetime.now(timezone.utc),
        status="started",
    )
    return test


@router.post("/{test_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_speaking_answers(
    test_id: int,
    question_id: int = Form(...),
    text_answer: Optional[str] = Form(None),
    audio_answer: Optional[UploadFile] = None,
):
    """
    Submit answers for a speaking test.
    """
    test = await Speaking.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")

    question = await SpeakingQuestions.get_or_none(id=question_id, speaking_id=test_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found for this test")

    if audio_answer:
        audio_path = f"audio_responses/{audio_answer.filename}"
        with open(audio_path, "wb") as f:
            f.write(await audio_answer.read())
    else:
        audio_path = None

    await SpeakingAnswers.create(
        question_id=question_id,
        text_answer=text_answer,
        audio_answer=audio_path,
    )

    return {"message": "Answer submitted successfully"}


@router.post("/{test_id}/complete/", status_code=status.HTTP_200_OK)
async def complete_speaking_test(test_id: int):
    """
    Mark a speaking test as completed.
    """
    test = await Speaking.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")

    if test.status == "completed":
        raise HTTPException(status_code=400, detail="Test is already completed")

    test.status = "completed"
    test.end_time = datetime.now(timezone.utc)
    await test.save()

    return {"message": "Speaking test completed successfully"}


@router.get("/{test_id}/questions/", response_model=List[SpeakingQuestionSerializer])
async def get_speaking_questions(test_id: int):
    """
    Retrieve all questions for a specific speaking test.
    """
    questions = await SpeakingQuestions.filter(speaking_id=test_id).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this test")
    return questions


@router.post("/{test_id}/questions/", response_model=SpeakingQuestionSerializer)
async def create_speaking_question(
    test_id: int,
    part: str = Form(...),
    title: Optional[str] = Form(None),
    content: str = Form(...),
):
    """
    Create a new question for a specific speaking test.
    """
    test = await Speaking.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")

    question = await SpeakingQuestions.create(
        speaking_id=test_id,
        part=part,
        title=title,
        content=content,
    )
    return question


@router.get("/{test_id}/answers/", response_model=List[SpeakingAnswerSerializer])
async def get_speaking_answers(test_id: int):
    """
    Retrieve all answers for a specific speaking test.
    """
    answers = await SpeakingAnswers.filter(question__speaking_id=test_id).all()
    if not answers:
        raise HTTPException(status_code=404, detail="No answers found for this test")
    return answers