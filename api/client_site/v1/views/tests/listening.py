import asyncio
from fastapi import APIRouter, Depends, status, Request
from typing import Dict

from models.transactions import TransactionType
from ...serializers.tests import (
    ListeningDataSlimSerializer,
    ListeningPartSerializer,
    ListeningAnswerSerializer,
    ListeningAnalyseResponseSerializer,
    ListeningSessionExamSerializer,
)
from services.tests import ListeningService
from models.tests import TestTypeEnum
from utils.auth import active_user
from utils import get_translation, check_user_tokens
from utils.arq_pool import get_arq_redis

router = APIRouter()


async def _serialize_listening_session(data):
    session_obj = type("SessionObj", (), {
        "id": data["session_id"],
        "status": data["status"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
    })()
    exam = await ListeningSessionExamSerializer.from_orm(data["exam"])
    parts = await asyncio.gather(*(ListeningPartSerializer.from_orm(p) for p in data["parts"]))
    return ListeningDataSlimSerializer(
        session_id=session_obj.id,
        status=session_obj.status,
        start_time=session_obj.start_time,
        end_time=session_obj.end_time,
        exam=exam,
        parts=parts,
    )


@router.post(
    "/start/",
    response_model=ListeningDataSlimSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new listening session"
)
async def start_listening_test(
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
    redis=Depends(get_arq_redis),
):
    await check_user_tokens(user, TransactionType.TEST_LISTENING, request, t)
    session_data = await ListeningService.start_session(user, t)
    return await _serialize_listening_session(session_data)


@router.get(
    "/session/{session_id}/",
    response_model=ListeningDataSlimSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get listening session details"
)
async def get_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a listening session.
    """
    data = await ListeningService.get_session_data(session_id, user.id, t)
    return await _serialize_listening_session(data)


@router.get(
    "/parts/{part_id}/",
    response_model=ListeningPartSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get listening part"
)
async def get_listening_part(
    part_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a listening part (sections and questions).
    """
    part = await ListeningService.get_part(part_id, t)
    return await ListeningPartSerializer.from_orm(part)


@router.post(
    "/session/{session_id}/submit/",
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a listening session"
)
async def submit_listening_answers(
    session_id: int,
    payload: ListeningAnswerSerializer,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    redis=Depends(get_arq_redis),
):
    result = await ListeningService.submit_answers(session_id, user.id, payload.answers, t)
    await redis.enqueue_job("analyse_listening", session_id=session_id)
    return result


@router.post(
    "/session/{session_id}/cancel/",
    status_code=status.HTTP_200_OK,
    summary="Cancel a listening session"
)
async def cancel_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Cancel a listening session.
    """
    result = await ListeningService.cancel_session(session_id, user.id, t)
    return result


@router.get(
    "/session/{session_id}/analyse/",
    response_model=ListeningAnalyseResponseSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get analysis for a completed listening session"
)
async def get_listening_analysis(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    """
    Get analysis for a completed listening session.
    """
    result = await ListeningService.get_analysis(session_id, user.id, t, request)
    return result