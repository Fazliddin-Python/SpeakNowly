from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Request
from typing import Dict, Any, Optional

from models.transactions import TransactionType

from ...serializers.tests.speaking import SpeakingSerializer
from services.tests import SpeakingService
from models.tests import TestTypeEnum
from utils.auth import active_user
from utils import get_translation, check_user_tokens
from utils.arq_pool import get_arq_redis

router = APIRouter()


@router.post(
    "/start/",
    response_model=SpeakingSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new speaking session"
)
async def start_speaking_test(
    request: Request,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Start a new speaking test session.
    """
    await check_user_tokens(user, TransactionType.TEST_SPEAKING, request, t)
    session_data = await SpeakingService.start_session(user, t)
    return session_data


@router.get(
    "/{session_id}/",
    response_model=SpeakingSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get speaking session details"
)
async def get_speaking_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a speaking session.
    """
    session_data = await SpeakingService.get_session(session_id, user.id, t)
    return session_data


@router.post(
    "/{session_id}/answers/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Submit audio answers for a speaking session"
)
async def submit_speaking_answers(
    session_id: int,
    part1_audio: Optional[UploadFile] = File(None),
    part2_audio: Optional[UploadFile] = File(None),
    part3_audio: Optional[UploadFile] = File(None),
    is_finished: bool = Form(True),
    is_cancelled: bool = Form(False),
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    redis=Depends(get_arq_redis),
):
    audio_files = {"part1": part1_audio, "part2": part2_audio, "part3": part3_audio}
    result = await SpeakingService.submit_answers(
        session_id=session_id,
        user_id=user.id,
        audio_files=audio_files,
        t=t
    )
    await redis.enqueue_job("analyse_speaking", test_id=session_id)
    return result


@router.post(
    "/{session_id}/cancel/",
    status_code=status.HTTP_200_OK,
    summary="Cancel a speaking session"
)
async def cancel_speaking_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Cancel a speaking session.
    """
    result = await SpeakingService.cancel_session(session_id, user.id, t)
    return result


@router.post(
    "/{session_id}/restart/",
    status_code=status.HTTP_200_OK,
    summary="Restart a speaking session"
)
async def restart_speaking_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Restart a speaking session.
    """
    result = await SpeakingService.restart_session(session_id, user.id, t)
    return result


@router.get(
    "/{session_id}/analysis/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get analysis for a completed speaking session"
)
async def get_speaking_analysis(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get analysis for a completed speaking session.
    """
    result = await SpeakingService.get_analysis(session_id, user.id, t)
    return result
