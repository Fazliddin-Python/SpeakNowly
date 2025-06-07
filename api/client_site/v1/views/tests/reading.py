import asyncio
import logging
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.params import Query

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
from utils.check_tokens import check_user_tokens
from models.tests.test_type import TestTypeEnum
from models.tests.constants import Constants
from services.tests.reading_service import ReadingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reading", tags=["Reading"])


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

@router.get(
    "/passages/",
    response_model=List[PassageSerializer],
    summary="List all passages (admin)"
)
async def list_passages(
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_passages")),
):
    passages = await ReadingService.list_passages(t=t)
    return [PassageSerializer.from_orm(p) for p in passages]


@router.get(
    "/passages/{passage_id}/",
    response_model=PassageSerializer,
    summary="Retrieve passage by ID (admin)"
)
async def retrieve_passage(
    passage_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("get_passage")),
):
    passage = await ReadingService.get_passage(passage_id, t=t)
    return PassageSerializer.from_orm(passage)


@router.post(
    "/passages/",
    response_model=PassageSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create passage (admin)"
)
async def create_passage(
    payload: PassageCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_passage")),
):
    passage = await ReadingService.create_passage(payload.dict(), t=t)
    return PassageSerializer.from_orm(passage)


@router.put(
    "/passages/{passage_id}/",
    response_model=PassageSerializer,
    summary="Update passage (admin)"
)
async def update_passage(
    passage_id: int,
    payload: PassageCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("update_passage")),
):
    passage = await ReadingService.update_passage(passage_id, payload.dict(), t=t)
    return PassageSerializer.from_orm(passage)


@router.delete(
    "/passages/{passage_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete passage (admin)"
)
async def delete_passage(
    passage_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("delete_passage")),
):
    await ReadingService.delete_passage(passage_id, t=t)


# -----------------------------
#   Admin / Question CRUD
# -----------------------------

@router.get(
    "/questions/",
    response_model=List[QuestionListSerializer],
    summary="List questions (admin)"
)
async def list_questions(
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_questions")),
):
    questions = await ReadingService.list_questions(t=t)
    return await asyncio.gather(*[QuestionListSerializer.from_orm(q) for q in questions])


@router.get(
    "/questions/{question_id}/",
    response_model=QuestionListSerializer,
    summary="Retrieve question by ID (admin)"
)
async def retrieve_question(
    question_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("get_question")),
):
    question = await ReadingService.get_question(question_id, t=t)
    return await QuestionListSerializer.from_orm(question)


@router.post(
    "/questions/",
    response_model=QuestionListSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create question (admin)"
)
async def create_question(
    payload: QuestionCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_question")),
):
    question = await ReadingService.create_question(payload.dict(), t=t)
    return await QuestionListSerializer.from_orm(question)


@router.put(
    "/questions/{question_id}/",
    response_model=QuestionListSerializer,
    summary="Update question (admin)"
)
async def update_question(
    question_id: int,
    payload: QuestionCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("update_question")),
):
    question = await ReadingService.update_question(question_id, payload.dict(), t=t)
    return await QuestionListSerializer.from_orm(question)


@router.delete(
    "/questions/{question_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete question (admin)"
)
async def delete_question(
    question_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("delete_question")),
):
    await ReadingService.delete_question(question_id, t=t)


# -----------------------------
#   Admin / Variant CRUD
# -----------------------------

@router.get(
    "/variants/",
    response_model=List[VariantSerializer],
    summary="List variants (admin)"
)
async def list_variants(
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_variants")),
):
    variants = await ReadingService.list_variants(t=t)
    return [VariantSerializer.from_orm(v) for v in variants]


@router.get(
    "/variants/{variant_id}/",
    response_model=VariantSerializer,
    summary="Retrieve variant (admin)"
)
async def retrieve_variant(
    variant_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("get_variant")),
):
    variant = await ReadingService.get_variant(variant_id, t=t)
    return VariantSerializer.from_orm(variant)


@router.post(
    "/variants/",
    response_model=VariantSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create variant (admin)"
)
async def create_variant(
    payload: VariantCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_variant")),
):
    variant = await ReadingService.create_variant(payload.dict(), t=t)
    return VariantSerializer.from_orm(variant)


@router.put(
    "/variants/{variant_id}/",
    response_model=VariantSerializer,
    summary="Update variant (admin)"
)
async def update_variant(
    variant_id: int,
    payload: VariantCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("update_variant")),
):
    variant = await ReadingService.update_variant(variant_id, payload.dict(), t=t)
    return VariantSerializer.from_orm(variant)


@router.delete(
    "/variants/{variant_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete variant (admin)"
)
async def delete_variant(
    variant_id: int,
    t: Dict[str, str] = Depends(get_translation),
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
    summary="Start a new reading session"
)
async def start_reading_session(
    request: Request,
    user=Depends(active_user),
    t=Depends(get_translation),
    _: Any = Depends(audit_action("start_reading")),
):
    # 1) проверка и списание токенов
    await check_user_tokens(user, TestTypeEnum.READING_ENG, request, t)

    # 2) создание сессии
    reading, error = await ReadingService.start_reading(user.id)
    if error == "invalid_gpt_output":
        raise HTTPException(status_code=500, detail=t["internal_error"])
    return ReadingSerializer.from_orm(reading)


@router.get(
    "/{session_id}/",
    response_model=ReadingSerializer,
    summary="Retrieve a reading session"
)
async def get_reading_session(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
    _: Any = Depends(audit_action("get_reading")),
):
    reading = await ReadingService.get_reading(session_id)
    if not reading or reading.user_id != user.id:
        raise HTTPException(status_code=404, detail=t["session_not_found"])
    return ReadingSerializer.from_orm(reading)


@router.post(
    "/{session_id}/submit/",
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a reading session"
)
async def submit_reading_answers(
    session_id: int,
    payload: SubmitPassageAnswerSerializer,
    user=Depends(active_user),
    t=Depends(get_translation),
    _: Any = Depends(audit_action("submit_passage_answers")),
):
    total_score, error = await ReadingService.submit_answers(session_id, user.id, payload.answers)
    if error == "session_not_found":
        raise HTTPException(404, t["session_not_found"])
    if error == "already_completed":
        raise HTTPException(400, t["session_already_completed"])
    if error.startswith("question_"):
        raise HTTPException(404, t["question_not_found"])
    return {"message": t["answers_submitted"], "total_score": total_score}


@router.post(
    "/{session_id}/cancel/",
    status_code=status.HTTP_200_OK,
    summary="Cancel a reading session"
)
async def cancel_reading_session(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
    _: Any = Depends(audit_action("cancel_reading")),
):
    ok = await ReadingService.cancel_reading(session_id, user.id)
    if not ok:
        raise HTTPException(404, t["session_not_found"])
    return {"message": t["session_cancelled"]}


@router.post(
    "/{session_id}/restart/",
    response_model=ReadingSerializer,
    summary="Restart a completed reading session"
)
async def restart_reading_session(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
    _: Any = Depends(audit_action("restart_reading")),
):
    reading, error = await ReadingService.restart_reading(session_id, user.id)
    if error == "session_not_found":
        raise HTTPException(404, t["session_not_found"])
    if error == "not_completed":
        raise HTTPException(400, t["session_not_completed"])
    return ReadingSerializer.from_orm(reading)


@router.get(
    "/{session_id}/analysis/",
    summary="Get detailed analysis for a reading session"
)
async def analyze_reading(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
    _: Any = Depends(audit_action("analyse_reading")),
):
    data = await ReadingService.analyse_reading(session_id, user.id)
    return data
