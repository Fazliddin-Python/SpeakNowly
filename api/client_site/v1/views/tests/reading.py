from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from typing import List, Any, Dict

import asyncio
import logging

from services.tests.reading_service import ReadingService
from ...serializers.tests.reading import (
    PassageSerializer,
    PassageCreateSerializer,
    QuestionListSerializer,
    QuestionCreateSerializer,
    VariantSerializer,
    VariantCreateSerializer,
    ReadingSerializer,
    StartReadingSerializer,
    SubmitPassageAnswerSerializer,
    FinishReadingSerializer,
    QuestionAnalysisSerializer,
)
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

logger = logging.getLogger(__name__)
router = APIRouter()


def audit_action(action: str):
    def wrapper(request: Request, user=Depends(get_current_user)):
        logger.info(f"User {user.id} action='{action}' path='{request.url.path}'")
        return user
    return wrapper


def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    if not user.is_active:
        logger.warning(f"Inactive user (id={user.id}) attempted access")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user


def admin_required(user=Depends(get_current_user), t=Depends(get_translation)):
    if not (user.is_staff and user.is_superuser):
        logger.warning(f"Permission denied for user_id={user.id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["permission_denied"])
    return user


# -----------------------------
#   Admin / Passage CRUD
# -----------------------------


@router.get("/passages/", response_model=List[PassageSerializer], summary="List all passages")
async def list_passages(
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_passages")),
):
    passages = await ReadingService.list_passages(t=t)
    return [PassageSerializer.from_orm(p) for p in passages]  # sync conversion is OK here


@router.get("/passages/{passage_id}/", response_model=PassageSerializer, summary="Get passage by ID")
async def retrieve_passage(
    passage_id: int,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("get_passage")),
):
    passage = await ReadingService.get_passage(passage_id, t=t)
    return PassageSerializer.from_orm(passage)


@router.post(
    "/passages/",
    response_model=PassageSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new passage",
)
async def create_passage(
    payload: PassageCreateSerializer,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_passage")),
):
    passage = await ReadingService.create_passage(payload.dict(), t=t)
    return PassageSerializer.from_orm(passage)


@router.put(
    "/passages/{passage_id}/",
    response_model=PassageSerializer,
    summary="Update a passage",
)
async def update_passage(
    passage_id: int,
    payload: PassageCreateSerializer,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("update_passage")),
):
    passage = await ReadingService.update_passage(passage_id, payload.dict(), t=t)
    return PassageSerializer.from_orm(passage)


@router.delete(
    "/passages/{passage_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a passage",
)
async def delete_passage(
    passage_id: int,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("delete_passage")),
):
    await ReadingService.delete_passage(passage_id, t=t)


# -----------------------------
#   Admin / Question CRUD
# -----------------------------


@router.get("/questions/", response_model=List[QuestionListSerializer], summary="List all questions")
async def list_questions(
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_questions")),
):
    questions = await ReadingService.list_questions(t=t)
    return await asyncio.gather(*[QuestionListSerializer.from_orm(q) for q in questions])


@router.get("/questions/{question_id}/", response_model=QuestionListSerializer, summary="Get question by ID")
async def retrieve_question(
    question_id: int,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("get_question")),
):
    question = await ReadingService.get_question(question_id, t=t)
    return await QuestionListSerializer.from_orm(question)


@router.post(
    "/questions/",
    response_model=QuestionListSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new question",
)
async def create_question(
    payload: QuestionCreateSerializer,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_question")),
):
    question = await ReadingService.create_question(payload.dict(), t=t)
    return await QuestionListSerializer.from_orm(question)


@router.put(
    "/questions/{question_id}/",
    response_model=QuestionListSerializer,
    summary="Update a question",
)
async def update_question(
    question_id: int,
    payload: QuestionCreateSerializer,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("update_question")),
):
    question = await ReadingService.update_question(question_id, payload.dict(), t=t)
    return await QuestionListSerializer.from_orm(question)


@router.delete(
    "/questions/{question_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
)
async def delete_question(
    question_id: int,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("delete_question")),
):
    await ReadingService.delete_question(question_id, t=t)


# -----------------------------
#   Admin / Variant CRUD
# -----------------------------


@router.get("/variants/", response_model=List[VariantSerializer], summary="List all variants")
async def list_variants(
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_variants")),
):
    variants = await ReadingService.list_variants(t=t)
    return [VariantSerializer.from_orm(v) for v in variants]


