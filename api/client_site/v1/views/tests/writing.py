from fastapi import APIRouter, HTTPException, status, Form
from typing import List, Optional
from datetime import datetime, timezone
from models.tests.writing import Writing, WritingPart1, WritingPart2
from ...serializers.tests.writing import (
    WritingSerializer,
    WritingPart1Serializer,
    WritingPart2Serializer,
)
from services.tests.writing_service import WritingService

router = APIRouter()


@router.get("/", response_model=List[WritingSerializer])
async def get_writing_tests(user_id: int):
    return await WritingService.get_writing_tests(user_id)


@router.get("/{test_id}/", response_model=WritingSerializer)
async def get_writing_test(test_id: int):
    return await WritingService.get_writing_test(test_id)


@router.post("/", response_model=WritingSerializer, status_code=status.HTTP_201_CREATED)
async def create_writing_test(user_id: int, start_time: Optional[datetime] = None):
    return await WritingService.create_writing_test(user_id, start_time)


@router.post("/{test_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_writing_test(
    test_id: int,
    part1_answer: Optional[str] = Form(None),
    part2_answer: Optional[str] = Form(None),
):
    return await WritingService.submit_writing_test(test_id, part1_answer, part2_answer)


@router.post("/{test_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_writing_test(test_id: int):
    return await WritingService.cancel_writing_test(test_id)


@router.get("/part1/{part1_id}/", response_model=WritingPart1Serializer)
async def get_writing_part1(part1_id: int):
    return await WritingService.get_writing_part1(part1_id)


@router.get("/part2/{part2_id}/", response_model=WritingPart2Serializer)
async def get_writing_part2(part2_id: int):
    return await WritingService.get_writing_part2(part2_id)