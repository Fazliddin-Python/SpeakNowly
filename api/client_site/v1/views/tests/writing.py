from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Dict, Any, Optional

from models.transactions import TransactionType

from ...serializers.tests.writing import WritingSerializer
from services.tests import WritingService
from models.tests import TestTypeEnum
from utils.auth import active_user
from utils import get_translation, check_user_tokens
from utils.arq_pool import get_arq_redis

router = APIRouter()


@router.post(
    "/start/",
    response_model=WritingSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new writing session"
)
async def start_writing_test(
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    """
    Start a new writing test session.
    """
    await check_user_tokens(user, TransactionType.TEST_WRITING, request, t)
    session_data = await WritingService.start_session(user, t)
    return await WritingSerializer.from_orm(session_data)


@router.get(
    "/{session_id}/",
    response_model=WritingSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get writing session details"
)
async def get_writing_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a writing session.
    """
    session_data = await WritingService.get_session(session_id, user.id, t)
    return await WritingSerializer.from_orm(session_data)


@router.post(
    "/{session_id}/submit/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a writing session"
)
async def submit_writing_answers(
    session_id: int,
    part1_answer: Optional[str] = None,
    part2_answer: Optional[str] = None,
    lang_code: str = "en",
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    redis=Depends(get_arq_redis),
):
    result = await WritingService.submit_answers(
        session_id=session_id,
        user_id=user.id,
        part1_answer=part1_answer,
        part2_answer=part2_answer,
        lang_code=lang_code,
        t=t
    )
    await redis.enqueue_job("analyse_writing", test_id=session_id)
    return result


@router.get(
    "/{session_id}/analysis/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get analysis for a completed writing session"
)
async def get_writing_analysis(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get analysis for a completed writing session.
    """
    result = await WritingService.get_analysis(session_id, user.id, t)
    return result