import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Request, Form, Depends
from tortoise.exceptions import DoesNotExist

from models.tests.writing import Writing, WritingPart1, WritingPart2
from models.transactions import TransactionType
from services.chatgpt.integration import ChatGPTIntegration
from services.tests.writing_service import WritingService
from services.analyses.writing_analyse_service import WritingAnalyseService
from utils.check_tokens import check_user_tokens
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

from ...serializers.tests.writing import (
    WritingSerializer,
    WritingPart1Serializer,
    WritingPart2Serializer,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user


@router.get("/", response_model=List[WritingSerializer])
async def list_writings(user=Depends(active_user)):
    return await WritingService.get_writing_tests(user.id)


@router.post("/", response_model=WritingSerializer, status_code=status.HTTP_201_CREATED)
async def create_writing(
    request: Request,
    start_time: Optional[datetime] = None,
    user=Depends(active_user),
    t=Depends(get_translation),
):
    # check tokens
    ok = await check_user_tokens(user, TransactionType.TEST_WRITING, request, t)
    if not ok:
        raise HTTPException(status_code=402, detail=t["insufficient_tokens"])
    # 1. create writing record
    writing = await Writing.create(
        user_id=user.id,
        start_time=start_time or datetime.now(timezone.utc),
        status="started"
    )
    # 2. generate questions
    chatgpt = ChatGPTIntegration()
    part1_data = await chatgpt.generate_writing_part1_question()
    part2_data = await chatgpt.generate_writing_part2_question()
    # 3. save parts
    await WritingPart1.create(
        writing_id=writing.id,
        content=part1_data["question"],
        diagram=None,
        diagram_data=None,
        answer=""
    )
    await WritingPart2.create(
        writing_id=writing.id,
        content=part2_data["task2_question"],
        answer=""
    )
    # 4. return full serialized test
    return await WritingService.get_writing_test(writing.id)


@router.get("/{test_id}/", response_model=WritingSerializer)
async def retrieve_writing(test_id: int, user=Depends(active_user)):
    try:
        return await WritingService.get_writing_test(test_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Writing not found")


@router.post("/{test_id}/submit/", response_model=WritingSerializer, status_code=status.HTTP_200_OK)
async def submit_writing(
    test_id: int,
    part1_answer: Optional[str] = Form(None),
    part2_answer: Optional[str] = Form(None),
    user=Depends(active_user),
    t=Depends(get_translation),
):
    # 1. fetch writing
    try:
        writing = await Writing.get(id=test_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Writing not found")
    # 2. update answers
    part1 = await WritingPart1.get(writing_id=test_id)
    part2 = await WritingPart2.get(writing_id=test_id)
    if part1_answer:
        part1.answer = part1_answer
        await part1.save()
    if part2_answer:
        part2.answer = part2_answer
        await part2.save()
    # 3. mark completed
    writing.status = "completed"
    writing.end_time = datetime.now(timezone.utc)
    await writing.save()
    return await WritingService.get_writing_test(test_id)


@router.post("/{test_id}/analyse/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def analyse_writing(
    test_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
):
    # 1. ensure completed
    writing = await Writing.get(id=test_id)
    if writing.status != "completed":
        raise HTTPException(status_code=400, detail="Test must be completed before analysis")
    # 2. run analysis
    result = await WritingAnalyseService.analyse(test_id)
    return result


@router.post("/{test_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_writing(test_id: int, user=Depends(active_user)):
    writing = await Writing.get(id=test_id)
    writing.status = "cancelled"
    await writing.save(update_fields=["status"])
    return {"detail": "cancelled successfully"}


@router.get("/part1/{part1_id}/", response_model=WritingPart1Serializer)
async def get_part1(part1_id: int, user=Depends(active_user)):
    return await WritingService.get_writing_part1(part1_id)


@router.get("/part2/{part2_id}/", response_model=WritingPart2Serializer)
async def get_part2(part2_id: int, user=Depends(active_user)):
    return await WritingService.get_writing_part2(part2_id)
