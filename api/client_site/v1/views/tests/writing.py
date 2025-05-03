from fastapi import APIRouter, HTTPException, status, Form
from typing import List, Optional
from datetime import datetime
from tortoise.exceptions import DoesNotExist
from models.tests.writing import Writing, WritingPart1, WritingPart2
from ...serializers.tests.writing import (
    WritingSerializer,
    WritingPart1Serializer,
    WritingPart2Serializer,
)

router = APIRouter()


@router.get("/", response_model=List[WritingSerializer])
async def get_writing_tests(user_id: int):
    """
    Retrieve all writing tests for a specific user.
    """
    tests = await Writing.filter(user_id=user_id).all()
    if not tests:
        raise HTTPException(status_code=404, detail="No writing tests found for the user")
    return tests


@router.get("/{test_id}/", response_model=WritingSerializer)
async def get_writing_test(test_id: int):
    """
    Retrieve a specific writing test by ID.
    """
    test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
    if not test:
        raise HTTPException(status_code=404, detail="Writing test not found")
    return test


@router.post("/", response_model=WritingSerializer, status_code=status.HTTP_201_CREATED)
async def create_writing_test(user_id: int, start_time: Optional[datetime] = None):
    """
    Create a new writing test for a user.
    """
    test = await Writing.create(
        user_id=user_id,
        start_time=start_time or datetime.utcnow(),
        status="started",
    )
    await WritingPart1.create(writing_id=test.id, content="Part 1 content")
    await WritingPart2.create(writing_id=test.id, content="Part 2 content")
    return test


@router.post("/{test_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_writing_test(
    test_id: int,
    part1_answer: Optional[str] = Form(None),
    part2_answer: Optional[str] = Form(None),
):
    """
    Submit answers for a writing test.
    """
    test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
    if not test:
        raise HTTPException(status_code=404, detail="Writing test not found")

    if test.status == "completed":
        raise HTTPException(status_code=400, detail="This test has already been completed")

    if test.part1:
        test.part1.answer = part1_answer
        await test.part1.save()

    if test.part2:
        test.part2.answer = part2_answer
        await test.part2.save()

    test.status = "completed"
    test.end_time = datetime.utcnow()
    await test.save()

    return {"message": "Writing test submitted successfully"}


@router.post("/{test_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_writing_test(test_id: int):
    """
    Cancel a writing test.
    """
    test = await Writing.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Writing test not found")

    if test.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Test cannot be cancelled")

    test.status = "cancelled"
    await test.save()
    return {"message": "Writing test cancelled successfully"}


@router.get("/part1/{part1_id}/", response_model=WritingPart1Serializer)
async def get_writing_part1(part1_id: int):
    """
    Retrieve details of a specific writing part 1 by ID.
    """
    part1 = await WritingPart1.get_or_none(id=part1_id)
    if not part1:
        raise HTTPException(status_code=404, detail="Writing part 1 not found")
    return part1


@router.get("/part2/{part2_id}/", response_model=WritingPart2Serializer)
async def get_writing_part2(part2_id: int):
    """
    Retrieve details of a specific writing part 2 by ID.
    """
    part2 = await WritingPart2.get_or_none(id=part2_id)
    if not part2:
        raise HTTPException(status_code=404, detail="Writing part 2 not found")
    return part2