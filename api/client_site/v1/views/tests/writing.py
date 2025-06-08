from fastapi import APIRouter, HTTPException, status, Form, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone
from models.tests.writing import Writing, WritingPart1, WritingPart2
from models.transactions import TransactionType
from ...serializers.tests.writing import (
    WritingSerializer,
    WritingPart1Serializer,
    WritingPart2Serializer,
)
from services.tests.writing_service import WritingService
from services.analyses.writing_analyse_service import WritingAnalyseService
from utils.check_tokens import check_user_tokens
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()

def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user

@router.get("/", response_model=List[WritingSerializer])
async def get_writing_tests(
    user=Depends(active_user),
):
    return await WritingService.get_writing_tests(user.id)

@router.get("/{test_id}/", response_model=WritingSerializer)
async def get_writing_test(
    test_id: int,
    user=Depends(active_user),
):
    return await WritingService.get_writing_test(test_id)

@router.post("/", response_model=WritingSerializer, status_code=status.HTTP_201_CREATED)
async def create_writing_test(
    request: Request,
    start_time: Optional[datetime] = None,
    user=Depends(active_user),
    t=Depends(get_translation),
):
    message, token_status = await check_user_tokens(user, TransactionType.TEST_WRITING, request, t)
    if token_status == 402:
        raise HTTPException(status_code=402, detail=message)
    return await WritingService.create_writing_test(user.id, start_time)

@router.post("/{test_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_writing_test(
    test_id: int,
    part1_answer: Optional[str] = Form(None),
    part2_answer: Optional[str] = Form(None),
    user=Depends(active_user),
):
    return await WritingService.submit_writing_test(test_id, part1_answer, part2_answer)

@router.post("/{test_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_writing_test(
    test_id: int,
    user=Depends(active_user),
):
    return await WritingService.cancel_writing_test(test_id)

@router.get("/part1/{part1_id}/", response_model=WritingPart1Serializer)
async def get_writing_part1(
    part1_id: int,
    user=Depends(active_user),
):
    return await WritingService.get_writing_part1(part1_id)

@router.get("/part2/{part2_id}/", response_model=WritingPart2Serializer)
async def get_writing_part2(
    part2_id: int,
    user=Depends(active_user),
):
    return await WritingService.get_writing_part2(part2_id)

@router.post("/{test_id}/analyse/", status_code=status.HTTP_201_CREATED)
async def analyse_writing_test(
    test_id: int,
    api_key: str,
    user=Depends(active_user),
):
    test = await WritingService.get_writing_test(test_id)
    if test.status != "completed":
        raise HTTPException(status_code=400, detail="Test must be completed before analysis")
    analyse = await WritingAnalyseService.analyse(test_id, api_key)
    return analyse