@router.get("/variants/{variant_id}/", response_model=VariantSerializer, summary="Get variant by ID")
async def retrieve_variant(
    variant_id: int,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("get_variant")),
):
    variant = await ReadingService.get_variant(variant_id, t=t)
    return VariantSerializer.from_orm(variant)


@router.post(
    "/variants/",
    response_model=VariantSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new variant",
)
async def create_variant(
    payload: VariantCreateSerializer,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_variant")),
):
    variant = await ReadingService.create_variant(payload.dict(), t=t)
    return VariantSerializer.from_orm(variant)


@router.put(
    "/variants/{variant_id}/",
    response_model=VariantSerializer,
    summary="Update a variant",
)
async def update_variant(
    variant_id: int,
    payload: VariantCreateSerializer,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("update_variant")),
):
    variant = await ReadingService.update_variant(variant_id, payload.dict(), t=t)
    return VariantSerializer.from_orm(variant)


@router.delete(
    "/variants/{variant_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a variant",
)
async def delete_variant(
    variant_id: int,
    t: dict = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("delete_variant")),
):
    await ReadingService.delete_variant(variant_id, t=t)


# -----------------------------
#   User / Reading session flow
# -----------------------------


@router.post(
    "/start/",
    response_model=ReadingSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new reading session",
)
async def start_reading_session(
    _: Any = Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    __: Any = Depends(audit_action("start_reading")),
    payload: StartReadingSerializer = Depends(),  # not strictly needed, we ignore reading_id here
    user=Depends(get_current_user),
):
    reading, error = await ReadingService.start_reading(user.id)
    if error == "no_passages":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["no_passages"])
    return ReadingSerializer.from_orm(reading)


@router.get(
    "/{reading_id}/",
    response_model=ReadingSerializer,
    summary="Get a reading session by ID",
)
async def get_reading_session(
    reading_id: int,
    _: Any = Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    __: Any = Depends(audit_action("get_reading")),
    user=Depends(get_current_user),
):
    reading = await ReadingService.get_reading(reading_id)
    if not reading or reading.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["reading_not_found"])
    return ReadingSerializer.from_orm(reading)


@router.post(
    "/{reading_id}/passages/{passage_id}/submit/",
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a passage",
)
async def submit_passage_answers(
    reading_id: int,
    passage_id: int,
    payload: SubmitPassageAnswerSerializer,
    _: Any = Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    __: Any = Depends(audit_action("submit_passage_answers")),
    user=Depends(get_current_user),
):
    total_score, error = await ReadingService.submit_answers(
        reading_id, user.id, payload.answers
    )
    if error == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["reading_not_found"])
    if error == "already_completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["reading_already_completed"])
    if error and error.startswith("question_"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["question_not_found"])
    return {"message": t["answers_submitted"], "total_score": total_score}


@router.post(
    "/{reading_id}/cancel/",
    status_code=status.HTTP_200_OK,
    summary="Cancel a reading session",
)
async def cancel_reading_session(
    reading_id: int,
    _: Any = Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    __: Any = Depends(audit_action("cancel_reading")),
    user=Depends(get_current_user),
):
    ok = await ReadingService.cancel_reading(reading_id, user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["reading_not_found"])
    return {"message": t["reading_cancelled"]}


@router.post(
    "/{reading_id}/restart/",
    response_model=ReadingSerializer,
    summary="Restart a completed reading session",
)
async def restart_reading_session(
    reading_id: int,
    _: Any = Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    __: Any = Depends(audit_action("restart_reading")),
    user=Depends(get_current_user),
):
    reading, error = await ReadingService.restart_reading(reading_id, user.id)
    if error == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["reading_not_found"])
    if error == "not_completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["reading_not_completed"])
    return ReadingSerializer.from_orm(reading)


@router.get(
    "/{reading_id}/analysis/",
    summary="Get analysis results for a reading session (paginated)",
)
async def analyze_reading(
    reading_id: int,
    # page: int = Query(1, ge=1),
    # page_size: int = Query(10, ge=1),
    _: Any = Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    __: Any = Depends(audit_action("analyse_reading")),
    user=Depends(get_current_user),
):
    analysis = await ReadingService.analyse_reading(reading_id, user.id)
    return analysis
