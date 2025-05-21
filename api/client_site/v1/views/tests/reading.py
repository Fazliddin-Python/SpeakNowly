from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import List
from tortoise.exceptions import DoesNotExist
from models.tests.reading import Reading, Passage, Question, Variant, Answer
from ...serializers.tests.reading import (
    ReadingSerializer,
    PassageSerializer,
    QuestionSerializer,
    VariantSerializer,
    AnswerSerializer,
)
from services.tests.reading_service import ReadingService
from utils.i18n import get_translation
from utils.auth.auth import get_current_user
from tasks.analyses.reading_tasks import analyse_reading_task

router = APIRouter()

@router.get("/", response_model=List[ReadingSerializer])
async def get_reading_tests(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Get all reading tests for the current user."""
    readings = await ReadingService.get_readings_for_user(user.id)
    if not readings:
        raise HTTPException(status_code=404, detail=t["no_reading_tests"])
    return readings

@router.get("/{reading_id}/", response_model=ReadingSerializer)
async def get_reading_test(
    reading_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Get a specific reading test by ID."""
    reading = await ReadingService.get_reading(reading_id)
    if not reading or reading.user_id != user.id:
        raise HTTPException(status_code=404, detail=t["reading_not_found"])
    return reading

@router.post("/start/", response_model=ReadingSerializer, status_code=status.HTTP_201_CREATED)
async def start_reading_test(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Start a new reading test for the current user."""
    reading, error = await ReadingService.start_reading(user.id)
    if error == "no_passages":
        raise HTTPException(status_code=404, detail=t["no_passages"])
    return reading

@router.post("/{reading_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_reading_answers(
    reading_id: int,
    answers: List[AnswerSerializer],
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Submit answers for a reading test."""
    total_score, error = await ReadingService.submit_answers(reading_id, user.id, [a.dict() for a in answers])
    if error == "not_found":
        raise HTTPException(status_code=404, detail=t["reading_not_found"])
    if error == "already_completed":
        raise HTTPException(status_code=400, detail=t["reading_already_completed"])
    if error and error.startswith("question_"):
        raise HTTPException(status_code=404, detail=t["question_not_found"])
    return {"message": t["answers_submitted"], "total_score": total_score}

@router.post("/{reading_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_reading_test(
    reading_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Cancel a reading test."""
    ok = await ReadingService.cancel_reading(reading_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail=t["reading_not_found"])
    return {"message": t["reading_cancelled"]}

@router.post("/{reading_id}/restart/", response_model=ReadingSerializer)
async def restart_reading_test(
    reading_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Restart a completed reading test."""
    reading, error = await ReadingService.restart_reading(reading_id, user.id)
    if error == "not_found":
        raise HTTPException(status_code=404, detail=t["reading_not_found"])
    if error == "not_completed":
        raise HTTPException(status_code=400, detail=t["reading_not_completed"])
    return reading

@router.get("/passage/{passage_id}/", response_model=PassageSerializer)
async def get_reading_passage(
    passage_id: int,
    user=Depends(get_current_user)
):
    """Get a specific reading passage by ID."""
    passage = await ReadingService.get_passage(passage_id)
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")
    return passage

@router.get("/questions/", response_model=List[QuestionSerializer])
async def get_questions(
    user=Depends(get_current_user)
):
    """Get all reading questions."""
    return await ReadingService.list_questions()

@router.get("/questions/{question_id}/", response_model=QuestionSerializer)
async def get_question(
    question_id: int,
    user=Depends(get_current_user)
):
    """Get a specific question by ID."""
    question = await ReadingService.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/questions/", response_model=QuestionSerializer, status_code=status.HTTP_201_CREATED)
async def create_question(
    data: QuestionSerializer,
    user=Depends(get_current_user)
):
    """Create a new reading question."""
    return await ReadingService.create_question(data.dict())

@router.delete("/questions/{question_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    user=Depends(get_current_user)
):
    """Delete a specific question by ID."""
    ok = await ReadingService.delete_question(question_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}

@router.get("/variants/", response_model=List[VariantSerializer])
async def get_variants(
    user=Depends(get_current_user)
):
    """Get all answer variants."""
    return await ReadingService.list_variants()

@router.get("/variants/{variant_id}/", response_model=VariantSerializer)
async def get_variant(
    variant_id: int,
    user=Depends(get_current_user)
):
    """Get a specific variant by ID."""
    variant = await ReadingService.get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant

@router.post("/variants/", response_model=VariantSerializer, status_code=status.HTTP_201_CREATED)
async def create_variant(
    data: VariantSerializer,
    user=Depends(get_current_user)
):
    """Create a new answer variant."""
    return await ReadingService.create_variant(data.dict())

@router.delete("/variants/{variant_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: int,
    user=Depends(get_current_user)
):
    """Delete a specific variant by ID."""
    ok = await ReadingService.delete_variant(variant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Variant not found")
    return {"message": "Variant deleted successfully"}

@router.post("/{reading_id}/analyse/", status_code=status.HTTP_202_ACCEPTED)
async def analyse_reading_test(
    reading_id: int,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """Start reading analysis asynchronously via Celery."""
    background_tasks.add_task(analyse_reading_task.delay, reading_id)
    return {"message": "Reading analysis started. Check back later for results."}